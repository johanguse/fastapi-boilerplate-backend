"""AI Document Intelligence service."""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import List, Optional, Tuple

from docx import Document as DocxDocument
from pypdf import PdfReader
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.service import AIService
from src.ai_core.usage import track_ai_usage
from src.common.config import settings
from src.utils.storage import upload_file_to_r2
from .models import AIDocument, AIDocumentChunk, AIDocumentChat

logger = logging.getLogger(__name__)


class AIDocumentService:
    """Service for AI document processing."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        organization_id: int,
        user_id: int,
    ) -> AIDocument:
        """Upload and create document record."""
        # Upload to R2 storage (with fallback for development)
        file_path = None
        try:
            if settings.R2_ENDPOINT_URL and settings.R2_ACCESS_KEY_ID and settings.R2_SECRET_ACCESS_KEY:
                file_path = await upload_file_to_r2(
                    file_content=file_content,
                    filename=filename,
                    bucket_name=settings.R2_BUCKET_NAME,
                )
            else:
                logger.warning("R2 storage not configured, using mock file path for development")
                file_path = f"mock://storage/{filename}"
        except Exception as e:
            logger.error(f"Failed to upload to R2: {str(e)}, using mock file path")
            file_path = f"mock://storage/{filename}"

        # Create document record
        document = AIDocument(
            organization_id=organization_id,
            uploaded_by=user_id,
            name=filename,
            file_path=file_path,
            file_size=len(file_content),
            mime_type=mime_type,
            status='pending',
        )

        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        # Start processing in background
        asyncio.create_task(
            self._process_document(document.id, organization_id, user_id)
        )

        return document

    async def _process_document(
        self, document_id: int, organization_id: int, user_id: int
    ) -> None:
        """Process document with AI (background task)."""
        try:
            # Get document
            result = await self.db.execute(
                select(AIDocument).where(AIDocument.id == document_id)
            )
            document = result.scalar_one()

            # Update status
            document.status = 'processing'
            await self.db.commit()

            # Extract text based on file type
            extracted_text = await self._extract_text(document.file_path, document.mime_type)
            
            if not extracted_text:
                raise ValueError("Could not extract text from document")

            document.extracted_text = extracted_text
            document.status = 'completed'
            document.processed_at = datetime.now(UTC)
            await self.db.commit()

            # Generate AI insights
            await self._generate_ai_insights(document, organization_id, user_id)

            # Create chunks for RAG
            await self._create_document_chunks(document, organization_id, user_id)

            logger.info(f"Document {document_id} processed successfully")

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            # Update status to failed
            result = await self.db.execute(
                select(AIDocument).where(AIDocument.id == document_id)
            )
            document = result.scalar_one()
            document.status = 'failed'
            await self.db.commit()

    async def _extract_text(self, file_path: str, mime_type: str) -> str:
        """Extract text from different file types."""
        # This would need to be implemented based on your storage setup
        # For now, return placeholder
        return "Extracted text from document"

    async def _generate_ai_insights(
        self, document: AIDocument, organization_id: int, user_id: int
    ) -> None:
        """Generate AI insights for the document."""
        try:
            # Generate summary
            summary = await self.ai_service.summarize_text(
                text=document.extracted_text or "",
                max_length=200,
                organization_id=organization_id,
                user_id=user_id,
            )

            # Extract key points
            key_points = await self.ai_service.extract_key_points(
                text=document.extracted_text or "",
                max_points=5,
                organization_id=organization_id,
                user_id=user_id,
            )

            # Update document
            document.summary = summary
            document.key_points = key_points
            await self.db.commit()

        except Exception as e:
            logger.error(f"AI insights generation failed: {str(e)}")

    async def _create_document_chunks(
        self, document: AIDocument, organization_id: int, user_id: int
    ) -> None:
        """Create document chunks for RAG."""
        try:
            text = document.extracted_text or ""
            if not text:
                return

            # Split text into chunks (simple approach)
            chunk_size = 1000  # characters
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

            # Generate embeddings for chunks
            embeddings = await self.ai_service.generate_embeddings(
                texts=chunks,
                organization_id=organization_id,
                user_id=user_id,
            )

            # Create chunk records
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk = AIDocumentChunk(
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=i,
                    embedding=embedding,
                )
                self.db.add(chunk)

            await self.db.commit()

        except Exception as e:
            logger.error(f"Document chunking failed: {str(e)}")

    async def chat_with_document(
        self,
        document_id: int,
        question: str,
        user_id: int,
        organization_id: int,
    ) -> AIDocumentChat:
        """Chat with document using RAG."""
        try:
            # Get document
            result = await self.db.execute(
                select(AIDocument).where(AIDocument.id == document_id)
            )
            document = result.scalar_one()

            if document.status != 'completed':
                raise ValueError("Document not ready for chat")

            # Find relevant chunks using semantic search
            relevant_chunks = await self._find_relevant_chunks(
                document_id, question, organization_id, user_id
            )

            # Build context
            context = "\n\n".join([chunk.content for chunk in relevant_chunks])

            # Generate answer
            answer = await self.ai_service.chat_with_context(
                question=question,
                context=context,
                organization_id=organization_id,
                user_id=user_id,
            )

            # Save chat
            chat = AIDocumentChat(
                document_id=document_id,
                user_id=user_id,
                question=question,
                answer=answer,
                context_chunks=[{"id": chunk.id, "content": chunk.content} for chunk in relevant_chunks],
            )

            self.db.add(chat)
            await self.db.commit()
            await self.db.refresh(chat)

            return chat

        except Exception as e:
            logger.error(f"Document chat failed: {str(e)}")
            raise

    async def _find_relevant_chunks(
        self, document_id: int, question: str, organization_id: int, user_id: int
    ) -> List[AIDocumentChunk]:
        """Find relevant chunks using semantic search."""
        try:
            # Generate embedding for question
            question_embeddings = await self.ai_service.generate_embeddings(
                texts=[question],
                organization_id=organization_id,
                user_id=user_id,
            )
            question_embedding = question_embeddings[0]

            # Get all chunks for document
            result = await self.db.execute(
                select(AIDocumentChunk).where(AIDocumentChunk.document_id == document_id)
            )
            chunks = result.scalars().all()

            # Simple cosine similarity (in production, use pgvector)
            scored_chunks = []
            for chunk in chunks:
                if chunk.embedding:
                    similarity = self._cosine_similarity(question_embedding, chunk.embedding)
                    scored_chunks.append((similarity, chunk))

            # Sort by similarity and return top 3
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            return [chunk for _, chunk in scored_chunks[:3]]

        except Exception as e:
            logger.error(f"Chunk search failed: {str(e)}")
            # Fallback: return first few chunks
            result = await self.db.execute(
                select(AIDocumentChunk)
                .where(AIDocumentChunk.document_id == document_id)
                .limit(3)
            )
            return result.scalars().all()

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)

    async def get_documents(
        self, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[AIDocument]:
        """Get documents for organization."""
        result = await self.db.execute(
            select(AIDocument)
            .where(AIDocument.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .order_by(AIDocument.created_at.desc())
        )
        return result.scalars().all()

    async def get_document(self, document_id: int, organization_id: int) -> Optional[AIDocument]:
        """Get single document."""
        result = await self.db.execute(
            select(AIDocument).where(
                AIDocument.id == document_id,
                AIDocument.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def get_document_chats(
        self, document_id: int, organization_id: int, skip: int = 0, limit: int = 50
    ) -> List[AIDocumentChat]:
        """Get chat history for document."""
        result = await self.db.execute(
            select(AIDocumentChat)
            .join(AIDocument)
            .where(
                AIDocumentChat.document_id == document_id,
                AIDocument.organization_id == organization_id
            )
            .offset(skip)
            .limit(limit)
            .order_by(AIDocumentChat.created_at.desc())
        )
        return result.scalars().all()

    async def delete_document(self, document_id: int, organization_id: int) -> bool:
        """Delete document."""
        result = await self.db.execute(
            select(AIDocument).where(
                AIDocument.id == document_id,
                AIDocument.organization_id == organization_id
            )
        )
        document = result.scalar_one_or_none()
        
        if document:
            await self.db.delete(document)
            await self.db.commit()
            return True
        
        return False
