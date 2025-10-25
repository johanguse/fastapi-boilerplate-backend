"""AI dashboard service for comprehensive AI metrics and insights."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.usage import AIUsageLog
from src.ai_documents.models import AIDocument
from src.ai_content.models import AIContentGeneration
from src.ai_analytics.models import AIAnalyticsQuery
from src.subscriptions.models import CustomerSubscription, SubscriptionPlan
from src.organizations.models import Organization

logger = logging.getLogger(__name__)


class AIDashboardService:
    """Service for AI dashboard metrics and insights."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_overview(self, organization_id: int) -> Dict[str, Any]:
        """Get comprehensive AI dashboard overview."""
        try:
            # Get current month stats
            current_month = datetime.now(UTC)
            month_start = current_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get subscription info
            subscription = await self._get_active_subscription(organization_id)
            plan_name = subscription.plan.name if subscription and subscription.plan else "No Plan"
            monthly_credits = subscription.plan.max_ai_credits_monthly if subscription and subscription.plan else 0
            ai_features = subscription.plan.ai_features_enabled if subscription and subscription.plan else []

            # Get usage stats
            usage_stats = await self._get_usage_for_period(organization_id, month_start, current_month)
            
            # Get feature-specific counts
            documents_count = await self._get_documents_count(organization_id)
            content_generations_count = await self._get_content_generations_count(organization_id)
            analytics_queries_count = await self._get_analytics_queries_count(organization_id)

            # Calculate metrics
            total_tokens = usage_stats.get("total_tokens", 0)
            total_cost = usage_stats.get("total_cost", 0.0)
            credits_used = total_tokens // 1000
            credits_remaining = max(0, monthly_credits - credits_used)

            # Get recent activity
            recent_activity = await self._get_recent_activity(organization_id, limit=10)

            # Get usage trends (last 7 days)
            week_ago = current_month - timedelta(days=7)
            week_usage = await self._get_usage_for_period(organization_id, week_ago, current_month)
            daily_avg = (week_usage.get("total_tokens", 0) / 7) if week_usage.get("total_tokens", 0) > 0 else 0

            return {
                "organization_id": organization_id,
                "subscription": {
                    "plan_name": plan_name,
                    "monthly_credits": monthly_credits,
                    "ai_features_enabled": ai_features,
                    "status": "active" if subscription else "inactive",
                },
                "usage": {
                    "total_tokens": total_tokens,
                    "total_cost": round(total_cost, 4),
                    "credits_used": credits_used,
                    "credits_remaining": credits_remaining,
                    "usage_percentage": round((credits_used / monthly_credits * 100), 2) if monthly_credits > 0 else 0,
                },
                "features": {
                    "documents": {
                        "count": documents_count,
                        "tokens": usage_stats.get("by_feature", {}).get("documents", {}).get("tokens", 0),
                        "cost": usage_stats.get("by_feature", {}).get("documents", {}).get("cost", 0),
                    },
                    "content": {
                        "count": content_generations_count,
                        "tokens": usage_stats.get("by_feature", {}).get("content", {}).get("tokens", 0),
                        "cost": usage_stats.get("by_feature", {}).get("content", {}).get("cost", 0),
                    },
                    "analytics": {
                        "count": analytics_queries_count,
                        "tokens": usage_stats.get("by_feature", {}).get("analytics", {}).get("tokens", 0),
                        "cost": usage_stats.get("by_feature", {}).get("analytics", {}).get("cost", 0),
                    },
                },
                "trends": {
                    "daily_average_tokens": round(daily_avg, 2),
                    "projected_monthly_tokens": round(daily_avg * 30, 2),
                    "projected_monthly_cost": round(daily_avg * 30 * 0.002, 4),
                },
                "recent_activity": recent_activity,
                "last_updated": current_month.isoformat(),
            }

        except Exception as e:
            logger.error(f"Dashboard overview failed: {str(e)}")
            return {"error": str(e)}

    async def get_usage_trends(
        self, organization_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Get AI usage trends over time."""
        try:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)

            # Get daily usage data
            daily_usage = await self._get_daily_usage(organization_id, start_date, end_date)

            # Calculate trends
            total_tokens = sum(day["tokens"] for day in daily_usage)
            total_cost = sum(day["cost"] for day in daily_usage)
            avg_daily_tokens = total_tokens / days if days > 0 else 0

            # Calculate growth rate (comparing first half vs second half)
            mid_point = days // 2
            first_half_tokens = sum(day["tokens"] for day in daily_usage[:mid_point])
            second_half_tokens = sum(day["tokens"] for day in daily_usage[mid_point:])
            
            growth_rate = 0
            if first_half_tokens > 0:
                growth_rate = ((second_half_tokens - first_half_tokens) / first_half_tokens) * 100

            return {
                "organization_id": organization_id,
                "period_days": days,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 4),
                "average_daily_tokens": round(avg_daily_tokens, 2),
                "growth_rate": round(growth_rate, 2),
                "daily_data": daily_usage,
                "trend_direction": "increasing" if growth_rate > 5 else "decreasing" if growth_rate < -5 else "stable",
            }

        except Exception as e:
            logger.error(f"Usage trends failed: {str(e)}")
            return {"error": str(e)}

    async def get_feature_insights(self, organization_id: int) -> Dict[str, Any]:
        """Get insights about AI feature usage patterns."""
        try:
            # Get current month usage by feature
            current_month = datetime.now(UTC)
            month_start = current_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            usage_by_feature = await self._get_usage_by_feature(organization_id, month_start, current_month)

            # Get most used features
            features_sorted = sorted(
                usage_by_feature.items(),
                key=lambda x: x[1]["tokens"],
                reverse=True
            )

            # Get feature efficiency (cost per token)
            feature_efficiency = {}
            for feature, stats in usage_by_feature.items():
                if stats["tokens"] > 0:
                    feature_efficiency[feature] = {
                        "cost_per_token": round(stats["cost"] / stats["tokens"], 6),
                        "tokens_per_operation": round(stats["tokens"] / stats["operations"], 2) if stats["operations"] > 0 else 0,
                    }

            # Get recommendations
            recommendations = self._generate_recommendations(usage_by_feature, features_sorted)

            return {
                "organization_id": organization_id,
                "usage_by_feature": usage_by_feature,
                "most_used_features": [{"feature": f, "tokens": t} for f, t in features_sorted[:3]],
                "feature_efficiency": feature_efficiency,
                "recommendations": recommendations,
                "total_features_used": len(usage_by_feature),
            }

        except Exception as e:
            logger.error(f"Feature insights failed: {str(e)}")
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

    async def _get_daily_usage(
        self, organization_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get daily usage data for trend analysis."""
        result = await self.db.execute(
            select(
                func.date(AIUsageLog.created_at).label('date'),
                func.sum(AIUsageLog.tokens_used).label('tokens'),
                func.sum(AIUsageLog.cost).label('cost'),
                func.count(AIUsageLog.id).label('operations')
            ).where(
                and_(
                    AIUsageLog.organization_id == organization_id,
                    AIUsageLog.created_at >= start_date,
                    AIUsageLog.created_at <= end_date
                )
            ).group_by(func.date(AIUsageLog.created_at))
            .order_by(func.date(AIUsageLog.created_at))
        )

        daily_data = []
        for row in result:
            daily_data.append({
                "date": row.date.isoformat(),
                "tokens": row.tokens or 0,
                "cost": round(float(row.cost or 0), 4),
                "operations": row.operations or 0,
            })

        return daily_data

    async def _get_usage_by_feature(
        self, organization_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """Get detailed usage statistics by feature."""
        result = await self.db.execute(
            select(
                AIUsageLog.feature,
                func.sum(AIUsageLog.tokens_used).label('tokens'),
                func.sum(AIUsageLog.cost).label('cost'),
                func.count(AIUsageLog.id).label('operations'),
                func.avg(AIUsageLog.tokens_used).label('avg_tokens_per_operation')
            ).where(
                and_(
                    AIUsageLog.organization_id == organization_id,
                    AIUsageLog.created_at >= start_date,
                    AIUsageLog.created_at <= end_date
                )
            ).group_by(AIUsageLog.feature)
        )

        usage_by_feature = {}
        for row in result:
            usage_by_feature[row.feature] = {
                "tokens": row.tokens or 0,
                "cost": round(float(row.cost or 0), 4),
                "operations": row.operations or 0,
                "avg_tokens_per_operation": round(float(row.avg_tokens_per_operation or 0), 2),
            }

        return usage_by_feature

    async def _get_documents_count(self, organization_id: int) -> int:
        """Get count of AI documents for organization."""
        result = await self.db.execute(
            select(func.count(AIDocument.id))
            .where(AIDocument.organization_id == organization_id)
        )
        return result.scalar() or 0

    async def _get_content_generations_count(self, organization_id: int) -> int:
        """Get count of AI content generations for organization."""
        result = await self.db.execute(
            select(func.count(AIContentGeneration.id))
            .where(AIContentGeneration.organization_id == organization_id)
        )
        return result.scalar() or 0

    async def _get_analytics_queries_count(self, organization_id: int) -> int:
        """Get count of AI analytics queries for organization."""
        result = await self.db.execute(
            select(func.count(AIAnalyticsQuery.id))
            .where(AIAnalyticsQuery.organization_id == organization_id)
        )
        return result.scalar() or 0

    async def _get_recent_activity(self, organization_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent AI activity for the organization."""
        result = await self.db.execute(
            select(
                AIUsageLog.feature,
                AIUsageLog.operation,
                AIUsageLog.tokens_used,
                AIUsageLog.cost,
                AIUsageLog.created_at
            ).where(AIUsageLog.organization_id == organization_id)
            .order_by(desc(AIUsageLog.created_at))
            .limit(limit)
        )

        activities = []
        for row in result:
            activities.append({
                "feature": row.feature,
                "operation": row.operation,
                "tokens_used": row.tokens_used,
                "cost": round(float(row.cost), 4),
                "created_at": row.created_at.isoformat(),
            })

        return activities

    def _generate_recommendations(
        self, usage_by_feature: Dict, features_sorted: List[Tuple[str, Dict]]
    ) -> List[str]:
        """Generate usage recommendations based on patterns."""
        recommendations = []

        if not usage_by_feature:
            recommendations.append("Start using AI features to see insights and recommendations.")
            return recommendations

        # Check for high-cost features
        for feature, stats in usage_by_feature.items():
            if stats["cost"] > 10:  # High cost threshold
                recommendations.append(
                    f"Consider optimizing {feature} usage - it's your highest cost feature at ${stats['cost']:.2f}"
                )

        # Check for unused features
        all_features = ["documents", "content", "analytics"]
        used_features = set(usage_by_feature.keys())
        unused_features = set(all_features) - used_features
        
        if unused_features:
            recommendations.append(
                f"Try exploring unused AI features: {', '.join(unused_features)}"
            )

        # Check for efficiency
        if len(features_sorted) > 1:
            most_used = features_sorted[0]
            least_used = features_sorted[-1]
            
            if most_used[1]["tokens"] > least_used[1]["tokens"] * 5:
                recommendations.append(
                    f"Consider balancing usage between features. {most_used[0]} is used much more than {least_used[0]}"
                )

        return recommendations
