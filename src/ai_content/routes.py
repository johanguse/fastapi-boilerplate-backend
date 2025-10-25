"""AI Content Generation routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.session import get_async_session
from src.common.security import get_current_active_user
from src.auth.models import User
from .models import AIContentTemplate, AIContentGeneration
from .schemas import (
    AIContentTemplateCreate,
    AIContentTemplateResponse,
    AIContentTemplateUpdate,
    AIContentGenerationResponse,
    ContentGenerationRequest,
    ContentGenerationResponse,
    ContentTemplateRequest,
)
from .service import AIContentService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Content"])


@router.get("/")
async def get_ai_content_info(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get AI Content service information."""
    try:
        if not current_user.organizations:
            return {
                "service": "AI Content Generation",
                "status": "available",
                "organization_id": None,
                "message": "User must belong to an organization to use AI features"
            }
        
        organization_id = current_user.organizations[0].id
        
        # Get basic stats
        service = AIContentService(db)
        stats = await service.get_organization_stats(organization_id)
        
        return {
            "service": "AI Content Generation",
            "status": "available",
            "organization_id": organization_id,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Get AI content info failed: {str(e)}")
        return {
            "service": "AI Content Generation",
            "status": "error",
            "error": str(e)
        }


@router.post("/templates", response_model=AIContentTemplateResponse)
async def create_template(
    template_data: ContentTemplateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new content template."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIContentService(db)
        template = await service.create_template(
            organization_id=organization_id,
            user_id=current_user.id,
            name=template_data.name,
            template_type=template_data.template_type,
            prompt_template=template_data.prompt_template,
            settings=template_data.settings,
        )

        return AIContentTemplateResponse.model_validate(template)

    except Exception as e:
        logger.error(f"Template creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template creation failed")


@router.get("/templates", response_model=Page[AIContentTemplateResponse])
async def get_templates(
    params: Params = Depends(),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get content templates for the user's organization."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIContentService(db)
        try:
            templates = await service.get_templates(
                organization_id=organization_id,
                skip=(params.page - 1) * params.size,
                limit=params.size,
            )
        except Exception as e:
            logger.error(f"Failed to get templates: {str(e)}")
            # Return empty list if there's an error
            templates = []

        # Convert to response format
        template_responses = [
            AIContentTemplateResponse.model_validate(template) for template in templates
        ]

        # Create paginated response
        from fastapi_pagination import create_page
        return create_page(
            template_responses,
            total=len(template_responses),  # In production, get total count
            params=params,
        )

    except Exception as e:
        logger.error(f"Get templates failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get templates")


@router.get("/templates/{template_id}", response_model=AIContentTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific template."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIContentService(db)
        template = await service.get_template(template_id, organization_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return AIContentTemplateResponse.model_validate(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get template failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get template")


@router.put("/templates/{template_id}", response_model=AIContentTemplateResponse)
async def update_template(
    template_id: int,
    template_data: AIContentTemplateUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Update a template."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIContentService(db)
        template = await service.update_template(
            template_id=template_id,
            organization_id=organization_id,
            name=template_data.name,
            prompt_template=template_data.prompt_template,
            settings=template_data.settings,
        )

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return AIContentTemplateResponse.model_validate(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update template failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update template")


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a template."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIContentService(db)
        deleted = await service.delete_template(template_id, organization_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Template not found")

        return {"message": "Template deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete template failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete template")


@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Generate content using AI."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIContentService(db)
        generation = await service.generate_content(
            user_id=current_user.id,
            organization_id=organization_id,
            content_type=request.content_type,
            topic=request.topic,
            tone=request.tone,
            length=request.length,
            language=request.language,
            additional_instructions=request.additional_instructions,
        )

        return ContentGenerationResponse(
            content=generation.output_content,
            tokens_used=generation.tokens_used,
            cost=generation.cost,
            generation_id=generation.id,
        )

    except Exception as e:
        logger.error(f"Content generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Content generation failed")


@router.get("/generations", response_model=Page[AIContentGenerationResponse])
async def get_generations(
    params: Params = Depends(),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get content generation history for the current user."""
    try:
        service = AIContentService(db)
        try:
            generations = await service.get_generations(
                user_id=current_user.id,
                skip=(params.page - 1) * params.size,
                limit=params.size,
            )
        except Exception as e:
            logger.error(f"Failed to get generations: {str(e)}")
            # Return empty list if there's an error
            generations = []

        # Convert to response format
        generation_responses = [
            AIContentGenerationResponse.model_validate(gen) for gen in generations
        ]

        # Create paginated response
        from fastapi_pagination import create_page
        return create_page(
            generation_responses,
            total=len(generation_responses),  # In production, get total count
            params=params,
        )

    except Exception as e:
        logger.error(f"Get generations failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get generations")


@router.get("/generations/{generation_id}", response_model=AIContentGenerationResponse)
async def get_generation(
    generation_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific generation."""
    try:
        service = AIContentService(db)
        generation = await service.get_generation(generation_id, current_user.id)

        if not generation:
            raise HTTPException(status_code=404, detail="Generation not found")

        return AIContentGenerationResponse.model_validate(generation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get generation")


@router.get("/stats")
async def get_content_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get content generation statistics for the user's organization."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIContentService(db)
        stats = await service.get_organization_stats(organization_id)

        return stats

    except Exception as e:
        logger.error(f"Get content stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get content stats")
