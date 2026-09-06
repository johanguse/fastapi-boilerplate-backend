# Fiscal Nacional NFS-e Integration Guide

This guide explains how to integrate the Fiscal Nacional NFS-e (Brazilian electronic service invoice) system into your SaaS application.

## Overview

The integration automatically generates NFS-e invoices for:

- **Brazilian customers**: Full NFS-e with CPF/CNPJ and complete address
- **International customers**: Export NFS-e with NIF and currency conversion

## Architecture

```
User Payment → Stripe Webhook → NFS-e Service → Fiscal Nacional API → Database + Email
```

### Components Created

1. **Database Models** (`src/fiscal/models.py`):
   - `UserTaxInfo`: Stores user tax information (Brazilian and international)
   - `NFSe`: Tracks NFS-e generation and status

2. **Validators** (`src/utils/brazilian_validators.py`):
   - CPF/CNPJ validation and formatting
   - CEP formatting
   - Brazilian states list

3. **Currency Utilities** (`src/utils/currencies.py`):
   - BACEN currency codes
   - Currency conversion helpers
   - Default currency by country

4. **API Client** (`src/services/fiscal_nacional.py`):
   - Fiscal Nacional API integration
   - Request/response handling
   - Error handling

5. **Service Layer** (`src/fiscal/service.py`):
   - High-level NFS-e operations
   - Stripe integration
   - Email notifications

6. **API Routes** (`src/fiscal/routes.py`):
   - Tax info CRUD operations
   - NFS-e listing and status sync
   - Brazilian cities/states endpoints
   - Document validation

## Environment Configuration

Add these variables to your `.env` file:

```bash
# NFS-e Configuration (optional - only needed if you use an NFS-e provider)
FISCAL_NACIONAL_API_KEY=your_nfse_api_key
NFSE_API_BASE_URL=https://api.your-nfse-provider.com
NFSE_ADMIN_EMAIL=admin@yourcompany.com
```

**Important**: Get your API key and base URL from your NFS-e provider's dashboard.

## Database Migration

Run the migration to create the fiscal tables:

```bash
# Using alembic directly
uv run alembic upgrade head

# Or using justfile
just migrate
```

## Configure API Base URL

Add to your `.env` file:

```bash
# NFS-e provider API base URL (contact your provider for the correct URL)
NFSE_API_BASE_URL=https://api.your-nfse-provider.com
```

Company-specific configuration (CNPJ, municipal registration, ISS rate, etc.) is managed in your NFS-e provider's dashboard — no hardcoded values are needed in the codebase.

## Stripe Webhook Integration

### For Subscriptions

Add to `src/subscriptions/webhooks.py`:

```python
from src.common.config import settings
from src.fiscal.models import UserTaxInfo
from src.fiscal.service import NFSeService
from sqlalchemy import select

@router.post('/stripe-webhook')
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    # ... existing webhook handling ...
    
    if event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        
        # Get subscription owner
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return {'status': 'success'}
        
        # Get user_id from subscription metadata
        subscription = stripe.Subscription.retrieve(subscription_id)
        user_id = subscription.metadata.get('userId')
        
        if not user_id:
            return {'status': 'success'}
        
        # Check if user has tax info (required for NFS-e)
        result = await db.execute(
            select(UserTaxInfo).where(UserTaxInfo.user_id == user_id)
        )
        tax_info = result.scalar_one_or_none()
        
        if not tax_info:
            logger.warning(f'User {user_id} has no tax info, skipping NFS-e generation')
            return {'status': 'success'}
        
        # Only generate if amount > 0 (not trial/free)
        amount_paid = invoice.get('amount_paid', 0)
        if amount_paid == 0:
            return {'status': 'success'}
        
        # Get charge ID
        charge_id = invoice.get('charge')
        payment_intent_id = invoice.get('payment_intent')
        
        # Convert amount from cents to dollars
        amount_usd = amount_paid / 100.0
        
        # TODO: Get BRL conversion (you'll need a currency API)
        # For now, use a fixed rate as placeholder
        amount_brl = amount_usd * 5.0  # Example: 1 USD = 5 BRL
        
        # Generate NFS-e
        nfse_service = NFSeService(
            db=db,
            api_key=settings.FISCAL_NACIONAL_API_KEY,
            base_url=settings.NFSE_API_BASE_URL,
            admin_email=settings.NFSE_ADMIN_EMAIL,
        )
        
        try:
            await nfse_service.create_nfse_for_subscription(
                user_id=int(user_id),
                stripe_invoice_id=invoice['id'],
                stripe_payment_intent_id=payment_intent_id,
                stripe_charge_id=charge_id,
                service_description='Monthly SaaS Subscription',
                amount_usd=amount_usd,
                amount_brl=amount_brl,
                customer_email=invoice.get('customer_email'),
                product_name='Pro Plan',
            )
        except Exception as e:
            logger.error(f'Failed to generate NFS-e: {e}')
            # Don't fail the webhook - NFS-e can be generated later
    
    return {'status': 'success'}
```

### For One-Time Payments

Add to `src/payments/webhooks.py`:

```python
if event['type'] == 'payment_intent.succeeded':
    payment_intent = event['data']['object']
    
    # Get user from metadata
    user_id = payment_intent.metadata.get('userId')
    if not user_id:
        return {'status': 'success'}
    
    # Check for tax info
    result = await db.execute(
        select(UserTaxInfo).where(UserTaxInfo.user_id == user_id)
    )
    tax_info = result.scalar_one_or_none()
    
    if tax_info:
        charge_id = payment_intent.get('latest_charge')
        amount_usd = payment_intent['amount'] / 100.0
        amount_brl = amount_usd * 5.0  # Get real conversion rate
        
        nfse_service = NFSeService(
            db=db,
            api_key=settings.FISCAL_NACIONAL_API_KEY,
            base_url=settings.NFSE_API_BASE_URL,
            admin_email=settings.NFSE_ADMIN_EMAIL,
        )
        
        try:
            await nfse_service.create_nfse_for_credit_purchase(
                user_id=int(user_id),
                stripe_payment_intent_id=payment_intent['id'],
                stripe_charge_id=charge_id,
                service_description='Credit Package Purchase',
                amount_usd=amount_usd,
                amount_brl=amount_brl,
                customer_email=payment_intent.get('receipt_email'),
                product_name='100 Credits',
            )
        except Exception as e:
            logger.error(f'Failed to generate NFS-e: {e}')
```

## API Endpoints

### Tax Information

```http
# Get tax info
GET /api/v1/fiscal/tax-info

# Create tax info
POST /api/v1/fiscal/tax-info
{
  "country": "BR",
  "full_name": "João da Silva",
  "cpf_cnpj": "12345678901",
  "address": "Rua Example",
  "number": "123",
  "neighborhood": "Centro",
  "city": "São Paulo",
  "city_code": 3550308,
  "state": "SP",
  "postal_code": "01310-100"
}

# Update tax info
PUT /api/v1/fiscal/tax-info
{
  "address": "New Address",
  "number": "456"
}

# Delete tax info
DELETE /api/v1/fiscal/tax-info
```

### NFS-e Management

```http
# List user's NFS-e records
GET /api/v1/fiscal/nfse?page=1&page_size=20

# Get specific NFS-e
GET /api/v1/fiscal/nfse/{nfse_id}

# Sync NFS-e status with Fiscal Nacional
POST /api/v1/fiscal/nfse/{nfse_id}/sync
```

### Utilities

```http
# Get Brazilian states
GET /api/v1/fiscal/brazilian-states

# Get cities for a state
GET /api/v1/fiscal/brazilian-cities/SP

# Validate CPF/CNPJ
GET /api/v1/fiscal/validate-cpf-cnpj/12345678901
```

## Frontend Integration Requirements

You need to create:

1. **Tax Info Modal** - Collect tax information before first purchase
2. **Billing History Page** - Show NFS-e records with download links
3. **Purchase Flow** - Block purchases if no tax info exists

### Example Tax Info Modal Logic

```typescript
async function handlePurchase() {
  // Check if user has tax info
  const response = await fetch('/api/v1/fiscal/tax-info');
  
  if (response.status === 404) {
    // Show tax info modal
    showTaxInfoModal();
    return;
  }
  
  // Proceed with purchase
  proceedToCheckout();
}
```

### Example Billing History

```typescript
interface NFSe {
  id: number;
  status: string;
  nfse_number: string | null;
  value_brl: number;
  customer_name: string;
  service_description: string;
  created_at: string;
  pdf_path: string | null;
}

async function loadBillingHistory() {
  const response = await fetch('/api/v1/fiscal/nfse');
  const data = await response.json();
  
  return data.items.map((nfse: NFSe) => ({
    id: nfse.id,
    date: new Date(nfse.created_at).toLocaleDateString(),
    description: nfse.service_description,
    amount: `R$ ${nfse.value_brl.toFixed(2)}`,
    status: nfse.status,
    canDownload: nfse.status === 'authorized' && !!nfse.pdf_path,
  }));
}
```

## Testing

### Staging Environment

1. Use `NFSE_API_BASE_URL=https://api-staging.your-nfse-provider.com` in `.env`
2. Test with both Brazilian and international customers
3. Verify NFS-e generation in Fiscal Nacional staging dashboard

### Test Cases

1. **Brazilian Customer**:
   - Valid CPF/CNPJ
   - Complete address with IBGE city code
   - NFS-e should include customer email

2. **International Customer**:
   - Country code (non-BR)
   - Optional NIF
   - NFS-e marked as export

3. **Error Handling**:
   - Invalid CPF/CNPJ
   - Missing required fields
   - API errors (should save error in database)

## Currency Conversion

**Important**: The current implementation uses a placeholder exchange rate. You should integrate a real currency conversion service:

### Recommended Services

1. **ExchangeRate-API** (Free tier available):

```python
import httpx

async def get_usd_to_brl_rate():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://api.exchangerate-api.com/v4/latest/USD'
        )
        data = response.json()
        return data['rates']['BRL']
```

1. **Open Exchange Rates** (Free tier: 1000 requests/month)
2. **Fixer.io** (Free tier with EUR base)

Add the conversion service to `NFSeService` before creating NFS-e.

## Monitoring and Maintenance

### Periodic Sync

Create a background job (using Celery, APScheduler, or similar) to sync pending NFS-e:

```python
from src.fiscal.service import NFSeService
from src.fiscal.models import NFSe
from src.common.session import get_db

async def sync_pending_nfse():
    """Sync all processing NFS-e records."""
    async with get_db() as db:
        nfse_service = NFSeService(
            db=db,
            api_key=settings.FISCAL_NACIONAL_API_KEY,
            base_url=settings.NFSE_API_BASE_URL,
            admin_email=settings.NFSE_ADMIN_EMAIL,
        )
        
        # Get all processing NFS-e
        result = await db.execute(
            select(NFSe).where(NFSe.status == 'processing')
        )
        pending = result.scalars().all()
        
        for nfse in pending:
            try:
                await nfse_service.sync_nfse(nfse.id)
            except Exception as e:
                logger.error(f'Failed to sync NFS-e {nfse.id}: {e}')
```

### Error Notifications

Errors are automatically sent to `NFSE_ADMIN_EMAIL`. Review these regularly to fix issues.

## Security Considerations

1. **API Key**: Store in environment variables, never commit
2. **Tax Info**: Sensitive data - ensure proper access control
3. **Webhooks**: Verify Stripe signatures
4. **Logs**: Don't log full CPF/CNPJ or tax IDs

## Support

- **NFS-e Provider API Docs**: Add your provider's API documentation URL here
- **IBGE Cities API**: <https://servicodados.ibge.gov.br/api/docs/localidades>
- **Integration Questions**: Check `docs/external-api-integration.md`

## Checklist Before Going Live

- [ ] Set `NFSE_API_BASE_URL` in `.env` (get URL from your NFS-e provider)
- [ ] Set `NFSE_API_BASE_URL` to your production endpoint
- [ ] Add real currency conversion service
- [ ] Test with real Stripe payments
- [ ] Verify emails are sent correctly
- [ ] Set up periodic sync job
- [ ] Configure monitoring/alerting for errors
- [ ] Test both Brazilian and international flows
- [ ] Update frontend to require tax info before purchase
- [ ] Add billing history page to frontend
