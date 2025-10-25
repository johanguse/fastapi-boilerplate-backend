"""Seed data for AI usage logs and analytics."""

from datetime import UTC, datetime, timedelta
import random

from src.ai_core.usage import AIUsageLog
from .constants import random_ip, random_user_agent


def create_ai_usage_logs(organizations):
    """Create AI usage log seed data."""
    usage_logs = []
    
    # Generate usage logs for the last 30 days
    for days_ago in range(30):
        date = datetime.now(UTC) - timedelta(days=days_ago)
        
        # Generate random usage for each organization
        for org in organizations[:3]:  # Only first 3 orgs have AI features
            # Documents usage
            if random.random() < 0.7:  # 70% chance of document usage
                tokens = random.randint(1200, 6000)
                cost = random.uniform(0.01, 0.05)
                usage_logs.append(AIUsageLog(
                    organization_id=org.id,
                    user_id=None,  # Anonymous usage
                    feature='documents',
                    operation='document_processing',
                    tokens_used=tokens,
                    cost=cost,
                    created_at=date
                ))
            
            # Content generation usage
            if random.random() < 0.5:  # 50% chance of content usage
                tokens = random.randint(1000, 5000)
                cost = random.uniform(0.02, 0.08)
                usage_logs.append(AIUsageLog(
                    organization_id=org.id,
                    user_id=None,
                    feature='content',
                    operation='content_generation',
                    tokens_used=tokens,
                    cost=cost,
                    created_at=date
                ))
            
            # Analytics usage
            if random.random() < 0.3:  # 30% chance of analytics usage
                tokens = random.randint(300, 1500)
                cost = random.uniform(0.005, 0.02)
                usage_logs.append(AIUsageLog(
                    organization_id=org.id,
                    user_id=None,
                    feature='analytics',
                    operation='query_processing',
                    tokens_used=tokens,
                    cost=cost,
                    created_at=date
                ))
    
    return usage_logs
