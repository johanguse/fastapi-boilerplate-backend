"""AI dashboard routes for comprehensive metrics and insights."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.security import get_current_active_user
from src.common.session import get_async_session

from .dashboard import AIDashboardService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Dashboard"])


@router.get("/overview")
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get comprehensive AI dashboard overview."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )

        organization_id = current_user.organizations[0].id

        service = AIDashboardService(db)
        overview = await service.get_dashboard_overview(organization_id)

        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])

        return overview

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard overview failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard overview")


@router.get("/trends")
async def get_usage_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get AI usage trends over time."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )

        organization_id = current_user.organizations[0].id

        service = AIDashboardService(db)
        trends = await service.get_usage_trends(organization_id, days)

        if "error" in trends:
            raise HTTPException(status_code=500, detail=trends["error"])

        return trends

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Usage trends failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get usage trends")


@router.get("/insights")
async def get_feature_insights(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get AI feature usage insights and recommendations."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )

        organization_id = current_user.organizations[0].id

        service = AIDashboardService(db)
        insights = await service.get_feature_insights(organization_id)

        if "error" in insights:
            raise HTTPException(status_code=500, detail=insights["error"])

        return insights

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature insights failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feature insights")


@router.get("/metrics")
async def get_ai_metrics(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get key AI metrics for quick overview."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )

        organization_id = current_user.organizations[0].id

        service = AIDashboardService(db)
        overview = await service.get_dashboard_overview(organization_id)

        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])

        # Extract key metrics
        metrics = {
            "credits_used": overview["usage"]["credits_used"],
            "credits_remaining": overview["usage"]["credits_remaining"],
            "usage_percentage": overview["usage"]["usage_percentage"],
            "total_cost": overview["usage"]["total_cost"],
            "plan_name": overview["subscription"]["plan_name"],
            "features_enabled": len(overview["subscription"]["ai_features_enabled"]),
            "total_operations": sum(
                feature["count"] for feature in overview["features"].values()
            ),
            "status": overview["subscription"]["status"],
        }

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI metrics failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get AI metrics")
