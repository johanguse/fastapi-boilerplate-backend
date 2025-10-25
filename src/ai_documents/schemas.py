"""AI Document Intelligence schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AIDocumentBase(BaseModel):
    """Base schema for AI documents."""
    name: str = Field(..., min_length=1, max_length=255)
    mime_type: str = Field(..., min_length=1, max_length=100)


class AIDocumentCreate(AIDocumentBase):
    """Schema for creating AI documents."""
    pass


class AIDocumentUpdate(BaseModel):
    """Schema for updating AI documents."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class AIDocumentResponse(AIDocumentBase):
    """Schema for AI document responses."""
    id: int
    organization_id: int
    uploaded_by: Optional[int]
    file_path: str
    file_size: int
    status: str
    summary: Optional[str]
    key_points: List[str]
    extracted_text: Optional[str]
    metadata: dict
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIDocumentChunkResponse(BaseModel):
    """Schema for document chunk responses."""
    id: int
    document_id: int
    content: str
    chunk_index: int
    created_at: datetime

    class Config:
        from_attributes = True


class AIDocumentChatCreate(BaseModel):
    """Schema for creating document chats."""
    question: str = Field(..., min_length=1, max_length=2000)


class AIDocumentChatResponse(BaseModel):
    """Schema for document chat responses."""
    id: int
    document_id: int
    user_id: int
    question: str
    answer: str
    context_chunks: List[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Schema for document upload responses."""
    document_id: int
    status: str
    message: str


class DocumentProcessingStatus(BaseModel):
    """Schema for document processing status."""
    document_id: int
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
