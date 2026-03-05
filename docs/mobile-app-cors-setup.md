# Mobile App CORS & Integration Setup

This document describes the backend configuration needed to support the Expo React Native mobile app.

## CORS Configuration

React Native apps do **not** send `Origin` headers the same way browsers do. However, if you're using Expo's dev tools or web mode during development, CORS matters.

### Development Setup

Add these to your `.env` file:

```env
# For Expo dev server access (if testing via web)
FRONTEND_URL="http://localhost:8081"
```

Or update `ALLOWED_ORIGINS` in your settings to include the Expo dev server URL.

### Production Setup

For production mobile apps, CORS headers are generally not enforced by native HTTP clients but it's still good practice to have proper origins configured:

```env
# Your production API domain
FRONTEND_URL="https://your-app-domain.com"
```

> **Note**: Native mobile HTTP requests (iOS/Android) typically bypass CORS entirely. The CORS middleware is mainly relevant for web-based testing and browser access to the API.

## API Endpoints Used by the Mobile App

The mobile app uses the following API endpoints:

### Authentication
| Method | Endpoint | Content-Type | Description |
|--------|----------|-------------|-------------|
| `POST` | `/api/v1/auth/jwt/login` | `application/x-www-form-urlencoded` | Login (fields: `username`, `password`) |
| `POST` | `/api/v1/auth/register` | `application/json` | Register (fields: `email`, `password`, `name`) |
| `POST` | `/api/v1/auth/forgot-password` | `application/json` | Reset password (field: `email`) |
| `GET`  | `/api/v1/users/me` | — | Get current user profile |

### Notes
- The login endpoint expects `username` field (which should contain the email) as per fastapi-users convention
- Auth uses Bearer JWT tokens via `Authorization: Bearer <token>` header
- Token is obtained from the login response's `access_token` field

## Mobile-Specific Considerations

### Push Notifications (Future)
If you plan to add push notifications, you'll need:
1. A new endpoint to register device tokens
2. A service to send notifications (e.g., Firebase Cloud Messaging, APNs)

### File Uploads
The existing `/api/v1/uploads` endpoints should work with `multipart/form-data` from the mobile app.

### Rate Limiting
The backend has rate limiting enabled. Mobile apps should handle `429 Too Many Requests` responses gracefully with retry logic.
