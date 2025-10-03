"""Seed data for activity logs."""
import random
from datetime import UTC, datetime, timedelta
from src.activity_log.models import ActivityLog
from .constants import random_ip, random_user_agent

def create_activity_logs(users, organizations, organization_members, projects):
    """Create comprehensive activity log seed data."""
    activities = []
    
    # User registration activities
    for user in users[:5]:
        activities.append(ActivityLog(
            action="user.register",
            action_type="auth",
            description=f"User {user.email} registered",
            user_id=user.id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=user.created_at
        ))
    
    # Login activities (spread over time)
    login_times = [90, 89, 87, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 3, 2, 1, 0]
    for days_ago in login_times:
        user = random.choice(users[:5])  # Only active users
        activities.append(ActivityLog(
            action="user.login",
            action_type="auth",
            description=f"User {user.email} logged in",
            user_id=user.id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=datetime.now(UTC) - timedelta(days=days_ago, hours=random.randint(0, 23))
        ))
    
    # Organization activities
    for org in organizations:
        owner_member = next(m for m in organization_members if m.organization_id == org.id and m.role == "owner")
        activities.append(ActivityLog(
            action="organization.created",
            action_type="organization",
            description=f"Organization '{org.name}' created",
            user_id=owner_member.user_id,
            organization_id=org.id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=org.created_at
        ))
    
    # Organization member invitations
    for member in organization_members[5:10]:  # Some members invited later
        activities.append(ActivityLog(
            action="organization.member.invited",
            action_type="organization",
            description="User invited to organization",
            user_id=users[0].id,  # Admin sent invites
            organization_id=member.organization_id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=datetime.now(UTC) - timedelta(days=random.randint(10, 30))
        ))
    
    # Project activities
    for project in projects:
        activities.append(ActivityLog(
            action="project.created",
            action_type="project",
            description=f"Project '{project.name}' created",
            user_id=users[0].id,
            organization_id=project.organization_id,
            project_id=project.id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=project.created_at
        ))
        
        # Project updates
        activities.append(ActivityLog(
            action="project.updated",
            action_type="project",
            description=f"Project '{project.name}' settings updated",
            user_id=random.choice(users[:4]).id,
            organization_id=project.organization_id,
            project_id=project.id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=project.created_at + timedelta(days=random.randint(1, 10))
        ))
    
    # Security events
    activities.extend([
        ActivityLog(
            action="user.password.changed",
            action_type="security",
            description="User changed password",
            user_id=users[1].id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=datetime.now(UTC) - timedelta(days=20)
        ),
        ActivityLog(
            action="user.email.verified",
            action_type="security",
            description="Email address verified",
            user_id=users[2].id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=datetime.now(UTC) - timedelta(days=44)
        ),
        ActivityLog(
            action="user.suspended",
            action_type="security",
            description="User account suspended by admin",
            user_id=users[6].id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=datetime.now(UTC) - timedelta(days=10)
        ),
        ActivityLog(
            action="security.2fa.enabled",
            action_type="security",
            description="Two-factor authentication enabled",
            user_id=users[0].id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=datetime.now(UTC) - timedelta(days=60)
        ),
    ])
    
    # System activities
    activities.extend([
        ActivityLog(
            action="system.backup.completed",
            action_type="system",
            description="Database backup completed successfully",
            ip_address="127.0.0.1",
            user_agent="System Cron Job",
            created_at=datetime.now(UTC) - timedelta(days=1)
        ),
        ActivityLog(
            action="system.maintenance.completed",
            action_type="system",
            description="Scheduled system maintenance completed",
            ip_address="127.0.0.1",
            user_agent="System Cron Job",
            created_at=datetime.now(UTC) - timedelta(days=7)
        ),
    ])
    
    return activities
