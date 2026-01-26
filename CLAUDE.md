# Facebook-TikTok Automation Project

## Architecture
```
VERCEL (React) → RAILWAY (FastAPI + Bot) → SUPABASE (PostgreSQL)
- Frontend: https://facebooktiktokautomation.vercel.app
- Backend: facebook-automation + api-gateway services
- Database: 6 schemas (public, invoice, inventory, scriptclient, audit_sales, ads_alert)
- Bot: @KS_automations_bot
```

## Environment Variables

**Railway: facebook-automation (Main)**
`DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `FB_APP_ID`, `FB_APP_SECRET`, `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `BASE_URL`, `FRONTEND_URL`, `MASTER_SECRET_KEY`

**Railway: api-gateway (Bot)**
`DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `CORE_API_URL`

**Vercel: Frontend**
`VITE_API_URL`

## Key Files
```
app/main.py                    - FastAPI entry
app/core/config.py            - Settings
app/routes/auth.py            - Authentication
app/routes/oauth.py           - Facebook/TikTok OAuth
api-gateway/src/main.py       - Bot + proxy
frontend/src/App.tsx          - React entry
```

## Critical Issues & Fixes

### Database Configuration (PRODUCTION-READY)
**Use NullPool + Transaction mode (port 6543):**
```python
# app/core/db.py & api-gateway/src/db/postgres.py
engine = create_engine(
    _get_psycopg3_url(DATABASE_URL),
    poolclass=NullPool,  # Let pgbouncer handle pooling
    isolation_level="AUTOCOMMIT",
    connect_args={
        "prepare_threshold": 0,  # Disable prepared statements
        "application_name": f"app_{os.getpid()}",
        "autocommit": True,
    }
)
```

**Why This Works:**
- Scales to 200+ users (vs 25 with Session mode)
- Eliminates "DuplicatePreparedStatement" errors
- No connection pool conflicts between SQLAlchemy and pgbouncer

### Common Fixes
- **"$NaN" totals**: Validate `formatCurrency()` inputs for null/undefined
- **Bot not responding**: Set `TELEGRAM_BOT_TOKEN` in Railway
- **Wrong bot link**: Set `TELEGRAM_BOT_USERNAME=KS_automations_bot`
- **Connection leaks**: Use `with get_db_session() as db:` not `next(get_db())`

### formatCurrency Pattern
```typescript
const formatCurrency = (amount: number | null | undefined): string => {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '$0.00'
  }
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}
```

## Features Status ✅

### Invoice System (LIVE)
- Create, send, verify payments via OCR
- PDF generation with verify button in Telegram
- Line items with currency support (USD/KHR)
- Real XLSX export capabilities

### Inventory System (LIVE)
- Product catalog with SKU, price, stock tracking
- Auto-deduct stock on payment verification
- Low stock alerts via Telegram bot
- Product picker in invoice creation

### Authentication (PRODUCTION-READY)
- JWT with role-based access (admin/user/viewer)
- OAuth Facebook/TikTok integration
- Telegram linking with smart unlinking
- Password reset with 1-hour tokens
- ⏸️ Email verification DISABLED (SMTP blocked on Railway)

### Subscription Tiers (IMPLEMENTED)
| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | Basic invoice + payment verification |
| Invoice Plus | $10/mo | + Inventory + customer management |
| Marketing Plus | $10/mo | + Social automation + ads alerts |
| Pro | $20/mo | All features combined |

**1-Month Pro Trial:** New users get 30-day Pro trial, auto-downgrade to Free

### Multi-Tenant Security ✅
- Complete tenant isolation (668 tenant_id references)
- Role-based authorization decorators
- Repository pattern prevents data leakage
- Owner-only operations (OAuth, user management, billing)

## Telegram Bot Commands
```
/start <code>  - Link account
/status        - System status
/invoice       - Invoice operations
/inventory     - Stock levels
/lowstock      - Products below threshold
/verify        - Payment verification
/help          - All commands
```

## Critical Workflows

### Invoice → Payment → Stock Deduction
```
1. Create invoice → Send PDF to Telegram with verify button
2. Customer pays → Sends screenshot
3. OCR verifies payment (80%+ confidence = auto-approve)
4. Stock automatically deducted with audit trail
5. Merchant notified via Telegram
```

### OCR Payment Verification (PROVEN)
```python
expected_payment = {
    "amount": float(invoice.amount),
    "currency": "KHR",
    "recipientNames": [invoice.recipient_name],  # Array format
    "toAccount": invoice.expected_account,       # camelCase
    "bank": invoice.bank
}
# Uses Mode A (no invoice_id) to avoid MongoDB lookup
```

### Subscription Payment (Local Bank)
- Generate QR code with bank details
- Customer transfers money → uploads screenshot
- Same OCR pipeline verifies payment
- 80%+ confidence = instant Pro upgrade

## Development Patterns

### Database Sessions
```python
# ✅ CORRECT - Background tasks
with get_db_session() as db:
    # operations

# ✅ CORRECT - FastAPI endpoints
def endpoint(db: Session = Depends(get_db)):

# ❌ WRONG - Leaks connections
db = next(get_db())
```

### Authorization
```python
# Owner-only endpoints
@require_owner
def manage_users(user: User = Depends(get_current_owner)):

# Feature gates
@require_subscription_feature('bulk_operations')
def export_invoices():
```

### Error Handling Standards
- 403: Role insufficient
- 402: Pro feature required
- 404: Tenant isolation (not found for this tenant)

## Database Schema Highlights

**Core Tables:**
- `public.user` - Multi-tenant users with roles
- `public.tenant` - Organization isolation
- `public.subscription` - Billing tiers with trial support
- `invoice.invoice` - Business invoices
- `inventory.products` - Product catalog
- `inventory.stock_movements` - Audit trail

## Backup System (R2 + Local)
```bash
# Daily backup with cloud upload
python backups/scripts/run_backup.py --type daily

# Restore from backup
python backups/scripts/restore_database.py backup.dump
```

## Competitive Advantage
1. **OCR Payment Verification** - Unique in Cambodia
2. **Telegram Bot Integration** - Unique workflow
3. **Inventory + Invoice + Social** - No competitor combines all

## Security Assessment: 8.5/10 (Production Ready)
✅ Multi-tenant isolation complete
✅ Role-based access enforced
✅ JWT security with refresh tokens
✅ OCR verification pipeline proven
⚠️ Missing: Account lockout (brute force risk)
⚠️ Missing: Password strength validation

## Production Checklist ✅
- [x] Database: NullPool + Transaction mode
- [x] Authentication: JWT + roles + OAuth
- [x] Multi-tenant: Complete isolation
- [x] Payments: OCR verification pipeline
- [x] Subscriptions: 4-tier model with trial
- [x] Backups: R2 cloud + local retention
- [x] Security: 8.5/10 rating
- [x] Scaling: 200+ concurrent users supported

## File Structure
```
app/                    - Main FastAPI backend
├── core/              - Config, models, auth
├── routes/            - API endpoints
├── services/          - Business logic
└── repositories/      - Database layer

api-gateway/           - Telegram bot service
├── src/bot/          - Bot handlers
├── src/services/     - Database services
└── src/api/          - Internal API proxy

frontend/             - React dashboard
├── src/components/   - UI components
├── src/services/     - API clients
└── src/hooks/        - Custom hooks
```