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
- `inventory` - **NEW** Lightweight product tracking and stock movements

---

## Implemented Features (2026-01-13)

### ✅ Lightweight Inventory System (COMPLETED)
**Migration:** `o5j6k7l8m9n0_add_inventory_system.py` - Successfully applied

**Positioning:** Simple product tracker for invoice line items - NOT competing with full ERP like MAQSU

**✅ Implemented Features:**
- ✅ Product catalog with SKU, price, current stock
- ✅ Stock movements tracking (in/out/adjustment)
- ✅ Low stock alerts via Telegram bot ← **Unique competitive advantage**
- ✅ Auto-populate invoice line items from products
- ✅ Auto-deduct stock when payment verified via OCR
- ✅ Complete tenant isolation and role-based access

**✅ Database Schema (Live):**
```sql
-- inventory.products (✅ Created)
id, tenant_id, name, sku, unit_price, cost_price, currency
current_stock, low_stock_threshold, track_stock, is_active
created_at, updated_at, meta (JSON)

-- inventory.stock_movements (✅ Created)
id, tenant_id, product_id, movement_type (in/out/adjustment)
quantity, reference_type, reference_id, notes, created_by, created_at
```

**✅ API Endpoints (Live):**
- ✅ `GET /inventory/products` - List products with stock levels
- ✅ `POST /inventory/products` - Create product (Member/Owner only)
- ✅ `PUT /inventory/products/{id}` - Update product (Member/Owner only)
- ✅ `DELETE /inventory/products/{id}` - Soft delete (Owner only)
- ✅ `POST /inventory/adjust-stock` - Manual stock adjustment
- ✅ `GET /inventory/movements` - Stock movement history
- ✅ `GET /inventory/low-stock` - Products below threshold
- ✅ `GET /inventory/movements/summary` - Movement analytics

**✅ Invoice Integration (Live):**
- ✅ `GET /api/integrations/invoice/products` - Product picker endpoint
- ✅ Auto-deduct stock when `verify_invoice()` API called with `verified` status
- ✅ Stock movements linked to invoice ID for audit trail
- ✅ Error handling - partial failures don't break payment verification

**✅ Telegram Bot Commands (Live):**
- ✅ `/inventory` - Check all stock levels with summary stats
- ✅ `/lowstock` - View products below threshold with restock recommendations
- ✅ Low stock alert notifications to all tenant users
- ✅ Role validation (Member/Owner access only, excludes viewers)
- ✅ Added to `/help` command

**✅ Security Implementation:**
- ✅ Complete tenant isolation - all queries filtered by `tenant_id`
- ✅ Role-based access using existing authorization decorators
- ✅ Repository pattern ensures no cross-tenant data leakage
- ✅ Input validation and SQL injection protection
- ✅ Owner-only delete operations

**✅ Frontend UI (2026-01-14):**
- ✅ Inventory List Page (`/dashboard/inventory`)
  - Product list with search and low-stock filter
  - Stats cards: Total Products, Active Products, Low Stock, Stock Value
  - CRUD modals: Create Product, Edit Product, Adjust Stock, Delete
  - Stock badge indicators (green/red based on threshold)
- ✅ Product Picker in Invoice Creation
  - Dropdown in LineItemsEditor header
  - Search products by name/SKU
  - Shows price and stock availability
  - Auto-fills line item with product details
  - Blocks selection of out-of-stock items

**Frontend Files:**
| File | Purpose |
|------|---------|
| `frontend/src/types/inventory.ts` | TypeScript interfaces for Product, StockMovement |
| `frontend/src/services/inventoryApi.ts` | API client for inventory endpoints |
| `frontend/src/components/dashboard/inventory/InventoryListPage.tsx` | Main inventory management page |
| `frontend/src/components/invoice/ProductPicker.tsx` | Product selection dropdown for invoices |
| `frontend/src/components/invoice/LineItemsEditor.tsx` | Updated with ProductPicker integration |

**Invoice-Inventory Integration Flow:**
```
1. Dashboard: Create Invoice → Select Customer
2. Line Items: Click "📦 Select Product" button
3. Search/select product from dropdown
4. Product name, SKU, unit_price auto-fill the line item
5. Adjust quantity if needed
6. Save Invoice → Send to Customer via Telegram
7. Customer pays → Sends screenshot → OCR verifies
8. Payment verified → Stock automatically deducted
9. Stock movement recorded with invoice_id reference
```

### Authentication System Status

**✅ Core Features (COMPLETED):**
- ✅ JWT authentication (production-ready)
- ✅ Role-based access (admin/user/viewer with decorators)
- ✅ OAuth Facebook/TikTok (working)
- ✅ Telegram linking (working)
- ✅ Session management with refresh tokens
- ✅ Rate limiting middleware (basic)
- ✅ IP blocking and access rules

**❌ Missing Security Features (NOT IMPLEMENTED):**
- ❌ **Email verification on signup** (security gap)
- ❌ **Account lockout after failed attempts** (brute force vulnerability)
- ❌ **Password strength validation** (weak password risk)
- ❌ **Forgot password flow** (user experience gap)
- ❌ **Password reset tokens** (recovery mechanism missing)
- ❌ **Login attempt logging** (security audit trail missing)

**🔍 Security Assessment:**
- **HIGH RISK:** No account lockout - brute force attacks possible
- **MEDIUM RISK:** No email verification - fake account registration
- **LOW RISK:** No password strength - users can set weak passwords
- **UX IMPACT:** No password reset - users locked out permanently

**🛡️ Next Security Priority:**
1. **Account lockout** (prevent brute force) - HIGH
2. **Email verification** (prevent fake accounts) - MEDIUM
3. **Password reset flow** (user recovery) - MEDIUM
4. **Password strength validation** - LOW

### Competitive Analysis Summary
**Cambodia Market Position:**
- BanhJi: General accounting + bank integration (no OCR verification)
- Invoice Mouy: Invoice-only (no OCR verification, no social media)
- MAQSU: Full ERP (too complex, enterprise-focused)

**Your Unique Value:**
1. **OCR Payment Verification** ← Nobody in Cambodia has this
2. **Telegram Bot Integration** ← Unique in Cambodia
3. **Social Media Automation** ← Nobody combines this with invoicing

**Pricing Strategy:**
- Free: Core invoice + payment verification
- Pro ($10-15/mo): Inventory + advanced reports + bulk operations
- Stay under $15/mo to compete in Cambodia market

---

## Change Log

### 2026-01-13 - Photo Handler & Invoice UX Fixes

#### 1. Photo Handler - FSM State Priority Fix (Critical)
**File:** `api-gateway/src/bot/handlers/client.py`

**Problem:** Merchants who are also customers (testing their own system) couldn't verify payments. Photo handler checked merchant status FIRST and blocked client payment flow.

**Railway Logs Showed:**
```
User 1450060367 is a merchant, checking OCR state...
Merchant 1450060367 in state ClientStates:waiting_for_payment_screenshot, delegating to state handler
```
But no state handler exists for merchants in `ClientStates` → Nothing happened.

**Root Cause:** User identity (merchant/customer) was checked before FSM state. Merchants with `ClientStates` were blocked from client payment processing.

**Fix:** Reordered logic to check FSM state FIRST:
```python
# BEFORE: Check user type first (blocked merchant-customers)
user = await get_user_by_telegram_id(telegram_id)
if user:
    if current_state:
        return  # ❌ Blocked here - no handler for merchants in ClientStates

# AFTER: Check FSM state first (allows merchant-customers)
current_state = await state.get_state()
if current_state == ClientStates.waiting_for_payment_screenshot:
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if customer:
        await process_client_payment_screenshot(...)  # ✅ Works for merchants too
        return
```

**Priority Order (Most Specific → Least Specific):**
1. `ClientStates.waiting_for_payment_screenshot` → Process client payment (merchants can be customers)
2. Merchant with other states (`OCRStates.*`) → Delegate to OCR handlers
3. Customer without state → Show pending invoices

#### 2. Invoice Button UX - Show Invoice Number
**File:** `api-gateway/src/api/internal.py`

**Problem:** Button text "Verify This Payment" was generic, not clear which invoice.

**Fix:** Changed button text to include invoice number:
```python
# BEFORE
text="Verify This Payment"
text="View Other Invoices"

# AFTER
text=f"✅ Verify {data.invoice_number}"  # e.g., "✅ Verify INV-2601-00002"
text="📋 Other Invoices"
```

#### 3. Invoice Selection - Inline Edit (No Content Push)
**File:** `api-gateway/src/bot/handlers/client.py`

**Problem:** "View Other Invoices" created a new message that pushed the PDF down.

**Fix:** Edit existing message buttons inline instead of creating new message:
```python
# BEFORE: New message pushes content down
await callback.message.answer("Select Invoice...", reply_markup=keyboard)

# AFTER: Edit buttons inline (keeps PDF in place)
await callback.message.edit_reply_markup(reply_markup=keyboard)
```

**Added:** "⬅️ Back" button to restore original buttons.

#### 4. PDF Generation - Remove Non-Existent Column
**File:** `app/services/invoice_mock_service.py`

**Problem:** SQL query referenced `c.company` column that doesn't exist in `invoice.customer` table.

**Error:** `column c.company does not exist`

**Fix:** Removed non-existent column from SQL query:
```sql
-- BEFORE (error)
SELECT ... c.company as customer_company ...

-- AFTER (works)
SELECT ... c.name, c.email, c.phone, c.address ...
```

**Actual `invoice.customer` columns:** id, tenant_id, name, email, phone, address, meta, created_at, updated_at

#### 5. PDF Generation - JSONB Auto-Deserialization
**File:** `app/services/invoice_mock_service.py`

**Problem:** SQLAlchemy auto-deserializes JSONB columns to Python lists, but code tried to parse again.

**Error:** `the JSON object must be str, bytes or bytearray, not list`

**Fix:** Handle both string and already-parsed list:
```python
# BEFORE (error when already parsed)
items = json.loads(result.items) if result.items else []

# AFTER (handles both cases)
if result.items:
    if isinstance(result.items, str):
        items = json.loads(result.items)
    else:
        items = result.items  # Already deserialized by SQLAlchemy
else:
    items = []
```

#### Photo Handler Decision Flow Reference
```
Photo Received
    │
    ├─ Check FSM State FIRST
    │   ├─ ClientStates.waiting_for_payment_screenshot?
    │   │   ├─ YES: Check customer registration
    │   │   │   ├─ Customer found → Process payment screenshot ✅
    │   │   │   └─ Not found → "Session expired" message
    │   │   └─ NO: Continue to next check
    │   │
    ├─ Check if Merchant
    │   ├─ YES: Has other state (OCRStates.*)?
    │   │   ├─ YES → Delegate to OCR handler
    │   │   └─ NO → Ignore photo
    │   └─ NO: Continue
    │
    └─ Check if Customer
        ├─ YES → Show pending invoices
        └─ NO → Ignore photo
```

#### Files Modified
| File | Changes |
|------|---------|
| `api-gateway/src/bot/handlers/client.py` | FSM state priority, inline selection, back button |
| `api-gateway/src/api/internal.py` | Button text with invoice number |
| `app/services/invoice_mock_service.py` | Remove company column, handle JSONB |

---

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

### 2026-01-11 - Role-Based Access Control & Subscription Management

#### Overview
Implemented comprehensive role-based access control (RBAC) and subscription-based feature gating to enforce tenant ownership permissions and Pro tier restrictions.

#### 1. Role-Based Authorization Infrastructure
**New File:** `app/core/authorization.py`

**Core Features:**
- `@require_owner` decorator for tenant owner-only endpoints
- `@require_role()` decorator for flexible role requirements
- `@require_subscription_feature()` decorator for Pro feature gates
- `get_current_owner()` dependency for owner-only routes
- `get_current_member_or_owner()` dependency (excludes viewers)

**Security Classes:**
```python
class TenantOwnerRequired(HTTPException):
    """Raised when operation requires tenant owner"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation is restricted to tenant owners only"
        )
```

#### 2. First User Becomes Owner Logic
**Files:** `app/routes/auth.py`, `app/repositories/user.py`

**Implementation:**
- Added `is_first_user_in_tenant()` method to UserRepository
- Registration endpoint checks user count and assigns `UserRole.admin` to first user
- Subsequent users automatically get `UserRole.user` (member role)

```python
# Determine role - first user in tenant becomes owner
role = UserRole.admin if user_repo.is_first_user_in_tenant(user_data.tenant_id) else UserRole.user
```

#### 3. Owner-Only Endpoint Protection
**File:** `app/routes/oauth.py`

**Protected Endpoints:**
- `GET /auth/facebook/authorize` - Owner only
- `GET /auth/facebook/authorize-url` - Owner only
- `GET /auth/tiktok/authorize` - Owner only
- `GET /auth/tiktok/authorize-url` - Owner only

**File:** `app/routes/auth.py`
- `POST /auth/revoke-all-sessions` - Owner only

**Implementation:**
```python
@router.get("/facebook/authorize")
def facebook_authorize(
    current_user: User = Depends(get_current_owner),  # Changed from get_current_user
    ...
):
```

#### 4. User Management Endpoints (Owner-Only)
**New File:** `app/routes/users.py`

**Endpoints:**
- `GET /users/` - List all tenant users with statistics
- `POST /users/invite` - Invite new users (creates user record)
- `PUT /users/{user_id}` - Update user role/status
- `DELETE /users/{user_id}` - Remove user (soft delete with is_active=False)
- `GET /users/{user_id}` - Get detailed user information

**Self-Protection Logic:**
```python
# Prevent owner from demoting themselves
if user.id == owner.id and update_request.role and update_request.role != UserRole.admin:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="You cannot change your own role"
    )
```

#### 5. Subscription Management (Owner-Only)
**New File:** `app/routes/subscription.py`

**Endpoints:**
- `GET /subscription/` - View current plan and available features
- `POST /subscription/change` - Change subscription plan (placeholder for payment integration)
- `POST /subscription/cancel` - Cancel subscription at period end
- `POST /subscription/reactivate` - Reactivate cancelled subscription

**Feature Matrix:**
```python
features = {
    "invoice_create": True,           # Free & Pro
    "invoice_send": True,            # Free & Pro
    "payment_verify": True,          # Free & Pro
    "advanced_reports": tier == SubscriptionTier.pro,  # Pro only
    "bulk_operations": tier == SubscriptionTier.pro,   # Pro only
    "custom_branding": tier == SubscriptionTier.pro,   # Pro only
    "unlimited_invoices": tier == SubscriptionTier.pro # Pro only
}
```

#### 6. Subscription Feature Gates on Invoice Operations
**File:** `app/routes/integrations/invoice.py`

**Protected Endpoints:**
```python
@router.get("/invoices/export")
@require_subscription_feature('bulk_operations')  # Pro only
async def export_invoices(...):

@router.get("/stats")
@require_subscription_feature('advanced_reports')  # Pro only
async def get_stats(...):

@router.post("/invoices")
async def create_invoice(
    current_user: User = Depends(get_current_member_or_owner),  # Excludes viewers
    ...
):
```

#### 7. Error Response Standards
**403 Forbidden (Insufficient Role):**
```json
{
  "detail": "This operation is restricted to tenant owners only"
}
```

**402 Payment Required (Pro Feature):**
```json
{
  "detail": "Feature 'bulk_operations' requires Pro subscription. Upgrade your plan to continue."
}
```

#### 8. Role Hierarchy
```
UserRole.admin (Owner)
├── All tenant management operations
├── OAuth connections (Facebook/TikTok)
├── User invite/manage/remove
├── Subscription management
├── Session revocation for all users
└── All member operations

UserRole.user (Member)
├── Invoice create/edit/send
├── Payment verification
├── View assigned data
├── Use subscription features (if Pro)
└── ❌ Cannot manage users/OAuth/subscription

UserRole.viewer
├── View-only access to assigned invoices
└── ❌ Cannot create/edit anything
```

#### Database Schema Updates
**No schema changes required** - existing `User.role` field supports the new authorization system.

#### Files Modified/Created
| Type | File | Purpose |
|------|------|---------|
| **New** | `app/core/authorization.py` | Authorization decorators & utilities |
| **New** | `app/routes/users.py` | User management endpoints |
| **New** | `app/routes/subscription.py` | Subscription management endpoints |
| **Modified** | `app/routes/auth.py` | First-user-becomes-owner logic |
| **Modified** | `app/routes/oauth.py` | Owner-only OAuth protection |
| **Modified** | `app/repositories/user.py` | User count queries |
| **Modified** | `app/routes/integrations/invoice.py` | Feature gates & role requirements |
| **Modified** | `app/main.py` | Include new routers |

#### Testing Checklist
- [x] Role-based decorators enforce permissions correctly
- [x] First user gets admin role, subsequent users get user role
- [x] OAuth endpoints return 403 for non-owners
- [x] Pro features return 402 for Free tier users
- [x] User management prevents self-demotion/deletion
- [ ] Frontend handles 403/402 responses with upgrade prompts
- [ ] Email invitations send actual emails (currently placeholder)
- [x] Subscription changes integrate with local payment + OCR verification

### 2026-01-11 - Local Subscription Payment Verification

#### Overview
Implemented local bank transfer subscription verification system that reuses the existing proven OCR verification pipeline - same logic, same confidence thresholds, same database patterns.

#### 1. Subscription Payment Flow
**New File:** `app/routes/subscription_payment.py`

**Customer Flow:**
1. Click "Upgrade to Pro" → Generate payment QR code
2. Transfer money to local bank using QR code
3. Upload transaction screenshot
4. OCR verifies payment (reuses existing system)
5. High confidence (≥80%) → Auto-approve in 30 seconds
6. Low confidence → Admin approval required
7. Pro subscription activated immediately

#### 2. OCR Integration (100% Reuse of Existing System)
**Reuses Proven Logic:** Same OCR service, same confidence checks, same error handling

**Data Transformation (Identical to Invoice OCR):**
```python
# Exact same pattern as your invoice verification
expected_payment = {
    "amount": float(invoice.amount),
    "currency": invoice.currency or "KHR",
    "recipientNames": [invoice.recipient_name],  # Array format (CLAUDE.md fix)
    "toAccount": invoice.expected_account,        # camelCase (CLAUDE.md fix)
    "bank": invoice.bank
}

# Uses Mode A (no invoice_id) to avoid MongoDB lookup (CLAUDE.md fix)
ocr_result = await ocr_service.verify_screenshot(
    image_data=image_data,
    filename=f"subscription_{subscription_invoice_id}_{screenshot.filename}",
    expected_payment=expected_payment,  # No invoice_id parameter
    customer_id=str(owner.tenant_id)
)
```

#### 3. Database Schema Consistency
**Subscription invoices stored in same `invoice.invoice` table:**
- `customer_id = 'subscription_customer'` (special identifier)
- `invoice_number = payment_reference` (e.g., "SUB-PRO-tenant123-20260111")
- Same verification fields: `status`, `verification_status`, `verified_at`, `verification_confidence`
- Same status flow: `pending` → `verified`/`rejected`/`pending_approval`

#### 4. Local Bank Configuration
```python
# Replace with your actual bank details
BANK_DETAILS = {
    "bank_name": "ACLEDA Bank",          # Your bank
    "account_number": "123-456-789",     # Your account
    "account_holder": "Your Business",   # Your name
    "currency": "KHR"
}

# Set your pricing
SUBSCRIPTION_PRICING = {
    SubscriptionTier.pro: {
        "monthly": {"usd": 29.99, "khr": 120000},   # Your prices
        "yearly": {"usd": 299.99, "khr": 1200000}
    }
}
```

#### 5. QR Code Payment Instructions
**Generated QR Code includes:**
- Bank account details
- Exact payment amount in KHR
- Reference number for tracking
- Payment instructions in local language

**Customer receives:**
- QR code for mobile banking app
- Manual bank details as backup
- Step-by-step payment instructions
- 7-day payment deadline

#### 6. Admin Approval Workflow
**Endpoints:**
- `GET /subscription-payment/admin/pending-approvals` - List pending verifications
- `POST /subscription-payment/admin/approve/{invoice_id}` - Approve/reject manually

**Auto-Approval Logic:**
- Confidence ≥ 80% → Instant Pro upgrade
- Confidence < 80% but verified → Admin review required
- Failed verification → Automatic rejection

#### 7. Subscription Activation
**Immediate Pro Upgrade:**
```python
async def upgrade_tenant_subscription(tenant_id: UUID, tier: SubscriptionTier, db: Session):
    # Updates subscription table
    # Sets tier = 'pro', status = 'active'
    # Sets billing period to 1 month from now
    # Pro features unlock immediately
```

#### 8. Error Handling (Matches Invoice OCR)
**Same validation as invoice verification:**
- Required fields check: `recipient_name`, `expected_account`
- Image validation: format, size limits
- OCR service availability check
- Exact same error messages and status codes

#### 9. Endpoints Summary
| Endpoint | Purpose | Role Required |
|----------|---------|---------------|
| `POST /subscription-payment/upgrade-request` | Generate QR code | Owner |
| `POST /subscription-payment/verify-payment` | Upload screenshot | Owner |
| `GET /subscription-payment/admin/pending-approvals` | List pending | Admin |
| `POST /subscription-payment/admin/approve/{id}` | Manual approval | Admin |

#### 10. Integration Points
**Connects to existing systems:**
- Uses same OCR service and confidence thresholds
- Stores in existing `invoice.invoice` table
- Follows same verification status workflow
- Reuses same database field patterns
- Leverages existing error handling logic

**What's Different:**
- Special `customer_id = 'subscription_customer'`
- Payment reference as invoice number
- Auto-upgrade subscription on verification
- QR code generation for local banks

#### Files Modified/Created
| Type | File | Purpose |
|------|------|---------|
| **New** | `app/routes/subscription_payment.py` | Local payment verification system |
| **Modified** | `app/routes/subscription.py` | Integration with payment flow |
| **Modified** | `app/main.py` | Include subscription payment router |
