"""AI usage dashboard routes."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.session import get_async_session
from src.common.security import get_current_active_user
from src.auth.models import User
from src.ai_core.usage_limits import AIUsageLimitService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Usage"])


@router.get("/dashboard")
async def get_ai_usage_dashboard(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get AI usage dashboard data."""
    try:
        if not current_user.organizations:
            # Return empty data if user has no organization
            return {
                "usage_summary": {
                    "has_subscription": False,
                    "ai_features_enabled": [],
                    "monthly_credits": 0,
                    "credits_used": 0,
                    "credits_remaining": 0,
                },
                "features_status": {
                    "documents": {"enabled": False, "error": "No organization"},
                    "content": {"enabled": False, "error": "No organization"},
                    "analytics": {"enabled": False, "error": "No organization"},
                },
                "organization_id": None,
            }
        
        organization_id = current_user.organizations[0].id

        service = AIUsageLimitService(db)
        
        # Get usage summary
        usage_summary = await service.get_usage_summary(organization_id)
        
        # Get features status
        features_status = await service.get_ai_features_status(organization_id)
        
        return {
            "usage_summary": usage_summary,
            "features_status": features_status,
            "organization_id": organization_id,
        }

    except Exception as e:
        logger.error(f"AI usage dashboard failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get AI usage dashboard")


@router.get("/limits")
async def get_usage_limits(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get current usage limits and status."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIUsageLimitService(db)
        usage_summary = await service.get_usage_summary(organization_id)
        
        return usage_summary

    except Exception as e:
        logger.error(f"Get usage limits failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get usage limits")


@router.get("/recent-activity")
async def get_recent_ai_activity(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get recent AI activity for the user's organization."""
    try:
        if not current_user.organizations:
            return {
                "activities": [],
                "message": "User must belong to an organization"
            }
        
        organization_id = current_user.organizations[0].id

        # Get recent AI usage logs
        from src.ai_core.usage import AIUsageLog
        from sqlalchemy import select, desc
        from datetime import datetime, timedelta
        
        # Get activities from the last 7 days
        since_date = datetime.utcnow() - timedelta(days=7)
        
        result = await db.execute(
            select(AIUsageLog)
            .where(
                AIUsageLog.organization_id == organization_id,
                AIUsageLog.created_at >= since_date
            )
            .order_by(desc(AIUsageLog.created_at))
            .limit(10)
        )
        
        activities = result.scalars().all()
        
        # Format activities for frontend
        formatted_activities = []
        for activity in activities:
            formatted_activities.append({
                "id": activity.id,
                "feature": activity.feature,
                "operation": activity.operation,
                "tokens_used": activity.total_tokens,
                "cost": activity.cost_usd,
                "created_at": activity.created_at.isoformat(),
                "metadata": activity.metadata or {}
            })
        
        return {
            "activities": formatted_activities,
            "organization_id": organization_id,
        }

    except Exception as e:
        logger.error(f"Get recent AI activity failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recent AI activity")
