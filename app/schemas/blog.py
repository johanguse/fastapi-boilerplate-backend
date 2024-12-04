from datetime import datetime

from pydantic import BaseModel


class BlogPostBase(BaseModel):
    title: str
    content: str


class BlogPostCreate(BlogPostBase):
    pass


class BlogPostUpdate(BlogPostBase):
    title: str | None = None
    content: str | None = None


class BlogPost(BlogPostBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
