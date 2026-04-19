# Fiscal Nacional Integration - Quick Start

## ✅ What Was Implemented

### Backend Components

1. **Database Models** (`src/fiscal/models.py`):
   - `UserTaxInfo`: Store Brazilian (CPF/CNPJ + address) and international (NIF) tax data
   - `NFSe`: Track NFS-e generation, status, and documents

2. **Validators & Utilities**:
   - `src/utils/brazilian_validators.py`: CPF/CNPJ validation, formatting, states list
   - `src/utils/currencies.py`: BACEN currency codes for international invoices

3. **API Integration**:
   - `src/services/fiscal_nacional.py`: Fiscal Nacional API client
   - `src/fiscal/service.py`: High-level NFS-e operations

4. **API Endpoints** (`src/fiscal/routes.py`):
   - Tax info CRUD: GET/POST/PUT/DELETE `/api/v1/fiscal/tax-info`
   - NFS-e listing: GET `/api/v1/fiscal/nfse`
   - Status sync: POST `/api/v1/fiscal/nfse/{id}/sync`
   - Utilities: Brazilian states,cities, document validation

5. **Database Migration**: `alembic/versions/add_fiscal_tables.py`

## 🚀 Setup Instructions

### 1. Environment Variables

Add to your `.env` file:

```bash
# NFS-e Configuration (optional - only needed if you use an NFS-e provider)
FISCAL_NACIONAL_API_KEY=your_nfse_api_key
NFSE_API_BASE_URL=https://api.your-nfse-provider.com
NFSE_ADMIN_EMAIL=admin@yourcompany.com
```

### 2. Configure API Base URL

Add to your `.env` file:

```bash
# NFS-e provider API base URL (contact your provider for the correct URL)
NFSE_API_BASE_URL=https://api.your-nfse-provider.com
```

Company-specific configuration (CNPJ, municipal registration, ISS rate, etc.) is managed directly in your NFS-e provider dashboard — no hardcoded values needed in the codebase.

### 3. Run Database Migration

```bash
# Using justfile
just migrate

# Or using alembic directly
uv run alembic upgrade head
```

### 4. Install Dependencies

The following packages are already in the code:

- `httpx` - For API requests (should already be installed)
- `pydantic` - For validation (already installed with FastAPI)

### 5. Test the API

```bash
# Start the server
just run

# Test the endpoints
curl http://localhost:8000/api/v1/fiscal/brazilian-states
```

## 📋 Integration Checklist

### Backend Integration

- [x] Database models created
- [x] API routes registered in `main.py`
- [x] Environment variables configured
- [ ] Set `NFSE_API_BASE_URL` in `.env` (get URL from your NFS-e provider)
- [ ] Integrate Stripe webhooks (see `docs/FISCAL_NACIONAL_INTEGRATION.md`)
- [ ] Add currency conversion service (currently uses placeholder)
- [ ] Set up periodic sync job for pending NFS-e

### Frontend Integration (TODO)

You need to implement:

- [ ] **Tax Info Modal** - Block purchases without tax info
- [ ] **Billing History Page** - Show NFS-e records with download buttons
- [ ] **Brazilian Address Form** - Use IBGE API for cities:

  ```typescript
  fetch('/api/v1/fiscal/brazilian-cities/SP')
  ```

- [ ] **Document Validation** - Real-time CPF/CNPJ validation:

  ```typescript
  fetch('/api/v1/fiscal/validate-cpf-cnpj/12345678901')
  ```

### Example Frontend Logic

#### Check Tax Info Before Purchase

```typescript
async function handleBuyCredits() {
  try {
    // Check if user has tax info
    const response = await fetch('/api/v1/fiscal/tax-info', {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    if (response.status === 404) {
      // Show tax info modal
      openTaxInfoModal();
      return;
    }
    
    // Proceed to checkout
    window.location.href = stripeCheckoutUrl;
  } catch (error) {
    console.error('Error checking tax info:', error);
  }
}
```

#### Tax Info Modal Component (React Example)

```tsx
import { useState } from 'react';

interface TaxInfoForm {
  country: string;
  full_name: string;
  cpf_cnpj?: string;
  nif?: string;
  address?: string;
  number?: string;
  // ... other fields
}

export function TaxInfoModal({ onComplete }: { onComplete: () => void }) {
  const [form, setForm] = useState<TaxInfoForm>({
    country: 'BR',
    full_name: '',
  });
  
  const isBrazilian = form.country === 'BR';
  
  const handleSubmit = async () => {
    const response = await fetch('/api/v1/fiscal/tax-info', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(form),
    });
    
    if (response.ok) {
      onComplete();
    }
  };
  
  return (
    <div className="modal">
      <h2>Tax Information Required</h2>
      <p>To comply with Brazilian tax law, we need your tax information.</p>
      
      <form onSubmit={handleSubmit}>
        <select value={form.country} onChange={e => setForm({...form, country: e.target.value})}>
          <option value="BR">Brazil</option>
          <option value="US">United States</option>
          {/* Add more countries */}
        </select>
        
        <input
          type="text"
          placeholder="Full Name"
          value={form.full_name}
          onChange={e => setForm({...form, full_name: e.target.value})}
          required
        />
        
        {isBrazilian ? (
          <>
            <input
              type="text"
              placeholder="CPF or CNPJ"
              value={form.cpf_cnpj || ''}
              onChange={e => setForm({...form, cpf_cnpj: e.target.value})}
              required
            />
            {/* Add address fields, city selector with IBGE API */}
          </>
        ) : (
          <input
            type="text"
            placeholder="Tax ID (NIF)"
            value={form.nif || ''}
            onChange={e => setForm({...form, nif: e.target.value})}
          />
        )}
        
        <button type="submit">Save and Continue</button>
      </form>
    </div>
  );
}
```

#### Billing History Component

```tsx
interface NFSeRecord {
  id: number;
  status: string;
  nfse_number: string | null;
  value_brl: number;
  service_description: string;
  created_at: string;
}

export function BillingHistory() {
  const [records, setRecords] = useState<NFSeRecord[]>([]);
  
  useEffect(() => {
    fetch('/api/v1/fiscal/nfse', {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setRecords(data.items));
  }, []);
  
  const downloadInvoice = async (nfseId: number) => {
    // Trigger download from your backend
    window.open(`/api/v1/fiscal/nfse/${nfseId}/download`, '_blank');
  };
  
  return (
    <div>
      <h2>Billing History</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Invoice</th>
          </tr>
        </thead>
        <tbody>
          {records.map(record => (
            <tr key={record.id}>
              <td>{new Date(record.created_at).toLocaleDateString()}</td>
              <td>{record.service_description}</td>
              <td>R$ {record.value_brl.toFixed(2)}</td>
              <td>{record.status}</td>
              <td>
                {record.status === 'authorized' && (
                  <button onClick={() => downloadInvoice(record.id)}>
                    Download NFS-e
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

## 📚 Documentation

Comprehensive documentation available at:

- `docs/FISCAL_NACIONAL_INTEGRATION.md` - Full integration guide
- `docs/external-api-integration.md` - API reference (from llmgenerator)

## 🔗 API Reference

### Tax Info Endpoints

```
GET    /api/v1/fiscal/tax-info           # Get user's tax info
POST   /api/v1/fiscal/tax-info           # Create tax info
PUT    /api/v1/fiscal/tax-info           # Update tax info
DELETE /api/v1/fiscal/tax-info           # Delete tax info
```

### NFS-e Endpoints

```
GET    /api/v1/fiscal/nfse               # List user's NFS-e
GET    /api/v1/fiscal/nfse/{id}          # Get specific NFS-e  
POST   /api/v1/fiscal/nfse/{id}/sync     # Sync status with API
```

### Utility Endpoints

```
GET    /api/v1/fiscal/brazilian-states              # List states
GET    /api/v1/fiscal/brazilian-cities/{state}      # List cities (IBGE)
GET    /api/v1/fiscal/validate-cpf-cnpj/{document}  # Validate document
```

## 🧪 Testing

### Test Brazilian User Flow

1. Create tax info with CPF/CNPJ:

```bash
curl -X POST http://localhost:8000/api/v1/fiscal/tax-info \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "BR",
    "full_name": "João da Silva",
    "cpf_cnpj": "12345678901",
    "address": "Rua Example",
    "number": "123",
    "neighborhood": "Centro",
    "city": "São Paulo",
    "city_code": 3550308,
    "state": "SP",
    "postal_code": "01310100"
  }'
```

1. Simulate a payment (you'll integrate with Stripe webhooks)
2. Check NFS-e was created:

```bash
curl http://localhost:8000/api/v1/fiscal/nfse \
  -H "Authorization: Bearer $TOKEN"
```

### Test International User Flow

1. Create tax info with NIF:

```bash
curl -X POST http://localhost:8000/api/v1/fiscal/tax-info \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "US",
    "full_name": "John Smith",
    "nif": "12-3456789",
    "nif_exemption_code": 0
  }'
```

## ⚠️ Important Notes

1. **Currency Conversion**: Currently uses placeholder rate (5.0). Implement real conversion before production.

2. **Stripe Integration**: Update your webhook handlers to call `NFSeService.create_nfse_for_subscription()` or `create_nfse_for_credit_purchase()`.

3. **Security**:
   - Never commit API keys
   - Validate all tax info before purchases
   - Use HTTPS in production

4. **Tax Compliance**:
   - Only generate NFS-e for paid transactions (amount > 0)
   - Don't generate for trials or $0 invoices
   - Keep records for 5 years (Brazilian tax law)

## 🆘 Troubleshooting

**Error: "User must provide tax information"**

- User needs to complete tax info form before purchasing

**Error: "CPF inválido"**

- CPF/CNPJ validation failed - check the document is correct

**Error: "Failed to create NFS-e"**

- Check `FISCAL_NACIONAL_API_KEY` is correct
- Verify API is accessible (not blocked by firewall)
- Check admin email for error details

**NFS-e stuck in "processing"**

- Run sync manually: `POST /api/v1/fiscal/nfse/{id}/sync`
- Set up periodic sync job (every 5 minutes)

## 📞 Support

- NFS-e Provider: Add your provider's website URL here
- IBGE API: <https://servicodados.ibge.gov.br/api/docs>
- Integration issues: Check logs and admin email notifications
