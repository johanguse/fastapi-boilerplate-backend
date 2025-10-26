"""AI billing and usage management service."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Dict, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.usage import AIUsageLog
from src.subscriptions.models import CustomerSubscription, SubscriptionPlan

logger = logging.getLogger(__name__)


class AIBillingService:
    """Service for AI usage billing and credit management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_usage_bill(
        self, organization_id: int, billing_period_start: datetime, billing_period_end: datetime
    ) -> Dict:
        """Calculate AI usage bill for a billing period."""
        try:
            # Get organization's subscription
            subscription = await self._get_active_subscription(organization_id)
            if not subscription:
                return {"error": "No active subscription found"}

            # Get usage for the period
            usage_stats = await self._get_usage_for_period(
                organization_id, billing_period_start, billing_period_end
            )

            # Calculate costs
            total_tokens = usage_stats.get("total_tokens", 0)
            total_cost = usage_stats.get("total_cost", 0.0)

            # Get plan limits
            plan = subscription.plan
            monthly_credits = plan.max_ai_credits_monthly or 0
            credits_used = total_tokens // 1000  # 1 credit = 1000 tokens
            credits_remaining = max(0, monthly_credits - credits_used)

            # Calculate overage
            overage_credits = max(0, credits_used - monthly_credits)
            overage_cost = overage_credits * 0.01  # $0.01 per overage credit

            return {
                "organization_id": organization_id,
                "billing_period": {
                    "start": billing_period_start.isoformat(),
                    "end": billing_period_end.isoformat(),
                },
                "subscription": {
                    "plan_name": plan.name,
                    "monthly_credits": monthly_credits,
                    "credits_used": credits_used,
                    "credits_remaining": credits_remaining,
                },
                "usage": {
                    "total_tokens": total_tokens,
                    "total_cost": total_cost,
                    "overage_credits": overage_credits,
                    "overage_cost": overage_cost,
                },
                "breakdown": usage_stats.get("by_feature", {}),
                "total_bill": total_cost + overage_cost,
            }

        except Exception as e:
            logger.error(f"Usage bill calculation failed: {str(e)}")
            return {"error": str(e)}

    async def get_usage_summary(
        self, organization_id: int, days: int = 30
    ) -> Dict:
        """Get AI usage summary for the last N days."""
        try:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)

            # Get usage stats
            usage_stats = await self._get_usage_for_period(
                organization_id, start_date, end_date
            )

            # Get subscription info
            subscription = await self._get_active_subscription(organization_id)
            plan_name = subscription.plan.name if subscription and subscription.plan else "No Plan"
            monthly_credits = subscription.plan.max_ai_credits_monthly if subscription and subscription.plan else 0

            # Calculate daily averages
            total_tokens = usage_stats.get("total_tokens", 0)
            total_cost = usage_stats.get("total_cost", 0.0)
            daily_avg_tokens = total_tokens / days if days > 0 else 0
            daily_avg_cost = total_cost / days if days > 0 else 0

            # Project monthly usage
            projected_monthly_tokens = daily_avg_tokens * 30
            projected_monthly_cost = daily_avg_cost * 30

            return {
                "organization_id": organization_id,
                "period_days": days,
                "plan_name": plan_name,
                "monthly_credits": monthly_credits,
                "usage": {
                    "total_tokens": total_tokens,
                    "total_cost": total_cost,
                    "daily_avg_tokens": round(daily_avg_tokens, 2),
                    "daily_avg_cost": round(daily_avg_cost, 4),
                    "projected_monthly_tokens": round(projected_monthly_tokens, 2),
                    "projected_monthly_cost": round(projected_monthly_cost, 4),
                },
                "breakdown": usage_stats.get("by_feature", {}),
                "credits_used": total_tokens // 1000,
                "credits_remaining": max(0, monthly_credits - (total_tokens // 1000)),
            }

        except Exception as e:
            logger.error(f"Usage summary failed: {str(e)}")
            return {"error": str(e)}

    async def check_usage_limits(
        self, organization_id: int, feature: str, estimated_tokens: int
    ) -> Tuple[bool, str]:
        """Check if organization can use AI feature within limits."""
        try:
            subscription = await self._get_active_subscription(organization_id)
            if not subscription or not subscription.plan:
                return False, "No active subscription"

            plan = subscription.plan
            monthly_credits = plan.max_ai_credits_monthly or 0

            if monthly_credits <= 0:
                return False, "No AI credits available in your plan"

            # Check if feature is enabled
            ai_features = plan.ai_features_enabled or []
            if feature not in ai_features:
                return False, f"AI feature '{feature}' not available in your plan"

            # Get current month usage
            current_month = datetime.now(UTC)
            usage_stats = await self._get_usage_for_period(
                organization_id,
                current_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                current_month
            )

            current_credits_used = usage_stats.get("total_tokens", 0) // 1000
            estimated_credits_needed = estimated_tokens // 1000

            if current_credits_used + estimated_credits_needed > monthly_credits:
                return False, f"Insufficient credits. Need {estimated_credits_needed}, have {monthly_credits - current_credits_used} remaining"

            return True, "OK"

        except Exception as e:
            logger.error(f"Usage limits check failed: {str(e)}")
            return False, f"Error checking limits: {str(e)}"

    async def get_organization_ai_stats(self, organization_id: int) -> Dict:
        """Get comprehensive AI statistics for an organization."""
        try:
            # Get current month stats
            current_month = datetime.now(UTC)
            month_start = current_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            current_month_usage = await self._get_usage_for_period(
                organization_id, month_start, current_month
            )

            # Get last 7 days stats
            week_ago = current_month - timedelta(days=7)
            week_usage = await self._get_usage_for_period(
                organization_id, week_ago, current_month
            )

            # Get subscription info
            subscription = await self._get_active_subscription(organization_id)
            plan_name = subscription.plan.name if subscription and subscription.plan else "No Plan"
            monthly_credits = subscription.plan.max_ai_credits_monthly if subscription and subscription.plan else 0

            # Calculate trends
            current_tokens = current_month_usage.get("total_tokens", 0)
            week_tokens = week_usage.get("total_tokens", 0)

            # Estimate daily usage from last week
            daily_avg = week_tokens / 7 if week_tokens > 0 else 0
            projected_monthly = daily_avg * 30

            return {
                "organization_id": organization_id,
                "plan_name": plan_name,
                "monthly_credits": monthly_credits,
                "current_month": {
                    "tokens_used": current_tokens,
                    "cost": current_month_usage.get("total_cost", 0),
                    "credits_used": current_tokens // 1000,
                    "credits_remaining": max(0, monthly_credits - (current_tokens // 1000)),
                },
                "last_7_days": {
                    "tokens_used": week_tokens,
                    "cost": week_usage.get("total_cost", 0),
                    "daily_average": round(daily_avg, 2),
                },
                "projections": {
                    "monthly_tokens": round(projected_monthly, 2),
                    "monthly_cost": round(projected_monthly * 0.002, 4),  # Rough cost estimate
                },
                "usage_by_feature": current_month_usage.get("by_feature", {}),
                "status": "active" if subscription else "inactive",
            }

        except Exception as e:
            logger.error(f"AI stats failed: {str(e)}")
            return {"error": str(e)}

    async def _get_active_subscription(self, organization_id: int) -> Optional[CustomerSubscription]:
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

    async def _get_usage_for_period(
        self, organization_id: int, start_date: datetime, end_date: datetime
    ) -> Dict:
        """Get AI usage statistics for a specific period."""
        # Get total usage
        total_result = await self.db.execute(
            select(
                func.sum(AIUsageLog.tokens_used).label('total_tokens'),
                func.sum(AIUsageLog.cost).label('total_cost'),
                func.count(AIUsageLog.id).label('total_operations')
            ).where(
                and_(
                    AIUsageLog.organization_id == organization_id,
                    AIUsageLog.created_at >= start_date,
                    AIUsageLog.created_at <= end_date
                )
            )
        )
        total_stats = total_result.first()

        # Get usage by feature
        feature_result = await self.db.execute(
            select(
                AIUsageLog.feature,
                func.sum(AIUsageLog.tokens_used).label('tokens'),
                func.sum(AIUsageLog.cost).label('cost'),
                func.count(AIUsageLog.id).label('operations')
            ).where(
                and_(
                    AIUsageLog.organization_id == organization_id,
                    AIUsageLog.created_at >= start_date,
                    AIUsageLog.created_at <= end_date
                )
            ).group_by(AIUsageLog.feature)
        )

        by_feature = {}
        for row in feature_result:
            by_feature[row.feature] = {
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0),
                "operations": row.operations or 0,
            }

        return {
            "total_tokens": total_stats.total_tokens or 0,
            "total_cost": float(total_stats.total_cost or 0),
            "total_operations": total_stats.total_operations or 0,
            "by_feature": by_feature,
        }
