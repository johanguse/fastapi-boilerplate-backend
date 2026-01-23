import logging
from typing import Optional

from fastapi import HTTPException
from fastapi_pagination import Page, paginate
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import UserUpdate
from src.common.pagination import CustomParams

logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email (case-insensitive)"""
    normalized_email = email.strip().lower()
    result = await db.execute(
        select(User).filter(User.normalized_email == normalized_email)
    )
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
    params: CustomParams,
    search: Optional[str] = None,
) -> Page[User]:
    """Get paginated list of users with optional search"""
    query = select(User).order_by(User.created_at.desc())

    if search:
        query = query.filter(
            or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )

    return await paginate(db, query, params)


async def update_user(
    db: AsyncSession,
    user_id: int,
    user_update: UserUpdate,
) -> Optional[User]:
    """Update a user's profile"""
    user = await db.get(User, user_id)
    if not user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        db.add(user)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f'User update failed: {str(e)}')
        raise HTTPException(status_code=400, detail='Database update error')
    await db.refresh(user)

    # Sync billing info to Stripe if billing fields were updated
    billing_fields = [
        'tax_id',
        'address_street',
        'address_city',
        'address_state',
        'address_postal_code',
        'country',
        'company_name',
    ]
    has_billing_update = any(field in update_data for field in billing_fields)

    if has_billing_update:
        try:
            # Import here to avoid circular imports
            from src.subscriptions.models import CustomerSubscription
            from src.subscriptions.service import update_customer_billing_info

            # Find user's Stripe customer ID from their organization's subscription
            result = await db.execute(
                select(CustomerSubscription.stripe_customer_id)
                .join(
                    # Simple approach: get any subscription where user might be related
                    # In production, this should query through organization membership
                    CustomerSubscription
                )
                .limit(1)
            )
            stripe_customer_id = result.scalar_one_or_none()

            if stripe_customer_id:
                await update_customer_billing_info(
                    customer_id=stripe_customer_id,
                    name=user.name,
                    email=user.email,
                    tax_id=user.tax_id,
                    address_line1=user.address_street,
                    address_city=user.address_city,
                    address_state=user.address_state,
                    address_postal_code=user.address_postal_code,
                    address_country=user.country,
                    company_name=user.company_name,
                    user_id=user.id,
                )
        except Exception as e:
            # Don't fail the profile update if Stripe sync fails
            logger.warning(f'Failed to sync billing info to Stripe: {str(e)}')

    return user
