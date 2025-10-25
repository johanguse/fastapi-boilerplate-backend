"""AI Document Intelligence routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi_pagination import Page, Params
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.session import get_async_session
from src.common.security import get_current_active_user
from src.auth.models import User
from .models import AIDocument, AIDocumentChat
from .schemas import (
    AIDocumentResponse,
    AIDocumentChatCreate,
    AIDocumentChatResponse,
    DocumentUploadResponse,
    DocumentProcessingStatus,
)
from .service import AIDocumentService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a document for AI processing."""
    try:
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not supported"
            )

        # Read file content
        content = await file.read()
        
        # Get user's organization (assuming user belongs to one organization)
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        # Upload document
        service = AIDocumentService(db)
        document = await service.upload_document(
            file_content=content,
            filename=file.filename,
            mime_type=file.content_type,
            organization_id=organization_id,
            user_id=current_user.id,
        )

        return DocumentUploadResponse(
            document_id=document.id,
            status=document.status,
            message="Document uploaded successfully. Processing will begin shortly.",
        )

    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Document upload failed")


@router.get("/", response_model=Page[AIDocumentResponse])
async def get_documents(
    params: Params = Depends(),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get documents for the user's organization."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIDocumentService(db)
        documents = await service.get_documents(
            organization_id=organization_id,
            skip=(params.page - 1) * params.size,
            limit=params.size,
        )

        # Convert to response format
        document_responses = [
            AIDocumentResponse.model_validate(doc) for doc in documents
        ]

        # Create paginated response
        from fastapi_pagination import create_page
        return create_page(
            document_responses,
            total=len(document_responses),  # In production, get total count
            params=params,
        )

    except Exception as e:
        logger.error(f"Get documents failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get documents")


@router.get("/{document_id}", response_model=AIDocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific document."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIDocumentService(db)
        document = await service.get_document(document_id, organization_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return AIDocumentResponse.model_validate(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document")


@router.get("/{document_id}/status", response_model=DocumentProcessingStatus)
async def get_document_status(
    document_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get document processing status."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIDocumentService(db)
        document = await service.get_document(document_id, organization_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentProcessingStatus(
            document_id=document.id,
            status=document.status,
            message=f"Document is {document.status}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document status failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document status")


@router.post("/{document_id}/chat", response_model=AIDocumentChatResponse)
async def chat_with_document(
    document_id: int,
    chat_data: AIDocumentChatCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Chat with a document using AI."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIDocumentService(db)
        chat = await service.chat_with_document(
            document_id=document_id,
            question=chat_data.question,
            user_id=current_user.id,
            organization_id=organization_id,
        )

        return AIDocumentChatResponse.model_validate(chat)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Document chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Document chat failed")


@router.get("/{document_id}/chats", response_model=List[AIDocumentChatResponse])
async def get_document_chats(
    document_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get chat history for a document."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIDocumentService(db)
        chats = await service.get_document_chats(
            document_id=document_id,
            organization_id=organization_id,
        )

        return [AIDocumentChatResponse.model_validate(chat) for chat in chats]

    except Exception as e:
        logger.error(f"Get document chats failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get document chats")


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a document."""
    try:
        if not current_user.organizations:
            raise HTTPException(
                status_code=400,
                detail="User must belong to an organization"
            )
        
        organization_id = current_user.organizations[0].id

        service = AIDocumentService(db)
        deleted = await service.delete_document(document_id, organization_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"message": "Document deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")
