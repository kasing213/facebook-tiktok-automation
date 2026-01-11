# Facebook-TikTok Automation Project

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         VERCEL                                   │
│  Frontend Only (React Static Files)                             │
│  URL: https://facebooktiktokautomation.vercel.app               │
│  - Serves index.html, JS, CSS, images                           │
│  - NO backend/API - just static files                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ API calls to
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         RAILWAY                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  SERVICE: facebook-automation (Main Backend)             │   │
│  │  Type: FastAPI                                           │   │
│  │  Source: / (root of repo)                                │   │
│  │  Start: uvicorn app.main:app                             │   │
│  │                                                          │   │
│  │  Endpoints:                                              │   │
│  │  - /api/auth/* - Authentication                          │   │
│  │  - /api/oauth/* - OAuth flows (Facebook, TikTok)         │   │
│  │  - /api/telegram/* - Telegram linking                    │   │
│  │  - /api/automations/* - Automation management            │   │
│  │  - /api/tokens/* - Token management                      │   │
│  │  - /health - Health check                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  SERVICE: api-gateway (Telegram Bot + API Proxy)         │   │
│  │  Type: FastAPI + aiogram                                 │   │
│  │  Source: /api-gateway                                    │   │
│  │  Start: python -m src.main                               │   │
│  │                                                          │   │
│  │  Features:                                               │   │
│  │  - Telegram bot polling (@KS_automations_bot)            │   │
│  │  - /api/invoice/* - Invoice service proxy                │   │
│  │  - /api/scriptclient/* - Screenshot service proxy        │   │
│  │  - /api/audit-sales/* - Sales audit proxy                │   │
│  │  - /api/ads-alert/* - Ads alert proxy                    │   │
│  │  - /health - Health check                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUPABASE (PostgreSQL)                         │
│  Schemas: public, invoice, scriptclient, audit_sales, ads_alert │
└─────────────────────────────────────────────────────────────────┘
```

## Environment Variables

### Railway: facebook-automation (Main Backend)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `OAUTH_STATE_SECRET` | Secret for OAuth state | `random-secret` |
| `MASTER_SECRET_KEY` | App master secret | `random-secret` |
| `FB_APP_ID` | Facebook App ID | `123456789` |
| `FB_APP_SECRET` | Facebook App Secret | `secret` |
| `TIKTOK_CLIENT_KEY` | TikTok Client Key | `key` |
| `TIKTOK_CLIENT_SECRET` | TikTok Client Secret | `secret` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | `123:ABC...` |
| `TELEGRAM_BOT_USERNAME` | Bot username (no @) | `KS_automations_bot` |
| `BASE_URL` | Backend URL | `https://xxx.railway.app` |
| `FRONTEND_URL` | Frontend URL | `https://xxx.vercel.app` |

### Railway: api-gateway (Telegram Bot)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Same PostgreSQL as main | `postgresql://...` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | `123:ABC...` |
| `TELEGRAM_BOT_USERNAME` | Bot username (no @) | `KS_automations_bot` |
| `CORE_API_URL` | Main backend URL | `https://facebook-automation.railway.app` |

### Vercel (Frontend)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Main backend URL | `https://xxx.railway.app` |

## Key Files

### Main Backend (app/)
- `app/main.py` - FastAPI entry point
- `app/core/config.py` - Settings (pydantic-settings)
- `app/routes/telegram.py` - Telegram linking endpoints
- `app/routes/oauth.py` - OAuth callbacks
- `app/routes/auth.py` - Authentication

### API Gateway (api-gateway/)
- `api-gateway/src/main.py` - FastAPI + Bot entry
- `api-gateway/src/config.py` - Settings
- `api-gateway/src/bot/` - Telegram bot handlers
- `api-gateway/src/services/` - PostgreSQL services

### Frontend (frontend/)
- `frontend/src/App.tsx` - React entry
- `frontend/src/services/api.ts` - API client
- `frontend/src/hooks/useTelegram.ts` - Telegram hook

### Invoice Components (frontend/src/components/invoice/)
- `InvoiceDetailPage.tsx` - Invoice view/edit page with totals calculation
- `InvoiceTable.tsx` - Invoice list table component
- `LineItemsEditor.tsx` - Line items editor with currency support (USD/KHR)
- `InvoiceForm.tsx` - Invoice create/edit form

**Important:** All `formatCurrency()` functions must validate inputs for null/undefined/NaN to prevent "$NaN" display. Use this pattern:
```typescript
const formatCurrency = (amount: number | null | undefined): string => {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '$0.00'
  }
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}
```

## Common Issues

### "Invoice totals show $NaN"
Invoice detail page shows `$NaN` for Subtotal or Total.

**Cause:** Backend API doesn't always return `subtotal` and `total` fields, and `formatCurrency()` doesn't handle null/undefined.

**Fix:**
1. Ensure `formatCurrency()` validates inputs (see pattern above)
2. Use fallback calculation from line items:
```typescript
const subtotal = invoice.subtotal ?? calculateSubtotalFromItems(invoice.items)
const total = invoice.total ?? calculateTotalFromItems(invoice)
```

### "Wrong bot link generated"
The dashboard generates `t.me/your_bot` instead of correct bot.

**Cause:** `TELEGRAM_BOT_USERNAME` not set in Railway (main backend)

**Fix:** Add to Railway → facebook-automation → Variables:
```
TELEGRAM_BOT_USERNAME=KS_automations_bot
```

### "Bot not responding"
Telegram bot doesn't respond to commands.

**Check:** Railway → api-gateway logs for:
- "Starting Telegram bot polling..."
- "Run polling for bot @KS_automations_bot"

**Common causes:**
- `TELEGRAM_BOT_TOKEN` not set
- Another bot instance running (conflict error - usually recovers)

### "Frontend can't reach API"
API calls fail from the dashboard.

**Check:** Vercel → Settings → Environment Variables:
```
VITE_API_URL=https://your-railway-backend.railway.app
```

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/start <code>` | Link Telegram to dashboard account |
| `/status` | Show all systems status |
| `/invoice` | Invoice operations |
| `/verify` | Screenshot verification |
| `/sales` | Sales reports |
| `/promo` | Promotion status |
| `/help` | Show all commands |

## Database Schemas

- `public` - Main app tables (users, tenants, tokens, automations)
- `invoice` - Invoice generator tables
- `scriptclient` - Screenshot verification tables
- `audit_sales` - Sales audit tables
- `ads_alert` - Ads alert/promo tables

---

## Change Log

### 2026-01-11 - OCR Verification & Invoice Edit Fixes

#### 1. OCR Verification - Recipient Name Array Fix
**File:** `api-gateway/src/bot/handlers/ocr.py`

**Problem:** OCR service expected `recipientNames` as an array, but api-gateway sent `recipient_name` as a string.

**Fix:** Transform `recipient_name` (singular string from DB) → `recipientNames` (array for OCR):
```python
recipient_name = invoice.get("recipient_name")
recipient_names = [recipient_name] if recipient_name else []
expected_payment = {
    ...
    "recipientNames": recipient_names,  # Array, not string
}
```

#### 2. OCR Verification - Required Fields Check
**File:** `api-gateway/src/bot/handlers/ocr.py`

**Problem:** OCR verification was skipping recipient check when `recipient_name` or `expected_account` was missing from invoice.

**Fix:** Added validation to reject verification if required fields are missing:
```python
if not invoice.get("recipient_name") or not invoice.get("expected_account"):
    await callback.message.answer(
        "❌ Cannot verify payment. Invoice is missing required fields...",
        parse_mode=ParseMode.HTML
    )
    return
```

#### 3. OCR Verification - 404 "Invoice does not exist" Fix
**File:** `api-gateway/src/bot/handlers/ocr.py`

**Problem:** `/verify_invoice` returned 404 "Invoice does not exist" while `/ocr` worked fine.

**Root Cause:** OCR service has two modes:
- Mode A: Uses inline `expectedPayment` parameters
- Mode B: If `invoice_id` passed, does MongoDB lookup

API gateway sent both `invoice_id` AND `expectedPayment`. OCR service checked `invoice_id` first, tried MongoDB lookup (but invoices are in PostgreSQL!), returned 404.

**Fix:** Removed `invoice_id` parameter from OCR service call to force Mode A:
```python
result = await ocr_service.verify_screenshot(
    image_data=image_data,
    filename=f"telegram_{photo.file_id}.jpg",
    # invoice_id=invoice.get("id"),  # REMOVED - causes MongoDB lookup
    expected_payment=expected_payment,
    customer_id=invoice.get("customer_id")
)
```

#### 4. OCR Verification - "Error Processing Screenshot" Fix
**File:** `api-gateway/src/bot/handlers/ocr.py`

**Problem:** OCR service returned 200 VERIFIED but Telegram showed "Error Processing Screenshot".

**Root Cause:** `verification_warnings` variable was used at line 506 but never defined (NameError).

**Fix:** Added missing variable extraction:
```python
extracted = result.get("extracted_data", {})
verification = result.get("verification", {})
confidence = result.get("confidence", 0)
verification_warnings = verification.get("warnings") or []  # Added this line
```

#### 5. Invoice Edit - Amount Recalculation Fix
**File:** `app/routes/integrations/invoice.py`

**Problem:** When editing invoice line items, the total amount was not recalculated.

**Fix:** Added amount recalculation when items are updated:
```python
new_amount = None
if data.items:
    items_json = json.dumps([...])
    # Recalculate amount from line items
    new_amount = sum(
        (item.quantity * item.unit_price * (1 + (item.tax_rate or 0) / 100))
        for item in data.items
    )

result = db.execute(text("""
    UPDATE invoice.invoice
    SET items = COALESCE(CAST(:items AS jsonb), items),
        amount = COALESCE(:amount, amount),  # Added this
        ...
"""), {"amount": new_amount, ...})
```

#### 6. Invoice Edit - 404 Error Handling Fix
**File:** `app/routes/integrations/invoice.py`

**Problem:** When PostgreSQL update returned no rows (invoice not found or wrong tenant), the code silently fell through to mock mode instead of returning 404.

**Fix:** Added explicit 404 handling:
```python
row = result.fetchone()
if row:
    db.commit()
    return {...}
else:
    # No row returned - invoice doesn't exist or doesn't belong to this tenant/merchant
    raise HTTPException(status_code=404, detail="Invoice not found")
```

#### OCR Verification Data Flow Reference
```
Database Field       → OCR Service Field    → Transformation
─────────────────────────────────────────────────────────────
recipient_name       → recipientNames       → Wrap in array []
expected_account     → toAccount            → Rename (camelCase)
amount               → amount               → Direct copy
currency             → currency             → Default "KHR"
bank                 → bank                 → Direct copy
due_date             → dueDate              → Rename (camelCase)
```
