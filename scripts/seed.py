"""
Seed data script for development database.
Creates sample users, teams, projects, and related data.
"""
import asyncio
from datetime import UTC, datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.common.config import settings
from src.common.database import Base

# Import all models
from src.auth.models import User
from src.organizations.models import Organization, OrganizationMember
from src.projects.models import Project
from src.activity_log.models import ActivityLog

# Import FastAPI Users password helper for proper hashing
from passlib.context import CryptContext

# Password context for hashing (same as FastAPI Users)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


async def create_seed_data():
    """Create comprehensive seed data for development."""
    
    # Create async engine and session
    database_url = str(settings.DATABASE_URL).replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        print("🌱 Creating seed data...")
        
        # Hash the password properly using FastAPI Users method
        admin_password = "admin123"
        hashed_password = pwd_context.hash(admin_password)
        print(f"🔐 Generated password hash for '{admin_password}'")
        
        # Check if users already exist
        existing_admin = await session.execute(select(User).where(User.email == "admin@example.com"))
        admin_user = existing_admin.scalar_one_or_none()
        
        if admin_user:
            print("⚠️ Admin user already exists, updating password hash...")
            # Update the password hash to ensure it works with the current password
            admin_user.hashed_password = hashed_password
            await session.commit()
            print(f"🔐 Updated admin password hash for: admin@example.com / {admin_password}")
            
            # Update other existing users' passwords too
            for email in ["john@example.com", "jane@example.com", "bob@example.com"]:
                result = await session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                if user:
                    user.hashed_password = hashed_password
                    print(f"🔐 Updated password hash for: {email}")
            
            await session.commit()
            print(f"✅ All user passwords updated to work with: {admin_password}")
            await engine.dispose()
            return
        
        # 1. Create Users
        print("👥 Creating users...")
        users = [
            User(
                email="admin@example.com",
                name="Admin User",
                role="admin",
                is_active=True,
                is_superuser=True,
                is_verified=True,
                hashed_password=hashed_password
            ),
            User(
                email="john@example.com",
                name="John Doe",
                role="member",
                is_active=True,
                is_verified=True,
                hashed_password=hashed_password
            ),
            User(
                email="jane@example.com",
                name="Jane Smith",
                role="member",
                is_active=True,
                is_verified=True,
                hashed_password=hashed_password
            ),
            User(
                email="bob@example.com",
                name="Bob Wilson",
                role="member",
                is_active=True,
                is_verified=True,
                hashed_password=hashed_password
            ),
        ]
        
        for user in users:
            session.add(user)
        await session.commit()
        
        # Refresh to get IDs
        for user in users:
            await session.refresh(user)
        
        print(f"✅ Created {len(users)} users")
        
        # 2. Create Organizations
        print("🏢 Creating organizations...")
        organizations = [
            Organization(
                name="Development Team",
            ),
            Organization(
                name="Marketing Team", 
            ),
            Organization(
                name="Research Team",
            ),
        ]
        
        for organization in organizations:
            session.add(organization)
        await session.commit()
        
        for organization in organizations:
            await session.refresh(organization)
        
        print(f"✅ Created {len(organizations)} organizations")
        
        # 3. Create Organization Members
        print("👤 Creating organization memberships...")
        organization_members = [
            # Development Team
            OrganizationMember(organization_id=organizations[0].id, user_id=users[0].id, role="owner"),
            OrganizationMember(organization_id=organizations[0].id, user_id=users[1].id, role="admin"),
            OrganizationMember(organization_id=organizations[0].id, user_id=users[2].id, role="member"),
            
            # Marketing Team
            OrganizationMember(organization_id=organizations[1].id, user_id=users[1].id, role="owner"),
            OrganizationMember(organization_id=organizations[1].id, user_id=users[3].id, role="member"),
            
            # Research Team
            OrganizationMember(organization_id=organizations[2].id, user_id=users[0].id, role="owner"),
            OrganizationMember(organization_id=organizations[2].id, user_id=users[2].id, role="admin"),
        ]
        
        for member in organization_members:
            session.add(member)
        await session.commit()
        
        print(f"✅ Created {len(organization_members)} organization memberships")
        
        # 4. Create Projects
        print("📁 Creating projects...")
        projects = [
            Project(
                name="AI Chatbot Platform",
                description="Customer service AI chatbot with RAG capabilities",
                organization_id=organizations[0].id
            ),
            Project(
                name="Content Generation Tool",
                description="AI-powered content creation for marketing",
                organization_id=organizations[1].id
            ),
            Project(
                name="Document Analyzer",
                description="Intelligent document processing and analysis",
                organization_id=organizations[0].id
            ),
            Project(
                name="Research Assistant",
                description="AI research assistant for academic papers",
                organization_id=organizations[2].id
            ),
        ]
        
        for project in projects:
            session.add(project)
        await session.commit()
        
        for project in projects:
            await session.refresh(project)
        
        print(f"✅ Created {len(projects)} projects")
        
        # 5. Create Activity Logs
        print("📝 Creating activity logs...")
        activities = [
            ActivityLog(
                action="user.created",
                action_type="create",
                description="User account created",
                user_id=users[1].id,
                organization_id=None,
                project_id=None,
                ip_address="127.0.0.1",
                user_agent=DEFAULT_USER_AGENT,
                created_at=datetime.now(UTC) - timedelta(days=5)
            ),
            ActivityLog(
                action="organization.created",
                action_type="create",
                description="Organization 'Development Team' created",
                user_id=users[0].id,
                organization_id=organizations[0].id,
                project_id=None,
                ip_address="127.0.0.1",
                user_agent=DEFAULT_USER_AGENT,
                created_at=datetime.now(UTC) - timedelta(days=4)
            ),
            ActivityLog(
                action="project.created",
                action_type="create",
                description="Project 'AI Chatbot Platform' created",
                user_id=users[0].id,
                organization_id=organizations[0].id,
                project_id=projects[0].id,
                ip_address="127.0.0.1",
                user_agent=DEFAULT_USER_AGENT,
                created_at=datetime.now(UTC) - timedelta(days=3)
            ),
        ]
        
        for activity in activities:
            session.add(activity)
        await session.commit()
        
        print(f"✅ Created {len(activities)} activity logs")
        
        print("\n🎉 Seed data creation completed successfully!")
        print("\n📊 Summary:")
        print(f"   • {len(users)} users (admin@example.com, john@example.com, jane@example.com, bob@example.com)")
        print(f"   • {len(organizations)} organizations with {len(organization_members)} memberships")
        print(f"   • {len(projects)} projects")
        print(f"   • {len(activities)} activity logs")
        print(f"\n🔐 Default password for all users: {admin_password}")
        print(f"🔑 Password hash: {hashed_password}")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_seed_data())