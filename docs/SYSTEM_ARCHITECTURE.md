# System Architecture Overview

## Projects Summary

| Project | Tech Stack | Database | Purpose |
|---------|------------|----------|---------|
| **Facebook-automation** | Python/FastAPI/aiogram | PostgreSQL | Main backend, Telegram bot, API gateway |
| **ocr-service** | Node.js/Express | MongoDB | Payment screenshot OCR verification |
| **General-invoice** | Node.js/Express | MongoDB | Standalone invoice management API |
| **scriptclient** | Node.js | - | Enhanced OCR engine (future integration) |

---

## 1. Facebook-automation (Main Backend)

**Location:** `D:/Facebook-automation`
**Deployment:** Railway
**Repository:** github.com/kasing213/facebook-tiktok-automation

### Components

```
Facebook-automation/
├── api-gateway/src/
│   ├── bot/handlers/
│   │   ├── ocr.py           # Telegram OCR verification commands
│   │   └── client.py        # Client management
│   ├── services/
│   │   ├── ocr_service.py   # OCR API client (calls ocr-service)
│   │   └── invoice_service.py # PostgreSQL invoice queries
│   └── main.py              # FastAPI + aiogram entry point
├── app/
│   ├── routes/integrations/
│   │   └── invoice.py       # Invoice CRUD API endpoints
│   └── core/config.py       # Environment configuration
└── frontend/                # React dashboard
```

### Key Functions

| File | Function | Purpose |
|------|----------|---------|
| `ocr.py` | `handle_invoice_screenshot()` | Process payment screenshot for invoice |
| `ocr.py` | `build expected_payment` | Map invoice fields to OCR expected format |
| `invoice_service.py` | `get_invoice_by_id()` | Fetch invoice from PostgreSQL |
| `invoice_service.py` | `update_invoice_verification()` | Update verification status |
| `ocr_service.py` | `verify_screenshot()` | Call external OCR API |

### Database Schema (PostgreSQL)

```sql
-- invoice.invoice table
CREATE TABLE invoice.invoice (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    customer_id UUID,
    invoice_number VARCHAR,
    amount DECIMAL,
    currency VARCHAR DEFAULT 'KHR',
    status VARCHAR,
    bank VARCHAR,
    expected_account VARCHAR,      -- Bank account to receive payment
    recipient_name VARCHAR,        -- Name on the bank account
    due_date DATE,
    verification_status VARCHAR,   -- pending/verified/rejected
    verified_at TIMESTAMP,
    verified_by VARCHAR,
    verification_note TEXT,
    items JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Environment Variables

```env
# OCR Service
OCR_API_URL=https://general-verification-production.up.railway.app
OCR_API_KEY=your-api-key
OCR_MOCK_MODE=false

# Invoice Service (optional external)
INVOICE_API_URL=https://general-invoice-production.up.railway.app
INVOICE_API_KEY=your-api-key
INVOICE_MOCK_MODE=false
```

---

## 2. ocr-service (Payment Verification)

**Location:** `D:/ocr-service`
**Deployment:** Railway (general-verification-production.up.railway.app)
**Repository:** github.com/kasing213/general-verification

### Components

```
ocr-service/
├── src/
│   ├── core/
│   │   ├── verification.js   # 3-stage verification pipeline
│   │   ├── ocr-engine.js     # OpenAI Vision API integration
│   │   └── fraud-detector.js # Date validation, fraud alerts
│   ├── routes/
│   │   ├── verify.js         # POST /api/v1/verify endpoint
│   │   ├── invoices.js       # Invoice management (MongoDB)
│   │   └── export.js         # Data export endpoints
│   ├── db/
│   │   └── mongo.js          # MongoDB + GridFS connections
│   └── middleware/
│       └── auth.js           # API key authentication
└── docs/
    └── API.md                # API documentation
```

### 3-Stage Verification Pipeline

```
Stage 1: Image Type Detection
├── isBankStatement = false → SILENT REJECT
└── isBankStatement = true → Stage 2

Stage 2: Confidence Check
├── confidence = low/medium → PENDING + "send clearer image"
└── confidence = high → Stage 3

Stage 3: Security Verification (HIGH confidence only)
├── Wrong recipient → REJECT
├── Old screenshot → REJECT + fraud alert
├── Duplicate Trx ID → REJECT + fraud alert
├── Amount mismatch → PENDING
└── All pass → VERIFIED
```

### Key Functions

| File | Function | Purpose |
|------|----------|---------|
| `verification.js` | `verifyPayment()` | Main verification pipeline |
| `verification.js` | `verifyRecipient()` | Check account/name match |
| `ocr-engine.js` | `analyzePaymentScreenshot()` | Call OpenAI Vision API |
| `fraud-detector.js` | `validateTransactionDate()` | Check screenshot age |
| `verify.js` | `normalizeRecipientNames()` | Convert string to array |

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/verify` | Verify payment screenshot |
| GET | `/api/v1/verify/:id` | Get verification result |
| GET | `/api/v1/verify/:id/image` | Get screenshot image |
| GET | `/health` | Health check |
| GET | `/status` | Service status |

### Response Format

```json
{
  "success": true,
  "record_id": "uuid",
  "confidence": 0.9,
  "extracted_data": {
    "amount": "36,000",
    "currency": "KHR",
    "date": "2026-01-10",
    "reference": "TXN123",
    "account": "086 228 226",
    "bank": "ABA",
    "recipient_name": "CHAN K."
  },
  "verification": {
    "status": "verified",
    "message": "Payment verified successfully",
    "rejectionReason": null,
    "expected": {
      "amount": 36000,
      "account": "086 228 226",
      "recipient_name": "CHAN K."
    },
    "matched": {
      "amount": true,
      "account": true,
      "recipient_name": true
    },
    "warnings": null
  }
}
```

### Database (MongoDB)

```javascript
// payments collection
{
  _id: "uuid",
  invoice_id: "uuid",
  customer_id: "uuid",
  amount: 36000,
  currency: "KHR",
  transactionId: "TXN123",  // sparse unique index
  transactionDate: ISODate(),
  toAccount: "086 228 226",
  recipientName: "CHAN K.",
  bankName: "ABA",
  verificationStatus: "verified",
  screenshotId: ObjectId(),  // GridFS reference
  uploadedAt: ISODate()
}

// fraudAlerts collection
{
  _id: ObjectId(),
  fraudType: "OLD_SCREENSHOT",
  severity: "high",
  invoiceId: "uuid",
  transactionId: "TXN123"
}
```

---

## 3. General-invoice (Standalone Invoice Service)

**Location:** `D:/Invoice-generator/General-invoice`
**Deployment:** Railway
**Repository:** github.com/kasing213/Invoice-generator

### Components

```
General-invoice/
├── src/
│   ├── models/
│   │   └── Invoice.js        # Mongoose schema
│   ├── controllers/
│   │   ├── invoiceController.js  # CRUD operations
│   │   └── exportController.js   # PDF/Excel export
│   ├── routes/
│   │   ├── invoices.js       # Invoice routes
│   │   └── export.js         # Export routes
│   └── utils/
│       ├── generatePdf.js    # PDF generation
│       └── formatData.js     # Data formatting
└── invoices/                 # Generated PDF storage
```

### Database Schema (MongoDB)

```javascript
const invoiceSchema = {
  invoiceNumber: String,       // Auto-generated: INV-YYMM-00001
  client: {
    name: String,
    email: String,
    phone: String,
    address: String
  },
  items: [{
    description: String,
    quantity: Number,
    unitPrice: Number,
    total: Number
  }],
  subtotal: Number,
  tax: Number,
  discount: Number,
  grandTotal: Number,
  status: String,              // draft/sent/paid/overdue/cancelled
  dueDate: Date,

  // Payment verification fields
  bank: String,                // Required
  expectedAccount: String,     // Required
  recipientName: String,       // For OCR matching
  currency: String,            // Required, default 'USD'

  // Verification state
  verificationStatus: String,  // pending/verified/rejected
  verifiedAt: Date,
  verifiedBy: String,
  verificationNote: String
}
```

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/invoices` | Create invoice |
| GET | `/api/invoices` | List invoices (paginated) |
| GET | `/api/invoices/:id` | Get single invoice |
| PUT | `/api/invoices/:id` | Update invoice |
| DELETE | `/api/invoices/:id` | Delete invoice |
| PATCH | `/api/invoices/:id/status` | Update status only |
| PATCH | `/api/invoices/:id/verify` | Update verification (called by OCR) |
| GET | `/api/invoices/:id/pdf` | Generate/download PDF |

---

## 4. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Telegram   │ │   Frontend   │ │  External    │
            │     Bot      │ │  Dashboard   │ │    API       │
            └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                   │                │                │
                   └────────────────┼────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FACEBOOK-AUTOMATION (Main Backend)                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  aiogram Bot    │  │   FastAPI       │  │  Invoice        │         │
│  │  Handlers       │──│   Routes        │──│  Service        │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                    │                   │
│           │         ┌──────────┴──────────┐        │                   │
│           │         ▼                     ▼        ▼                   │
│           │  ┌──────────────┐     ┌──────────────────┐                 │
│           └──│  OCR Service │     │    PostgreSQL    │                 │
│              │    Client    │     │  invoice.invoice │                 │
│              └──────┬───────┘     └──────────────────┘                 │
└─────────────────────┼───────────────────────────────────────────────────┘
                      │
                      ▼ HTTP POST /api/v1/verify
┌─────────────────────────────────────────────────────────────────────────┐
│                         OCR-SERVICE                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  verify.js      │  │  verification.js│  │  ocr-engine.js  │         │
│  │  Route Handler  │──│  Pipeline       │──│  OpenAI Vision  │         │
│  └────────┬────────┘  └────────┬────────┘  └─────────────────┘         │
│           │                    │                                        │
│           ▼                    ▼                                        │
│  ┌─────────────────┐  ┌─────────────────┐                              │
│  │    MongoDB      │  │    GridFS       │                              │
│  │   payments      │  │  screenshots    │                              │
│  │   fraudAlerts   │  │                 │                              │
│  └─────────────────┘  └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────┘
                      │
                      ▼ (Optional - Standalone)
┌─────────────────────────────────────────────────────────────────────────┐
│                       GENERAL-INVOICE                                    │
│  ┌─────────────────┐  ┌─────────────────┐                              │
│  │  Invoice API    │  │    MongoDB      │                              │
│  │  CRUD + PDF     │──│   invoices      │                              │
│  └─────────────────┘  └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. OCR Verification Flow

```
1. User sends screenshot via Telegram
   └── /ocr INV-001

2. Main Backend (ocr.py)
   ├── Fetch invoice from PostgreSQL
   ├── Build expectedPayment:
   │   ├── amount: invoice.amount
   │   ├── toAccount: invoice.expected_account
   │   └── recipientName: invoice.recipient_name
   └── Call OCR service

3. OCR Service (verify.js)
   ├── Normalize recipientName → recipientNames[]
   ├── Run verification pipeline
   └── Return transformed response

4. Main Backend
   ├── Display result to user
   └── Update invoice verification status

5. Response to User:
   ┌────────────────────────────────────────┐
   │ [OK] Payment Verified                  │
   │                                        │
   │ Invoice: INV-001                       │
   │ Expected: KHR 36,000                   │
   │ Detected: KHR 36,000                   │
   │                                        │
   │ Confidence: [########--] 90%           │
   │                                        │
   │ Invoice marked as PAID                 │
   └────────────────────────────────────────┘
```

---

## 6. Field Mapping Reference

### Invoice Fields (PostgreSQL → OCR Service)

| PostgreSQL Field | OCR Service Field | Description |
|------------------|-------------------|-------------|
| `amount` | `expectedPayment.amount` | Expected payment amount |
| `currency` | `expectedPayment.currency` | Currency code (KHR/USD) |
| `expected_account` | `expectedPayment.toAccount` | Bank account number |
| `recipient_name` | `expectedPayment.recipientName` | Account holder name |
| `bank` | `expectedPayment.bank` | Bank name |
| `due_date` | `expectedPayment.dueDate` | Payment due date |

### OCR Response Fields (OCR Service → Main Backend)

| OCR Service Field | Main Backend Usage | Description |
|-------------------|-------------------|-------------|
| `record_id` | Display/logging | Verification record ID |
| `confidence` | Progress bar | 0-1 float value |
| `extracted_data.amount` | Display | Formatted amount string |
| `extracted_data.recipient_name` | Display | Detected name |
| `verification.status` | Update invoice | verified/rejected/pending |
| `verification.warnings` | Display | Skipped check warnings |

---

## 7. Common Issues & Solutions

### Issue: Recipient verification always SKIPPED

**Cause:** Invoice missing `expected_account` and `recipient_name`

**Solution:** Fill in fields when creating invoice:
```sql
UPDATE invoice.invoice
SET expected_account = '086 228 226',
    recipient_name = 'CHAN K.'
WHERE id = 'invoice-uuid';
```

### Issue: Telegram bot shows N/A for all values

**Cause:** Response format mismatch between services

**Solution:** OCR service transforms response (already implemented):
- `payment` → `extracted_data`
- `recordId` → `record_id`
- `verification.confidence` (string) → `confidence` (float)

### Issue: MongoDB duplicate key error on transactionId

**Cause:** Sparse index doesn't skip null values

**Solution:** Only include field when truthy:
```javascript
...(result.payment.transactionId && { transactionId: result.payment.transactionId })
```

---

## 8. Deployment URLs

| Service | Production URL |
|---------|----------------|
| Facebook-automation | social-media-automation-production.up.railway.app |
| OCR Service | general-verification-production.up.railway.app |
| General Invoice | general-invoice-production.up.railway.app |

---

*Last Updated: January 10, 2026*
