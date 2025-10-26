"""AI billing and usage routes."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.security import get_current_active_user
from src.common.session import get_async_session

from .billing import AIBillingService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Billing"])


@router.get("/usage-summary")
async def get_usage_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get AI usage summary for the last N days."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )

        organization_id = current_user.organizations[0].id

        service = AIBillingService(db)
        summary = await service.get_usage_summary(organization_id, days)

        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Usage summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get usage summary")


@router.get("/billing-period")
async def get_billing_period(
    start_date: str = Query(..., description="Start date in ISO format"),
    end_date: str = Query(..., description="End date in ISO format"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get AI usage bill for a specific billing period."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )

        organization_id = current_user.organizations[0].id

        # Parse dates
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")

        service = AIBillingService(db)
        bill = await service.calculate_usage_bill(organization_id, start_dt, end_dt)

        if "error" in bill:
            raise HTTPException(status_code=500, detail=bill["error"])

        return bill

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Billing period failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get billing period")


@router.get("/stats")
async def get_ai_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get comprehensive AI statistics for the organization."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )

        organization_id = current_user.organizations[0].id

        service = AIBillingService(db)
        stats = await service.get_organization_ai_stats(organization_id)

        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get AI stats")


@router.get("/check-limits")
async def check_usage_limits(
    feature: str = Query(..., description="AI feature name"),
    estimated_tokens: int = Query(..., ge=1, description="Estimated tokens needed"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Check if organization can use AI feature within limits."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )

        organization_id = current_user.organizations[0].id

        service = AIBillingService(db)
        can_use, message = await service.check_usage_limits(
            organization_id, feature, estimated_tokens
        )

        return {
            "can_use": can_use,
            "message": message,
            "feature": feature,
            "estimated_tokens": estimated_tokens,
        }

    except Exception as e:
        logger.error(f"Check limits failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check usage limits")


@router.get("/monthly-report")
async def get_monthly_report(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get detailed monthly AI usage report."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )

        organization_id = current_user.organizations[0].id

        # Calculate month boundaries
        month_start = datetime(year, month, 1, tzinfo=UTC)
        if month == 12:
            month_end = datetime(year + 1, 1, 1, tzinfo=UTC) - timedelta(seconds=1)
        else:
            month_end = datetime(year, month + 1, 1, tzinfo=UTC) - timedelta(seconds=1)

        service = AIBillingService(db)
        report = await service.calculate_usage_bill(organization_id, month_start, month_end)

        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])

        # Add additional report data
        report["report_type"] = "monthly"
        report["year"] = year
        report["month"] = month
        report["generated_at"] = datetime.now(UTC).isoformat()

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Monthly report failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate monthly report")
