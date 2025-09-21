from typing import Dict, Any
from fastapi_users.password import PasswordHelper
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, UTC
import jwt
from src.common.config import settings
from fastapi_users.jwt import generate_jwt
from fastapi import Depends
from src.auth.models import User  # Add this import
from fastapi.security import OAuth2PasswordBearer
from fastapi_users.authentication import Strategy, JWTStrategy
from src.auth.routes import fastapi_users
from src.main import app  # Make sure this is already imported
from src.auth.users import current_active_user


async def create_test_user_raw(async_session: AsyncSession, email: str = "test@example.com", password: str = "test123"):
    """Create a test user using raw SQL to bypass mapper issues."""
    # Clean up any existing user with this email
    try:
        await async_session.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": email}
        )
        await async_session.commit()
    except Exception:
        await async_session.rollback()
    
    # Create a new user with hashed password in a single transaction
    password_helper = PasswordHelper()
    hashed_password = password_helper.hash(password)
    
    async with async_session.begin():
        # Detect if max_teams column exists to keep compatibility with older schemas
        col_check = await async_session.execute(
            text(
                """
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'max_teams'
                """
            )
        )
        has_max_teams = col_check.scalar() is not None

        if has_max_teams:
            result = await async_session.execute(
                text(
                    """
                    INSERT INTO users(
                        email, 
                        hashed_password, 
                        name, 
                        is_active, 
                        is_verified, 
                        role, 
                        is_superuser,
                        max_teams,
                        created_at, 
                        updated_at
                    )
                    VALUES(
                        :email, 
                        :password, 
                        :name, 
                        :is_active, 
                        :is_verified, 
                        :role, 
                        :is_superuser,
                        :max_teams,
                        NOW(), 
                        NOW()
                    )
                    RETURNING id
                    """
                ),
                {
                    "email": email,
                    "password": hashed_password,
                    "name": "Test User",
                    "is_active": True,
                    "is_verified": True,
                    "role": "member",
                    "is_superuser": False,
                    "max_teams": 5,
                },
            )
        else:
            result = await async_session.execute(
                text(
                    """
                    INSERT INTO users(
                        email, 
                        hashed_password, 
                        name, 
                        is_active, 
                        is_verified, 
                        role, 
                        is_superuser,
                        created_at, 
                        updated_at
                    )
                    VALUES(
                        :email, 
                        :password, 
                        :name, 
                        :is_active, 
                        :is_verified, 
                        :role, 
                        :is_superuser,
                        NOW(), 
                        NOW()
                    )
                    RETURNING id
                    """
                ),
                {
                    "email": email,
                    "password": hashed_password,
                    "name": "Test User",
                    "is_active": True,
                    "is_verified": True,
                    "role": "member",
                    "is_superuser": False,
                },
            )
        user_id = result.scalar_one()
    
    # Return a dictionary of user data
    return {
        "id": user_id,
        "email": email,
        "name": "Test User",
        "is_active": True,
        "is_verified": True,
        "is_superuser": False,
    "max_teams": 5,
        "role": "member"
    }


async def create_test_organization_raw(async_session: AsyncSession, user_id: int):
    """Create a test organization using raw SQL."""
    # Clean up any existing teams for this user
    try:
        team_query = await async_session.execute(
            text("""
            SELECT o.id FROM organizations o
            JOIN organization_members om ON o.id = om.organization_id
            WHERE om.user_id = :user_id
            """),
            {"user_id": user_id}
        )
        
        team_ids = team_query.scalars().all()
        for org_id in team_ids:
            await async_session.execute(
                text("DELETE FROM organization_members WHERE organization_id = :org_id"),
                {"org_id": org_id}
            )
            await async_session.execute(
                text("DELETE FROM organizations WHERE id = :org_id"),
                {"org_id": org_id}
            )
        
        await async_session.commit()
    except Exception:
        await async_session.rollback()
    
    # Create a new team with required fields in a single transaction
    async with async_session.begin():
        result = await async_session.execute(
            text("""
            INSERT INTO organizations(
                name, 
                max_projects,
                active_projects,
                created_at, 
                updated_at
            )
            VALUES(
                'Test Org', 
                5, 
                0, 
                NOW(), 
                NOW()
            )
            RETURNING id
            """)
        )
        org_id = result.scalar_one()
        
        # Add org member
        await async_session.execute(
            text("""
            INSERT INTO organization_members(organization_id, user_id, role, created_at, updated_at)
            VALUES (:org_id, :user_id, 'admin', NOW(), NOW())
            """),
            {"org_id": org_id, "user_id": user_id}
        )
    
    return {
        "id": org_id,
        "name": "Test Org",
        "max_projects": 5,
        "active_projects": 0
    }


async def create_test_project_raw(async_session: AsyncSession, organization_id: int):
    """Create a test project using raw SQL."""
    # Clean up any existing projects for this team
    try:
        await async_session.execute(
            text("DELETE FROM projects WHERE organization_id = :org_id"),
            {"org_id": organization_id}
        )
        await async_session.commit()
    except Exception:
        await async_session.rollback()
    
    # Create a new project in a single transaction
    async with async_session.begin():
        result = await async_session.execute(
            text("""
            INSERT INTO projects(name, description, organization_id, created_at, updated_at)
            VALUES('Test Project', 'A test project', :org_id, NOW(), NOW())
            RETURNING id
            """),
            {"org_id": organization_id}
        )
        project_id = result.scalar_one()
    
    return {
        "id": project_id,
        "name": "Test Project",
        "description": "A test project",
        "organization_id": organization_id
    }


async def create_test_auth_token(user_id: int, email: str) -> str:
    """Generate a JWT token compatible with FastAPI Users."""
    # Use FastAPI Users' built-in token generation
    data = {
        "sub": str(user_id),
        "email": email,
        "aud": "fastapi-users:auth"  # This audience is required by FastAPI Users
    }
    
    token = generate_jwt(
        data=data,
        secret=settings.JWT_SECRET,  # Use JWT_SECRET for consistency
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        algorithm="HS256"
    )
    
    return token 


def create_mock_user(user_id: int = 1, email: str = "test@example.com", max_teams: int = 5) -> Dict[str, Any]:
    """Create a mock user dictionary for testing."""
    # Return a dictionary instead of a User instance
    return {
        "id": user_id,
        "email": email,
        "name": "Test User",
        "is_active": True,
        "is_verified": True,
        "is_superuser": False,
        "role": "member",
        "max_teams": max_teams
    }


def get_mock_auth_deps(app, mock_user: Dict[str, Any] = None):
    """Set up mock authentication for testing."""
    if mock_user is None:
        mock_user = create_mock_user()
    
    # Import the necessary dependencies
    from src.auth.users import current_active_user
    
    # Create a Mock User class to avoid SQLAlchemy initialization issues
    class MockUser:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    # Create a mock user from the dictionary
    user_obj = MockUser(
        id=mock_user["id"],
        email=mock_user["email"],
        name=mock_user.get("name", "Test User"),
        is_active=mock_user.get("is_active", True),
        is_verified=mock_user.get("is_verified", True),
        is_superuser=mock_user.get("is_superuser", False),
        role=mock_user.get("role", "member"),
        max_teams=mock_user.get("max_teams", 5)
    )
    
    # Define the override function
    async def override_user_dependency():
        return user_obj
    
    # Override the current_active_user dependency directly
    app.dependency_overrides[current_active_user] = override_user_dependency
    
    return app.dependency_overrides

# Get the actual dependency references from your FastAPI app
current_user_dependency = fastapi_users.current_user()
current_active_user_dependency = fastapi_users.current_user(active=True) 