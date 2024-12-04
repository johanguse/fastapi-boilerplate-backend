from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.blog import BlogPost
from app.models.user import User
from app.schemas.blog import BlogPostCreate, BlogPostUpdate


async def create_blog_post(
    db: AsyncSession, post: BlogPostCreate, current_user: User
) -> BlogPost:
    db_post = BlogPost(**post.dict(), user_id=current_user.id)
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    return db_post


async def get_blog_posts(db: AsyncSession) -> list[BlogPost]:
    result = await db.execute(
        select(BlogPost).order_by(BlogPost.created_at.desc())
    )
    return result.scalars().all()


async def get_blog_post(db: AsyncSession, post_id: int) -> BlogPost:
    result = await db.execute(select(BlogPost).filter(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail='Blog post not found')
    return post


async def update_blog_post(
    db: AsyncSession, post_id: int, post: BlogPostUpdate, current_user: User
) -> BlogPost:
    db_post = await get_blog_post(db, post_id)

    if db_post.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail='Not authorized to update this post'
        )

    update_data = post.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)

    await db.commit()
    await db.refresh(db_post)
    return db_post


async def delete_blog_post(
    db: AsyncSession, post_id: int, current_user: User
) -> bool:
    db_post = await get_blog_post(db, post_id)

    if db_post.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail='Not authorized to delete this post'
        )

    await db.delete(db_post)
    await db.commit()
    return True
