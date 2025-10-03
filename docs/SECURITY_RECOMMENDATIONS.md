# 🔒 Backend Security Recommendations

## 📋 Current Security Status

### ✅ **What's Already Implemented:**

#### 1. Authentication & Authorization ✅
- **JWT Token Authentication (RS256)** - Industry standard asymmetric encryption
- **Password Hashing (bcrypt)** - Secure password storage with salt
- **Token Validation with Expiration** - 15-minute access tokens, 7-day refresh tokens
- **Role-Based Access Control (RBAC)** - Owner/Admin/Member roles
- **Email Verification System** - Secure token-based verification (24-hour expiration)
- **Password Reset Flow** - Secure token-based reset with expiration

**Files:**
- `src/common/security.py` - Core security functions
- `src/auth/models.py` - User model with roles
- `src/invitations/models.py` - Email verification and reset tokens

#### 2. Input Validation ✅
- **Pydantic V2 Models** - Automatic request validation
- **Type Validation** - Strong typing for all endpoints
- **Email Validation** - RFC-compliant email validation
- **Required Field Validation** - Enforced at schema level

**Files:**
- `src/*/schemas.py` - Pydantic schemas for all domains

#### 3. Database Security ✅
- **SQLAlchemy ORM** - Prevents SQL injection via parameterized queries
- **Async Sessions** - Modern async/await pattern
- **Proper Transaction Management** - ACID compliance
- **Organization-Scoped Queries** - Multi-tenancy data isolation

**Files:**
- `src/common/database.py` - Database configuration
- `src/common/session.py` - Session management

#### 4. API Security ✅
- **OAuth2 Password Bearer** - Standard OAuth2 implementation
- **Protected Endpoints** - Dependency injection for auth
- **Organization-Scoped Access** - Users only see their organization data
- **Proper Error Handling** - No sensitive data in error messages

#### 5. Email Security ✅
- **Token-Based Verification** - Cryptographically secure tokens
- **Token Expiration** - 24-hour validity for email tokens
- **Secure Invitation System** - Token-based team invitations
- **Resend Integration** - Professional email delivery

**Files:**
- `src/invitations/service.py` - Email security logic
- `src/invitations/email_service.py` - Email sending service

---

## ⚠️ **CRITICAL SECURITY IMPROVEMENTS NEEDED**

### 1. 🔴 **CORS Configuration** (HIGH PRIORITY)

**Current Issue:** CORS allows all origins (security risk)

**Fix Required:**
```python
# File: src/main.py

from fastapi.middleware.cors import CORSMiddleware
from src.common.config import settings

# Add after app initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Restrict to specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Accept-Language"],
    expose_headers=["Content-Language"],
    max_age=600,  # Cache preflight for 10 minutes
)
```

**Add to `src/common/config.py`:**
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # CORS Settings
    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:3000"
        ).split(",")
    )
```

**Environment Variables:**
```bash
# .env (development)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# .env.production
ALLOWED_ORIGINS=https://yourapp.com,https://www.yourapp.com
```

**Time Estimate:** 30 minutes  
**Priority:** 🔴 CRITICAL

---

### 2. 🔴 **Rate Limiting** (HIGH PRIORITY)

**Current Issue:** No rate limiting - vulnerable to brute force attacks

**Fix Required:**
```bash
# Install dependencies
poetry add slowapi
```

**Implementation:**
```python
# File: src/common/rate_limiter.py (NEW)

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # Global default
    storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
)

async def rate_limit_exceeded_handler(
    request: Request, 
    exc: RateLimitExceeded
) -> Response:
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please try again later.",
            "retry_after": exc.detail,
        },
    )
```

**Add to `src/main.py`:**
```python
from src.common.rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Add to app initialization
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

**Apply to Critical Endpoints:**
```python
# File: src/auth/routes.py

from src.common.rate_limiter import limiter
from fastapi import Request

@router.post('/login')
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(
    request: Request,  # Required for rate limiter
    credentials: LoginCredentials,
    db: AsyncSession = Depends(get_async_session)
):
    # ... login logic ...
    pass

@router.post('/register')
@limiter.limit("3/hour")  # 3 registrations per hour
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    # ... registration logic ...
    pass
```

**Rate Limit Recommendations:**
- `/auth/login` - 5 attempts per minute
- `/auth/register` - 3 attempts per hour
- `/auth/forgot-password` - 3 attempts per hour
- `/invitations/send` - 10 per hour
- `/api/v1/*` (general) - 100 per minute per user

**Time Estimate:** 2 hours  
**Priority:** 🔴 CRITICAL

---

### 3. 🔴 **Security Headers** (HIGH PRIORITY)

**Current Issue:** Missing security headers - vulnerable to XSS, clickjacking, MIME sniffing

**Fix Required:**
```python
# File: src/common/middleware.py (UPDATE)

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

async def security_headers_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Add security headers to all responses.
    """
    response = await call_next(request)
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # XSS Protection (legacy, but doesn't hurt)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # HTTPS enforcement (HSTS) - only in production
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://api.stripe.com; "
        "frame-ancestors 'none';"
    )
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy (formerly Feature-Policy)
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=(), payment=(self)"
    )
    
    return response

def add_security_headers_middleware(app: FastAPI) -> None:
    """Add security headers middleware to FastAPI application."""
    app.middleware('http')(security_headers_middleware)
```

**Add to `src/main.py`:**
```python
from src.common.middleware import add_security_headers_middleware

# Add after other middleware
add_security_headers_middleware(app)
```

**Time Estimate:** 1 hour  
**Priority:** 🔴 CRITICAL

---

### 4. 🟡 **Hide API Documentation in Production** (MEDIUM PRIORITY)

**Current Issue:** API docs (`/docs`, `/redoc`) are publicly accessible

**Fix Required:**
```python
# File: src/main.py (UPDATE)

import os

IS_PRODUCTION = os.getenv('ENVIRONMENT', 'development') == 'production'

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    # Conditionally disable docs in production
    docs_url='/docs' if not IS_PRODUCTION else None,
    redoc_url='/redoc' if not IS_PRODUCTION else None,
    openapi_url='/openapi.json' if not IS_PRODUCTION else None,
    default_response_class=ORJSONResponse,
)
```

**Or implement authentication for docs:**
```python
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def verify_docs_credentials(
    credentials: HTTPBasicCredentials = Depends(security)
):
    """Require basic auth for API docs in production."""
    if not IS_PRODUCTION:
        return True
    
    correct_username = secrets.compare_digest(
        credentials.username, 
        os.getenv("DOCS_USERNAME", "admin")
    )
    correct_password = secrets.compare_digest(
        credentials.password, 
        os.getenv("DOCS_PASSWORD", "")
    )
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

@app.get("/docs", include_in_schema=False)
async def get_documentation(authenticated: bool = Depends(verify_docs_credentials)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
```

**Time Estimate:** 30 minutes  
**Priority:** 🟡 MEDIUM

---

### 5. 🟡 **Structured Logging & Audit Logs** (MEDIUM PRIORITY)

**Current Issue:** Basic logging, no audit trail for sensitive operations

**Fix Required:**
```python
# File: src/common/audit_logger.py (NEW)

import logging
import json
from datetime import UTC, datetime
from typing import Any, Optional
from fastapi import Request

logger = logging.getLogger("audit")

class AuditLogger:
    """Structured audit logging for security-sensitive operations."""
    
    @staticmethod
    def log_event(
        event_type: str,
        user_id: Optional[int],
        organization_id: Optional[int],
        action: str,
        resource: str,
        resource_id: Optional[str],
        status: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Log a security audit event."""
        audit_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "organization_id": organization_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "status": status,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "metadata": metadata or {},
        }
        logger.info(json.dumps(audit_data))
    
    @staticmethod
    def log_auth_event(
        action: str,
        user_id: Optional[int],
        email: str,
        status: str,
        request: Request,
        reason: Optional[str] = None,
    ):
        """Log authentication events."""
        AuditLogger.log_event(
            event_type="authentication",
            user_id=user_id,
            organization_id=None,
            action=action,
            resource="user",
            resource_id=email,
            status=status,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"reason": reason} if reason else None,
        )
    
    @staticmethod
    def log_data_access(
        user_id: int,
        organization_id: int,
        resource: str,
        resource_id: str,
        action: str,
        request: Request,
    ):
        """Log data access events."""
        AuditLogger.log_event(
            event_type="data_access",
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            status="success",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
```

**Usage Examples:**
```python
# In login endpoint
from src.common.audit_logger import AuditLogger

@router.post('/login')
async def login(request: Request, credentials: LoginCredentials, ...):
    try:
        user = await authenticate_user(...)
        AuditLogger.log_auth_event(
            action="login",
            user_id=user.id,
            email=credentials.email,
            status="success",
            request=request,
        )
        return {"access_token": token}
    except HTTPException:
        AuditLogger.log_auth_event(
            action="login",
            user_id=None,
            email=credentials.email,
            status="failure",
            request=request,
            reason="invalid_credentials",
        )
        raise
```

**Events to Log:**
- Authentication (login, logout, failed attempts)
- Authorization (permission denied)
- Data access (sensitive resource access)
- Data modification (create, update, delete)
- Role changes
- Organization membership changes
- Email verification
- Password resets

**Time Estimate:** 3-4 hours  
**Priority:** 🟡 MEDIUM

---

### 6. 🟡 **Input Sanitization & Length Limits** (MEDIUM PRIORITY)

**Current Issue:** No HTML sanitization, no maximum length validation

**Fix Required:**
```bash
# Install dependency
poetry add bleach
```

**Implementation:**
```python
# File: src/common/sanitization.py (NEW)

import bleach
from typing import Optional

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt'],
}

def sanitize_html(html: str) -> str:
    """Sanitize HTML content to prevent XSS."""
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )

def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize plain text input."""
    # Remove any HTML tags
    clean_text = bleach.clean(text, tags=[], strip=True)
    
    # Trim to max length if specified
    if max_length and len(clean_text) > max_length:
        clean_text = clean_text[:max_length]
    
    return clean_text.strip()
```

**Add Length Limits to Schemas:**
```python
# File: src/organizations/schemas.py (UPDATE)

from pydantic import BaseModel, Field, field_validator
from src.common.sanitization import sanitize_text

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name', 'description')
    @classmethod
    def sanitize_fields(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return sanitize_text(v)
        return v
```

**Common Length Limits:**
- Organization name: 100 characters
- Project name: 100 characters
- Description: 500 characters
- Bio: 1000 characters
- Email: 255 characters
- Name: 100 characters

**Time Estimate:** 2 hours  
**Priority:** 🟡 MEDIUM

---

### 7. 🟢 **Environment Secrets Management** (LOW PRIORITY)

**Current Issue:** Secrets in .env file (acceptable for now, but improve for production)

**Production Recommendations:**

**Option 1: AWS Secrets Manager**
```python
# File: src/common/secrets.py (NEW)

import boto3
import json
from functools import lru_cache

@lru_cache()
def get_secret(secret_name: str) -> dict:
    """Retrieve secrets from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage in config.py
if os.getenv('ENVIRONMENT') == 'production':
    secrets = get_secret('prod/saas-boilerplate')
    DATABASE_URL = secrets['DATABASE_URL']
    JWT_SECRET = secrets['JWT_SECRET']
else:
    DATABASE_URL = os.getenv('DATABASE_URL')
    JWT_SECRET = os.getenv('JWT_SECRET')
```

**Option 2: HashiCorp Vault**
**Option 3: Docker Secrets**
**Option 4: Kubernetes Secrets**

**Time Estimate:** 4-6 hours (depends on infrastructure)  
**Priority:** 🟢 LOW (but CRITICAL for production)

---

### 8. 🟢 **Database Connection Security** (LOW PRIORITY)

**Current Status:** Using SSL for Neon PostgreSQL ✅

**Additional Recommendations:**
```python
# File: src/common/database.py (ENHANCE)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # Disable in production
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={
        "ssl": "require",  # Force SSL
        "server_settings": {
            "application_name": "saas-boilerplate"
        }
    }
)
```

**Time Estimate:** 30 minutes  
**Priority:** 🟢 LOW

---

## 📋 **SECURITY IMPLEMENTATION CHECKLIST**

### 🔴 Critical (Week 1):
- [ ] Configure CORS with allowed origins
- [ ] Implement rate limiting on auth endpoints
- [ ] Add security headers middleware
- [ ] Test all security features

### 🟡 High Priority (Week 2):
- [ ] Hide API docs in production
- [ ] Implement structured audit logging
- [ ] Add input sanitization and length limits
- [ ] Security code review

### 🟢 Medium Priority (Week 3-4):
- [ ] Set up secrets management for production
- [ ] Enhance database connection security
- [ ] Implement monitoring and alerting
- [ ] Create incident response plan

### 📊 Ongoing:
- [ ] Regular dependency updates (`poetry update`)
- [ ] Security vulnerability scanning
- [ ] Penetration testing (quarterly)
- [ ] Security training for team
- [ ] OWASP Top 10 compliance check

---

## 🛡️ **SECURITY BEST PRACTICES**

### Authentication
- ✅ Use strong password hashing (bcrypt)
- ✅ Implement JWT with short expiration
- ✅ Require email verification
- ⚠️ Add rate limiting on auth endpoints
- ⚠️ Log all authentication attempts
- ⏳ Consider adding 2FA (future)

### Authorization
- ✅ Implement RBAC (Role-Based Access Control)
- ✅ Use dependency injection for auth checks
- ✅ Scope all queries to user's organization
- ⚠️ Audit permission checks
- ⏳ Consider ABAC for complex permissions (future)

### API Security
- ✅ Use HTTPS in production
- ⚠️ Implement rate limiting
- ⚠️ Add CORS restrictions
- ⚠️ Include security headers
- ✅ Validate all inputs with Pydantic
- ⚠️ Sanitize user-generated content

### Data Security
- ✅ Use SQLAlchemy ORM (SQL injection prevention)
- ✅ Encrypt sensitive data in transit (HTTPS)
- ⚠️ Consider encrypting sensitive data at rest
- ✅ Implement proper data isolation (multi-tenancy)
- ⚠️ Regular database backups

### Monitoring & Logging
- ⚠️ Implement structured logging
- ⚠️ Log security events (audit trail)
- ⏳ Set up monitoring and alerting
- ⏳ Integrate with SIEM (future)
- ⚠️ Monitor for suspicious activity

---

## 🚨 **INCIDENT RESPONSE PLAN**

### Detection
1. Monitor logs for suspicious activity
2. Set up alerts for security events
3. Regular security audits

### Response
1. **Immediate Actions:**
   - Identify affected systems
   - Contain the breach
   - Preserve evidence

2. **Investigation:**
   - Determine scope of breach
   - Identify root cause
   - Document timeline

3. **Recovery:**
   - Patch vulnerabilities
   - Restore from backups if needed
   - Verify system integrity

4. **Post-Incident:**
   - Update security measures
   - Notify affected users (if required)
   - Document lessons learned

---

## 📚 **ADDITIONAL RESOURCES**

### Security Standards
- OWASP Top 10: https://owasp.org/Top10/
- OWASP API Security: https://owasp.org/API-Security/
- CWE Top 25: https://cwe.mitre.org/top25/

### Tools
- **Bandit** - Python security linter
- **Safety** - Dependency vulnerability scanner
- **Snyk** - Continuous security monitoring
- **OWASP ZAP** - Penetration testing

### Testing
```bash
# Security vulnerability scanning
poetry add --group dev bandit safety

# Run security checks
poetry run bandit -r src/
poetry run safety check

# In CI/CD
poetry run bandit -r src/ -f json -o bandit-report.json
poetry run safety check --json > safety-report.json
```

---

## ⏱️ **ESTIMATED TIME TO COMPLETE ALL SECURITY FIXES**

| Priority | Time Estimate |
|----------|--------------|
| 🔴 Critical | 3-4 days |
| 🟡 High Priority | 5-6 days |
| 🟢 Medium Priority | 4-5 days |
| **Total** | **12-15 days (2.5-3 weeks)** |

---

## 🎯 **NEXT IMMEDIATE STEPS**

### Today (Day 1):
1. ✅ Review this security document
2. 🔴 Add CORS configuration
3. 🔴 Implement rate limiting
4. 🔴 Test changes

### This Week (Days 2-5):
1. 🔴 Add security headers
2. 🟡 Hide API docs in production
3. 🟡 Set up audit logging
4. 🟡 Security testing

### Next Week (Days 6-10):
1. 🟡 Input sanitization
2. 🟢 Secrets management planning
3. 📊 Security code review
4. 📊 Penetration testing

---

**Your backend has solid security foundations. Implement these critical fixes (3-4 days) to be production-ready!** 🔒🚀
