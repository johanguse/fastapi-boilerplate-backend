# 📚 Complete API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

---

## 🔐 Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer {access_token}
```

### Get Token
**POST** `/auth/login`

**Body (form-urlencoded):**
```
username=admin@example.com
password=admin123
```

**Response:**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

---

## 📋 Table of Contents
1. [Authentication](#authentication-endpoints)
2. [Users](#user-endpoints)
3. [Organizations](#organization-endpoints)
4. [Organization Members](#organization-member-endpoints)
5. [Team Invitations](#team-invitation-endpoints)
6. [Email Verification](#email-verification-endpoints)
7. [Subscriptions](#subscription-endpoints)
8. [Billing](#billing-endpoints)
9. [Projects](#project-endpoints)
10. [Webhooks](#webhook-endpoints)

---

## 🔑 Authentication Endpoints

### Register User
**POST** `/auth/register`

**Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

### Login
**POST** `/auth/login`

**Body (form-urlencoded):**
```
username=user@example.com
password=password123
```

### Get Current User
**GET** `/users/me`

**Headers:** `Authorization: Bearer {token}`

---

## 👤 User Endpoints

### Get User Profile
**GET** `/users/me`

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-09-30T00:00:00Z"
}
```

---

## 🏢 Organization Endpoints

### List Organizations
**GET** `/organizations`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Development Team",
    "description": null,
    "created_at": "2025-09-30T00:00:00Z"
  }
]
```

### Create Organization
**POST** `/organizations`

**Body:**
```json
{
  "name": "My Organization",
  "description": "Description here"
}
```

### Get Organization
**GET** `/organizations/{id}`

### Update Organization
**PUT** `/organizations/{id}`

**Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Delete Organization
**DELETE** `/organizations/{id}`

---

## 👥 Organization Member Endpoints

### List Organization Members
**GET** `/organizations/{id}/members`

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "organization_id": 1,
    "role": "owner",
    "user": {
      "id": 1,
      "email": "admin@example.com",
      "name": "Admin User"
    },
    "joined_at": "2025-09-30T00:00:00Z"
  }
]
```

### Remove Organization Member
**DELETE** `/organizations/{org_id}/members/{member_id}`

### Update Member Role
**PATCH** `/organizations/{org_id}/members/{member_id}`

**Body:**
```json
{
  "role": "admin"
}
```

**Roles:** `owner`, `admin`, `member`, `viewer`

---

## 📧 Team Invitation Endpoints

### Invite Team Member
**POST** `/invitations/organizations/{id}/invitations`

**Body:**
```json
{
  "email": "newmember@example.com",
  "role": "member",
  "message": "Welcome to our team!"
}
```

**Response:**
```json
{
  "id": 1,
  "organization_id": 1,
  "email": "newmember@example.com",
  "role": "member",
  "status": "pending",
  "message": "Welcome to our team!",
  "expires_at": "2025-10-07T00:00:00Z",
  "created_at": "2025-09-30T00:00:00Z"
}
```

### List Pending Invitations
**GET** `/invitations/organizations/{id}/invitations`

**Response:**
```json
[
  {
    "id": 1,
    "email": "newmember@example.com",
    "role": "member",
    "status": "pending",
    "message": "Welcome!",
    "invited_by_name": "Admin User",
    "expires_at": "2025-10-07T00:00:00Z",
    "created_at": "2025-09-30T00:00:00Z"
  }
]
```

### Accept Invitation
**POST** `/invitations/invitations/{token}/accept`

**Response:**
```json
{
  "message": "Invitation accepted",
  "organization_id": 1
}
```

### Decline Invitation
**POST** `/invitations/invitations/{token}/decline`

### Cancel Invitation (Admin Only)
**DELETE** `/invitations/organizations/{org_id}/invitations/{invitation_id}`

---

## ✉️ Email Verification Endpoints

### Resend Verification Email
**POST** `/invitations/verify-email/resend`

**Response:**
```json
{
  "message": "Verification email sent"
}
```

### Verify Email with Token
**POST** `/invitations/verify-email/{token}`

**Response:**
```json
{
  "message": "Email verified successfully",
  "email": "user@example.com"
}
```

---

## 💳 Subscription Endpoints

### List Subscription Plans
**GET** `/subscriptions/plans`

**Response:**
```json
[
  {
    "id": 1,
    "name": "free",
    "display_name": "Free",
    "description": "Perfect for trying out the platform",
    "price_monthly_usd": 0,
    "price_yearly_usd": 0,
    "price_monthly_eur": 0,
    "price_yearly_eur": 0,
    "max_projects": 1,
    "max_users": 1,
    "max_storage_gb": 1,
    "features": {
      "features": ["1 project", "1 user", "1GB storage"]
    },
    "is_active": true
  }
]
```

### Create Checkout Session
**POST** `/subscriptions/organizations/{id}/checkout`

**Body:**
```json
{
  "plan_id": 2,
  "billing_cycle": "monthly",
  "success_url": "http://localhost:5173/billing/success",
  "cancel_url": "http://localhost:5173/pricing"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/..."
}
```

### Get Organization Subscription
**GET** `/subscriptions/organizations/{id}/subscription`

**Response:**
```json
{
  "id": 1,
  "organization_id": 1,
  "plan_id": 2,
  "status": "active",
  "current_period_start": "2025-09-01T00:00:00Z",
  "current_period_end": "2025-10-01T00:00:00Z",
  "cancel_at_period_end": false,
  "plan": {
    "name": "starter",
    "display_name": "Starter",
    "price_monthly_usd": 990
  }
}
```

### Get Usage Metrics
**GET** `/subscriptions/organizations/{id}/usage`

**Response:**
```json
{
  "current_projects_count": 2,
  "max_projects": 3,
  "current_users_count": 3,
  "max_users": 5,
  "current_storage_gb": 1.5,
  "max_storage_gb": 5,
  "projects_percentage": 66.67,
  "users_percentage": 60.0,
  "storage_percentage": 30.0
}
```

### Create Customer Portal Session
**POST** `/subscriptions/organizations/{id}/portal`

**Response:**
```json
{
  "portal_url": "https://billing.stripe.com/..."
}
```

### Cancel Subscription
**POST** `/subscriptions/organizations/{id}/cancel`

**Response:**
```json
{
  "message": "Subscription will be cancelled at period end",
  "cancel_at": "2025-10-01T00:00:00Z"
}
```

---

## 📊 Billing Endpoints

### Get Billing History
**GET** `/subscriptions/organizations/{id}/billing-history`

**Response:**
```json
[
  {
    "id": 1,
    "amount": 990,
    "currency": "usd",
    "status": "paid",
    "description": "Starter Plan - Monthly",
    "invoice_date": "2025-09-01T00:00:00Z",
    "paid_at": "2025-09-01T00:01:00Z",
    "invoice_url": "https://invoice.stripe.com/...",
    "invoice_pdf": "https://invoice.stripe.com/.../pdf"
  }
]
```

---

## 📁 Project Endpoints

### List Projects
**GET** `/projects`

**Query Parameters:**
- `organization_id` (optional): Filter by organization

**Response:**
```json
[
  {
    "id": 1,
    "name": "AI Chatbot Platform",
    "description": "Customer service AI chatbot",
    "organization_id": 1,
    "created_at": "2025-09-30T00:00:00Z"
  }
]
```

### Create Project
**POST** `/projects`

**Body:**
```json
{
  "name": "New Project",
  "description": "Project description",
  "organization_id": 1
}
```

### Get Project
**GET** `/projects/{id}`

### Update Project
**PUT** `/projects/{id}`

### Delete Project
**DELETE** `/projects/{id}`

---

## 🔔 Webhook Endpoints

### Stripe Subscription Webhooks
**POST** `/webhooks/stripe`

**Headers:**
```
Stripe-Signature: {signature}
Content-Type: application/json
```

**Handled Events:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `checkout.session.completed`

---

## 🗄️ Seeded Test Data

### Users (All use password: `admin123`)
```
admin@example.com    - Admin User     - Owner of Dev Team
john@example.com     - John Doe       - Admin in Dev, Owner of Marketing
jane@example.com     - Jane Smith     - Member in Dev, Admin in Research
bob@example.com      - Bob Wilson     - Member in Marketing
```

### Organizations
```
1. Development Team  - 3 members (admin, john, jane)
2. Marketing Team    - 2 members (john, bob)
3. Research Team     - 2 members (admin, jane)
```

### Subscription Plans
```
1. Free         - $0/month    - 1 project, 1 user, 1GB
2. Starter      - $9.90/month - 3 projects, 5 users, 5GB
3. Professional - $29.90/month - 10 projects, 20 users, 50GB
4. Business     - $99.90/month - 50 projects, 100 users, 500GB
```

### Projects
```
1. AI Chatbot Platform       - Development Team
2. Content Generation Tool   - Marketing Team
3. Document Analyzer         - Development Team
4. Research Assistant        - Research Team
```

---

## 🚀 Quick Start Examples

### 1. Login and Get Organizations
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# Save the access_token from response

# Get organizations
curl http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer {access_token}"
```

### 2. Invite Team Member
```bash
curl -X POST http://localhost:8000/api/v1/invitations/organizations/1/invitations \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newmember@example.com",
    "role": "member",
    "message": "Welcome to the team!"
  }'
```

### 3. Subscribe to Plan
```bash
# Get available plans
curl http://localhost:8000/api/v1/subscriptions/plans

# Create checkout session
curl -X POST http://localhost:8000/api/v1/subscriptions/organizations/1/checkout \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 2,
    "billing_cycle": "monthly",
    "success_url": "http://localhost:5173/success",
    "cancel_url": "http://localhost:5173/pricing"
  }'
```

---

## 🔒 Security Notes

### Authentication
- All protected endpoints require valid JWT token
- Tokens expire after configured time (default: 30 minutes)
- Use refresh tokens for long-lived sessions

### Authorization
- Organization owners can: manage members, change settings, delete org
- Organization admins can: manage members, invite users
- Organization members can: view organization, access projects
- Organization viewers can: view organization only

### Invitations
- Invitations expire after 7 days
- Only admins and owners can invite members
- Invitation tokens are single-use
- Email must match invited email to accept

---

## 📖 Response Codes

```
200 OK              - Success
201 Created         - Resource created
204 No Content      - Success with no response body
400 Bad Request     - Invalid request data
401 Unauthorized    - Missing or invalid token
403 Forbidden       - Insufficient permissions
404 Not Found       - Resource not found
409 Conflict        - Resource already exists
422 Unprocessable   - Validation error
500 Server Error    - Internal server error
```

---

## 🧪 Testing with Postman

1. Import `postman_collection.json`
2. Set `base_url` to `http://localhost:8000`
3. Login using the "Login" request (saves token automatically)
4. Test all endpoints!

**Collection includes:**
- ✅ All 30+ endpoints
- ✅ Auto-authentication
- ✅ Environment variables
- ✅ Example requests
- ✅ Test scripts

---

## 📞 Support

For issues or questions:
- Check logs: `poetry run uvicorn src.main:app --reload`
- Test database: `poetry run python scripts/seed.py`
- View API docs: `http://localhost:8000/docs`
- View Redoc: `http://localhost:8000/redoc`

---

**Last Updated:** September 30, 2025
**API Version:** v1
**Total Endpoints:** 30+
