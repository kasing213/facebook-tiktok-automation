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

### 2026-01-11 - PDF/XLSX Export & Telegram PDF with Verify Button

#### Overview
Implemented real PDF generation (matching frontend invoice design), real XLSX export, and Telegram PDF document sending with inline "Verify Payment" button for enhanced customer UX.

#### 1. Added PDF/XLSX Dependencies
**File:** `requirements.txt`

```
# PDF and Excel export
fpdf2==2.7.6       # PDF generation (pure Python)
openpyxl==3.1.2    # XLSX export
```

#### 2. Real PDF Generation (Matching Frontend Design)
**File:** `app/services/invoice_mock_service.py`

**Before:** Mock PDF using raw string formatting - minimal, unstyled output.

**After:** Professional PDF using fpdf2 matching InvoiceDetailPage.tsx design:
- Blue header (#4A90E2) with invoice number and status
- Customer info and due date section
- Line items table with headers
- Subtotal, tax, and grand total
- Payment information section (bank, account, recipient)

```python
def generate_pdf(invoice_id: str) -> Optional[bytes]:
    from fpdf import FPDF

    # Colors (matching frontend)
    BLUE = (74, 144, 226)
    DARK = (31, 41, 55)
    GRAY = (107, 114, 128)

    pdf = FPDF()
    pdf.add_page()
    # Header, customer info, line items table, totals, payment info
    return bytes(pdf.output())
```

#### 3. Real XLSX Export
**File:** `app/services/invoice_mock_service.py`

**Before:** Returned placeholder bytes `b"PK\x03\x04XLSX_MOCK_CONTENT"` - not valid XLSX.

**After:** Real Excel file using openpyxl:
- Styled header row (blue background, white bold text)
- All invoice data columns
- Auto-sized columns
- Proper Excel formatting

```python
def _generate_xlsx_export(invoices: List[Dict]) -> bytes:
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4A90E2")
    # Headers, data rows, auto-size columns

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
```

#### 4. Telegram PDF Document Sending with Verify Button
**File:** `api-gateway/src/api/internal.py`

**New endpoint:** `POST /internal/telegram/send-invoice-pdf`

Sends invoice as PDF document attachment (not text) with inline "Verify Payment" button:

```python
class InvoicePDFRequest(BaseModel):
    chat_id: str
    invoice_id: str
    invoice_number: str
    amount: str
    pdf_data: str  # Base64-encoded PDF
    customer_name: Optional[str] = None

@router.post("/telegram/send-invoice-pdf")
async def send_invoice_pdf(data: InvoicePDFRequest):
    pdf_bytes = base64.b64decode(data.pdf_data)
    pdf_file = BufferedInputFile(file=pdf_bytes, filename=f"{data.invoice_number}.pdf")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Verify Payment",
            callback_data=f"verify_invoice:{data.invoice_id}"
        )]
    ])

    await bot.send_document(
        chat_id=data.chat_id,
        document=pdf_file,
        caption=caption,
        reply_markup=keyboard
    )
```

#### 5. Verify Invoice Button Handler
**File:** `api-gateway/src/bot/handlers/client.py`

**New handler:** `verify_invoice:{invoice_id}` callback

When customer clicks "Verify Payment" button on the PDF:
1. Validates customer is linked
2. Fetches invoice details
3. Sets FSM state to `waiting_for_payment_screenshot`
4. Prompts customer to send payment screenshot

```python
@router.callback_query(F.data.startswith("verify_invoice:"))
async def handle_verify_invoice_button(callback: types.CallbackQuery, state: FSMContext):
    invoice_id = callback.data.split(":")[1]
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)

    if not customer:
        await callback.message.answer("You need to link your account first...")
        return

    invoice = await invoice_service.get_invoice_by_id(invoice_id)
    await state.update_data(selected_invoice=invoice)
    await state.set_state(ClientStates.waiting_for_payment_screenshot)
    await callback.message.answer("Please send a screenshot of your payment receipt...")
```

#### 6. Updated Send Invoice to Customer Flow
**File:** `app/routes/integrations/invoice.py`

`send_invoice_to_telegram()` now:
1. Generates real PDF using fpdf2
2. Base64 encodes the PDF
3. Sends to api-gateway's new `/telegram/send-invoice-pdf` endpoint
4. Falls back to text message if PDF generation fails

```python
async def send_invoice_to_telegram(invoice: dict, customer: dict, db: Session) -> dict:
    from app.services import invoice_mock_service

    pdf_bytes = invoice_mock_service.generate_pdf(str(invoice_id))
    if not pdf_bytes:
        return await _send_invoice_text_fallback(...)

    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    response = await client.post(
        f"{api_gateway_url}/internal/telegram/send-invoice-pdf",
        json={
            "chat_id": telegram_chat_id,
            "invoice_id": str(invoice_id),
            "invoice_number": invoice_number,
            "amount": amount_str,
            "pdf_data": pdf_b64,
            "customer_name": customer_name
        }
    )
```

#### Complete Flow Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│               MERCHANT DASHBOARD                                 │
│  [Create Invoice] → [Send to Customer]                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               TELEGRAM (Customer receives)                       │
│  ┌─────────────────────────────────────┐                        │
│  │ INV-2601-00001.pdf                  │  ← PDF Document        │
│  │ Invoice INV-2601-00001              │                        │
│  │ Amount: 100,000 KHR                 │                        │
│  │                                     │                        │
│  │ After payment, click below to verify│                        │
│  └─────────────────────────────────────┘                        │
│  ┌─────────────────────────────────────┐                        │
│  │      Verify Payment                 │  ← Inline Button       │
│  └─────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Customer clicks button
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               BOT PROMPTS FOR SCREENSHOT                         │
│  "Please send a screenshot of your payment receipt..."          │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Customer sends screenshot
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               OCR VERIFICATION                                   │
│  Checks: amount, date, recipient, account number                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               MERCHANT NOTIFICATION                              │
│  [OK] Payment Verified! or [WARN] Verification issue            │
└─────────────────────────────────────────────────────────────────┘
```

#### Files Modified
| File | Changes |
|------|---------|
| `requirements.txt` | Added fpdf2, openpyxl |
| `app/services/invoice_mock_service.py` | Real PDF + XLSX generation |
| `api-gateway/src/api/internal.py` | New `/telegram/send-invoice-pdf` endpoint |
| `api-gateway/src/bot/handlers/client.py` | New `verify_invoice` callback handler |
| `app/routes/integrations/invoice.py` | Updated to send PDF with verify button |
