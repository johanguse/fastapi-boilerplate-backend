from fastapi import APIRouter

from src.auth.schemas import UserCreate, UserRead
from src.auth.users import auth_backend, fastapi_users

router = APIRouter()

# Auth routes (login, register, reset password, verify)
auth_router = fastapi_users.get_auth_router(auth_backend)
for route in auth_router.routes:
    route.tags = ['auth']
router.include_router(
    auth_router,
    prefix='/auth/jwt',
)

register_router = fastapi_users.get_register_router(UserRead, UserCreate)
for route in register_router.routes:
    route.tags = ['auth']
router.include_router(
    register_router,
    prefix='/auth',
)

reset_router = fastapi_users.get_reset_password_router()
for route in reset_router.routes:
    route.tags = ['auth']
router.include_router(
    reset_router,
    prefix='/auth',
)

verify_router = fastapi_users.get_verify_router(UserRead)
for route in verify_router.routes:
    route.tags = ['auth']
router.include_router(
    verify_router,
    prefix='/auth',
)
