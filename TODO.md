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

**Last Updated**: 2025-11-17
**Status**: 🔴 Critical - Application not starting
**Priority**: Phase 1, Step 1 (Make integrations optional)
