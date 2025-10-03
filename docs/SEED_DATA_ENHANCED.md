# Enhanced Seed Data Script

## 🎉 What's New

The seed data script (`scripts/seed.py`) has been significantly enhanced with:

### 📊 More Diverse Users (9 total)
- **3 Admins**: admin@example.com (superuser), emma@example.com
- **4 Active Members**: john@example.com, jane@example.com, sarah@example.com, mike@example.com  
- **2 Invited Users**: bob@example.com, alice@example.com (not verified yet)
- **1 Suspended User**: suspended@example.com
- Different creation dates (from 120 days ago to recent)
- Different verification states

### 🏢 More Organizations (5 total)
- Development Team
- Marketing Team
- Research Team
- Sales Department
- Customer Success

### 👥 Organization Memberships (17 total)
- Realistic multi-organization memberships
- Different roles: owner, admin, member
- Some users in multiple organizations

### 📁 More Projects (7 total)
- AI Chatbot Platform
- Content Generation Tool
- Document Analyzer
- Research Assistant
- Sales Analytics Dashboard
- Customer Feedback System
- Email Campaign Manager

### 📝 Comprehensive Activity Logs (100+ entries)
- **Diverse action types**:
  - `auth`: user.register, user.login
  - `organization`: organization.created, organization.member.invited
  - `project`: project.created, project.updated
  - `security`: user.password.changed, user.email.verified, user.suspended, security.2fa.enabled
  - `system`: system.backup.completed, system.maintenance.completed
  - `payment`: payment.succeeded

- **Realistic data**:
  - 8 different IP addresses (IPv4 and IPv6)
  - 8 different user agents (Chrome, Firefox, Safari, mobile devices)
  - Timestamps spread over 90 days
  - Different hours of the day

### 💳 Active Subscriptions (5 total)
- **Development Team**: Business Plan - $99.90/month (active)
- **Marketing Team**: Pro Plan - $29.90/month (active)
- **Research Team**: Starter Plan - $9.90/month (active)
- **Sales Department**: Pro Plan (trialing - 14-day trial)
- **Customer Success**: Free Plan

### 💰 Billing History (6 records)
- **Development Team**: 3 months of billing history ($299.70 total)
- **Marketing Team**: 2 months of billing history ($59.80 total)
- **Research Team**: 1 month of billing history ($9.90 total)
- **Total Revenue**: $369.40

All payments marked as "paid" with realistic timestamps

## 🚀 How to Use

### Option 1: Update Existing Data (Safe)
If you already have data in your database, the script will:
- Update existing user passwords to "admin123"
- Keep existing data intact

```bash
cd backend
poetry run python scripts/seed.py
```

### Option 2: Fresh Start (Destructive)
To get all the new enhanced data, you need a fresh database:

```bash
cd backend

# Method 1: Using Alembic
poetry run alembic downgrade base
poetry run alembic upgrade head
poetry run python scripts/seed.py

# Method 2: Manual cleanup (if migrations fail)
# Connect to your database and drop all tables, then:
poetry run alembic upgrade head
poetry run python scripts/seed.py
```

## 📋 Default Credentials

**Password for ALL users**: `admin123`

### User Accounts:
- `admin@example.com` - Admin (superuser)
- `john@example.com` - Member (active)
- `jane@example.com` - Member (active)
- `sarah@example.com` - Member (active)
- `bob@example.com` - Member (invited, not verified)
- `alice@example.com` - Member (invited, not verified)
- `suspended@example.com` - Member (suspended)
- `mike@example.com` - Member (active)
- `emma@example.com` - Admin (active)

## 📈 What You'll See in the Admin Dashboard

### Users Page
- 9 total users
- 6 active, 2 invited, 1 suspended
- 7 verified, 2 unverified
- 2 admins, 7 members

### Reports/Analytics Page
- **Active Subscriptions**: 4 active + 1 trialing
- **Total Revenue**: $369.40 from billing history
- **User Growth Chart**: Shows 9 users added over 90 days
- **Revenue Chart**: Shows monthly payments over time

### Activity Logs Page
- 100+ activity logs with varied types
- Filterable by action type (auth, organization, project, security, system, payment)
- Filterable by user ID
- Diverse IP addresses and user agents
- Timestamps from 90 days ago to now

## 🎯 Benefits

1. **Realistic Testing Data**: Diverse scenarios for testing all features
2. **Analytics Ready**: Enough data to populate charts and graphs
3. **Multi-organization**: Test organization-specific features
4. **Subscription Testing**: Different subscription tiers and statuses
5. **Activity Tracking**: Rich activity log history for auditing
6. **Time-based Data**: Historical data for testing time-series features

## 🔧 Technical Details

### Revenue Tracking
- Revenue data comes from `BillingHistory` table (NOT Stripe directly)
- This is a local database representation of payments
- In production, you would sync this from Stripe webhooks
- The seed data simulates this billing history for development/testing

### Subscription Status
- `active` - Currently subscribed and paying
- `trialing` - In free trial period
- `inactive` - No active subscription
- `past_due` - Payment failed
- `canceled` - Subscription canceled

### Data Relationships
- Users can belong to multiple organizations
- Organizations have one subscription
- Subscriptions have billing history
- Activity logs track all user actions
- Projects belong to organizations

## 📝 Notes

- All data uses UTC timezone
- Passwords are hashed with bcrypt
- IP addresses are documentation IPs (safe for demo)
- User agents represent common browsers and devices
- Billing amounts are in cents (USD)
