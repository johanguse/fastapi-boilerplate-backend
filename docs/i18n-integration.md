# Full-Stack Internationalization Integration Guide

## Overview

This guide demonstrates how to integrate the backend FastAPI i18n system with the React frontend for a seamless multilingual user experience.

## Architecture Overview

### Backend (FastAPI)
- File-based translation system with JSON locale files
- Cookie-based language persistence
- Automatic language detection from headers/cookies/query params
- RESTful API endpoints with localized responses

### Frontend (React + TypeScript)
- react-i18next for component translations
- localStorage for language persistence
- Language switcher component
- Form validation with localized messages

### Integration Points
1. **Language Selection**: Frontend language switcher sets backend cookie
2. **API Responses**: Backend returns localized error/success messages
3. **Shared Language State**: Both systems use the same language codes
4. **Persistent Preferences**: Language choice persists across sessions

## Shared Language Configuration

### Supported Languages (Both Systems)

```typescript
// Shared language configuration
export const SUPPORTED_LANGUAGES = {
  en: { name: 'English', nativeName: 'English' },
  es: { name: 'Spanish', nativeName: 'Español' },
  fr: { name: 'French', nativeName: 'Français' },
  de: { name: 'German', nativeName: 'Deutsch' },
  pt: { name: 'Portuguese', nativeName: 'Português' }
} as const

export type LanguageCode = keyof typeof SUPPORTED_LANGUAGES
```

## Integration Patterns

### 1. Unified Language Switcher

Create a language switcher that updates both frontend and backend:

```tsx
// components/LanguageSwitcher.tsx
import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import { SUPPORTED_LANGUAGES, type LanguageCode } from '@/lib/constants'

export function LanguageSwitcher() {
  const { i18n } = useTranslation()
  const [isUpdating, setIsUpdating] = useState(false)

  const changeLanguage = async (newLanguage: LanguageCode) => {
    setIsUpdating(true)
    
    try {
      // 1. Update frontend language
      await i18n.changeLanguage(newLanguage)
      
      // 2. Set backend cookie by making a request
      await fetch(`/api/v1/i18n/set-language?lang=${newLanguage}`, {
        method: 'POST',
        credentials: 'include' // Important: include cookies
      })
      
      // 3. Optional: Refresh current page to get localized content
      window.location.reload()
      
    } catch (error) {
      console.error('Failed to change language:', error)
    } finally {
      setIsUpdating(false)
    }
  }

  return (
    <select 
      value={i18n.language} 
      onChange={(e) => changeLanguage(e.target.value as LanguageCode)}
      disabled={isUpdating}
      className="border rounded px-2 py-1"
    >
      {Object.entries(SUPPORTED_LANGUAGES).map(([code, lang]) => (
        <option key={code} value={code}>
          {lang.nativeName}
        </option>
      ))}
    </select>
  )
}
```

### 2. Backend Language Setting Endpoint

Add an endpoint to set the language cookie:

```python
# src/auth/user_routes.py
@router.post('/i18n/set-language')
async def set_language(
    request: Request,
    response: Response,
    lang: str = Query(..., description='Language code to set')
):
    """
    Set the user's preferred language cookie
    """
    if not i18n.is_supported_language(lang):
        raise HTTPException(status_code=400, detail="Unsupported language")
    
    # Set the language cookie
    response.set_cookie(
        key="preferred_locale",
        value=lang,
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=True,
        samesite="lax"
    )
    
    return {
        "message": i18n.translate("success.language_updated", lang),
        "language": lang
    }
```

### 3. API Client with Language Headers

Create an API client that automatically includes language information:

```typescript
// lib/api.ts
import axios from 'axios'
import i18n from './i18n'

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // Include cookies in requests
})

// Add language header to all requests
api.interceptors.request.use((config) => {
  config.headers['Accept-Language'] = i18n.language
  return config
})

// Handle localized error responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Backend returns localized error messages
    const message = error.response?.data?.detail || 'An error occurred'
    
    // Show localized error (backend already localized it)
    toast.error(message)
    
    return Promise.reject(error)
  }
)

export { api }
```

### 4. Localized Form Validation

Combine frontend validation with backend error messages:

```tsx
// components/forms/LoginForm.tsx
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useTranslation } from 'react-i18next'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { toast } from 'sonner'

export function LoginForm() {
  const { t } = useTranslation()

  // Frontend validation (immediate feedback)
  const schema = z.object({
    email: z.string()
      .min(1, t('auth.emailRequired'))
      .email(t('auth.emailInvalid')),
    password: z.string()
      .min(1, t('auth.passwordRequired'))
      .min(8, t('auth.passwordTooShort'))
  })

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema)
  })

  // Backend API call (server validation + localized responses)
  const loginMutation = useMutation({
    mutationFn: async (data: z.infer<typeof schema>) => {
      const response = await api.post('/auth/login', data)
      return response.data
    },
    onSuccess: (data) => {
      // Backend returns localized success message
      toast.success(data.message || t('auth.loginSuccess'))
    },
    onError: (error: any) => {
      // Backend returns localized error message
      const message = error.response?.data?.detail || t('auth.loginFailed')
      toast.error(message)
    }
  })

  const onSubmit = (data: z.infer<typeof schema>) => {
    loginMutation.mutate(data)
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* Form fields with frontend validation */}
      <div>
        <label>{t('auth.email')}</label>
        <input 
          {...form.register('email')}
          placeholder={t('auth.emailPlaceholder')}
        />
        {form.formState.errors.email && (
          <span className="error">
            {form.formState.errors.email.message}
          </span>
        )}
      </div>

      <div>
        <label>{t('auth.password')}</label>
        <input 
          type="password"
          {...form.register('password')}
          placeholder={t('auth.passwordPlaceholder')}
        />
        {form.formState.errors.password && (
          <span className="error">
            {form.formState.errors.password.message}
          </span>
        )}
      </div>

      <button 
        type="submit" 
        disabled={loginMutation.isPending}
      >
        {loginMutation.isPending 
          ? t('common.loading') 
          : t('auth.signIn')
        }
      </button>
    </form>
  )
}
```

## Complete Integration Example

### Frontend Application Setup

```tsx
// App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { I18nextProvider } from 'react-i18next'
import i18n from './lib/i18n'
import { LanguageSwitcher } from './components/LanguageSwitcher'
import { Router } from './Router'

const queryClient = new QueryClient()

function AppContent() {
  return (
    <div className="min-h-screen">
      <header className="border-b p-4 flex justify-between items-center">
        <h1>My App</h1>
        <LanguageSwitcher />
      </header>
      
      <main>
        <Router />
      </main>
      
      <Toaster />
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>
        <AppContent />
      </I18nextProvider>
    </QueryClientProvider>
  )
}
```

### Backend Integration in Main App

```python
# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.common.middleware import I18nMiddleware

app = FastAPI()

# Add i18n middleware early in the stack
app.add_middleware(I18nMiddleware)

# CORS configuration to allow credentials (cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with i18n endpoints
app.include_router(
    user_router,
    prefix='/api/v1',
)
```

## Testing Integration

### Frontend Tests with Backend Mock

```tsx
// __tests__/integration/LanguageIntegration.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { I18nextProvider } from 'react-i18next'
import i18n from '@/lib/i18n'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'

// Mock backend responses
const server = setupServer(
  rest.post('/api/v1/i18n/set-language', (req, res, ctx) => {
    const url = new URL(req.url)
    const lang = url.searchParams.get('lang')
    
    return res(
      ctx.status(200),
      ctx.json({
        message: 'Language updated successfully',
        language: lang
      })
    )
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>
        {component}
      </I18nextProvider>
    </QueryClientProvider>
  )
}

test('language switcher updates both frontend and backend', async () => {
  renderWithProviders(<LanguageSwitcher />)
  
  const switcher = screen.getByRole('combobox')
  
  // Change language to Spanish
  fireEvent.change(switcher, { target: { value: 'es' } })
  
  // Wait for both frontend and backend updates
  await waitFor(() => {
    expect(i18n.language).toBe('es')
  })
})
```

## Best Practices

### 1. Language Synchronization
- Always update both frontend and backend when language changes
- Use cookies for backend persistence, localStorage for frontend
- Include credentials in API requests to maintain cookie state

### 2. Error Handling
- Backend should return localized error messages
- Frontend should display backend errors without re-translation
- Provide fallbacks for network failures

### 3. Performance
- Cache translations on both frontend and backend
- Use CDN for translation files in production
- Lazy load language-specific content

### 4. SEO Considerations
- Use language prefixes in URLs (`/en/dashboard`, `/es/dashboard`)
- Set appropriate `lang` attributes on HTML elements
- Provide language-specific meta tags

### 5. Testing
- Test language switching end-to-end
- Mock backend responses for frontend tests
- Verify cookie persistence across requests

This integration guide provides a complete blueprint for connecting your backend and frontend i18n systems for a seamless multilingual user experience.