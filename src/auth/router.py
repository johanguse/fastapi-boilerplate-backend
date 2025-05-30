from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_active_user
from src.auth.models import User
from src.auth.schemas import (
    Token,
    UserLogin,
    UserProfile,
    UserRegister,
    UserUpdate,
)
from src.auth.service import AuthService
from src.common.database import get_async_session

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """Register a new user."""
    # Check if user already exists
    existing_user = await AuthService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    user = await AuthService.create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        name=user_data.name,
    )

    return user


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Authenticate user and return tokens."""
    user = await AuthService.authenticate_user(
        db, user_credentials.email, user_credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token = AuthService.create_access_token(data={"sub": user.id})
    refresh_token = AuthService.create_refresh_token(data={"sub": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """Update current user profile."""
    update_data = user_update.model_dump(exclude_unset=True)

    # Check if email is being changed and if it's already taken
    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = await AuthService.get_user_by_email(db, update_data["email"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        # If email is changed, mark as unverified
        update_data["is_verified"] = False

    # Update user
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return current_user
