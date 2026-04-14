from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel
from src.auth.dependencies import get_current_user_optional

from src.common.config import Settings, get_settings

router = APIRouter(prefix='/chat', tags=['AI Chat'])


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


@router.post('/stream')
async def stream_chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
    # Require user or allow optional? Assuming optional for demo, change if needed
    user=Depends(get_current_user_optional),
):
    """
    Stream chat completions from OpenRouter via standard Server-Sent Events (SSE).
    This format is compatible with TanStack AI and Vercel AI SDK.
    """

    # Ensure OPENROUTER is available
    if not settings.OPENROUTER_API_KEY:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=500, detail='OPENROUTER_API_KEY is not configured'
        )

    client = AsyncOpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=settings.OPENROUTER_API_KEY,
    )

    # Format messages to OpenAI / OpenRouter format
    # E.g. [{"role": "user", "content": "..."}]
    formatted_messages = [msg.model_dump() for msg in request.messages]

    async def generate_chunks() -> AsyncGenerator[str, None]:
        try:
            # We use an appropriate fallback model like the one defined in settings, or a generic open source one
            model = 'anthropic/claude-3.5-sonnet'  # You can change this or map to openrouter variants

            logger.info(f'Starting stream with model: {model}')

            stream = await client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                stream=True,
                max_tokens=settings.AI_MAX_TOKENS,
            )

            # Formatting as Server-Sent Events (SSE) stream text (standard text stream format)
            # TanStack AI's streamText handles these plain text chunks if appropriately structured.
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    content = chunk.choices[0].delta.content
                    if content:
                        # Vercel/TanStack generally accept standard text chunking simply by returning the string chunks
                        yield content

        except Exception as e:
            logger.error(f'Error streaming from OpenRouter: {e}')
            yield f'\n[Error: {str(e)}]'

    return StreamingResponse(
        generate_chunks(),
        media_type='text/plain',  # TanStack default parser handles text/plain text streams
    )
