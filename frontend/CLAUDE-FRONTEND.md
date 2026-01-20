# Frontend Documentation (CLAUDE-FRONTEND.md)

## Architecture Overview

```
frontend/
├── src/
│   ├── App.tsx                    # Router configuration
│   ├── i18n/                      # Internationalization (NEW)
│   │   ├── index.ts               # i18n configuration
│   │   └── locales/
│   │       ├── en.json            # English translations
│   │       └── km.json            # Khmer translations
│   ├── components/
│   │   ├── layouts/               # DashboardLayout, Header, Sidebar
│   │   │   └── LanguageSwitcher   # EN/ខ្មែរ toggle
│   │   ├── LoginPageNew.tsx       # Login page
│   │   ├── RegisterPage.tsx       # Registration page
│   │   ├── EmailVerificationPage.tsx    # Email verification handler
│   │   ├── VerificationPendingPage.tsx  # "Check your email" page
│   │   ├── ForgotPasswordPage.tsx       # Password reset request
│   │   ├── ResetPasswordPage.tsx        # Password reset form
│   │   ├── dashboard/             # All dashboard pages
│   │   │   ├── OverviewPage.tsx   # Main dashboard
│   │   │   ├── SocialMediaPage.tsx # Platform connections
│   │   │   ├── ClientsPage.tsx    # Customer management with QR
│   │   │   ├── inventory/         # Inventory management
│   │   │   ├── invoices/          # Invoice CRUD
│   │   │   ├── integrations/      # OAuth pages
│   │   │   └── billing/           # Subscription
│   │   └── invoice/               # Reusable invoice components
│   ├── services/                  # API service layer
│   ├── types/                     # TypeScript interfaces
│   └── hooks/                     # Custom React hooks
├── package.json
└── vite.config.ts
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18+ with TypeScript |
| Routing | React Router v6 |
| Styling | **Styled Components** (CSS-in-JS) |
| HTTP Client | Axios with interceptors |
| i18n | react-i18next (English/Khmer) |
| Build Tool | Vite |
| Deployment | Vercel (static files only) |

**IMPORTANT:** This codebase uses **Styled Components**, NOT Tailwind CSS.

---

## Language System (i18n)

### Overview
The app supports English and Khmer (ភាសាខ្មែរ) with a toggle in the dashboard header.

**Why Khmer Support:**
- Target market is Cambodia
- Better UX for local merchants
- Competitive advantage over English-only apps

### Language Switcher Location
```
┌─────────────────────────────────────────────────────────┐
│  KS Automation          [Search]    [🔔]  [EN|ខ្មែរ] [U] │  ← Header
└─────────────────────────────────────────────────────────┘
```

### Usage in Components

```tsx
import { useTranslation } from 'react-i18next';

const MyComponent = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('clients.title')}</h1>          {/* "Clients" or "អតិថិជន" */}
      <button>{t('common.save')}</button>     {/* "Save" or "រក្សាទុក" */}
    </div>
  );
};
```

### Translation File Structure

**en.json:**
```json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "loading": "Loading..."
  },
  "clients": {
    "title": "Clients",
    "generateQR": "Generate QR",
    "totalClients": "Total Clients",
    "telegramLinked": "Telegram Linked",
    "scanInstructions": "Scan this QR code to link your account"
  },
  "invoices": {
    "title": "Invoices",
    "createNew": "Create Invoice"
  }
}
```

**km.json:**
```json
{
  "common": {
    "save": "រក្សាទុក",
    "cancel": "បោះបង់",
    "delete": "លុប",
    "loading": "កំពុងផ្ទុក..."
  },
  "clients": {
    "title": "អតិថិជន",
    "generateQR": "បង្កើត QR",
    "totalClients": "អតិថិជនសរុប",
    "telegramLinked": "បានភ្ជាប់ Telegram",
    "scanInstructions": "ស្កេន QR code នេះដើម្បីភ្ជាប់គណនី"
  },
  "invoices": {
    "title": "វិក្កយបត្រ",
    "createNew": "បង្កើតវិក្កយបត្រ"
  }
}
```

### Persistence
- Language preference saved in `localStorage.language`
- Defaults to browser language or 'en'
- Persists across sessions

---

## Authentication System

### Overview
Complete authentication flow with email verification and password reset functionality.

### Auth Pages

| Route | Component | Purpose |
|-------|-----------|---------|
| `/login` | LoginPageNew | User login with email/password |
| `/register` | RegisterPage | New user registration |
| `/verify-email` | EmailVerificationPage | Handles email verification tokens |
| `/verification-pending` | VerificationPendingPage | "Check your email" confirmation |
| `/forgot-password` | ForgotPasswordPage | Request password reset |
| `/reset-password` | ResetPasswordPage | Set new password with token |

### Authentication Flow

**Registration Flow:**
```
1. User fills registration form (/register)
2. Backend creates user with email_verified=false
3. Backend sends verification email
4. User redirected to /verification-pending
5. User clicks link in email
6. Opens /verify-email?token=xxx
7. Backend verifies token, sets email_verified=true
8. User redirected to /login with success message
```

**Password Reset Flow:**
```
1. User clicks "Forgot Password" on login page
2. Opens /forgot-password
3. User enters email address
4. Backend sends reset email with token
5. User clicks link in email
6. Opens /reset-password?token=xxx
7. User enters new password
8. Backend validates token, updates password
9. User redirected to /login
```

### User Type (types/auth.ts)

```typescript
interface User {
  id: string
  username: string
  email?: string
  tenant_id: string
  role: string           // 'admin' | 'user' | 'viewer'
  is_active: boolean
  email_verified: boolean  // NEW: Required for login
}
```

### Security Features
- **Email Verification:** Users must verify email before accessing dashboard
- **Password Reset:** Secure token-based password recovery
- **Token Expiry:** Verification and reset tokens expire after set time
- **Rate Limiting:** Prevent abuse of email sending endpoints

---

## Page Purposes & Features

### 1. Clients Page (`/dashboard/clients`)

**Purpose:** Manage Telegram-linked customers for invoice delivery and payment verification.

**Target Users:** Merchants who need to:
- Track which customers are linked to Telegram bot
- Generate QR codes for easy customer linking
- View payment status and pending amounts
- Send invoices directly to customers

**Prerequisite Check:**
Merchants must connect their Telegram account first. If not connected, show warning banner:

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️ Connect Telegram First                                       │
│                                                                  │
│ You need to connect your Telegram account before you can:        │
│ • Send invoices to customers via Telegram                        │
│ • Receive payment verification notifications                     │
│ • Generate QR codes for customer linking                         │
│                                                                  │
│ [Connect Telegram →]                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- **Telegram Warning Banner:** Shows if merchant not connected (with link to setup)
- **Stats Cards:** Total Clients, Telegram Linked %, Total Receivable
- **QR Code Generation:** Modal with scannable QR for customer linking
- **Client Table:** Search, filter (All/Linked/Not Linked)
- **Actions:** Generate QR, Send Link, New Invoice, View Details

**QR Code Flow (Better UX than text links):**
```
1. Merchant clicks "Generate QR" on client row
2. Modal displays QR code for t.me/KS_automations_bot?start={code}
3. Customer scans QR with phone camera
4. Opens Telegram → Auto-starts bot with linking code
5. Bot links customer to merchant's account
6. Customer can now receive invoices via Telegram
```

**Why QR > Text Link:**
- Works in-person (merchant shows phone to customer)
- No typing required (scan and done)
- Universal (all phones have camera)
- Professional appearance
- Cambodia market: QR payments are familiar (ABA, Wing)

---

### 2. Social Media Page (`/dashboard/social`) - IMPLEMENTED

**Purpose:** Central hub for managing Facebook and TikTok connections for marketing.

**Target Users:** Merchants who want to:
- Connect Facebook Pages for post scheduling
- Connect TikTok for video publishing
- Track social media analytics (coming soon)

**Current Implementation:**

**Features:**
- **Stats Overview:** Connected Platforms count, Linked Accounts, Scheduled Posts
- **Platform Cards:** Facebook and TikTok with connection status
- **Account List:** Shows all connected accounts with expiration dates
- **Quick Actions:** Connect, Add Account, Manage
- **Coming Soon Section:** Post Scheduling, Analytics, Ad Management, Unified Inbox

**UI Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Social Media                                                   │
│  Connect and manage your social media accounts for marketing    │
├─────────────────────────────────────────────────────────────────┤
│  [Connected: 1/2]  [Linked Accounts: 2]  [Scheduled Posts: 0]   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │ [FB Logo] Facebook       │  │ [TT Logo] TikTok         │    │
│  │ ● Connected              │  │ ○ Not Connected          │    │
│  │                          │  │                          │    │
│  │ • Page Name A            │  │                          │    │
│  │   Expires: Jan 2027      │  │                          │    │
│  │                          │  │                          │    │
│  │ [Manage] [+ Add Account] │  │   [Connect TikTok]       │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  Features                                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Schedule │ │Analytics │ │   Ads    │ │  Inbox   │           │
│  │  Posts   │ │Dashboard │ │Management│ │ Unified  │           │
│  │ COMING   │ │ COMING   │ │ COMING   │ │ COMING   │           │
│  │  SOON    │ │  SOON    │ │  SOON    │ │  SOON    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

**Translation Support:**
- Full EN/ខ្មែរ support for all labels
- Keys in `socialMedia.*` namespace

**Hooks Used:**
- `useAuth()` - Get Facebook/TikTok connection status
- `useOAuth()` - Initiate OAuth flows

**Coming Soon Platforms:**
- Instagram
- YouTube
- Twitter/X
- LinkedIn

---

### 3. Invoice System (`/dashboard/invoices/*`)

**Purpose:** Core invoice creation, management, and payment verification.

**Pages:**
- `/invoices` - List all invoices with filters
- `/invoices/new` - Create new invoice
- `/invoices/:id` - View/edit invoice details

**Key Features:**
- Line items editor with product picker (inventory integration)
- Currency support (USD/KHR)
- PDF generation
- Send to customer via Telegram
- OCR payment verification

---

### 4. Inventory System (`/dashboard/inventory`)

**Purpose:** Lightweight product tracking for invoice auto-population.

**Features:**
- Product catalog (name, SKU, price, stock)
- Low stock alerts
- Product picker in invoice creation
- Auto-deduct stock on payment verification

---

## Component Patterns

### Styled Components Convention

```tsx
// ✅ Correct: Use styled-components
import styled from 'styled-components';

const Container = styled.div`
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 1.25rem;
`;

const Title = styled.h2`
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
`;

// ❌ Wrong: Don't use Tailwind classes
<div className="bg-white rounded-xl border border-gray-200 p-5">
```

### Color Palette

```tsx
const colors = {
  // Primary
  primary: '#4a90e2',        // Bright blue
  primaryDark: '#2a5298',    // Darker blue
  primaryLight: '#e8f4fd',   // Very light blue

  // Status
  success: '#10b981',        // Green (emerald-500)
  warning: '#f59e0b',        // Amber
  error: '#ef4444',          // Red

  // Text
  textPrimary: '#1f2937',    // Dark gray
  textSecondary: '#6b7280',  // Medium gray
  textMuted: '#9ca3af',      // Light gray

  // Background
  bgPrimary: '#ffffff',
  bgSecondary: '#f9fafb',
  border: '#e5e7eb',
};
```

### Modal Pattern

```tsx
const ModalOverlay = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
`;
```

### API Service Pattern

```tsx
// services/clientApi.ts
export const clientService = {
  async listClients(params?: ClientListParams): Promise<ClientListResponse> {
    const response = await api.get('/api/integrations/invoice/clients', { params });
    return response.data;
  },

  async generateLinkQR(clientId: string): Promise<LinkCodeResponse> {
    const response = await api.post(`/api/integrations/invoice/clients/${clientId}/link-code`);
    return response.data;
  },
};
```

---

## Route Structure

### Public Routes (No Auth Required)
```
/                              # HomePage (landing page)
/login                         # LoginPageNew
/register                      # RegisterPage
/oauth                         # OAuthLoginPage (OAuth callback)
/verify-email                  # EmailVerificationPage (?token=xxx)
/verification-pending          # VerificationPendingPage
/forgot-password               # ForgotPasswordPage
/reset-password                # ResetPasswordPage (?token=xxx)
/privacy-policy                # PrivacyPolicy
/terms-of-service              # TermsOfService
/data-deletion                 # DataDeletion
```

### Protected Routes (Auth Required)
```
/dashboard/
├── /                          # OverviewPage (stats dashboard)
├── /social                    # SocialMediaPage (platform connections)
├── /clients                   # ClientsPage (customer management)
├── /invoices                  # InvoiceListPage
├── /invoices/new              # InvoiceCreatePage
├── /invoices/:id              # InvoiceDetailPage
├── /inventory                 # InventoryListPage
├── /integrations/             # IntegrationsOverviewPage
│   ├── /facebook              # FacebookIntegrationPage
│   ├── /tiktok                # TikTokIntegrationPage
│   └── /telegram              # TelegramIntegrationPage
├── /billing/                  # BillingOverviewPage
│   ├── /pricing               # PricingPage
│   └── /payments              # PaymentHistoryPage
├── /usage                     # UsagePage
├── /logs                      # LogsPage
└── /settings                  # SettingsPage
```

---

## Data Types

### Client Types

```typescript
// Existing in types/invoice.ts
interface RegisteredClient {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  telegram_chat_id?: string;
  telegram_username?: string;
  telegram_linked: boolean;
  telegram_linked_at?: string;
  pending_invoices: PendingInvoice[];
}

// For QR code generation
interface LinkCodeResponse {
  code: string;
  expires_at: string;
  bot_url: string;           // e.g., "t.me/KS_automations_bot"
  deep_link: string;         // e.g., "t.me/KS_automations_bot?start=ABC123"
}

// Client stats
interface ClientStats {
  total_clients: number;
  linked_clients: number;
  total_receivable: number;
  currency: 'KHR' | 'USD';
}
```

### Client Statuses

| Status | Badge Color | Actions Available |
|--------|-------------|-------------------|
| `active` (linked) | Green | New Invoice, View Details |
| `not_linked` | Amber | Generate QR, Send Link, New Invoice |
| `pending` | Blue | Resend QR, Cancel Link |

---

## QR Code Feature Specification

### Dependencies
```bash
npm install qrcode.react
```

### QRCodeModal Component

```tsx
// components/dashboard/clients/QRCodeModal.tsx
import { QRCodeSVG } from 'qrcode.react';

interface QRCodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  client: RegisteredClient;
  linkCode: LinkCodeResponse | null;
  onGenerate: () => Promise<void>;
  isGenerating: boolean;
}

const QRCodeModal: React.FC<QRCodeModalProps> = ({
  isOpen,
  onClose,
  client,
  linkCode,
  onGenerate,
  isGenerating,
}) => {
  if (!isOpen) return null;

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={(e) => e.stopPropagation()}>
        <Title>Link {client.name} via Telegram</Title>

        {linkCode ? (
          <>
            <QRContainer>
              <QRCodeSVG
                value={linkCode.deep_link}
                size={200}
                level="H"  // High error correction
              />
            </QRContainer>

            <Instructions>
              <p>ស្កេន QR code នេះដើម្បីភ្ជាប់គណនី</p>
              <p>Scan this QR code to link your account</p>
            </Instructions>

            <ExpiryText>
              Expires: {formatExpiry(linkCode.expires_at)}
            </ExpiryText>

            <ButtonGroup>
              <DownloadButton onClick={downloadQR}>
                Download QR
              </DownloadButton>
              <CopyButton onClick={() => copyToClipboard(linkCode.deep_link)}>
                Copy Link
              </CopyButton>
            </ButtonGroup>
          </>
        ) : (
          <GenerateButton onClick={onGenerate} disabled={isGenerating}>
            {isGenerating ? 'Generating...' : 'Generate QR Code'}
          </GenerateButton>
        )}
      </ModalContent>
    </ModalOverlay>
  );
};
```

### QR Download Function

```typescript
const downloadQR = () => {
  const svg = document.getElementById('qr-code-svg');
  if (!svg) return;

  const svgData = new XMLSerializer().serializeToString(svg);
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const img = new Image();

  img.onload = () => {
    canvas.width = 400;
    canvas.height = 400;
    ctx?.drawImage(img, 0, 0, 400, 400);

    const pngFile = canvas.toDataURL('image/png');
    const downloadLink = document.createElement('a');
    downloadLink.download = `qr-${client.name}.png`;
    downloadLink.href = pngFile;
    downloadLink.click();
  };

  img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
};
```

---

## API Endpoints Used

### Clients Page

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/integrations/invoice/clients` | List all registered clients |
| GET | `/api/integrations/invoice/clients/:id` | Get client details |
| POST | `/api/integrations/invoice/clients/:id/link-code` | Generate link code for QR |
| POST | `/api/integrations/invoice/customers` | Create new customer |

### Response Examples

**List Clients:**
```json
{
  "clients": [
    {
      "id": "uuid",
      "name": "Sokha Trading",
      "telegram_username": "@sokha",
      "telegram_linked": true,
      "telegram_linked_at": "2025-12-15T10:00:00Z",
      "pending_invoices": [
        { "id": "inv-1", "amount": 890000, "currency": "KHR" }
      ]
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 20
}
```

**Generate Link Code:**
```json
{
  "code": "ABC123XYZ",
  "expires_at": "2026-01-16T12:00:00Z",
  "bot_url": "t.me/KS_automations_bot",
  "deep_link": "t.me/KS_automations_bot?start=ABC123XYZ"
}
```

---

## Development Guidelines

### Adding New Pages

1. Create component in `components/dashboard/`
2. Add route in `App.tsx`
3. Update sidebar if needed in `DashboardSidebar.tsx`
4. Create API service if new endpoints needed
5. Add types to `types/` folder

### Styling Checklist

- [ ] Use styled-components, not inline styles or Tailwind
- [ ] Follow color palette defined above
- [ ] Ensure mobile responsiveness
- [ ] Match existing component patterns
- [ ] Use consistent spacing (rem units)

### Error Handling

```tsx
try {
  const data = await clientService.listClients();
  setClients(data.clients);
} catch (error) {
  setError(getErrorMessage(error) || 'Failed to load clients');
} finally {
  setLoading(false);
}
```

---

## Priority Order for Implementation

### Phase 1: Core (Complete)
1. ✅ Invoice System - DONE
2. ✅ Inventory System - DONE
3. ✅ Clients Page with QR - DONE
4. ✅ Social Media Page - DONE
5. ✅ Authentication System - DONE
   - ✅ Email verification flow
   - ✅ Password reset flow
   - ✅ User type with `email_verified` field

### Phase 2: Enhancement
6. Payment verification status dashboard
7. Bulk invoice operations
8. Client communication history

### Phase 3: Future Features
9. Post scheduling UI (Social Media)
10. Analytics dashboards
11. Ad campaign management
12. Unified inbox for messages

---

## Testing

### Manual Testing Checklist

**Clients Page:**
- [ ] Page loads without errors
- [ ] Stats cards show correct numbers
- [ ] Search filters work
- [ ] Filter buttons (All/Linked/Not Linked) work
- [ ] Generate QR button opens modal
- [ ] QR code displays correctly
- [ ] Download QR saves PNG file
- [ ] Copy link copies to clipboard
- [ ] Expiry timer counts down
- [ ] Mobile layout is usable

**QR Code Linking:**
- [ ] Scan QR with phone camera
- [ ] Opens Telegram app
- [ ] Bot starts with correct code
- [ ] Customer account links successfully
- [ ] Status updates in Clients page

---

## Common Issues

### "QR code not scannable"
- Ensure high error correction level (`level="H"`)
- QR should be at least 200x200px
- Avoid low contrast colors

### "Link expired before customer scanned"
- Default expiry is 24 hours
- Show clear expiry warning
- Allow regenerating link easily

### "Customer already linked to another merchant"
- Backend returns specific error
- Show helpful message with instructions
