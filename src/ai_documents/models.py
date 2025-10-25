"""AI Document Intelligence models."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base

if TYPE_CHECKING:
    from src.organizations.models import Organization
    from src.auth.models import User


class AIDocument(Base):
    """AI Document model for storing processed documents."""

    __tablename__ = 'ai_documents'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('organizations.id', ondelete='CASCADE'), index=True
    )
    uploaded_by: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    
    # Document metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Processing status
    status: Mapped[str] = mapped_column(
        String(20), default='pending', index=True
    )  # pending, processing, completed, failed
    
    # AI processing results
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_points: Mapped[dict] = mapped_column(JSON, default=list)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Document metadata
    document_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    organization: Mapped['Organization'] = relationship('Organization')
    uploaded_by_user: Mapped[Optional['User']] = relationship('User')
    chunks: Mapped[list['AIDocumentChunk']] = relationship(
        'AIDocumentChunk', back_populates='document', cascade='all, delete-orphan'
    )
    chats: Mapped[list['AIDocumentChat']] = relationship(
        'AIDocumentChat', back_populates='document', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<AIDocument {self.name} status={self.status}>'


class AIDocumentChunk(Base):
    """Document chunks for RAG (Retrieval Augmented Generation)."""

    __tablename__ = 'ai_document_chunks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('ai_documents.id', ondelete='CASCADE'), index=True
    )
    
    # Chunk content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    
    # Embedding for semantic search (stored as JSON array)
    embedding: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    document: Mapped['AIDocument'] = relationship('AIDocument', back_populates='chunks')

    def __repr__(self) -> str:
        return f'<AIDocumentChunk doc={self.document_id} index={self.chunk_index}>'


class AIDocumentChat(Base):
    """Chat history with documents."""

    __tablename__ = 'ai_document_chats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('ai_documents.id', ondelete='CASCADE'), index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    
    # Chat content
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Context used for answer
    context_chunks: Mapped[dict] = mapped_column(JSON, default=list)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    document: Mapped['AIDocument'] = relationship('AIDocument', back_populates='chats')
    user: Mapped['User'] = relationship('User')

    def __repr__(self) -> str:
        return f'<AIDocumentChat doc={self.document_id} user={self.user_id}>'
