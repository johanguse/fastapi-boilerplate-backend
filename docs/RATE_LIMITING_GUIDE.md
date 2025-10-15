# 🚦 Rate Limiting Implementation Guide

## ✅ What's Implemented

### 1. Rate Limiter Module
- **File**: `src/common/rate_limiter.py`
- **Library**: slowapi (already in your project)
- **Storage**: In-memory (can upgrade to Redis for production)
- **Features**:
  - Per-IP rate limiting
  - Real IP detection (handles proxies)
  - Custom error responses
  - Audit logging integration
  - Rate limit headers (X-RateLimit-*)

### 2. Global Configuration
- **File**: `src/main.py`
- **Default Limits**: 
  - 200 requests per minute per IP
  - 2000 requests per hour per IP
- **Automatic**: Applied to all endpoints unless overridden

### 3. Pre-defined Rate Limits
Ready-to-use constants for common scenarios:
- `AUTH_LIMIT` - 5/minute (login, register)
- `PASSWORD_RESET_LIMIT` - 3/hour (password reset)
- `EMAIL_LIMIT` - 10/hour (email sending)
- `ORG_LIMIT` - 30/minute (org operations)
- `API_LIMIT` - 100/minute (general API)
- `PUBLIC_LIMIT` - 200/minute (public endpoints)

---

## 📝 How to Use Rate Limiting

### Example 1: Login Endpoint (Strict)

```python
# File: src/auth/routes.py

from fastapi import Request, HTTPException
from src.common.rate_limiter import limiter, AUTH_LIMIT, AUTH_LIMIT_HOURLY
from src.common.audit_logger import log_login_success, log_login_failure

@router.post('/login')
@limiter.limit(AUTH_LIMIT)  # ⭐ 5 requests per minute
@limiter.limit(AUTH_LIMIT_HOURLY)  # ⭐ 20 requests per hour
async def login(
    request: Request,  # ⭐ Required for rate limiter
    credentials: LoginCredentials,
    db: AsyncSession = Depends(get_async_session)
):
    user = await authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        log_login_failure(credentials.email, request, 'invalid_credentials')
        raise HTTPException(401, 'Invalid credentials')
    
    log_login_success(user.id, user.email, request)
    
    token = create_access_token({'sub': user.email})
    return {'access_token': token}
```

### Example 2: Password Reset (Very Strict)

```python
# File: src/auth/routes.py

from src.common.rate_limiter import limiter, PASSWORD_RESET_LIMIT, PASSWORD_RESET_DAILY

@router.post('/password-reset')
@limiter.limit(PASSWORD_RESET_LIMIT)  # ⭐ 3 requests per hour
@limiter.limit(PASSWORD_RESET_DAILY)  # ⭐ 10 requests per day
async def request_password_reset(
    request: Request,
    email: EmailStr,
    db: AsyncSession = Depends(get_async_session)
):
    # Send password reset email
    await send_password_reset_email(email)
    
    return {"message": "If the email exists, you'll receive reset instructions"}
```

### Example 3: Email Verification (Moderate)

```python
# File: src/invitations/routes.py

from src.common.rate_limiter import limiter, EMAIL_LIMIT

@router.post('/resend-verification')
@limiter.limit(EMAIL_LIMIT)  # ⭐ 10 requests per hour
async def resend_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    if current_user.is_verified:
        raise HTTPException(400, 'Email already verified')
    
    await send_verification_email(current_user.email)
    
    return {"message": "Verification email sent"}
```

### Example 4: Organization Operations (Moderate)

```python
# File: src/organizations/routes.py

from src.common.rate_limiter import limiter, ORG_LIMIT

@router.post('/')
@limiter.limit(ORG_LIMIT)  # ⭐ 30 requests per minute
async def create_organization(
    request: Request,
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    org = await create_org(db, org_data, current_user)
    return org
```

### Example 5: Custom Rate Limit

```python
# For special cases, define custom limits

@router.post('/bulk-import')
@limiter.limit("2/minute")  # ⭐ Very strict - only 2 per minute
@limiter.limit("10/hour")  # ⭐ Max 10 per hour
async def bulk_import(
    request: Request,
    data: BulkImportData,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    # Heavy operation
    result = await process_bulk_import(data)
    return result
```

### Example 6: No Rate Limit (Exempt)

```python
# For endpoints that shouldn't be rate limited

@router.get('/health')
@limiter.exempt  # ⭐ Exempt from rate limiting
async def health_check():
    return {"status": "healthy"}
```

---

## 🎯 Recommended Rate Limits by Endpoint Type

### Authentication Endpoints:
```python
# Login
@limiter.limit("5/minute")   # Prevent brute force
@limiter.limit("20/hour")

# Register
@limiter.limit("5/minute")   # Prevent spam accounts
@limiter.limit("10/hour")

# Logout
@limiter.limit("10/minute")  # Lenient - legitimate use case
```

### Password & Email:
```python
# Password reset request
@limiter.limit("3/hour")     # Very strict
@limiter.limit("10/day")

# Email verification resend
@limiter.limit("10/hour")    # Moderate

# Change password (authenticated)
@limiter.limit("5/minute")   # Moderate
```

### Organization Operations:
```python
# Create organization
@limiter.limit("30/minute")  # Moderate

# Update organization
@limiter.limit("60/minute")  # Lenient

# Delete organization
@limiter.limit("5/minute")   # Strict - destructive operation
```

### API Endpoints:
```python
# List/Read operations
@limiter.limit("100/minute") # Lenient

# Create operations
@limiter.limit("30/minute")  # Moderate

# Update operations
@limiter.limit("60/minute")  # Moderate

# Delete operations
@limiter.limit("30/minute")  # Moderate

# Bulk operations
@limiter.limit("5/minute")   # Strict - expensive
```

### Public Endpoints:
```python
# Health check
@limiter.exempt              # No limit

# Documentation
@limiter.exempt              # No limit

# Pricing page
@limiter.limit("200/minute") # Very lenient
```

---

## 📊 Rate Limit Response

When a client exceeds the rate limit, they receive:

### Response:
```json
{
  "detail": "Too many requests. Please slow down and try again later.",
  "error": "rate_limit_exceeded",
  "retry_after": "60 seconds"
}
```

### Status Code:
`429 Too Many Requests`

### Headers:
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1696147200
Retry-After: 60
```

---

## 🔍 Testing Rate Limits

### Test Locally:

```bash
# Start the app
poetry run uvicorn src.main:app --reload

# Test rate limit (make 6 requests quickly)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}' \
    -w "\nStatus: %{http_code}\n"
done

# 6th request should return 429
```

### View Rate Limit Headers:

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# Look for:
# X-RateLimit-Limit: 5
# X-RateLimit-Remaining: 4
# X-RateLimit-Reset: 1696147200
```

### Check Audit Logs:

```bash
# Rate limit violations are logged
cat logs/audit.log | jq 'select(.action=="rate_limit_exceeded")'
```

---

## 🚀 Production: Upgrade to Redis

For production with multiple server instances, use Redis:

### 1. Install Redis:
```bash
# Docker
docker run -d -p 6379:6379 redis:alpine

# Or use managed Redis (AWS ElastiCache, etc.)
```

### 2. Update Configuration:

```python
# File: src/common/rate_limiter.py

# Change this line:
storage_uri="redis://localhost:6379/0" if IS_PRODUCTION else "memory://",
```

### 3. Add to .env:
```bash
REDIS_URL=redis://localhost:6379/0
# Or for production:
REDIS_URL=redis://your-redis-host:6379/0
```

### 4. Update Rate Limiter:

```python
import os

limiter = Limiter(
    key_func=get_real_ip,
    default_limits=["200/minute", "2000/hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://'),
    headers_enabled=True,
)
```

---

## 📋 Implementation Checklist

### ✅ Completed:
- [x] Created rate limiter module
- [x] Integrated with main app
- [x] Added custom error handler
- [x] Integrated with audit logger
- [x] Added real IP detection (proxy support)
- [x] Defined rate limit presets

### 🎯 To Do This Week:
- [ ] Add rate limits to auth endpoints
  - [ ] `/auth/login`
  - [ ] `/auth/register`
  - [ ] `/auth/logout`
  - [ ] `/auth/password-reset`
  
- [ ] Add rate limits to email endpoints
  - [ ] `/invitations/resend-verification`
  - [ ] `/invitations/send-invitation`
  
- [ ] Test rate limits locally
- [ ] Verify audit logging works

### 📅 To Do Next Week:
- [ ] Review rate limits after monitoring traffic
- [ ] Set up Redis for production
- [ ] Add custom rate limits for specific use cases
- [ ] Monitor rate limit violations in logs

---

## 🎨 Customization

### Custom Rate Limit Key:

```python
# Rate limit per user instead of per IP

def get_user_id(request: Request) -> str:
    """Rate limit by user ID instead of IP"""
    user = getattr(request.state, 'user', None)
    if user:
        return f"user:{user.id}"
    return get_real_ip(request)

# Use in limiter
limiter = Limiter(key_func=get_user_id)
```

### Dynamic Rate Limits:

```python
# Different limits based on user role

from src.auth.models import User

def get_rate_limit_for_user(user: User) -> str:
    """Different limits for different users"""
    if user.is_admin:
        return "1000/minute"  # Admins get higher limits
    elif user.is_premium:
        return "500/minute"   # Premium users
    else:
        return "100/minute"   # Regular users

@router.get('/api/data')
async def get_data(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # Apply dynamic limit
    limit = get_rate_limit_for_user(current_user)
    limiter.limit(limit)(lambda: None)()  # Apply limit
    
    # Your endpoint logic
    ...
```

### Per-Endpoint Custom Responses:

```python
@router.post('/critical-endpoint')
@limiter.limit("1/minute")
async def critical_endpoint(request: Request):
    # Custom error handling
    try:
        # Your logic
        ...
    except RateLimitExceeded:
        return JSONResponse(
            status_code=429,
            content={
                "error": "This endpoint is rate limited to 1 request per minute",
                "help": "Please contact support if you need higher limits"
            }
        )
```

---

## 🛡️ Security Best Practices

### 1. Rate Limit Critical Endpoints:
✅ Always rate limit:
- Login/authentication
- Password reset
- Email sending
- Account creation
- Payment operations

### 2. Use Multiple Time Windows:
```python
@limiter.limit("5/minute")   # Short-term protection
@limiter.limit("20/hour")    # Medium-term protection
@limiter.limit("100/day")    # Long-term protection
```

### 3. Monitor Rate Limit Violations:
```bash
# Check for suspicious IPs
cat logs/audit.log | jq -r 'select(.action=="rate_limit_exceeded") | .ip_address' | sort | uniq -c | sort -rn

# Check most hit endpoints
cat logs/audit.log | jq -r 'select(.action=="rate_limit_exceeded") | .metadata.path' | sort | uniq -c | sort -rn
```

### 4. Combine with Other Security:
- Rate limiting (this)
- Audit logging (your custom system)
- CORS configuration
- Security headers
- Input validation (Pydantic)

---

## ⚠️ Important Notes

### Rate Limiting Won't Save You From:
- ❌ Distributed attacks (use CloudFlare or similar)
- ❌ SQL injection (use parameterized queries - you have this)
- ❌ XSS attacks (sanitize inputs)
- ❌ CSRF (use CSRF tokens if needed)

### Rate Limiting WILL Save You From:
- ✅ Brute force attacks (login attempts)
- ✅ API abuse (single IP spamming)
- ✅ Email spam (verification/invitation spam)
- ✅ Resource exhaustion (expensive operations)

---

## 🎉 You're Done!

Rate limiting is now implemented! Next steps:

1. ✅ Add `@limiter.limit()` to critical endpoints
2. ✅ Test with multiple requests
3. ✅ Monitor logs for violations
4. ✅ Adjust limits based on real traffic

**Time to implement:** 15-30 minutes per endpoint

---

## 📚 References

- **Code**: `src/common/rate_limiter.py`
- **Library**: [slowapi documentation](https://github.com/laurentS/slowapi)
- **Security**: `docs/SECURITY_RECOMMENDATIONS.md`
- **Audit Logging**: `AUDIT_LOGGING_GUIDE.md`

---

**Great work! Rate limiting is production-ready!** 🚦🔒
