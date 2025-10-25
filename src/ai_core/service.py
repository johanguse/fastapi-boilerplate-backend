"""AI service layer with error handling and retries."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from .providers import AIProvider, get_ai_provider
from .usage import track_ai_usage

logger = logging.getLogger(__name__)


class AIService:
    """High-level AI service with error handling and usage tracking."""

    def __init__(self, provider: Optional[AIProvider] = None):
        try:
            self.provider = provider or get_ai_provider()
        except Exception as e:
            logger.error(f"Failed to initialize AI provider: {str(e)}")
            # Create a mock provider for development
            from .providers import MockAIProvider
            self.provider = MockAIProvider()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        feature: str = "text_generation",
        **kwargs: Any,
    ) -> str:
        """Generate text with retry logic and usage tracking."""
        try:
            # Count input tokens
            input_tokens = self.provider.count_tokens(prompt)
            
            # Generate text
            response = await self.provider.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )
            
            # Count output tokens
            output_tokens = self.provider.count_tokens(response)
            
            # Track usage
            if organization_id and user_id:
                cost = self.provider.estimate_cost(input_tokens, output_tokens)
                await track_ai_usage(
                    organization_id=organization_id,
                    user_id=user_id,
                    feature=feature,
                    operation="generate_text",
                    tokens_used=input_tokens + output_tokens,
                    cost=cost,
                )
            
            logger.info(
                f"AI text generation completed: {input_tokens} input, "
                f"{output_tokens} output tokens"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"AI text generation failed: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def generate_embeddings(
        self,
        texts: List[str],
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        feature: str = "embeddings",
    ) -> List[List[float]]:
        """Generate embeddings with retry logic and usage tracking."""
        try:
            # Count tokens
            total_tokens = sum(self.provider.count_tokens(text) for text in texts)
            
            # Generate embeddings
            embeddings = await self.provider.generate_embeddings(texts)
            
            # Track usage
            if organization_id and user_id:
                cost = self.provider.estimate_cost(total_tokens, 0)
                await track_ai_usage(
                    organization_id=organization_id,
                    user_id=user_id,
                    feature=feature,
                    operation="generate_embeddings",
                    tokens_used=total_tokens,
                    cost=cost,
                )
            
            logger.info(f"AI embeddings generated: {len(texts)} texts, {total_tokens} tokens")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"AI embeddings generation failed: {str(e)}")
            raise

    async def summarize_text(
        self,
        text: str,
        max_length: int = 200,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> str:
        """Summarize text using AI."""
        prompt = f"""Please provide a concise summary of the following text in no more than {max_length} words:

{text}

Summary:"""
        
        return await self.generate_text(
            prompt=prompt,
            max_tokens=max_length * 2,  # Rough estimate
            temperature=0.3,  # Lower temperature for more consistent summaries
            organization_id=organization_id,
            user_id=user_id,
            feature="summarization",
        )

    async def extract_key_points(
        self,
        text: str,
        max_points: int = 5,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> List[str]:
        """Extract key points from text."""
        prompt = f"""Extract the {max_points} most important key points from the following text. Return them as a numbered list:

{text}

Key points:"""
        
        response = await self.generate_text(
            prompt=prompt,
            max_tokens=max_points * 50,  # Rough estimate
            temperature=0.3,
            organization_id=organization_id,
            user_id=user_id,
            feature="key_points_extraction",
        )
        
        # Parse numbered list
        points = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering
                point = line.split('.', 1)[-1].strip()
                if point:
                    points.append(point)
        
        return points[:max_points]

    async def chat_with_context(
        self,
        question: str,
        context: str,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> str:
        """Answer a question based on provided context."""
        prompt = f"""Based on the following context, please answer the question. If the answer cannot be found in the context, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        return await self.generate_text(
            prompt=prompt,
            temperature=0.3,
            organization_id=organization_id,
            user_id=user_id,
            feature="chat_with_context",
        )

    async def generate_content(
        self,
        content_type: str,
        topic: str,
        tone: str = "professional",
        length: str = "medium",
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> str:
        """Generate content based on type and parameters."""
        prompts = {
            "blog_post": f"""Write a {tone} blog post about "{topic}". 
            Length: {length}. Include an engaging title, introduction, main points, and conclusion.""",
            
            "email": f"""Write a {tone} email about "{topic}". 
            Length: {length}. Make it engaging and actionable.""",
            
            "social_media": f"""Write a {tone} social media post about "{topic}". 
            Length: {length}. Make it engaging and include relevant hashtags.""",
            
            "product_description": f"""Write a {tone} product description for "{topic}". 
            Length: {length}. Highlight key features and benefits.""",
        }
        
        prompt = prompts.get(content_type, f"Write {tone} content about {topic}")
        
        return await self.generate_text(
            prompt=prompt,
            temperature=0.7,
            organization_id=organization_id,
            user_id=user_id,
            feature="content_generation",
        )
