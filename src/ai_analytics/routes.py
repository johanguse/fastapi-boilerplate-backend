"""AI Analytics routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.session import get_async_session
from src.common.security import get_current_active_user
from src.auth.models import User
from .models import AIAnalyticsQuery
from .schemas import (
    AIAnalyticsQueryCreate,
    AIAnalyticsQueryResponse,
    AnalyticsQueryRequest,
    AnalyticsQueryResponse,
    AnalyticsInsightResponse,
)
from .service import AIAnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Analytics"])


@router.post("/query", response_model=AnalyticsQueryResponse)
async def process_analytics_query(
    request: AnalyticsQueryRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Process a natural language analytics query."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIAnalyticsService(db)
        query_record = await service.process_analytics_query(
            natural_query=request.query,
            organization_id=organization_id,
            user_id=current_user.id,
            chart_type=request.chart_type,
        )

        if query_record.status == 'failed':
            raise HTTPException(
                status_code=400,
                detail=query_record.error_message or "Query processing failed"
            )

        # Generate insights from results
        insights = []
        if query_record.results and query_record.results.get('data'):
            # Convert insights to response format
            insights = [
                AnalyticsInsightResponse(
                    insight=insight.get('insight', ''),
                    chart_type=query_record.chart_config.get('type', 'table'),
                    data=query_record.results,
                    recommendations=[insight.get('recommendation', '')] if insight.get('recommendation') else []
                )
                for insight in query_record.chart_config.get('insights', [])
            ]

        return AnalyticsQueryResponse(
            query_id=query_record.id,
            results=query_record.results,
            chart_config=query_record.chart_config,
            insights=insights,
            tokens_used=query_record.tokens_used,
            cost=query_record.cost,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analytics query failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analytics query failed")


@router.get("/queries", response_model=Page[AIAnalyticsQueryResponse])
async def get_queries(
    params: Params = Depends(),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get analytics queries for the user's organization."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIAnalyticsService(db)
        queries = await service.get_queries(
            organization_id=organization_id,
            skip=(params.page - 1) * params.size,
            limit=params.size,
        )

        # Convert to response format
        query_responses = [
            AIAnalyticsQueryResponse.model_validate(query) for query in queries
        ]

        # Create paginated response
        from fastapi_pagination import create_page
        return create_page(
            query_responses,
            total=len(query_responses),  # In production, get total count
            params=params,
        )

    except Exception as e:
        logger.error(f"Get queries failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get queries")


@router.get("/queries/{query_id}", response_model=AIAnalyticsQueryResponse)
async def get_query(
    query_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific analytics query."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIAnalyticsService(db)
        query = await service.get_query(query_id, organization_id)

        if not query:
            raise HTTPException(status_code=404, detail="Query not found")

        return AIAnalyticsQueryResponse.model_validate(query)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get query failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get query")


@router.get("/stats")
async def get_analytics_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get analytics usage statistics for the user's organization."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIAnalyticsService(db)
        stats = await service.get_organization_stats(organization_id)

        return stats

    except Exception as e:
        logger.error(f"Get analytics stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analytics stats")


@router.get("/insights")
async def get_quick_insights(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get quick insights about the organization's data."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        # Generate some quick insights about the organization
        service = AIAnalyticsService(db)
        
        # This would typically run some predefined queries
        # For now, return placeholder insights
        insights = [
            {
                "title": "AI Usage Overview",
                "description": "Track your AI feature usage across documents, content, and analytics",
                "chart_type": "bar",
                "data": {
                    "labels": ["Documents", "Content", "Analytics"],
                    "values": [15, 23, 8]
                }
            },
            {
                "title": "Monthly Growth",
                "description": "See how your organization's AI usage is growing over time",
                "chart_type": "line",
                "data": {
                    "labels": ["Jan", "Feb", "Mar", "Apr"],
                    "values": [10, 15, 22, 28]
                }
            }
        ]

        return {"insights": insights}

    except Exception as e:
        logger.error(f"Get quick insights failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get quick insights")
