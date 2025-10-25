"""
Onboarding routes for user profile completion and organization setup.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import OnboardingComplete, OnboardingProfileUpdate, OnboardingStepUpdate
from src.common.security import get_current_active_user
from src.common.session import get_async_session
from src.organizations.models import Organization, OrganizationMember
from src.organizations.schemas import OrganizationCreate
from src.organizations.service import create_organization as create_organization_service

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
            'message': 'Profile updated successfully',
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
        raise HTTPException(
            status_code=500,
            detail='Failed to update profile'
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
            'message': 'Organization created successfully',
            'organization': {
                'id': organization.id,
                'name': organization.name,
                'slug': organization.slug
            },
            'onboarding_step': current_user.onboarding_step
        }
        
    except Exception as e:
        logger.exception(f'Error creating onboarding organization for user {current_user.id}: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to create organization'
        )


@router.patch('/onboarding/step')
async def update_onboarding_step(
    step_data: OnboardingStepUpdate,
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
            'message': 'Onboarding step updated successfully',
            'onboarding_step': current_user.onboarding_step,
            'onboarding_completed': current_user.onboarding_completed
        }
        
    except Exception as e:
        logger.exception(f'Error updating onboarding step for user {current_user.id}: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to update onboarding step'
        )


@router.post('/onboarding/complete')
async def complete_onboarding(
    completion_data: OnboardingComplete,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Mark onboarding as completed."""
    try:
        current_user.onboarding_completed = True
        current_user.onboarding_step = 3  # Final step
        
        await session.commit()
        await session.refresh(current_user)
        
        logger.info(f'Completed onboarding for user {current_user.id}')
        
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


def _get_next_onboarding_step(user: User, has_organization: bool) -> str:
    """Determine the next onboarding step for the user."""
    if not user.name or not user.company or not user.country:
        return 'profile'
    elif not has_organization:
        return 'organization'
    else:
        return 'complete'
