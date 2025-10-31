"""
Onboarding routes for user profile completion and organization setup.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import (
    OnboardingComplete,
    OnboardingProfileUpdate,
    OnboardingStepUpdate,
)
from src.common.security import get_current_active_user
from src.common.session import get_async_session
from src.common.utils import translate_message
from src.organizations.models import Organization, OrganizationMember
from src.organizations.schemas import OrganizationCreate
from src.organizations.service import (
    create_organization as create_organization_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/onboarding/status')
async def get_onboarding_status(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get the current onboarding status for the user."""
    # Check if user has any organizations
    result = await session.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
    )
    has_organization = result.scalar_one_or_none() is not None

    return {
        'user_id': current_user.id,
        'onboarding_completed': current_user.onboarding_completed,
        'onboarding_step': current_user.onboarding_step,
        'has_organization': has_organization,
        'profile_complete': bool(
            current_user.name and
            current_user.company and
            current_user.country
        ),
        'next_step': _get_next_onboarding_step(current_user, has_organization)
    }


@router.patch('/onboarding/profile')
async def update_onboarding_profile(
    profile_data: OnboardingProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update user profile during onboarding."""
    try:
        # Update user fields
        for field, value in profile_data.model_dump(exclude_unset=True).items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)

        # Update onboarding step
        current_user.onboarding_step = max(current_user.onboarding_step, 1)

        await session.commit()
        await session.refresh(current_user)

        logger.info(f'Updated onboarding profile for user {current_user.id}')

        return {
            'success': True,
            'message': translate_message('success.updated', request),
            'user': {
                'id': current_user.id,
                'name': current_user.name,
                'company': current_user.company,
                'country': current_user.country,
                'onboarding_step': current_user.onboarding_step
            }
        }

    except Exception as e:
        logger.exception(f'Error updating onboarding profile for user {current_user.id}: {str(e)}')
        error_msg = translate_message('onboarding.profile_update_failed', request)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@router.post('/onboarding/organization')
async def create_onboarding_organization(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Create user's first organization during onboarding."""
    try:
        # Parse request body
        try:
            body = await request.json()
        except Exception:
            body = {}

        # Use company name or default to user's name
        org_name = body.get('name') or current_user.company or f"{current_user.name}'s Organization"
        org_slug = body.get('slug')

        # Create organization
        org_create = OrganizationCreate(name=org_name, slug=org_slug)
        organization = await create_organization_service(session, org_create, current_user)

        # Update onboarding step
        current_user.onboarding_step = max(current_user.onboarding_step, 2)

        await session.commit()
        await session.refresh(current_user)

        logger.info(f'Created onboarding organization for user {current_user.id}: {organization.name}')

        return {
            'success': True,
            'message': translate_message('organization.created', request),
            'organization': {
                'id': organization.id,
                'name': organization.name,
                'slug': organization.slug
            },
            'onboarding_step': current_user.onboarding_step
        }

    except Exception as e:
        logger.exception(f'Error creating onboarding organization for user {current_user.id}: {str(e)}')
        error_msg = translate_message('organization.failed_to_create', request)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@router.patch('/onboarding/step')
async def update_onboarding_step(
    step_data: OnboardingStepUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update the current onboarding step."""
    try:
        current_user.onboarding_step = step_data.step
        if step_data.completed:
            current_user.onboarding_completed = True

        await session.commit()
        await session.refresh(current_user)

        logger.info(f'Updated onboarding step for user {current_user.id} to step {step_data.step}')

        return {
            'success': True,
            'message': translate_message('success.updated', request),
            'onboarding_step': current_user.onboarding_step,
            'onboarding_completed': current_user.onboarding_completed
        }

    except Exception as e:
        logger.exception(f'Error updating onboarding step for user {current_user.id}: {str(e)}')
        error_msg = translate_message('onboarding.step_update_failed', request)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@router.post('/onboarding/complete')
async def complete_onboarding(
    completion_data: OnboardingComplete,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Mark onboarding as completed and send welcome email."""
    try:
        current_user.onboarding_completed = True
        current_user.onboarding_step = 3  # Final step

        await session.commit()
        await session.refresh(current_user)

        logger.info(f'Completed onboarding for user {current_user.id}')

        # Send welcome email after onboarding completion
        try:
            from src.services.email_service import email_service
            welcome_sent = await email_service.send_welcome_email(
                current_user.email, current_user.name, is_onboarding=True
            )
            if welcome_sent:
                logger.info(f'Welcome email sent to {current_user.email} after onboarding completion')
            else:
                logger.warning(f'Failed to send welcome email to {current_user.email} after onboarding completion')
        except Exception as e:
            # Don't fail onboarding completion if welcome email fails
            logger.exception(f'Exception sending welcome email to {current_user.email} after onboarding completion: {str(e)}')

        return {
            'success': True,
            'message': 'Onboarding completed successfully',
            'onboarding_completed': current_user.onboarding_completed,
            'onboarding_step': current_user.onboarding_step
        }

    except Exception as e:
        logger.exception(f'Error completing onboarding for user {current_user.id}: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to complete onboarding'
        )


@router.post('/onboarding/save-all')
async def save_all_onboarding_data(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Save all onboarding data at once (profile + organization)."""
    try:
        # Parse request body
        try:
            body = await request.json()
        except Exception:
            body = {}

        profile_data = body.get('profile', {})
        organization_data = body.get('organization', {})

        # Update user profile fields
        if profile_data:
            for field, value in profile_data.items():
                if hasattr(current_user, field):
                    setattr(current_user, field, value)

        # Create organization if data provided
        organization = None
        organization_data_response = None
        if organization_data:
            org_name = organization_data.get('name') or current_user.company or f"{current_user.name}'s Organization"
            org_slug = organization_data.get('slug')
            org_description = organization_data.get('description')
            
            org_create = OrganizationCreate(
                name=org_name, 
                slug=org_slug,
                description=org_description
            )
            try:
                organization = await create_organization_service(session, org_create, current_user)
                # Capture organization data before commit to avoid lazy loading issues
                organization_data_response = {
                    'id': organization.id,
                    'name': organization.name,
                    'slug': organization.slug
                }
            except HTTPException as e:
                # Re-raise HTTPException (like 409 for duplicate) with proper status code
                raise e

        # Mark onboarding as completed
        current_user.onboarding_completed = True
        current_user.onboarding_step = 3  # Final step

        await session.commit()
        await session.refresh(current_user)

        logger.info(f'Saved all onboarding data for user {current_user.id}')

        # Send welcome email after onboarding completion
        try:
            from src.services.email_service import email_service
            welcome_sent = await email_service.send_welcome_email(
                current_user.email, current_user.name, is_onboarding=True
            )
            if welcome_sent:
                logger.info(f'Welcome email sent to {current_user.email} after onboarding completion')
            else:
                logger.warning(f'Failed to send welcome email to {current_user.email} after onboarding completion')
        except Exception as e:
            # Don't fail onboarding completion if welcome email fails
            logger.exception(f'Exception sending welcome email to {current_user.email} after onboarding completion: {str(e)}')

        response_data = {
            'success': True,
            'message': translate_message('onboarding.completed', request),
            'user': {
                'id': current_user.id,
                'name': current_user.name,
                'company': current_user.company,
                'country': current_user.country,
                'onboarding_completed': current_user.onboarding_completed,
                'onboarding_step': current_user.onboarding_step
            }
        }

        if organization_data_response:
            response_data['organization'] = organization_data_response

        return response_data

    except HTTPException as e:
        # Re-raise HTTPException (like 409 for duplicate organization) as-is
        logger.warning(f'HTTPException saving onboarding data for user {current_user.id}: {e.status_code} - {e.detail}')
        raise e
    except Exception as e:
        # Avoid accessing ORM attributes during exception (can trigger async lazy loads)
        logger.exception(f'Error saving onboarding data: {str(e)}')
        error_msg = translate_message('onboarding.save_failed', request)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


def _get_next_onboarding_step(user: User, has_organization: bool) -> str:
    """Determine the next onboarding step for the user."""
    if not user.name or not user.company or not user.country:
        return 'profile'
    elif not has_organization:
        return 'organization'
    else:
        return 'complete'
