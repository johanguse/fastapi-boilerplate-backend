"""AI Content Generation schemas."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AIContentTemplateBase(BaseModel):
    """Base schema for AI content templates."""
    name: str = Field(..., min_length=1, max_length=255)
    template_type: str = Field(..., min_length=1, max_length=50)
    prompt_template: str = Field(..., min_length=1)
    settings: Dict = Field(default_factory=dict)


class AIContentTemplateCreate(AIContentTemplateBase):
    """Schema for creating AI content templates."""
    pass


class AIContentTemplateUpdate(BaseModel):
    """Schema for updating AI content templates."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    prompt_template: Optional[str] = Field(None, min_length=1)
    settings: Optional[Dict] = None


class AIContentTemplateResponse(AIContentTemplateBase):
    """Schema for AI content template responses."""
    id: int
    organization_id: int
    created_by: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIContentGenerationCreate(BaseModel):
    """Schema for creating AI content generations."""
    content_type: str = Field(..., min_length=1, max_length=50)
    input_data: Dict = Field(default_factory=dict)
    template_id: Optional[int] = None


class AIContentGenerationResponse(BaseModel):
    """Schema for AI content generation responses."""
    id: int
    user_id: int
    template_id: Optional[int]
    content_type: str
    input_data: Dict
    output_content: str
    tokens_used: int
    cost: float
    created_at: datetime

    class Config:
        from_attributes = True


class ContentGenerationRequest(BaseModel):
    """Schema for content generation requests."""
    content_type: str = Field(..., min_length=1, max_length=50)
    topic: str = Field(..., min_length=1, max_length=500)
    tone: str = Field(default="professional", max_length=50)
    length: str = Field(default="medium", max_length=50)
    language: str = Field(default="en", max_length=10)
    additional_instructions: Optional[str] = Field(None, max_length=1000)


class ContentGenerationResponse(BaseModel):
    """Schema for content generation responses."""
    content: str
    tokens_used: int
    cost: float
    generation_id: int


class ContentTemplateRequest(BaseModel):
    """Schema for creating content templates."""
    name: str = Field(..., min_length=1, max_length=255)
    template_type: str = Field(..., min_length=1, max_length=50)
    prompt_template: str = Field(..., min_length=1)
    settings: Dict = Field(default_factory=dict)
