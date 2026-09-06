"""Seed data for AI usage logs and analytics."""

import secrets
from datetime import UTC, datetime, timedelta

from src.ai_core.usage import AIUsageLog


def create_ai_usage_logs(organizations):
    """Create AI usage log seed data."""
    usage_logs = []

    # Generate usage logs for the last 30 days
    for days_ago in range(30):
        date = datetime.now(UTC) - timedelta(days=days_ago)

        # Generate random usage for each organization
        for org in organizations[:3]:  # Only first 3 orgs have AI features
            # Documents usage
            if secrets.randbelow(100) < 70:  # 70% chance of document usage
                tokens = 1200 + secrets.randbelow(4801)  # 1200-6000
                cost = 0.01 + (secrets.randbelow(401) / 10000)  # 0.01-0.05
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
            if secrets.randbelow(100) < 50:  # 50% chance of content usage
                tokens = 1000 + secrets.randbelow(4001)  # 1000-5000
                cost = 0.02 + (secrets.randbelow(601) / 10000)  # 0.02-0.08
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
            if secrets.randbelow(100) < 30:  # 30% chance of analytics usage
                tokens = 300 + secrets.randbelow(1201)  # 300-1500
                cost = 0.005 + (secrets.randbelow(151) / 10000)  # 0.005-0.02
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
