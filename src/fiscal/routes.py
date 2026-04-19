"""API routes for managing user tax information and NFS-e records."""

import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import current_active_user

from src.auth.models import User
from src.common.config import get_settings
from src.common.session import get_async_session
from src.fiscal.models import NFSe, UserTaxInfo
from src.fiscal.schemas import (
    NFSeListResponse,
    NFSeResponse,
    UserTaxInfoCreate,
    UserTaxInfoResponse,
    UserTaxInfoUpdate,
)
from src.fiscal.service import NFSeService
from src.fiscal.webhooks import router as webhook_router
from src.utils.brazilian_validators import (
    BRAZILIAN_STATES,
    validate_cpf_or_cnpj,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Include webhook router without authentication
router.include_router(webhook_router, tags=['Fiscal Webhooks'])
settings = get_settings()


# ==== Tax Info Endpoints ====


@router.get('/tax-info', response_model=UserTaxInfoResponse)
async def get_tax_info(
    current_user: Annotated[User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_async_session),
):
    """Get current user's tax information."""
    result = await db.execute(
        select(UserTaxInfo).where(UserTaxInfo.user_id == current_user.id)
    )
    tax_info = result.scalar_one_or_none()

    if not tax_info:
        raise HTTPException(status_code=404, detail='Tax info not found')

    return tax_info


@router.post('/tax-info', response_model=UserTaxInfoResponse, status_code=201)
async def create_tax_info(
    data: UserTaxInfoCreate,
    current_user: Annotated[User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_async_session),
):
    """Create user's tax information."""
    # Check if already exists
    result = await db.execute(
        select(UserTaxInfo).where(UserTaxInfo.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail='Tax info already exists. Use PUT to update.',
        )

    # Validate based on country
    is_brazilian = data.country.upper() == 'BR'

    if is_brazilian:
        # Validate Brazilian requirements
        if not data.cpf_cnpj:
            raise HTTPException(
                status_code=400,
                detail='CPF/CNPJ is required for Brazilian users',
            )

        validation = validate_cpf_or_cnpj(data.cpf_cnpj)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['message'])

        # Address required for Brazilian users
        if not all([
            data.address,
            data.number,
            data.neighborhood,
            data.city,
            data.city_code,
            data.state,
            data.postal_code,
        ]):
            raise HTTPException(
                status_code=400,
                detail='Complete address is required for Brazilian users',
            )
    # International user
    elif not data.nif and data.nif_exemption_code != 1:
        raise HTTPException(
            status_code=400,
            detail='NIF is required for international users (or exemption code)',
        )

    # Create tax info
    tax_info = UserTaxInfo(
        user_id=current_user.id,
        country=data.country.upper(),
        is_brazilian=is_brazilian,
        full_name=data.full_name,
        cpf_cnpj=data.cpf_cnpj,
        inscricao_municipal=data.inscricao_municipal,
        nif=data.nif,
        nif_exemption_code=data.nif_exemption_code,
        address=data.address,
        number=data.number,
        complement=data.complement,
        neighborhood=data.neighborhood,
        city=data.city,
        city_code=data.city_code,
        state=data.state,
        postal_code=data.postal_code,
    )

    db.add(tax_info)
    await db.commit()
    await db.refresh(tax_info)

    logger.info(f'Tax info created for user {current_user.id}')

    return tax_info


@router.put('/tax-info', response_model=UserTaxInfoResponse)
async def update_tax_info(
    data: UserTaxInfoUpdate,
    current_user: Annotated[User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_async_session),
):
    """Update user's tax information."""
    result = await db.execute(
        select(UserTaxInfo).where(UserTaxInfo.user_id == current_user.id)
    )
    tax_info = result.scalar_one_or_none()

    if not tax_info:
        raise HTTPException(
            status_code=404, detail='Tax info not found. Use POST to create.'
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # Validate if updating country
    if 'country' in update_data:
        is_brazilian = update_data['country'].upper() == 'BR'
        tax_info.is_brazilian = is_brazilian

    # Validate Brazilian-specific fields
    if tax_info.is_brazilian and 'cpf_cnpj' in update_data:
        validation = validate_cpf_or_cnpj(update_data['cpf_cnpj'])
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['message'])

    # Update attributes
    for field, value in update_data.items():
        setattr(tax_info, field, value)

    await db.commit()
    await db.refresh(tax_info)

    logger.info(f'Tax info updated for user {current_user.id}')

    return tax_info


@router.delete('/tax-info', status_code=204)
async def delete_tax_info(
    current_user: Annotated[User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_async_session),
):
    """Delete user's tax information."""
    result = await db.execute(
        select(UserTaxInfo).where(UserTaxInfo.user_id == current_user.id)
    )
    tax_info = result.scalar_one_or_none()

    if not tax_info:
        raise HTTPException(status_code=404, detail='Tax info not found')

    await db.delete(tax_info)
    await db.commit()

    logger.info(f'Tax info deleted for user {current_user.id}')


# ==== NFS-e Endpoints ====


@router.get('/nfse', response_model=NFSeListResponse)
async def list_nfse(
    current_user: Annotated[User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List user's NFS-e records."""
    nfse_service = NFSeService(
        db=db,
        api_key=settings.FISCAL_NACIONAL_API_KEY,
        base_url=settings.NFSE_API_BASE_URL,
        admin_email=settings.NFSE_ADMIN_EMAIL,
    )

    skip = (page - 1) * page_size
    items = await nfse_service.list_user_nfse(
        user_id=current_user.id, skip=skip, limit=page_size
    )

    # Get total count
    from sqlalchemy import func

    result = await db.execute(
        select(func.count(NFSe.id)).where(NFSe.user_id == current_user.id)
    )
    total = result.scalar() or 0

    return NFSeListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get('/nfse/{nfse_id}', response_model=NFSeResponse)
async def get_nfse(
    nfse_id: int,
    current_user: Annotated[User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_async_session),
):
    """Get specific NFS-e record."""
    result = await db.execute(
        select(NFSe).where(NFSe.id == nfse_id, NFSe.user_id == current_user.id)
    )
    nfse = result.scalar_one_or_none()

    if not nfse:
        raise HTTPException(status_code=404, detail='NFS-e not found')

    return nfse


@router.post('/nfse/{nfse_id}/sync', response_model=NFSeResponse)
async def sync_nfse(
    nfse_id: int,
    current_user: Annotated[User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_async_session),
):
    """Sync NFS-e status with Fiscal Nacional API."""
    # Verify ownership
    result = await db.execute(
        select(NFSe).where(NFSe.id == nfse_id, NFSe.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail='NFS-e not found')

    nfse_service = NFSeService(
        db=db,
        api_key=settings.FISCAL_NACIONAL_API_KEY,
        base_url=settings.NFSE_API_BASE_URL,
        admin_email=settings.NFSE_ADMIN_EMAIL,
    )

    try:
        nfse = await nfse_service.sync_nfse(nfse_id)
        return nfse
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Failed to sync NFS-e {nfse_id}: {e}')
        raise HTTPException(status_code=500, detail='Failed to sync NFS-e')


# ==== Utility Endpoints ====


@router.get('/brazilian-states')
async def get_brazilian_states():
    """Get list of Brazilian states."""
    return BRAZILIAN_STATES


@router.get('/brazilian-cities/{state_code}')
async def get_brazilian_cities(state_code: str):
    """Get list of cities for a Brazilian state using IBGE API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://servicodados.ibge.gov.br/api/v1/localidades/estados/{state_code}/municipios',
                timeout=10.0,
            )
            response.raise_for_status()
            cities = response.json()

            # Format response
            return [
                {
                    'id': city['id'],
                    'name': city['nome'],
                    'state': state_code.upper(),
                }
                for city in cities
            ]
    except httpx.HTTPError as e:
        logger.error(f'Failed to fetch cities from IBGE: {e}')
        raise HTTPException(
            status_code=500, detail='Failed to fetch cities from IBGE'
        )


@router.get('/validate-cpf-cnpj/{document}')
async def validate_document(document: str):
    """Validate Brazilian CPF or CNPJ."""
    return validate_cpf_or_cnpj(document)
