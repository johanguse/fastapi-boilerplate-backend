"""AI usage limits and billing service."""

import logging
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.usage import get_monthly_usage
from src.subscriptions.models import CustomerSubscription, SubscriptionPlan

logger = logging.getLogger(__name__)


class AIUsageLimitService:
    """Service for checking AI usage limits and billing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_usage_limit(
        self, organization_id: int, feature: str
    ) -> tuple[bool, Optional[str]]:
        """Check if organization can use AI feature."""
        try:
            # Get organization's subscription
            subscription = await self._get_organization_subscription(organization_id)
            if not subscription or not subscription.plan:
                return False, "No active subscription"

            plan = subscription.plan

            # Check if feature is enabled for this plan
            ai_features = plan.ai_features_enabled or []
            if feature not in ai_features:
                return False, f"AI feature '{feature}' not available in your plan"

            # Check monthly credit limit
            max_credits = plan.max_ai_credits_monthly or 0
            if max_credits <= 0:
                return False, "No AI credits available in your plan"

            # Get current month usage
            current_month = datetime.now(UTC)
            usage_stats = await get_monthly_usage(
                self.db, organization_id, current_month.year, current_month.month
            )

            total_tokens = usage_stats.get('total_tokens', 0)

            # Convert tokens to credits (1 credit ≈ 1000 tokens)
            credits_used = total_tokens // 1000

            if credits_used >= max_credits:
                return False, f"Monthly AI credit limit reached ({max_credits} credits)"

            return True, None

        except Exception as e:
            logger.error(f"Usage limit check failed: {str(e)}")
            return False, "Error checking usage limits"

    async def get_usage_summary(self, organization_id: int) -> dict:
        """Get AI usage summary for organization."""
        try:
            # Get subscription info
            subscription = await self._get_organization_subscription(organization_id)
            if not subscription or not subscription.plan:
                return {
                    "has_subscription": False,
                    "ai_features_enabled": [],
                    "monthly_credits": 0,
                    "credits_used": 0,
                    "credits_remaining": 0,
                }

            plan = subscription.plan
            current_month = datetime.now(UTC)

            # Get usage stats
            usage_stats = await get_monthly_usage(
                self.db, organization_id, current_month.year, current_month.month
            )

            total_tokens = usage_stats.get('total_tokens', 0)
            credits_used = total_tokens // 1000
            monthly_credits = plan.max_ai_credits_monthly or 0
            credits_remaining = max(0, monthly_credits - credits_used)

            return {
                "has_subscription": True,
                "plan_name": plan.name,
                "ai_features_enabled": plan.ai_features_enabled or [],
                "monthly_credits": monthly_credits,
                "credits_used": credits_used,
                "credits_remaining": credits_remaining,
                "usage_by_feature": usage_stats.get('by_feature', {}),
                "total_cost": usage_stats.get('total_cost', 0),
            }

        except Exception as e:
            logger.error(f"Usage summary failed: {str(e)}")
            return {
                "has_subscription": False,
                "ai_features_enabled": [],
                "monthly_credits": 0,
                "credits_used": 0,
                "credits_remaining": 0,
                "error": str(e),
            }

    async def _get_organization_subscription(
        self, organization_id: int
    ) -> Optional[CustomerSubscription]:
        """Get organization's active subscription."""
        result = await self.db.execute(
            select(CustomerSubscription)
            .join(SubscriptionPlan)
            .where(
                CustomerSubscription.organization_id == organization_id,
                CustomerSubscription.status == 'active'
            )
        )
        return result.scalar_one_or_none()

    async def get_ai_features_status(self, organization_id: int) -> dict:
        """Get status of all AI features for organization."""
        features = ['documents', 'content', 'analytics']
        status = {}

        for feature in features:
            can_use, error = await self.check_usage_limit(organization_id, feature)
            status[feature] = {
                "enabled": can_use,
                "error": error,
            }

        return status
