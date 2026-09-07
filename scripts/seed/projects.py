"""Seed data for projects."""

from datetime import UTC, datetime, timedelta

from src.projects.models import Project


def create_projects(organizations):
    """Create project seed data."""
    projects = [
        Project(
            name='AI Chatbot Platform',
            description='Customer service AI chatbot with RAG capabilities',
            organization_id=organizations[0].id,
            created_at=datetime.now(UTC) - timedelta(days=70),
        ),
        Project(
            name='Content Generation Tool',
            description='AI-powered content creation for marketing',
            organization_id=organizations[1].id,
            created_at=datetime.now(UTC) - timedelta(days=55),
        ),
        Project(
            name='Document Analyzer',
            description='Intelligent document processing and analysis',
            organization_id=organizations[0].id,
            created_at=datetime.now(UTC) - timedelta(days=45),
        ),
        Project(
            name='Research Assistant',
            description='AI research assistant for academic papers',
            organization_id=organizations[2].id,
            created_at=datetime.now(UTC) - timedelta(days=40),
        ),
        Project(
            name='Sales Analytics Dashboard',
            description='Real-time sales data visualization and insights',
            organization_id=organizations[3].id,
            created_at=datetime.now(UTC) - timedelta(days=30),
        ),
        Project(
            name='Customer Feedback System',
            description='Automated customer feedback collection and analysis',
            organization_id=organizations[4].id,
            created_at=datetime.now(UTC) - timedelta(days=20),
        ),
        Project(
            name='Email Campaign Manager',
            description='Automated email marketing campaigns',
            organization_id=organizations[1].id,
            created_at=datetime.now(UTC) - timedelta(days=15),
        ),
    ]
    return projects
