# Authentication Specification

> **Date**: February 2026
> **Status**: ✅ **ACTIVE — Production-Ready**
> **Scope**: Backend (`usercenter_backend`) + Frontend (`usercenter_frontend`)

---

## Overview

This project uses a **custom Better Auth compatibility layer** on top of **FastAPI Users**. The frontend speaks the Better Auth client protocol; the backend translates every call to FastAPI Users internals.

There is **no real Better Auth server** — the backend implements the same HTTP contract so the `better-auth` npm client works unmodified.

```
Browser (better-auth client)
    │  POST /api/v1/auth/sign-in/email   {email, password}
    │  GET  /api/v1/auth/session
    ▼
FastAPI  —  better_auth_compat.py
    │  verifies via FastAPI Users → UserManager
    │  issues its own HS256 JWT  ← JWT_SECRET
    │  sets   HttpOnly ba_session cookie
    ▼
Protected Routes  —  current_active_user (FastAPI Users)
                     get_current_user     (common/security.py)
```

---

## Architecture Decision: Why Not "Real" Better Auth?

| Approach | Chosen | Reason |
|----------|--------|--------|
| Better Auth (Next.js server) | ✗ | Frontend is a pure Vite SPA (no server) |
| JWKS / EdDSA bridge | ✗ | Over-engineered for single backend; requires JWKS endpoint |
| Shared-secret HS256 compat layer | ✅ | Simple, stateless, one database, one auth source |

---

## Token Architecture

### JWT Format

Tokens are **HS256-signed JWTs** created by `create_better_auth_jwt()`:

```json
{
  "sub":   "42",                              // str(user.id) — numeric DB PK
  "email": "user@example.com",
  "name":  "User Name",
  "iat":   1740000000,
  "exp":   1740003600,                        // iat + JWT_LIFETIME_SECONDS (default 3600)
  "aud":   ["fastapi-users:auth"],
  "iss":   "better-auth-compat"
}
```

> **Important:** `sub` is the **numeric integer user ID cast to a string**, not an email address.
> Backend code must always `int(payload["sub"])` and query `WHERE users.id = ?`.

### Signing Secret

| Setting | Env Var | Used By |
|---------|---------|---------|
| `JWT_SECRET` | `JWT_SECRET` | `better_auth_compat.py` — issues & verifies compat tokens |
| `SECRET_KEY` | `SECRET_KEY` | `common/security.py` — fallback verify for FastAPI Users tokens |

`common/security.py::get_current_user` tries **both secrets** in order so both token issuers are accepted:

```python
for secret in (settings.JWT_SECRET, settings.SECRET_KEY):
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"],
                             audience=["fastapi-users:auth"])
        break
    except jwt.InvalidTokenError:
        continue
```

> **Production rule:** Set `JWT_SECRET` and `SECRET_KEY` to the **same strong value** via env var to keep a single secret in rotation.

---

## Cookie Strategy

The backend issues **one HttpOnly cookie** on sign-in and sign-up:

| Cookie | Value | Flags |
|--------|-------|-------|
| `ba_session` | Raw JWT string | `HttpOnly`, `SameSite=lax` (dev) / `SameSite=none; Secure` (prod) |
| `ba_active_org` | Active team/org ID (string) | Same flags |
| `ba_active_team` | Active team ID (string) | Same flags |

Cookie security flags are derived dynamically from `FRONTEND_URL`:

```python
def _cookie_options() -> dict:
    secure   = settings.FRONTEND_URL.startswith("https")
    samesite = "none" if secure else "lax"
    domain   = parsed.hostname  # only when not localhost
```

> **Do not** `document.cookie` or `localStorage` for the session token — it lives in an HttpOnly cookie and is intentionally inaccessible to JavaScript.

---

## Backend Auth Endpoints

All endpoints are mounted at `/api/v1` via `better_auth_router`.

### `POST /api/v1/auth/sign-in/email`

**Request body:**
```json
{ "email": "user@example.com", "password": "secret" }
```

**Success (`200`):**
```json
{
  "user": {
    "id": "42",
    "email": "user@example.com",
    "name": "User Name",
    "emailVerified": false,
    "createdAt": "2026-01-01T00:00:00+00:00",
    "updatedAt": null
  },
  "session": {
    "token": "<JWT>",
    "expiresAt": "2026-01-01T01:00:00+00:00"
  }
}
```

Sets `ba_session` cookie.

**Error responses:**

| Code | `error` field | Meaning |
|------|--------------|---------|
| `400` | `INVALID_CREDENTIALS` | Wrong email or password |
| `400` | `USER_INACTIVE` | Account disabled |

---

### `POST /api/v1/auth/sign-up/email`

**Request body:**
```json
{ "email": "user@example.com", "password": "secret", "name": "User Name" }
```

**Success (`200`):** Same shape as sign-in.

Sets `ba_session` cookie.

**Error responses:**

| Code | `error` field | Meaning |
|------|--------------|---------|
| `400` | `USER_EXISTS` | Email already registered |
| `400` | `SIGN_UP_FAILED` | Unexpected creation error |

---

### `POST /api/v1/auth/sign-out`

Clears `ba_session`, `ba_active_org`, `ba_active_team` cookies.

**Response:** `{ "success": true }`

---

### `GET /api/v1/auth/session`
### `GET /api/v1/auth/get-session` *(alias)*

Reads the token from `Authorization: Bearer <token>` header **or** the `ba_session` cookie.

**Success (`200`):**
```json
{
  "user": {
    "id": "42",
    "email": "user@example.com",
    "name": "User Name",
    "emailVerified": false,
    "createdAt": "...",
    "updatedAt": "..."
  },
  "session": {
    "expiresAt": "2026-01-01T01:00:00+00:00",
    "activeOrganizationId": "7",
    "activeTeamId": null
  }
}
```

> **Note:** The raw JWT is intentionally **omitted** from the session body — it lives in the HttpOnly cookie and must not be exposed to JavaScript.

**Error responses:**

| Code | Meaning |
|------|---------|
| `401 No valid session` | No cookie or header found |
| `401 Invalid token` | JWT malformed or wrong signature |
| `401 Invalid token subject` | `sub` is not a valid integer |
| `401 User not found or inactive` | User deleted or disabled |

---

### Organization Endpoints

These map Better Auth's **organization** concept to the application's **Team** model.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/auth/organization` | List teams the user belongs to |
| `GET` | `/auth/organization/list` | Alias for the above |
| `POST` | `/auth/organization` | Create a new team; sets `ba_active_org` cookie |
| `POST` | `/auth/organization/create` | Alias for the above |
| `POST` | `/auth/organization/set-active` | Switch active organization; sets cookie |
| `GET` | `/auth/organization/list-teams` | Returns `[]` (no nested teams) |
| `POST` | `/auth/organization/set-active-team` | Sets `ba_active_team` cookie |
| `GET` | `/auth/organization/list-members` | Returns `{ members: [] }` (stub) |
| `POST` | `/auth/organization/invite-member` | Returns `{ success: true }` (stub) |
| `POST` | `/auth/organization/accept-invitation` | Returns `{ success: true }` (stub) |
| Others | Various | Stubs returning `{ success: true }` or `[]` |

> Organization endpoints require a valid `ba_session` cookie or `Authorization: Bearer` header.

---

## Frontend Auth Client

### Configuration (`src/lib/api/auth.ts`)

```typescript
const authClient = createAuthClient({
  baseURL: import.meta.env.VITE_API_URL.replace('/api/v1', ''),  // e.g. http://localhost:8000
  basePath: '/api/v1/auth',
  fetchOptions: {
    credentials: 'include',          // sends ba_session HttpOnly cookie
    onError(e) {
      if (e.error?.status === 401) window.location.href = '/auth/login'
    },
  },
  plugins: [organizationClient({ teams: { enabled: true } })],
})
```

> `credentials: 'include'` is **mandatory** — it tells the browser to attach cookies on cross-origin requests.

### Auth Store (`src/stores/auth-store.ts`)

Zustand store with the following key actions:

| Action | Behaviour |
|--------|-----------|
| `login(email, password)` | Calls `signIn.email()`, hydrates `user` from response |
| `register(email, password, name)` | Calls `signUp.email()`, hydrates `user` from response |
| `logout()` | Calls `signOut()`, clears state |
| `checkSession()` | Calls `authClient.getSession()`, hydrates `session` + `user` |
| `reset()` | Clears all state, resets `isInitialized` |

**Error normalization:** Every action wraps raw API errors through `_resolveErrorMessage()` which maps common error codes (`INVALID_CREDENTIALS`, `USER_EXISTS`, `email_not_verified`, etc.) to user-friendly English strings.

### Route Guard (`src/routes/_authenticated/route.tsx`)

TanStack Router `beforeLoad` is the **authoritative** session check:

```typescript
beforeLoad: async () => {
  const { isInitialized, checkSession } = useAuthStore.getState()
  if (!isInitialized) await checkSession()
  if (!useAuthStore.getState().user) {
    throw redirect({ to: '/auth/login', search: { redirect: window.location.pathname } })
  }
}
```

After guarding, the route `loader` fetches organizations and pre-selects the active one.

> `AuthProvider` is a **passthrough wrapper** only — it does NOT call `checkSession()`. All session initialization is owned by the router guard to avoid double-fetching.

---

## Protected Route Patterns (Backend)

### Standard FastAPI Users guard

Used in: `user_routes.py`, most feature routers.

```python
from src.auth.users import current_active_user

@router.get("/me")
async def get_me(user: User = Depends(current_active_user)):
    return user
```

`current_active_user` reads the `Authorization: Bearer` header using the FastAPI Users JWT strategy (validates against `SECRET_KEY`).

### Compat-layer guard

Used inside `better_auth_compat.py` for organization endpoints.

```python
user = await _get_user_from_request(request, session)
```

This helper reads the `Authorization: Bearer` header **or** the `ba_session` HttpOnly cookie, verifies the JWT (using `JWT_SECRET`), then fetches the `User` row. Falls back to the cookie when no header is present — important for browser-only clients.

### `common/security.py` guard

Used by legacy routes that were written before the compat layer.

```python
from src.common.security import get_current_user

@router.get("/example")
async def example(user: User = Depends(get_current_user)):
    ...
```

This verifier tries `JWT_SECRET` first, then `SECRET_KEY`, and queries `WHERE users.id = int(sub)`.

---

## Token Extraction Priority

Both the compat layer and `security.py` follow the same priority:

1. `Authorization: Bearer <token>` header
2. `ba_session` HttpOnly cookie (browser fallback)

---

## API Clients — Auth Requirements

All frontend API clients **must** use `credentials: 'include'` to send the HttpOnly cookie:

| Client | File | Status |
|--------|------|--------|
| Better Auth client | `src/lib/api/auth.ts` | ✅ `credentials: 'include'` |
| Workflow API | `src/lib/api/workflows.ts` | ✅ `credentials: 'include'` |
| Payments API | `src/lib/api/payments.ts` | ✅ `credentials: 'include'` |

> Any new API client **must** include `credentials: 'include'` on every `fetch()` call, or use the shared `authClient` from `auth.ts`.

---

## User Model

```python
class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = 'users'

    id:           Mapped[int]           # PK — used as JWT `sub`
    email:        Mapped[str]           # Unique
    hashed_password: Mapped[str]        # bcrypt via pwdlib
    is_active:    Mapped[bool]          # False = login denied
    is_verified:  Mapped[bool]          # Email verification flag
    is_superuser: Mapped[bool]          # Admin flag
    name:         Mapped[Optional[str]] # Display name
    role:         Mapped[str]           # default 'member'
    otp_data:     Mapped[Optional[dict]]# 2FA OTP state
    is_2fa_enabled: Mapped[bool]
    totp_secret:  Mapped[Optional[str]]
```

---

## Environment Variables

### Backend (`.env`)

```bash
# Auth secrets — MUST be unique, 32+ characters each
SECRET_KEY=<random-hex-32>       # FastAPI Users JWT strategy
JWT_SECRET=<random-hex-32>       # better_auth_compat JWT issuer
# For simplicity, set both to the same value in production

JWT_LIFETIME_SECONDS=3600        # Token TTL (1 hour default)
ALGORITHM=HS256

# CORS — comma-separated list of allowed origins
FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
# Production example:
# ALLOWED_ORIGINS=https://app.yourdomain.com,https://yourdomain.com
```

### Frontend (`.env`)

```bash
VITE_API_URL=http://localhost:8000/api/v1
# The auth client strips /api/v1 to derive the base origin for /auth/* paths
```

---

## Session Lifecycle

```
1. User submits login form
       ↓
2. POST /api/v1/auth/sign-in/email
       ↓
3. Backend verifies password via FastAPI Users UserManager
       ↓
4. Backend issues HS256 JWT  →  sets ba_session HttpOnly cookie
       ↓
5. Response body: { user, session: { expiresAt } }
       ↓
6. Frontend auth store: set({ user, isInitialized: true })
       ↓
7. Router redirects to dashboard
       ↓
8. Each API request: browser auto-attaches ba_session cookie
       ↓
9. Backend verifies cookie JWT → serves data
       ↓
10. User signs out:
    POST /api/v1/auth/sign-out → clears all ba_* cookies
    Frontend: set({ user: null, session: null })
```

---

## Token Expiration & Refresh

| Aspect | Value | Notes |
|--------|-------|-------|
| Access token TTL | `JWT_LIFETIME_SECONDS` (default 3600 = 1hr) | Configured in `.env` |
| Refresh token | **Not implemented** | Session ends on expiry; user must log in again |
| Automatic refresh | **Not implemented** | Future improvement |
| 401 handling | Redirect to `/auth/login` | Configured in `authClient.fetchOptions.onError` |

> **Future work:** Consider implementing a `/auth/refresh` endpoint that issues a new JWT when the current one is within 5 minutes of expiry.

---

## CORS Configuration

CORS is handled in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),  # from ALLOWED_ORIGINS env var
    allow_credentials=True,            # required for cookie-based auth
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`ALLOWED_ORIGINS` is a dynamic `@property` on `Settings` that reads from the `ALLOWED_ORIGINS` env var (comma-separated). It always falls back to include `FRONTEND_URL` plus local dev addresses.

> `allow_credentials=True` requires that `allow_origins` never contains `"*"`. Always use explicit origin lists.

---

## Security Checklist

### ✅ Implemented

- [x] HttpOnly cookies — session token not accessible to JavaScript
- [x] Secure + SameSite=none in production (derived from FRONTEND_URL scheme)
- [x] bcrypt password hashing via `pwdlib`
- [x] JWT expiration enforced (`exp` claim validated)
- [x] JWT audience validated (`fastapi-users:auth`)
- [x] Duplicate registration rejected with clean 400 error
- [x] Invalid `sub` claim caught — returns 401, not 500
- [x] CORS restricted to explicit origin list
- [x] Session token omitted from JSON response body (cookie-only)
- [x] 401 on any unrecognized or expired token
- [x] `ba_active_team` cookie cleared on sign-out
- [x] `/auth/organization/list-teams` stub endpoint
- [x] `/auth/organization/set-active-team` stub endpoint

### ⚠️ Known Deviations (not spec-violations, but worth noting)

- **Hono backend JWT** (`backend_bun_hono`) does not validate the `audience` claim on verify — acceptable because the Hono service is a first-party internal consumer and shares the same `JWT_SECRET`.

### 🔲 Planned / Not Yet Implemented

- [ ] Token refresh endpoint
- [ ] Rate limiting on auth endpoints (5 req/15 min recommended)
- [ ] Email verification flow (model field exists, endpoint stub needed)
- [ ] Password reset flow (FastAPI Users token exists, endpoint needed)
- [ ] 2FA / TOTP enforcement at login (schema fields exist)
- [ ] Account lockout after N failed attempts
- [ ] Audit log on auth events (partial: `on_after_login` / `on_after_register` hooks exist)
- [ ] Social auth (GitHub, Google — OAuth router exists, wiring incomplete)

---

## Troubleshooting

| Symptom | Most Likely Cause | Fix |
|---------|------------------|-----|
| 401 on every request after login | `credentials: 'include'` missing | Add to every `fetch()` call |
| `USER_EXISTS` error not returned | Old broad `except Exception` swallowed it | Fixed in Feb 2026 |
| 401 "Could not validate credentials" on `/me` | `security.py` was querying by email; `sub` is now always `int(sub)` | Fixed in Feb 2026 |
| CORS blocked in production | `ALLOWED_ORIGINS` env var not set | Set `ALLOWED_ORIGINS=https://yourapp.com` in `.env.production` |
| Cookie not set on Safari / cross-site | `SameSite=None` requires `Secure` | Ensure `FRONTEND_URL` starts with `https://` in production |
| `int(sub)` ValueError → 500 on bad token | Raw PyJWT exception not caught | Fixed in Feb 2026 — wrapped in `try/except (TypeError, ValueError)` |

---

*Last updated: February 2026*
