# Railway Deployment TODO - Issue Resolution

## 🔴 Critical Issues (Application Crashing)

The application is failing to start on Railway due to **7 missing required environment variables**. These are all defined in `app/core/config.py` with `Field(...)` which means they are **required** and have no defaults.

---

## 📋 Task Breakdown

### ✅ Phase 1: Fix Configuration Schema (PRIORITY)

**Issue**: Required environment variables are blocking application startup on Railway.

**Root Cause**: The `Settings` class in [app/core/config.py](app/core/config.py) has 7 fields marked as required (`Field(...)`) without default values:

1. ❌ `OAUTH_STATE_SECRET` (line 39)
2. ❌ `MASTER_SECRET_KEY` (line 40)
3. ❌ `FB_APP_ID` (line 43)
4. ❌ `FB_APP_SECRET` (line 44)
5. ❌ `TIKTOK_CLIENT_KEY` (line 48)
6. ❌ `TIKTOK_CLIENT_SECRET` (line 49)
7. ❌ `TELEGRAM_BOT_TOKEN` (line 53)

**Solution Options**:

#### Option A: Add Default Values (RECOMMENDED for MVP/Testing)
Make the application startable without external integrations by providing safe defaults.

**Files to modify**:
- [app/core/config.py](app/core/config.py) - Add default values to all required fields

**Benefits**:
- ✅ Application can start immediately
- ✅ Core functionality works without external APIs
- ✅ Can add real credentials later
- ✅ Good for CI/CD and testing

**Risks**:
- ⚠️ OAuth flows won't work until real credentials are added
- ⚠️ Must validate credentials before using external APIs

#### Option B: Set Environment Variables in Railway
Add all 7 required environment variables in Railway dashboard.

**Steps**:
1. Go to Railway project dashboard
2. Navigate to Variables tab
3. Add each required variable
4. Redeploy

**Benefits**:
- ✅ No code changes needed
- ✅ Proper security practices

**Risks**:
- ⚠️ Need to obtain all credentials first
- ⚠️ More complex initial setup
- ⚠️ Blocks deployment until all credentials ready

---

### ✅ Phase 2: Implement Configuration Safety

**Tasks**:

#### Task 2.1: Add Runtime Validation
- [ ] Create function to check which integrations are available
- [ ] Disable OAuth routes if credentials missing
- [ ] Add `/health` endpoint status for each integration
- [ ] Return clear error messages when features unavailable

**Files to create/modify**:
- `app/core/feature_flags.py` - Feature availability checker
- [app/main.py](app/main.py) - Conditional route registration
- `app/routes/health.py` - Enhanced health check

#### Task 2.2: Add Startup Validation
- [ ] Add startup checks in `app/main.py` lifespan
- [ ] Log which features are enabled/disabled
- [ ] Warn about missing optional credentials
- [ ] Fail fast if critical credentials missing (DATABASE_URL)

**Files to modify**:
- [app/main.py](app/main.py) - Add validation in lifespan startup

---

### ✅ Phase 3: Environment Variable Management

**Tasks**:

#### Task 3.1: Create .env.example
- [ ] Document all environment variables
- [ ] Mark which are required vs optional
- [ ] Provide example/dummy values
- [ ] Add comments explaining each variable

**Files to create**:
- `.env.example` - Template for environment setup

#### Task 3.2: Create Railway-specific Environment Setup
- [ ] Document Railway environment variable setup
- [ ] Create script to generate secure random keys
- [ ] Add instructions for obtaining OAuth credentials

**Files to create/update**:
- [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) - Add environment setup section
- `scripts/generate_secrets.py` - Generate secure random keys

---

### ✅ Phase 4: Database Migration Safety

**Current Issue**: Database migrations may fail on first deploy

**Tasks**:

#### Task 4.1: Add Migration Health Check
- [ ] Check if database is accessible before running migrations
- [ ] Add retry logic for database connection
- [ ] Log migration status clearly

**Files to modify**:
- [app/main.py](app/main.py) - Add database connection check in lifespan

#### Task 4.2: Handle Migration Failures Gracefully
- [ ] Catch migration errors and log clearly
- [ ] Allow application to start even if migrations fail (with warning)
- [ ] Add `/health` endpoint to report migration status

---

### ✅ Phase 5: Deployment Configuration

**Tasks**:

#### Task 5.1: Update nixpacks.toml
- [ ] Ensure correct Python version (3.12.3)
- [ ] Add migration command to build or start
- [ ] Configure proper health check endpoint

**Files to modify**:
- `nixpacks.toml` - Build and start configuration

#### Task 5.2: Add Procfile (Alternative)
- [ ] Create Procfile for explicit process definition
- [ ] Add migration step
- [ ] Configure uvicorn properly

**Files to create**:
- `Procfile` - Railway process definition

---

## 🎯 Recommended Immediate Action Plan

### Step 1: Quick Fix (Get App Running)
**Modify [app/core/config.py](app/core/config.py)** to make external integrations optional:

```python
# Change from:
FB_APP_ID: str = Field(..., description="Facebook App ID")

# To:
FB_APP_ID: str | None = Field(default=None, description="Facebook App ID")
```

Do this for all 7 required fields EXCEPT `DATABASE_URL`.

**Time**: 10 minutes
**Impact**: Application will start successfully on Railway

### Step 2: Add Feature Flags
Create `app/core/feature_flags.py`:

```python
from app.core.config import get_settings

def is_facebook_enabled() -> bool:
    settings = get_settings()
    return bool(settings.FB_APP_ID and settings.FB_APP_SECRET)

def is_tiktok_enabled() -> bool:
    settings = get_settings()
    return bool(settings.TIKTOK_CLIENT_KEY and settings.TIKTOK_CLIENT_SECRET)

def is_telegram_enabled() -> bool:
    settings = get_settings()
    return bool(settings.TELEGRAM_BOT_TOKEN)
```

**Time**: 15 minutes
**Impact**: Can conditionally enable features

### Step 3: Update Routes to Check Features
Modify [app/main.py](app/main.py) to only register routes if features enabled:

```python
from app.core.feature_flags import is_facebook_enabled, is_tiktok_enabled

# Only add OAuth routes if credentials available
if is_facebook_enabled() or is_tiktok_enabled():
    app.include_router(oauth_router)
```

**Time**: 20 minutes
**Impact**: App won't crash when OAuth routes are called without credentials

### Step 4: Create .env.example
Document all environment variables with examples.

**Time**: 15 minutes
**Impact**: Clear documentation for setup

### Step 5: Update Railway Variables
Add at minimum:
- `DATABASE_URL` (already set from Postgres plugin)
- `OAUTH_STATE_SECRET` (generate random string)
- `MASTER_SECRET_KEY` (generate random string)

**Time**: 5 minutes
**Impact**: Core security features work

---

## 📊 Progress Tracking

- [ ] **Phase 1**: Fix Configuration Schema
  - [ ] Make external integrations optional
  - [ ] Keep DATABASE_URL required
  - [ ] Test locally without .env file

- [ ] **Phase 2**: Implement Configuration Safety
  - [ ] Create feature_flags.py
  - [ ] Add startup validation
  - [ ] Update health endpoint

- [ ] **Phase 3**: Environment Variable Management
  - [ ] Create .env.example
  - [ ] Update RAILWAY_DEPLOYMENT.md
  - [ ] Create secret generation script

- [ ] **Phase 4**: Database Migration Safety
  - [ ] Add connection retry logic
  - [ ] Graceful migration failure handling
  - [ ] Migration status in health check

- [ ] **Phase 5**: Deployment Configuration
  - [ ] Update nixpacks.toml
  - [ ] Test deployment
  - [ ] Verify all features work

---

## 🔍 Error Log Analysis

### Error 1: OAUTH_STATE_SECRET missing
```
Field required [type=missing, input_value={'DATABASE_URL': 'postgre...
```
**Impact**: OAuth flows cannot validate state parameters (CSRF protection broken)
**Fix**: Add default or set in Railway

### Error 2: MASTER_SECRET_KEY missing
**Impact**: Token encryption/decryption will fail
**Fix**: CRITICAL - Must be set in Railway for production

### Error 3-4: FB_APP_ID, FB_APP_SECRET missing
**Impact**: Facebook OAuth won't work
**Fix**: Optional - Can make nullable

### Error 5-6: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET missing
**Impact**: TikTok OAuth won't work
**Fix**: Optional - Can make nullable

### Error 7: TELEGRAM_BOT_TOKEN missing
**Impact**: Telegram bot won't start
**Fix**: Optional - Can make nullable

---

## 🎓 Lessons Learned

1. **Never make external API credentials required** - They should be optional to allow app to start
2. **Use feature flags** - Conditionally enable functionality based on configuration
3. **Fail gracefully** - App should start even if some features unavailable
4. **Document everything** - .env.example is critical
5. **Test without .env** - Ensures Railway deployment will work

---

## 📝 Next Steps After Deployment

Once the app is running on Railway:

1. Add real OAuth credentials when ready to test integrations
2. Set up proper monitoring and logging
3. Configure production CORS settings
4. Set up SSL/TLS
5. Add rate limiting configuration
6. Configure backup strategy for database

---

**Last Updated**: 2025-11-20
**Status**: ✅ Backend Complete - Now Working on Frontend
**Priority**: Frontend UI Implementation

---

## 🎨 Phase 6: Frontend UI Development (CURRENT FOCUS)

### Current State Analysis
- ✅ OAuth connection page exists (OAuthLoginPage.tsx)
- ✅ Dashboard exists (Dashboard.tsx) - shows connected platforms
- ✅ Basic LoginPage exists but needs backend integration
- ❌ No Register/Sign-up page
- ❌ No proper Home page
- ❌ LoginPage not connected to backend API

### Task 6.1: Update Login Page with Backend Integration
**Goal**: Connect existing LoginPage.tsx to FastAPI authentication endpoints

**Files to modify**:
- `frontend/src/components/LoginPage.tsx` - Add API integration
- `frontend/src/hooks/useAuth.ts` - Create/update authentication hook
- `frontend/src/services/api.ts` - Add login API calls

**Required API Integration**:
```typescript
// POST /auth/login
{
  username: string,
  password: string
}
// Response: { access_token: string, token_type: string }
```

**Tasks**:
- [ ] Create API service for login (`api.login()`)
- [ ] Update LoginPage to call backend API
- [ ] Store JWT token in localStorage/sessionStorage
- [ ] Redirect to Dashboard on successful login
- [ ] Handle error messages from backend
- [ ] Add email validation
- [ ] Test with real backend at localhost:8000

---

### Task 6.2: Create Register/Sign-up Page
**Goal**: Build registration page based on Figma template design

**Files to create**:
- `frontend/src/components/RegisterPage.tsx` - New registration component

**Design Requirements** (from Figma):
- Use Montserrat font family
- Purple/blue gradient background: `linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)`
- White card with rounded corners (20px)
- Form fields:
  - Email (with email validation)
  - Username
  - Password (with strength indicator)
  - Confirm Password
  - Terms & Conditions checkbox
- Social registration options (Facebook, Google, Twitter)
- "Already have an account? Login" link

**API Endpoint**:
```typescript
// POST /auth/register
{
  email: string,
  username: string,
  password: string,
  tenant_id?: string
}
```

**Tasks**:
- [ ] Extract design from Figma Register page (ID: 0:66 for dark theme)
- [ ] Create RegisterPage.tsx component
- [ ] Implement form validation
- [ ] Add password strength indicator
- [ ] Connect to `/auth/register` endpoint
- [ ] Add success/error handling
- [ ] Link to LoginPage
- [ ] Test registration flow

---

### Task 6.3: Create Home/Landing Page
**Goal**: Build attractive home page for visitors before login

**Files to create**:
- `frontend/src/components/HomePage.tsx` - Landing page component

**Design Elements**:
- Hero section with project description
- Features showcase (Facebook & TikTok automation)
- Call-to-action buttons (Login, Sign Up)
- Clean modern design matching overall theme

**Tasks**:
- [ ] Design hero section
- [ ] Add feature cards
- [ ] Create navigation header
- [ ] Add footer with links
- [ ] Make responsive for mobile
- [ ] Add smooth scroll animations
- [ ] Link to Login and Register pages

---

### Task 6.4: Update Routing Structure
**Goal**: Organize page navigation properly

**Files to modify**:
- `frontend/src/App.tsx` - Update routes

**New Route Structure**:
```typescript
/ → HomePage (public)
/login → LoginPage (public)
/register → RegisterPage (public)
/dashboard → Dashboard (protected, requires auth)
/oauth/callback → OAuthCallback (public)
```

**Tasks**:
- [ ] Add HomePage as default route
- [ ] Add RegisterPage route
- [ ] Implement route protection for Dashboard
- [ ] Add redirect if not authenticated
- [ ] Update navigation between pages

---

### Task 6.5: Figma Template Integration
**Goal**: Use Figma MCP to extract and implement professional designs

**Available Figma Designs** (from RYqxoTNCQwnLOhkkECKBRr):
- **Dark Theme**:
  - Login (ID: 0:2)
  - Register (ID: 0:66)
  - Contact (ID: 0:130)
  - Error (ID: 2104:1223)
  - Maintenance (ID: 2104:1237)
  - Coming Soon (ID: 2104:1252)

- **Light Theme** (also available)
- **Components**:
  - Header and Footer
  - Color Palette
  - Button components

**Tasks**:
- [ ] Extract Login page design from Figma
- [ ] Extract Register page design
- [ ] Get color palette and fonts (Montserrat)
- [ ] Generate React components from designs
- [ ] Apply Tailwind CSS / styled-components
- [ ] Test responsive layouts
- [ ] Match exact colors and spacing

---

### Task 6.6: UI/UX Improvements
**Goal**: Polish existing pages and add missing features

**Tasks**:
- [ ] Add loading states to all forms
- [ ] Improve error message display
- [ ] Add success notifications (toast/snackbar)
- [ ] Make all pages responsive
- [ ] Add dark mode toggle (optional)
- [ ] Add animations and transitions
- [ ] Improve accessibility (ARIA labels, keyboard nav)
- [ ] Add password visibility toggle
- [ ] Add "Remember me" checkbox to login

---

### Task 6.7: Testing & Validation
**Goal**: Ensure all frontend features work correctly

**Tasks**:
- [ ] Test login flow end-to-end
- [ ] Test registration flow
- [ ] Test OAuth connections (Facebook, TikTok)
- [ ] Verify token storage and retrieval
- [ ] Test protected routes
- [ ] Test error handling
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile responsiveness testing
- [ ] Validate forms with edge cases

---

## 📊 Frontend Progress Tracking

- [ ] **Task 6.1**: Login Page Backend Integration
  - [ ] Create API service
  - [ ] Update LoginPage component
  - [ ] Add JWT token handling
  - [ ] Test login flow

- [ ] **Task 6.2**: Register/Sign-up Page
  - [ ] Extract Figma design
  - [ ] Create RegisterPage component
  - [ ] Add form validation
  - [ ] Connect to backend API

- [ ] **Task 6.3**: Home/Landing Page
  - [ ] Design hero section
  - [ ] Add features showcase
  - [ ] Make responsive

- [ ] **Task 6.4**: Update Routing
  - [ ] Add new routes
  - [ ] Implement route protection
  - [ ] Test navigation

- [ ] **Task 6.5**: Figma Integration
  - [ ] Extract designs
  - [ ] Generate components
  - [ ] Apply styling

- [ ] **Task 6.6**: UI/UX Polish
  - [ ] Add loading states
  - [ ] Improve error handling
  - [ ] Make responsive

- [ ] **Task 6.7**: Testing
  - [ ] End-to-end testing
  - [ ] Cross-browser testing
  - [ ] Mobile testing

---

**Last Updated**: 2025-11-20
**Current Focus**: 🎨 Frontend UI Development
**Priority**: Task 6.5 (Extract Figma designs for Login & Register pages)
