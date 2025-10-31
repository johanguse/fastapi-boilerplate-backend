from fastapi import APIRouter

from src.auth.better_auth import router as better_auth_router
from src.auth.onboarding_routes import router as onboarding_router
from src.auth.otp_routes import router as otp_router
from src.auth.schemas import UserCreate, UserRead
from src.auth.users import auth_backend, fastapi_users  # type: ignore

router = APIRouter()

# Constants
AUTH_PREFIX = '/auth'

# Better Auth compatibility routes
router.include_router(better_auth_router, tags=['better-auth'])

# Onboarding routes
router.include_router(onboarding_router, prefix='/auth', tags=['onboarding'])

# OTP routes
router.include_router(otp_router, tags=['otp'])

# Auth routes (login, register, reset password, verify)
# Set requires_verification=False to allow unverified users to login
auth_router = fastapi_users.get_auth_router(auth_backend, requires_verification=False)  # type: ignore
for route in auth_router.routes:
    route.tags = ['auth']  # type: ignore
router.include_router(
    auth_router,
    prefix='/auth/jwt',
)

register_router = fastapi_users.get_register_router(UserRead, UserCreate)
for route in register_router.routes:
    route.tags = ['auth']  # type: ignore
router.include_router(
    register_router,
    prefix=AUTH_PREFIX,
)

reset_router = fastapi_users.get_reset_password_router()
for route in reset_router.routes:
    route.tags = ['auth']  # type: ignore
router.include_router(
    reset_router,
    prefix=AUTH_PREFIX,
)

verify_router = fastapi_users.get_verify_router(UserRead)
for route in verify_router.routes:
    route.tags = ['auth']  # type: ignore
router.include_router(
    verify_router,
    prefix=AUTH_PREFIX,
)
