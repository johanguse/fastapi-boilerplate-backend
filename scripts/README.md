# Seed Data System

## 📁 New Structure

The seed data system has been reorganized into a modular structure for better maintainability:

```
scripts/
├── run_seed.py              # Main seed runner script
├── drop_alembic_version.py  # Utility to reset migration history
└── seed/                     # Seed data package
    ├── __init__.py
    ├── constants.py          # Shared constants and utilities
    ├── reset.py              # Database reset functionality
    ├── users.py              # User seed data
    ├── organizations.py      # Organization & membership seed data
    ├── projects.py           # Project seed data
    ├── activity_logs.py      # Activity log seed data
    ├── subscription_plans.py # Subscription plan seed data
    └── subscriptions.py      # Subscription & billing seed data
```

## 🚀 Quick Start

### Run Seed Data (Automatic Reset)

The seed script **automatically resets the database** before creating fresh data:

```bash
cd backend
uv run python scripts/run_seed.py
```

This will:

1. ✅ Drop all existing tables
2. ✅ Recreate all tables from SQLAlchemy models
3. ✅ Populate with fresh seed data

**⚠️ WARNING**: This deletes ALL data! Only use in development.

## 📦 What Gets Created

### Users (9 total)

- **<admin@example.com>** - Admin (superuser)
- **<john@example.com>** - Member (active, verified)
- **<jane@example.com>** - Member (active, verified)
- **<sarah@example.com>** - Member (active, verified)
- **<bob@example.com>** - Member (invited, not verified)
- **<alice@example.com>** - Member (invited, not verified)
- **<suspended@example.com>** - Member (suspended)
- **<mike@example.com>** - Member (active, verified)
- **<emma@example.com>** - Admin (active, verified)

**Password for all users**: `admin123`

### Organizations (5)

- Development Team
- Marketing Team
- Research Team
- Sales Department
- Customer Success

### Projects (7)

- AI Chatbot Platform
- Content Generation Tool
- Document Analyzer
- Research Assistant
- Sales Analytics Dashboard
- Customer Feedback System
- Email Campaign Manager

### Activity Logs (100+)

- Diverse action types: auth, organization, project, security, system, payment
- 8 different IP addresses
- 8 different user agents
- Timestamps spread over 90 days

### Subscriptions (5)

- **Development Team**: Business Plan - $99.90/mo (active)
- **Marketing Team**: Pro Plan - $29.90/mo (active)
- **Research Team**: Starter Plan - $9.90/mo (active)
- **Sales Department**: Pro Plan (14-day trial)
- **Customer Success**: Free Plan

### Billing History (6 records)

- Total Revenue: **$369.40**
- Spread across 3 organizations
- Realistic payment timestamps

## 🔧 Modular Structure Benefits

### Easy to Maintain

Each data type is in its own file, making it easy to:

- Find and update specific seed data
- Add new data types
- Modify existing data without affecting others

### Easy to Extend

To add new seed data:

1. Create a new file in `scripts/seed/` (e.g., `teams.py`)
2. Define a creation function
3. Import and call it in `run_seed.py`

Example:

```python
# scripts/seed/teams.py
def create_teams(organizations):
    teams = [
        Team(name="Backend Team", organization_id=organizations[0].id),
        # ...
    ]
    return teams

# In run_seed.py
from seed.teams import create_teams
# ... in run_seed():
teams = create_teams(organizations)
for team in teams:
    session.add(team)
await session.commit()
```

### Reusable Components

- `constants.py`: Shared utilities like `random_ip()` and `random_user_agent()`
- `reset.py`: Database reset logic (reusable across different seed scripts)

## 🎯 Development Workflow

### First Time Setup

```bash
cd backend

# Run seed (automatic reset)
uv run python scripts/run_seed.py
```

### Daily Development

```bash
# Just run seed - it resets everything automatically
just seed  # or: uv run python scripts/run_seed.py
```

### After Model Changes

```bash
# The seed script uses Base.metadata.create_all()
# So it automatically picks up model changes
just seed  # or: uv run python scripts/run_seed.py
```

## ⚙️ How It Works

### Automatic Reset

The `run_seed.py` script calls `reset_database()` which:

1. Drops all tables: `Base.metadata.drop_all()`
2. Drops enum types: `DROP TYPE ... CASCADE`
3. Recreates tables: `Base.metadata.create_all()`

### Data Creation Flow

```
1. Subscription Plans (foundation)
2. Users (independent)
3. Organizations (independent)
4. Organization Members (depends on users + orgs)
5. Projects (depends on organizations)
6. Activity Logs (depends on everything)
7. Subscriptions (depends on organizations + plans)
8. Billing History (depends on subscriptions)
9. Payment Activity Logs (depends on billing)
```

## 📝 Customization

### Change Default Password

Edit `scripts/seed/constants.py`:

```python
DEFAULT_PASSWORD = "your_password_here"
```

### Add More Users

Edit `scripts/seed/users.py`:

```python
def create_users():
    users = [
        # ... existing users ...
        User(
            email="newuser@example.com",
            name="New User",
            # ...
        ),
    ]
    return users
```

### Modify Activity Log Diversity

Edit `scripts/seed/constants.py` to add more:

- IP addresses
- User agents
- Any other reusable data

## 🔒 Safety Features

### Development Only

The seed script is designed for **development only**. In production:

- Never run the seed script
- Use proper migrations (Alembic)
- Import real data through APIs or migration scripts

### Confirmation (Optional)

If you want to add a confirmation prompt, modify `run_seed.py`:

```python
async def run_seed():
    print("⚠️  WARNING: This will delete ALL data!")
    confirm = input("Type 'yes' to continue: ")
    if confirm != 'yes':
        print("Cancelled.")
        return
    # ... rest of code
```

## 🐛 Troubleshooting

### "Table already exists"

The reset should handle this, but if you get this error:

```bash
uv run python scripts/drop_alembic_version.py
uv run python scripts/run_seed.py
```

### "Cannot connect to database"

Check your `.env` file has the correct `DATABASE_URL`:

```env
DATABASE_URL=postgresql://user:pass@host/database
```

### Import Errors

Make sure you're running from the `backend` directory:

```bash
cd backend
just seed  # or: uv run python scripts/run_seed.py
```

## 📚 Related Documentation

- [SEED_DATA_ENHANCED.md](../SEED_DATA_ENHANCED.md) - Detailed seed data documentation
- [Database Models](../src/) - SQLAlchemy model definitions
- [Alembic Migrations](../alembic/) - Production migration system

## ⚡ Performance Tips

The seed script is optimized for speed:

- ✅ Bulk creates (add all, then single commit)
- ✅ Minimal refreshes (only when IDs needed)
- ✅ Single database connection
- ✅ No unnecessary queries

Typical run time: **2-5 seconds** for all data.
