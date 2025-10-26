"""AI provider abstraction layer."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, List, Optional

import tiktoken
from anthropic import Anthropic
from openai import AsyncOpenAI

from src.common.config import settings


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate text from a prompt."""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_text = settings.AI_MODEL_TEXT or "gpt-4-turbo"
        self.model_embeddings = settings.AI_MODEL_EMBEDDINGS or "text-embedding-3-small"

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model_text)
        except KeyError:
            # Fallback to cl100k_base for newer models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate text using OpenAI."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_text,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or settings.AI_MAX_TOKENS,
                temperature=temperature,
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        try:
            response = await self.client.embeddings.create(
                model=self.model_embeddings,
                input=texts,
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            raise Exception(f"OpenAI embeddings error: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.tokenizer.encode(text))

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on OpenAI pricing."""
        # GPT-4 Turbo pricing (as of 2024)
        input_cost_per_1k = 0.01
        output_cost_per_1k = 0.03

        return (input_tokens / 1000 * input_cost_per_1k) + (
            output_tokens / 1000 * output_cost_per_1k
        )


class OpenRouterProvider(AIProvider):
    """OpenRouter provider implementation."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model_text = settings.AI_MODEL_TEXT or "openai/gpt-4-turbo"
        self.model_embeddings = settings.AI_MODEL_EMBEDDINGS or "openai/text-embedding-3-small"

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except KeyError:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate text using OpenRouter."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_text,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or settings.AI_MAX_TOKENS,
                temperature=temperature,
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise Exception(f"OpenRouter API error: {str(e)}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenRouter."""
        try:
            response = await self.client.embeddings.create(
                model=self.model_embeddings,
                input=texts,
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            raise Exception(f"OpenRouter embeddings error: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.tokenizer.encode(text))

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on OpenRouter pricing."""
        # OpenRouter pricing is typically much lower
        # These are rough estimates - actual costs depend on the specific model
        input_cost_per_1k = 0.002  # Much cheaper than direct OpenAI
        output_cost_per_1k = 0.006

        return (input_tokens / 1000 * input_cost_per_1k) + (
            output_tokens / 1000 * output_cost_per_1k
        )


class AnthropicProvider(AIProvider):
    """Anthropic provider implementation."""

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model_text = settings.AI_MODEL_TEXT or "claude-3-5-sonnet-20241022"

    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate text using Anthropic."""
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model_text,
                max_tokens=max_tokens or settings.AI_MAX_TOKENS,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Anthropic doesn't provide embeddings API."""
        raise NotImplementedError(
            "Anthropic doesn't provide embeddings API. Use OpenAI for embeddings."
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens using Anthropic's tokenizer."""
        try:
            # Use Anthropic's tokenizer
            return self.client.count_tokens(text)
        except Exception:
            # Fallback to tiktoken
            tokenizer = tiktoken.get_encoding("cl100k_base")
            return len(tokenizer.encode(text))

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on Anthropic pricing."""
        # Claude 3.5 Sonnet pricing (as of 2024)
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015

        return (input_tokens / 1000 * input_cost_per_1k) + (
            output_tokens / 1000 * output_cost_per_1k
        )


class MockAIProvider(AIProvider):
    """Mock AI provider for development when no API keys are configured."""

    def __init__(self):
        self.name = "Mock Provider"

    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate mock text for development."""
        return f"Mock AI Response: {prompt[:100]}..."

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for development."""
        # Return random embeddings of dimension 1536 (OpenAI's embedding dimension)
        import random
        return [[random.random() for _ in range(1536)] for _ in texts]

    def count_tokens(self, text: str) -> int:
        """Count tokens using simple word count."""
        return len(text.split()) * 1.3  # Rough approximation

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost (free for mock)."""
        return 0.0


def get_ai_provider() -> AIProvider:
    """Get the configured AI provider."""
    try:
        provider_name = getattr(settings, 'AI_PROVIDER', None) or "openai"

        if provider_name.lower() == "openrouter":
            api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
            if not api_key:
                logger.warning("OPENROUTER_API_KEY not set, using mock provider")
                return MockAIProvider()
            return OpenRouterProvider()

        if provider_name.lower() == "anthropic":
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not set, using mock provider")
                return MockAIProvider()
            return AnthropicProvider()

        # Default to OpenAI
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, using mock provider")
            return MockAIProvider()
        return OpenAIProvider()
    except Exception as e:
        logger.error(f"Failed to initialize AI provider: {str(e)}, using mock provider")
        return MockAIProvider()
