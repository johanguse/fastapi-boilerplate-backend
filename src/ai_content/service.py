"""AI Content Generation service."""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.service import AIService

from .models import AIContentGeneration, AIContentTemplate

logger = logging.getLogger(__name__)


class AIContentService:
    """Service for AI content generation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        try:
            self.ai_service = AIService()
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {str(e)}")
            self.ai_service = None

    async def create_template(
        self,
        organization_id: int,
        user_id: int,
        name: str,
        template_type: str,
        prompt_template: str,
        settings: dict = None,
    ) -> AIContentTemplate:
        """Create a new content template."""
        template = AIContentTemplate(
            organization_id=organization_id,
            created_by=user_id,
            name=name,
            template_type=template_type,
            prompt_template=prompt_template,
            settings=settings or {},
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        return template

    async def get_templates(
        self, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[AIContentTemplate]:
        """Get content templates for organization."""
        result = await self.db.execute(
            select(AIContentTemplate)
            .where(
                AIContentTemplate.organization_id == organization_id,
                AIContentTemplate.is_active == True
            )
            .offset(skip)
            .limit(limit)
            .order_by(AIContentTemplate.created_at.desc())
        )
        return result.scalars().all()

    async def get_template(
        self, template_id: int, organization_id: int
    ) -> Optional[AIContentTemplate]:
        """Get a specific template."""
        result = await self.db.execute(
            select(AIContentTemplate).where(
                AIContentTemplate.id == template_id,
                AIContentTemplate.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def update_template(
        self,
        template_id: int,
        organization_id: int,
        name: Optional[str] = None,
        prompt_template: Optional[str] = None,
        settings: Optional[dict] = None,
    ) -> Optional[AIContentTemplate]:
        """Update a template."""
        result = await self.db.execute(
            select(AIContentTemplate).where(
                AIContentTemplate.id == template_id,
                AIContentTemplate.organization_id == organization_id
            )
        )
        template = result.scalar_one_or_none()

        if template:
            if name is not None:
                template.name = name
            if prompt_template is not None:
                template.prompt_template = prompt_template
            if settings is not None:
                template.settings = settings

            await self.db.commit()
            await self.db.refresh(template)

        return template

    async def delete_template(
        self, template_id: int, organization_id: int
    ) -> bool:
        """Delete a template (soft delete)."""
        result = await self.db.execute(
            select(AIContentTemplate).where(
                AIContentTemplate.id == template_id,
                AIContentTemplate.organization_id == organization_id
            )
        )
        template = result.scalar_one_or_none()

        if template:
            template.is_active = False
            await self.db.commit()
            return True

        return False

    async def generate_content(
        self,
        user_id: int,
        organization_id: int,
        content_type: str,
        topic: str,
        tone: str = "professional",
        length: str = "medium",
        language: str = "en",
        additional_instructions: Optional[str] = None,
        template_id: Optional[int] = None,
    ) -> AIContentGeneration:
        """Generate content using AI."""
        try:
            # Build prompt
            prompt = await self._build_prompt(
                content_type=content_type,
                topic=topic,
                tone=tone,
                length=length,
                language=language,
                additional_instructions=additional_instructions,
                template_id=template_id,
                organization_id=organization_id,
            )

            # Generate content
            if self.ai_service and self.ai_service.provider:
                content = await self.ai_service.generate_text(
                    prompt=prompt,
                    organization_id=organization_id,
                    user_id=user_id,
                    feature="content_generation",
                )
            else:
                # Fallback for development when AI service is not available
                content = f"Mock AI Content: {content_type} about {topic} in {tone} tone"

            # Count tokens (rough estimate)
            if self.ai_service and self.ai_service.provider:
                tokens_used = self.ai_service.provider.count_tokens(prompt + content)
                cost = self.ai_service.provider.estimate_cost(
                    len(prompt.split()), len(content.split())
                )
            else:
                # Fallback for development
                tokens_used = len((prompt + content).split()) * 1.3
                cost = 0.0

            # Save generation
            generation = AIContentGeneration(
                user_id=user_id,
                template_id=template_id,
                content_type=content_type,
                input_data={
                    "topic": topic,
                    "tone": tone,
                    "length": length,
                    "language": language,
                    "additional_instructions": additional_instructions,
                },
                output_content=content,
                tokens_used=tokens_used,
                cost=cost,
            )

            self.db.add(generation)
            await self.db.commit()
            await self.db.refresh(generation)

            return generation

        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise

    async def _build_prompt(
        self,
        content_type: str,
        topic: str,
        tone: str,
        length: str,
        language: str,
        additional_instructions: Optional[str],
        template_id: Optional[int],
        organization_id: int,
    ) -> str:
        """Build prompt for content generation."""
        # Try to use template if provided
        if template_id:
            template = await self.get_template(template_id, organization_id)
            if template:
                return template.prompt_template.format(
                    topic=topic,
                    tone=tone,
                    length=length,
                    language=language,
                    additional_instructions=additional_instructions or "",
                )

        # Use default prompts
        prompts = {
            "blog_post": f"""Write a {tone} blog post about "{topic}". 
            Length: {length}. Language: {language}.
            Include an engaging title, introduction, main points, and conclusion.
            {additional_instructions or ""}""",

            "email": f"""Write a {tone} email about "{topic}". 
            Length: {length}. Language: {language}.
            Make it engaging and actionable.
            {additional_instructions or ""}""",

            "social_media": f"""Write a {tone} social media post about "{topic}". 
            Length: {length}. Language: {language}.
            Make it engaging and include relevant hashtags.
            {additional_instructions or ""}""",

            "product_description": f"""Write a {tone} product description for "{topic}". 
            Length: {length}. Language: {language}.
            Highlight key features and benefits.
            {additional_instructions or ""}""",

            "marketing_copy": f"""Write {tone} marketing copy about "{topic}". 
            Length: {length}. Language: {language}.
            Focus on benefits and call-to-action.
            {additional_instructions or ""}""",
        }

        return prompts.get(content_type, f"Write {tone} content about {topic}")

    async def get_generations(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[AIContentGeneration]:
        """Get content generation history for user."""
        result = await self.db.execute(
            select(AIContentGeneration)
            .where(AIContentGeneration.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(AIContentGeneration.created_at.desc())
        )
        return result.scalars().all()

    async def get_generation(
        self, generation_id: int, user_id: int
    ) -> Optional[AIContentGeneration]:
        """Get a specific generation."""
        result = await self.db.execute(
            select(AIContentGeneration).where(
                AIContentGeneration.id == generation_id,
                AIContentGeneration.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_organization_stats(
        self, organization_id: int
    ) -> dict:
        """Get content generation stats for organization."""
        from sqlalchemy import func

        result = await self.db.execute(
            select(
                func.count(AIContentGeneration.id).label('total_generations'),
                func.sum(AIContentGeneration.tokens_used).label('total_tokens'),
                func.sum(AIContentGeneration.cost).label('total_cost'),
            ).join(AIContentTemplate).where(
                AIContentTemplate.organization_id == organization_id
            )
        )
        stats = result.first()

        return {
            "total_generations": stats.total_generations or 0,
            "total_tokens": stats.total_tokens or 0,
            "total_cost": float(stats.total_cost or 0),
        }
