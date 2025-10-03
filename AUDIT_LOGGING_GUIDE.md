# 📊 Audit Logging Implementation Guide

## ✅ What's Implemented

### 1. Structured Audit Logger
- **File**: `src/common/audit_logger.py`
- **Logs to**: `logs/audit.log` (separate from application logs)
- **Format**: JSON for easy parsing by external tools
- **Separate from**: Application logs (`logs/app.log`)

### 2. Hidden API Docs in Production
- **File**: `src/main.py`
- **Behavior**: 
  - Development: `/docs`, `/redoc`, `/openapi.json` available
  - Production: All docs endpoints return 404

### 3. Structured Application Logging
- **File**: `src/main.py`
- **Development**: Human-readable format
- **Production**: JSON format for log aggregation tools

---

## 📝 How to Use Audit Logging

### Example 1: Login Endpoint

```python
# File: src/auth/routes.py

from fastapi import Request, HTTPException
from src.common.audit_logger import log_login_success, log_login_failure

@router.post('/login')
async def login(
    request: Request,  # Add Request parameter
    credentials: LoginCredentials,
    db: AsyncSession = Depends(get_async_session)
):
    try:
        user = await authenticate_user(db, credentials.email, credentials.password)
        
        if not user:
            # Log failed attempt
            log_login_failure(
                email=credentials.email,
                request=request,
                reason='invalid_credentials'
            )
            raise HTTPException(
                status_code=401,
                detail='Incorrect email or password'
            )
        
        # Log successful login
        log_login_success(
            user_id=user.id,
            email=user.email,
            request=request
        )
        
        token = create_access_token({'sub': user.email})
        return {'access_token': token}
        
    except HTTPException:
        raise
    except Exception as e:
        log_login_failure(
            email=credentials.email,
            request=request,
            reason=f'error: {str(e)}'
        )
        raise
```

### Example 2: Role Change

```python
# File: src/organizations/routes.py

from fastapi import Request
from src.common.audit_logger import log_role_change

@router.patch('/{organization_id}/members/{member_id}/role')
async def update_member_role(
    organization_id: int,
    member_id: int,
    new_role: str,
    request: Request,  # Add Request parameter
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    # Get current member
    member = await get_organization_member(db, organization_id, member_id)
    old_role = member.role
    
    # Update role
    member.role = new_role
    await db.commit()
    
    # Log the change
    log_role_change(
        user_id=current_user.id,
        organization_id=organization_id,
        target_user_id=member_id,
        old_role=old_role,
        new_role=new_role,
        request=request
    )
    
    return {'message': 'Role updated successfully'}
```

### Example 3: Data Access

```python
# File: src/organizations/routes.py

from src.common.audit_logger import AuditLogger, EventStatus

@router.get('/{organization_id}/billing')
async def get_billing_info(
    organization_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    # Log access to sensitive billing data
    AuditLogger.log_data_access(
        action='view_billing',
        user_id=current_user.id,
        organization_id=organization_id,
        resource='billing',
        resource_id=str(organization_id),
        request=request,
        metadata={'endpoint': '/billing'}
    )
    
    billing_info = await get_billing(db, organization_id)
    return billing_info
```

### Example 4: Permission Denied

```python
# File: src/organizations/service.py

from src.common.audit_logger import log_permission_denied
from fastapi import Request

async def delete_organization(
    db: AsyncSession,
    organization_id: int,
    user: User,
    request: Request
):
    member = await get_member(db, organization_id, user.id)
    
    if member.role != 'owner':
        # Log permission denied
        log_permission_denied(
            user_id=user.id,
            organization_id=organization_id,
            resource='organization',
            resource_id=str(organization_id),
            request=request,
            required_permission='owner'
        )
        
        raise HTTPException(
            status_code=403,
            detail='Only organization owners can delete organizations'
        )
    
    # Proceed with deletion...
```

---

## 📋 Events to Log

### Authentication Events (Use these functions):
- ✅ `log_login_success(user_id, email, request)`
- ✅ `log_login_failure(email, request, reason)`
- ✅ `log_logout(user_id, email, request)`
- ✅ `log_password_reset_request(email, request)`
- ✅ `log_password_reset_complete(user_id, email, request)`
- ✅ `log_email_verification(user_id, email, request)`

### Authorization Events:
- ✅ `log_permission_denied(user_id, org_id, resource, resource_id, request, required_permission)`

### Data Modification Events:
- ✅ `log_role_change(user_id, org_id, target_user_id, old_role, new_role, request)`
- ✅ `log_organization_member_added(user_id, org_id, new_member_id, role, request)`
- ✅ `log_organization_member_removed(user_id, org_id, removed_member_id, request)`

### Custom Events (Use AuditLogger directly):
```python
from src.common.audit_logger import AuditLogger, EventStatus

# Data access
AuditLogger.log_data_access(
    action='export_data',
    user_id=user.id,
    organization_id=org.id,
    resource='user_data',
    resource_id='all',
    request=request
)

# Data modification
AuditLogger.log_data_modification(
    action='bulk_delete',
    user_id=user.id,
    organization_id=org.id,
    resource='projects',
    resource_id='multiple',
    request=request,
    metadata={'count': 10}
)
```

---

## 📊 Log Output Examples

### Successful Login:
```json
{
  "timestamp": "2025-09-30T12:34:56.789Z",
  "event_type": "authentication",
  "action": "login",
  "status": "success",
  "user_id": 123,
  "organization_id": null,
  "resource": "user",
  "resource_id": "user@example.com",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "metadata": {
    "email": "user@example.com"
  }
}
```

### Failed Login:
```json
{
  "timestamp": "2025-09-30T12:35:01.234Z",
  "event_type": "authentication",
  "action": "login",
  "status": "failure",
  "user_id": null,
  "organization_id": null,
  "resource": "user",
  "resource_id": "user@example.com",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "metadata": {
    "email": "user@example.com",
    "reason": "invalid_credentials"
  }
}
```

### Role Change:
```json
{
  "timestamp": "2025-09-30T12:36:15.456Z",
  "event_type": "data_modification",
  "action": "role_change",
  "status": "success",
  "user_id": 123,
  "organization_id": 456,
  "resource": "user_role",
  "resource_id": "789",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "metadata": {
    "changes": {
      "old_role": "member",
      "new_role": "admin"
    }
  }
}
```

---

## 🔍 Analyzing Audit Logs

### View Recent Logs:
```bash
# View last 20 audit events
tail -n 20 logs/audit.log | jq .

# View failed login attempts
cat logs/audit.log | jq 'select(.action=="login" and .status=="failure")'

# View all actions by a specific user
cat logs/audit.log | jq 'select(.user_id==123)'

# View permission denied events
cat logs/audit.log | jq 'select(.action=="permission_denied")'

# View events for a specific organization
cat logs/audit.log | jq 'select(.organization_id==456)'

# Count failed login attempts by email
cat logs/audit.log | jq -r 'select(.action=="login" and .status=="failure") | .metadata.email' | sort | uniq -c | sort -rn
```

---

## 🚀 Next Steps: External Logging Tools

### Option 1: Sentry (Recommended for Getting Started)

**Setup:**
```bash
poetry add sentry-sdk[fastapi]
```

**Configuration:**
```python
# File: src/main.py

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if IS_PRODUCTION:
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FastApiIntegration()],
        environment='production',
        traces_sample_rate=0.1,  # 10% of transactions
    )
```

**Benefits:**
- Error tracking with stack traces
- Performance monitoring
- User context tracking
- Breadcrumbs for debugging

**Cost:** Free tier + $26/month for teams

---

### Option 2: ELK Stack (For Advanced Users)

**Components:**
- **Elasticsearch**: Search and analytics
- **Logstash**: Log collection and parsing
- **Kibana**: Visualization

**Setup:**
```bash
# Install Filebeat for log shipping
# Configure to send logs to Logstash/Elasticsearch
```

**Benefits:**
- Full-text search
- Powerful visualizations
- Alerting
- Custom dashboards

**Cost:** Self-hosted (free) or Elastic Cloud ($95/month)

---

### Option 3: AWS CloudWatch (If on AWS)

**Setup:**
```python
# Install watchtower
poetry add watchtower

# Configure CloudWatch handler
import watchtower
import boto3

cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group='saas-boilerplate',
    stream_name='audit-logs'
)
audit_logger.addHandler(cloudwatch_handler)
```

**Benefits:**
- Integrated with AWS services
- Good search capabilities
- Alarms and metrics

**Cost:** Pay-per-use ($0.50 per GB)

---

### Option 4: Grafana Loki (Cost-Effective)

**Setup:**
```yaml
# docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
  
  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./logs:/logs
      - ./promtail-config.yaml:/etc/promtail/config.yaml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
```

**Benefits:**
- Free and open source
- Great for logs + metrics
- Beautiful dashboards
- Low resource usage

**Cost:** Free (hosting costs only)

---

## 📋 Implementation Checklist

### ✅ Completed:
- [x] Created audit logger module
- [x] Added structured logging
- [x] Hidden API docs in production
- [x] Created logs directory
- [x] System startup/shutdown logging
- [x] Documentation

### 🎯 Next Steps (This Week):
- [ ] Add audit logging to auth endpoints
- [ ] Add audit logging to organization endpoints
- [ ] Test audit logs locally
- [ ] Review and add missing events
- [ ] Choose external logging tool
- [ ] Set up log rotation

### 📅 Future (Next Month):
- [ ] Integrate Sentry for error tracking
- [ ] Set up log retention policy (30-90 days)
- [ ] Create audit log dashboard
- [ ] Set up alerts for security events
- [ ] Compliance review (GDPR, SOC2)

---

## 🔒 Security Best Practices

### What to Log:
✅ Authentication attempts (success and failure)
✅ Authorization failures
✅ Sensitive data access
✅ Data modifications (especially role/permission changes)
✅ Account changes (email, password)
✅ Administrative actions

### What NOT to Log:
❌ Passwords (plain or hashed)
❌ Sensitive personal data (SSN, credit cards)
❌ Session tokens
❌ API keys
❌ Full request/response bodies (may contain sensitive data)

### Log Retention:
- **Audit logs**: Keep for 90 days minimum (compliance)
- **Application logs**: Keep for 30 days
- **Archive**: Consider archiving to S3/cold storage after 90 days

---

## 🎯 Quick Start

### 1. Test Locally:
```bash
# Start the app
cd backend
poetry run uvicorn src.main:app --reload

# Make some requests to generate logs
# Check logs directory
ls -la logs/
cat logs/audit.log | jq .
```

### 2. Add to Existing Endpoints:
Pick 2-3 critical endpoints (login, role change, etc.) and add audit logging following the examples above.

### 3. Review Logs:
Check that logs are being generated correctly with proper structure.

### 4. Plan External Tool:
Decide on Sentry or another tool for production.

---

## 📞 Questions?

- **Where are logs stored?** `logs/audit.log` and `logs/app.log`
- **How to rotate logs?** Use `logrotate` on Linux or similar tools
- **Can I change log format?** Yes, modify `audit_logger.py`
- **How to add custom events?** Use `AuditLogger._log_event()` directly
- **Is this GDPR compliant?** Yes, but avoid logging PII

---

**Your audit logging system is ready! Start adding it to critical endpoints.** 📊🔒


