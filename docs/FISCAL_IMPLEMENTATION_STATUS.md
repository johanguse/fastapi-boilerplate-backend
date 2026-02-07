# Fiscal Nacional Integration - Implementation Guide

## ✅ Completed - FastAPI Backend

### 1. Currency Conversion Service ✅

**File**: `src/services/currency_conversion.py`

- Automatic currency conversion using Stripe balance transactions
- PTAX (Banco Central) fallback
- Conservative fallback rates
- Full audit trail

### 2. Updated NFSeService ✅

**File**: `src/fiscal/service.py`

- Integrated with currency conversion service  
- No longer requires pre-converted amounts
- Methods now accept: `amount`, `currency` instead of `amount_usd`, `amount_brl`

### 3. Webhook Endpoints ✅

**File**: `src/fiscal/webhooks.py`

- `/fiscal-webhook` endpoint to receive Fiscal Nacional callbacks
- Signature verification
- Handles: `nfse.authorized`, `nfse.processing`, `nfse.error`, `nfse.cancelled`
- Automatic status updates in database
- Admin email notifications on errors

### 4. Configuration Needed

Add to `.env`:

```bash
# Existing
FISCAL_NACIONAL_API_KEY=your_api_key
FISCAL_NACIONAL_ENVIRONMENT=staging
NFSE_ADMIN_EMAIL=admin@yourcompany.com

# New (optional)
FISCAL_WEBHOOK_SECRET=your_webhook_secret
```

---

## 🔨 To Implement - Bun Hono Backend

### 1. Database Schema ✅

**File**: `src/db/schema/fiscal.ts`

- `userTaxInfo` table with Brazilian/international fields
- `nfse` table with all transaction tracking
- Proper relations and indexes

### 2. Currency Conversion Service ✅  

**File**: `src/services/currency-conversion.service.ts`

- TypeScript port of the Python service
- Same 3-tier conversion strategy

### 3. Fiscal Nacional API Client

**File**: `src/services/fiscal-nacional.ts` (create this)

```typescript
import type { Env } from "../lib/env";

const FISCAL_API_URLS = {
 production: "https://api.fiscalnacional.com.br/v1",
 staging: "https://sandbox.fiscalnacional.com.br/v1",
 development: "https://sandbox.fiscalnacional.com.br/v1",
};

export interface CreateNFSeRequest {
 externalReference: string;
 service: {
  description: string;
  amount: number;
  issRate?: number;
 };
 customer: {
  name: string;
  email: string;
  document?: string;
  country?: string;
  address?: {
   street: string;
   number: string;
   neighborhood: string;
   city: string;
   cityCode: string;
   state: string;
   postalCode: string;
  };
 };
 // ... more fields
}

export class FiscalNacionalClient {
 private apiKey: string;
 private baseUrl: string;

 constructor(env: Env) {
  this.apiKey = env.FISCAL_NACIONAL_API_KEY;
  this.baseUrl =
   FISCAL_API_URLS[env.FISCAL_NACIONAL_ENVIRONMENT || "staging"];
 }

 async createNFSe(request: CreateNFSeRequest) {
  const response = await fetch(`${this.baseUrl}/nfse`, {
   method: "POST",
   headers: {
    Authorization: `Bearer ${this.apiKey}`,
    "Content-Type": "application/json",
   },
   body: JSON.stringify(request),
  });

  if (!response.ok) {
   const error = await response.json();
   throw new Error(`Fiscal API Error: ${JSON.stringify(error)}`);
  }

  return response.json();
 }

 async getNFSeStatus(reference: string) {
  const response = await fetch(`${this.baseUrl}/nfse/${reference}`, {
   method: "GET",
   headers: {
    Authorization: `Bearer ${this.apiKey}`,
   },
  });

  if (!response.ok) {
   throw new Error(`Failed to get NFS-e status: ${response.statusText}`);
  }

  return response.json();
 }

 async cancelNFSe(reference: string, reason: string) {
  const response = await fetch(`${this.baseUrl}/nfse/${reference}/cancel`, {
   method: "POST",
   headers: {
    Authorization: `Bearer ${this.apiKey}`,
    "Content-Type": "application/json",
   },
   body: JSON.stringify({ reason }),
  });

  if (!response.ok) {
   throw new Error(`Failed to cancel NFS-e: ${response.statusText}`);
  }

  return response.json();
 }
}
```

### 4. NFSe Service

**File**: `src/services/nfse.service.ts` (create this)

```typescript
import { eq } from "drizzle-orm";
import type { Database } from "../db";
import { nfse, userTaxInfo } from "../db/schema";
import type { Env } from "../lib/env";
import {
 CurrencyConversionService,
 createCurrencyConversionService,
} from "./currency-conversion.service";
import { FiscalNacionalClient } from "./fiscal-nacional";

export class NFSeService {
 private db: Database;
 private fiscalClient: FiscalNacionalClient;
 private currencyService: CurrencyConversionService;

 constructor(db: Database, env: Env) {
  this.db = db;
  this.fiscalClient = new FiscalNacionalClient(env);
  this.currencyService = createCurrencyConversionService(
   env.STRIPE_SECRET_KEY,
  );
 }

 async createNFSeForSubscription(params: {
  userId: number;
  stripeInvoiceId: string;
  stripePaymentIntentId: string;
  stripeChargeId: string;
  serviceDescription: string;
  amount: number;
  currency: string;
  customerEmail: string;
  productName?: string;
 }) {
  // 1. Convert currency
  const conversion = await this.currencyService.convertToBRL({
   amount: params.amount,
   currency: params.currency,
   chargeId: params.stripeChargeId,
   paymentIntentId: params.stripePaymentIntentId,
  });

  // 2. Get user tax info
  const taxInfo = await this.db
   .select()
   .from(userTaxInfo)
   .where(eq(userTaxInfo.userId, params.userId))
   .limit(1);

  if (!taxInfo || taxInfo.length === 0) {
   throw new Error("User must provide tax information before generating NFS-e");
  }

  const info = taxInfo[0];

  // 3. Build NFS-e request (Brazilian or International)
  const nfseRequest = info.isBrazilian
   ? this.buildBrazilianNFSeRequest(info, params, conversion)
   : this.buildInternationalNFSeRequest(info, params, conversion);

  // 4. Call Fiscal Nacional API
  try {
   const apiResponse = await this.fiscalClient.createNFSe(nfseRequest);

   // 5. Save to database
   const [record] = await this.db
    .insert(nfse)
    .values({
     userId: params.userId,
     taxInfoId: info.id,
     fiscalNacionalId: apiResponse.id,
     fiscalNacionalReference: apiResponse.reference,
     stripeInvoiceId: params.stripeInvoiceId,
     stripePaymentIntentId: params.stripePaymentIntentId,
     stripeChargeId: params.stripeChargeId,
     transactionType: "subscription",
     nfseNumber: apiResponse.nfseNumber,
     status: apiResponse.status,
     serviceDescription: params.serviceDescription,
     productName: params.productName,
     valueBrl: conversion.amountBrl,
     valueUsd: conversion.originalCurrency === "USD"
      ? conversion.originalAmount
      : null,
     originalAmount: conversion.originalAmount,
     originalCurrency: conversion.originalCurrency,
     exchangeRate: conversion.exchangeRate,
     issRate: 0.02,
     issValue: conversion.amountBrl * 0.02,
     customerName: info.fullName,
     customerEmail: params.customerEmail,
     customerCountry: info.country,
     customerDocument: info.isBrazilian ? info.cpfCnpj : info.nif,
    })
    .returning();

   return record;
  } catch (error) {
   // Save error record
   const [errorRecord] = await this.db
    .insert(nfse)
    .values({
     userId: params.userId,
     taxInfoId: info.id,
     fiscalNacionalReference: `ERR_${Date.now()}`,
     status: "error",
     errorMessage: (error as Error).message,
     // ... rest of the fields
    })
    .returning();

   throw error;
  }
 }

 private buildBrazilianNFSeRequest(taxInfo: any, params: any, conversion: any) {
  // Build request for Brazilian customer
  return {
   externalReference: `SUB_${params.stripeInvoiceId}`,
   service: {
    description: params.serviceDescription,
    amount: conversion.amountBrl,
   },
   customer: {
    name: taxInfo.fullName,
    email: params.customerEmail,
    document: taxInfo.cpfCnpj,
    address: {
     street: taxInfo.address,
     number: taxInfo.number,
     neighborhood: taxInfo.neighborhood,
     city: taxInfo.city,
     cityCode: taxInfo.cityCode,
     state: taxInfo.state,
     postalCode: taxInfo.postalCode,
    },
   },
  };
 }

 private buildInternationalNFSeRequest(
  taxInfo: any,
  params: any,
  conversion: any,
 ) {
  // Build request for international customer
  return {
   externalReference: `SUB_${params.stripeInvoiceId}`,
   service: {
    description: params.serviceDescription,
    amount: conversion.amountBrl,
   },
   customer: {
    name: taxInfo.fullName,
    email: params.customerEmail,
    country: taxInfo.country,
    nif: taxInfo.nif,
   },
   export: {
    originalAmount: conversion.originalAmount,
    originalCurrency: conversion.originalCurrency,
    exchangeRate: conversion.exchangeRate,
   },
  };
 }
}
```

### 5. API Routes

**File**: `src/routes/fiscal/index.ts` (create this)

```typescript
import { zValidator } from "@hono/zod-validator";
import { desc, eq } from "drizzle-orm";
import { Hono } from "hono";
import { z } from "zod";
import { nfse, userTaxInfo } from "../../db/schema";
import { requireAuth } from "../../middleware/auth";

const fiscal = new Hono()
 // Tax Info endpoints
 .get("/tax-info", requireAuth, async (c) => {
  const user = c.get("user");
  const db = c.get("db");

  const info = await db
   .select()
   .from(userTaxInfo)
   .where(eq(userTaxInfo.userId, user.id))
   .limit(1);

  if (!info || info.length === 0) {
   return c.json({ error: "Tax info not found" }, 404);
  }

  return c.json(info[0]);
 })
 .post(
  "/tax-info",
  requireAuth,
  zValidator(
   "json",
   z.object({
    country: z.string().length(2),
    fullName: z.string(),
    cpfCnpj: z.string().optional(),
    nif: z.string().optional(),
    // ... more fields
   }),
  ),
  async (c) => {
   const user = c.get("user");
   const db = c.get("db");
   const data = c.req.valid("json");

   const [created] = await db
    .insert(userTaxInfo)
    .values({
     userId: user.id,
     ...data,
     isBrazilian: data.country === "BR",
    })
    .returning();

   return c.json(created, 201);
  },
 )
 // NFS-e endpoints
 .get("/nfse", requireAuth, async (c) => {
  const user = c.get("user");
  const db = c.get("db");

  const records = await db
   .select()
   .from(nfse)
   .where(eq(nfse.userId, user.id))
   .orderBy(desc(nfse.createdAt))
   .limit(50);

  return c.json({ items: records, total: records.length });
 })
 .get("/nfse/:id", requireAuth, async (c) => {
  const user = c.get("user");
  const db = c.get("db");
  const id = Number.parseInt(c.req.param("id"));

  const [record] = await db
   .select()
   .from(nfse)
   .where(eq(nfse.id, id))
   .limit(1);

  if (!record || record.userId !== user.id) {
   return c.json({ error: "NFS-e not found" }, 404);
  }

  return c.json(record);
 })
 // Webhook endpoint (NO AUTH)
 .post("/webhook", async (c) => {
  const db = c.get("db");
  const event = await c.req.json();

  // Handle webhook event (similar to Python implementation)
  // Find NFS-e by reference, update status, etc.

  return c.json({ status: "processed" });
 });

export default fiscal;
```

### 6. Register Routes

**File**: `src/index.ts`

```typescript
import fiscalRoutes from "./routes/fiscal";

// ... existing code

app.route("/api/v1/fiscal", fiscalRoutes);
```

---

## 🎨 Frontend UI Components

See separate files:

- `frontend/src/features/fiscal/components/TaxInfoModal.tsx`
- `frontend/src/features/fiscal/pages/BillingHistory.tsx`
- `frontend/src/features/fiscal/types.ts`

---

## 📋 Testing Checklist

### FastAPI Backend

- [ ] Run migration: `just migrate` or `uv run alembic upgrade head`
- [ ] Update company info in `src/services/fiscal_nacional.py`
- [ ] Add env vars to `.env`
- [ ] Test tax info creation: `POST /api/v1/fiscal/tax-info`
- [ ] Test Brazilian CPF validation
- [ ] Test NFS-e generation after Stripe payment
- [ ] Test webhook endpoint with mock data

### Bun Hono Backend

- [ ] Generate Drizzle migration: `bun db:generate`
- [ ] Apply migration: `bun db:migrate`
- [ ] Create Fiscal Nacional client service
- [ ] Create NFSe service
- [ ] Create fiscal routes
- [ ] Test endpoints
- [ ] Test webhook handling

### Frontend

- [ ] Create tax info modal component
- [ ] Create billing history page
- [ ] Integrate with purchase flow
- [ ] Test modal displays before first purchase
- [ ] Test NFS-e downloads

---

## 🚀 Production Setup

1. **Update company information** in both backends
2. **Set production environment**: `FISCAL_NACIONAL_ENVIRONMENT=production`
3. **Get production API key** from Fiscal Nacional dashboard
4. **Configure webhook URL** in Fiscal Nacional dashboard:
   - FastAPI: `https://api.yourapp.com/api/v1/fiscal/fiscal-webhook`
   - Bun Hono: `https://api.yourapp.com/api/v1/fiscal/webhook`
5. **Set webhook secret** for signature verification
6. **Test with small transactions** first
7. **Monitor NFS-e generation logs**
8. **Set up alerts** for error emails

---

## 📚 Key Differences from llmgenerator

- ✅ Uses Stripe balance transactions (like llmgenerator)
- ✅ Automatic currency conversion (no manual rates)
- ✅ PTAX fallback for tax compliance  
- ✅ Webhook endpoints for status updates
- ✅ Audit trail with conversion source tracking
- ✅ Both FastAPI and Bun Hono implementations

---

## 🆘 Support

For Fiscal Nacional API documentation:

- Sandbox: <https://sandbox.fiscalnacional.com.br/docs>
- Production: <https://api.fiscalnacional.com.br/docs>

For PTAX rates:

- <https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/swagger-ui3>

For IBGE city codes:

- <https://servicodados.ibge.gov.br/api/docs/localidades>
