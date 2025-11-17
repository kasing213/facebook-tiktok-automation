# FastAPI Configuration Architecture Analysis

**Generated**: 2025-11-14  
**Project**: Facebook/TikTok Automation Platform  
**Version**: 0.2.0

---

## Executive Summary

This FastAPI application uses **Pydantic Settings (v2)** with strict environment variable validation. The configuration is centralized in `app/core/config.py` using the `BaseSettings` class, supporting multi-environment deployment (dev/staging/prod) with PostgreSQL as the primary database.

### Key Highlights
- **Framework**: Pydantic v2.8.2 + pydantic-settings v2.4.0
- **Database**: PostgreSQL with Supabase support (Session Pooler recommended)
- **Security**: Fernet encryption (cryptography v42.0.8) + bcrypt hashing
- **Authentication**: JWT tokens + Username/Password + OAuth 2.0
- **No Supabase-specific integration**: Uses direct PostgreSQL connection only
- **Configuration Loading**: From `.env` file + environment variables

---

## Settings Class Structure

### File Location
**`app/core/config.py`** (104 lines)

### Settings Base Configuration
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),          # Loads from .env
        env_file_encoding="utf-8",
        case_sensitive=True,              # Case-sensitive env vars
        extra="allow"                     # Allows extra env vars
    )
```

### Configuration Loading
- **Project Root**: `d:\Facebook-automation`
- **ENV File Path**: `.env` (at project root)
- **Priority**: Environment variables > `.env` file > Defaults
- **Caching**: `@lru_cache()` on `get_settings()` function (loads once)

---

## Environment Variables Breakdown

### Required Variables (5 CRITICAL)
Must be provided - application will fail without these:

| Variable | Type | Format | Used For |
|----------|------|--------|----------|
| `DATABASE_URL` | `str` | `postgresql://...` | PostgreSQL connection |
| `OAUTH_STATE_SECRET` | `SecretStr` | URL-safe random string | CSRF protection for OAuth |
| `MASTER_SECRET_KEY` | `SecretStr` | Base64 or raw key | Fernet token encryption |
| `FB_APP_ID` | `str` | Facebook App ID | Facebook OAuth |
| `FB_APP_SECRET` | `SecretStr` | Facebook App Secret | Facebook OAuth |
| `TIKTOK_CLIENT_KEY` | `str` | TikTok Client Key | TikTok OAuth |
| `TIKTOK_CLIENT_SECRET` | `SecretStr` | TikTok Client Secret | TikTok OAuth |
| `TELEGRAM_BOT_TOKEN` | `SecretStr` | Telegram Bot Token | Telegram bot |

### Optional Variables (With Defaults)

| Variable | Type | Default Value | Description |
|----------|------|---------------|-------------|
| `ENV` | `Literal["dev", "staging", "prod"]` | `"dev"` | Environment mode |
| `BASE_URL` | `AnyHttpUrl` | `http://localhost:8000` | API base URL |
| `FRONTEND_URL` | `AnyHttpUrl` | `http://localhost:3000` | Frontend base URL |
| `REDIS_URL` | `str \| None` | `None` | Redis connection (optional) |
| `FB_SCOPES` | `str` | `"ads_read"` | Facebook OAuth scopes |
| `TIKTOK_SCOPES` | `str` | `"user.info.basic,video.upload,video.publish"` | TikTok OAuth scopes |
| `FACEBOOK_WEBHOOK_VERIFY_TOKEN` | `SecretStr` | `"my_facebook_verify_token_change_me"` | Webhook verification |
| `TIKTOK_WEBHOOK_VERIFY_TOKEN` | `SecretStr` | `"my_tiktok_verify_token_change_me"` | Webhook verification |
| `API_HOST` | `str` | `"0.0.0.0"` | Server bind address |
| `API_PORT` | `int` | `8000` | Server port (1024-65535) |
| `TOKEN_REFRESH_INTERVAL` | `int` | `3600` | Token refresh check (seconds, min 60) |
| `AUTOMATION_CHECK_INTERVAL` | `int` | `60` | Automation scheduler check (seconds, min 10) |
| `CLEANUP_INTERVAL` | `int` | `86400` | Token cleanup interval (seconds, min 3600) |

---

## Pydantic Validators

### 1. DATABASE_URL Validator
**Lines 68-74**
```python
@field_validator('DATABASE_URL')
@classmethod
def validate_database_url(cls, v: str) -> str:
    """Validate DATABASE_URL format"""
    if not v.startswith(('postgresql://', 'postgresql+psycopg2://')):
        raise ValueError('DATABASE_URL must be a valid PostgreSQL connection string')
    return v
```

**Validation Rules**:
- Must start with `postgresql://` OR `postgresql+psycopg2://`
- Example formats accepted:
  - `postgresql://user:pass@localhost:5432/dbname`
  - `postgresql+psycopg2://user:pass@localhost:5432/dbname`
  - `postgresql://postgres:pass@db.supabase.co:5432/postgres` (Supabase direct)
  - `postgresql://postgres:pass@db.supabase.co:6543/postgres?pgbouncer=true` (Supabase pooler)

### 2. OAuth Scopes Validator
**Lines 76-83**
```python
@field_validator('FB_SCOPES', 'TIKTOK_SCOPES')
@classmethod
def validate_scopes(cls, v: str) -> str:
    """Validate and normalize OAuth scopes"""
    if not v:
        raise ValueError('OAuth scopes cannot be empty')
    # Normalize scopes by removing extra whitespace
    return ','.join(scope.strip() for scope in v.split(',') if scope.strip())
```

**Validation Rules**:
- Cannot be empty
- Splits by comma
- Strips whitespace from each scope
- Removes empty scopes
- Returns normalized comma-separated string

### 3. API_PORT Validator
**Lines 61**
```python
API_PORT: int = Field(default=8000, description="API server port", ge=1024, le=65535)
```

**Validation Rules**:
- `ge=1024`: Greater than or equal to 1024 (no root ports)
- `le=65535`: Less than or equal to 65535 (max port)

### 4. Interval Validators
**Lines 64-66**
```python
TOKEN_REFRESH_INTERVAL: int = Field(..., ge=60)           # Min 60 seconds
AUTOMATION_CHECK_INTERVAL: int = Field(..., ge=10)        # Min 10 seconds
CLEANUP_INTERVAL: int = Field(..., ge=3600)               # Min 3600 seconds (1 hour)
```

---

## Database Configuration

### Engine Configuration
**File**: `app/core/db.py` (lines 13-27)

```python
engine = create_engine(
    _settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,              # Maintain 10 connections
    max_overflow=20,           # Additional 20 on demand (total 30)
    pool_pre_ping=True,        # Validate connections before use
    pool_recycle=3600,         # Recycle after 1 hour
    pool_timeout=30,           # 30 second timeout
    connect_args={
        "connect_timeout": 10,
        "options": "-c timezone=utc"
    },
    future=True,
    echo=_settings.ENV == "dev"  # SQL logging in dev only
)
```

### Connection Pooling Details
| Setting | Value | Purpose |
|---------|-------|---------|
| `pool_size` | 10 | Base connections to maintain |
| `max_overflow` | 20 | Extra connections on demand |
| `pool_pre_ping` | True | Validate before use (prevents stale connections) |
| `pool_recycle` | 3600s | Refresh connections after 1 hour |
| `pool_timeout` | 30s | Wait time for connection from pool |
| `connect_timeout` | 10s | TCP connection timeout |
| `timezone` | UTC | All connections use UTC timezone |

### Session Configuration
```python
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,    # Manual transaction control
    autoflush=False,     # Manual flush control
    future=True          # SQLAlchemy 2.0 behavior
)
```

### Database Initialization
**Function**: `init_db()` (lines 96-140)
- Tests PostgreSQL connectivity
- Validates schema existence
- Reports table count
- Provides detailed troubleshooting on failure

---

## Security Configuration

### Token Encryption (Fernet)
**File**: `app/core/crypto.py`

```python
class TokenEncryptor:
    def __init__(self, key_b64: str):
        self._fernet = Fernet(key_b64.encode())
    
    def enc(self, s: str) -> str:
        return self._fernet.encrypt(s.encode()).decode()
    
    def dec(self, s: str) -> str:
        return self._fernet.decrypt(s.encode()).decode()
```

**Key Details**:
- Uses `cryptography.fernet.Fernet` for symmetric encryption
- Accepts raw key or base64-encoded key
- Automatically encodes raw keys to base64
- Encrypts OAuth tokens stored in database
- Loaded via `load_encryptor(settings.MASTER_SECRET_KEY.get_secret_value())`

### Password Hashing (bcrypt)
**File**: `app/core/security.py`

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Details**:
- Uses `passlib` with bcrypt
- Automatic salt generation
- Used for user password storage

### JWT Token Generation
**File**: `app/core/security.py`

```python
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    secret_key = settings.MASTER_SECRET_KEY.get_secret_value()
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
```

**Token Details**:
- **Algorithm**: HS256
- **Expiration**: 30 minutes (default)
- **Secret Key**: Uses `MASTER_SECRET_KEY`
- **Payload**: Custom data + exp claim

### OAuth Security
**File**: `app/integrations/oauth.py`

```python
def _sign(self, payload: str) -> str:
    mac = hmac.new(
        self.s.OAUTH_STATE_SECRET.get_secret_value().encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(mac).decode().rstrip("=")
```

**State Parameter Protection**:
- HMAC-SHA256 signed state parameters
- CSRF protection for OAuth flows
- Optional Redis backing (fallback to in-memory)

---

## OAuth Configuration

### Facebook OAuth
**Required Variables**:
- `FB_APP_ID`: Facebook App ID (string)
- `FB_APP_SECRET`: Facebook App Secret (SecretStr)

**Optional Variables**:
- `FB_SCOPES`: OAuth scopes (default: `"ads_read"`)
- `FACEBOOK_WEBHOOK_VERIFY_TOKEN`: Webhook verification token

**Scope Examples**:
```
ads_read,pages_show_list,pages_read_engagement,business_management
pages_manage_posts,pages_manage_ads,ads_management
```

### TikTok OAuth
**Required Variables**:
- `TIKTOK_CLIENT_KEY`: TikTok Client Key (string)
- `TIKTOK_CLIENT_SECRET`: TikTok Client Secret (SecretStr)

**Optional Variables**:
- `TIKTOK_SCOPES`: OAuth scopes (default: `"user.info.basic,video.upload,video.publish"`)
- `TIKTOK_WEBHOOK_VERIFY_TOKEN`: Webhook verification token

**Scope Examples**:
```
user.info.basic,user.info.profile,user.info.stats
video.upload,video.publish
```

### OAuth Flow
**File**: `app/integrations/oauth.py` (80+ lines shown)
- State-based CSRF protection
- HMAC-SHA256 signing
- Redis or in-memory state storage
- Token encryption before database storage
- Automatic token refresh on schedule

---

## Application Initialization

### Lifespan Management
**File**: `app/main.py` (lines 39-92)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    app.state.settings = s
    
    init_db()  # Initialize database connection
    
    # Start background tasks
    token_refresh_task = asyncio.create_task(run_token_refresh_scheduler())
    cleanup_task = asyncio.create_task(run_daily_cleanup_scheduler())
    automation_task = asyncio.create_task(
        run_automation_scheduler(check_interval=s.AUTOMATION_CHECK_INTERVAL)
    )
    
    yield
    
    # Graceful shutdown
    # Cancel tasks...
    dispose_engine()
```

### Background Jobs Configuration
| Job | Interval Setting | Default | Min Value |
|-----|------------------|---------|-----------|
| Token Refresh | `TOKEN_REFRESH_INTERVAL` | 3600s (1h) | 60s |
| Automation Check | `AUTOMATION_CHECK_INTERVAL` | 60s | 10s |
| Daily Cleanup | `CLEANUP_INTERVAL` | 86400s (24h) | 3600s (1h) |

---

## Dependency Injection

### FastAPI Dependencies
**File**: `app/deps.py` (100+ lines)

```python
def get_settings_dep() -> Settings:
    return get_settings()

def get_db() -> Generator[Session, None, None]:
    yield from get_database_session()

def get_token_encryptor(settings: Settings = Depends(get_settings_dep)) -> TokenEncryptor:
    global _encryptor_cache
    if _encryptor_cache is None:
        _encryptor_cache = load_encryptor(settings.MASTER_SECRET_KEY.get_secret_value())
    return _encryptor_cache
```

### Type Annotations
Used throughout for dependency injection:
```python
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
TenantSvc = Annotated[TenantService, Depends(get_tenant_service)]
AuthSvc = Annotated[AuthService, Depends(get_auth_service)]
```

---

## Supabase Integration Analysis

### Current Status: NO DIRECT SUPABASE INTEGRATION

The codebase supports **Supabase PostgreSQL databases** through standard PostgreSQL connection strings, but does NOT use:
- Supabase Authentication
- Supabase Storage
- Supabase Realtime
- Supabase JS Client
- Supabase-specific APIs

### Supported Supabase Configurations
1. **Direct Connection** (requires IPv6 or Supabase IPv4 add-on):
   ```
   postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres
   ```

2. **Session Pooler** (recommended for Railway/Vercel):
   ```
   postgresql://postgres:PASSWORD@db.xxx.supabase.co:6543/postgres?pgbouncer=true
   ```

### Implementation Notes
- `.env.example` includes Supabase connection string examples
- No Supabase client libraries in `requirements.txt`
- Authentication handled by custom JWT implementation
- Encryption handled by Fernet (not Supabase)

---

## Configuration Files

### Primary Config File
**Path**: `d:\Facebook-automation\app\core\config.py`
- **Lines**: 104 total
- **Dependencies**: pydantic, pydantic-settings, cryptography
- **Class**: `Settings(BaseSettings)`
- **Caching**: `@lru_cache()` on `get_settings()`

### Environment File
**Path**: `d:\Facebook-automation\.env.example`
- **Lines**: 175
- **Purpose**: Template for environment variables
- **Not Committed**: Real `.env` is in `.gitignore`
- **Updated**: 2025-11-14

### Database File
**Path**: `d:\Facebook-automation\app\core\db.py`
- **Lines**: 164
- **Engine**: SQLAlchemy 2.0 with QueuePool
- **SessionLocal**: Sessionmaker with future=True

---

## Pydantic Field Types

### Pydantic Custom Types Used
| Type | Module | Usage |
|------|--------|-------|
| `SecretStr` | `pydantic` | OAuth secrets, JWT keys, tokens |
| `AnyHttpUrl` | `pydantic` | BASE_URL, FRONTEND_URL |
| `Literal` | `typing` | ENV environment selection |
| `Field` | `pydantic` | Validation, defaults, descriptions |

### SecretStr Handling
```python
OAUTH_STATE_SECRET: SecretStr = Field(...)
MASTER_SECRET_KEY: SecretStr = Field(...)
FB_APP_SECRET: SecretStr = Field(...)

# Usage
secret_value = settings.FB_APP_SECRET.get_secret_value()  # Retrieve actual value
# Does NOT print in repr() for security
```

---

## Environment-Specific Behavior

### Development (ENV="dev")
```python
echo=True              # SQL query logging enabled
pool_pre_ping=True    # Validate connections
log_sql_queries=True  # Database debugging
```

### Production (ENV="prod")
```python
echo=False            # No SQL logging
log_min_duration_statement=1000  # Only slow queries (>1s)
CORS origins = specific domains
```

---

## Configuration Entry Points

### 1. Application Startup
**File**: `app/main.py` (lines 40-51)
```python
s = get_settings()  # Load settings once
app.state.settings = s  # Store in app state
init_db()  # Connect to database
```

### 2. Endpoint Access
**Example from `app/main.py` (lines 143-148)**
```python
@app.get("/health")
def health_check(settings: SettingsDep):
    snapshot = collect_monitoring_snapshot(settings)
    if settings.ENV == "dev":
        log_monitoring_snapshot(get_logger(), snapshot, context="health")
```

### 3. Service/Repository Access
```python
def __init__(self, settings: Settings = Depends(get_settings_dep)):
    self.settings = settings
    self.database_url = settings.DATABASE_URL
    self.master_key = settings.MASTER_SECRET_KEY.get_secret_value()
```

---

## Validation Error Examples

### Missing Required Variable
```
Error: 1 validation error for Settings
DATABASE_URL
  Field required [type=missing, input_value={...}, input_type=dict, ...]
```

### Invalid DATABASE_URL
```
Error: 1 validation error for Settings
DATABASE_URL
  Value error, DATABASE_URL must be a valid PostgreSQL connection string [type=value_error, ...]
```

### Invalid Port
```
Error: 1 validation error for Settings
API_PORT
  Input should be less than or equal to 65535 [type=less_than_equal, ...]
```

### Empty OAuth Scopes
```
Error: 1 validation error for Settings
FB_SCOPES
  Value error, OAuth scopes cannot be empty [type=value_error, ...]
```

---

## Summary of Key Properties

### Settings Class Summary
| Property | Type | Required | Validated | Cached |
|----------|------|----------|-----------|--------|
| DATABASE_URL | str | YES | YES | YES |
| OAUTH_STATE_SECRET | SecretStr | YES | - | YES |
| MASTER_SECRET_KEY | SecretStr | YES | - | YES |
| FB_APP_ID | str | YES | - | YES |
| FB_APP_SECRET | SecretStr | YES | - | YES |
| TIKTOK_CLIENT_KEY | str | YES | - | YES |
| TIKTOK_CLIENT_SECRET | SecretStr | YES | - | YES |
| TELEGRAM_BOT_TOKEN | SecretStr | YES | - | YES |
| ENV | Literal | NO | - | YES |
| BASE_URL | AnyHttpUrl | NO | - | YES |
| FRONTEND_URL | AnyHttpUrl | NO | - | YES |
| REDIS_URL | str\|None | NO | - | YES |
| FB_SCOPES | str | NO | YES | YES |
| TIKTOK_SCOPES | str | NO | YES | YES |
| TOKEN_REFRESH_INTERVAL | int | NO | YES | YES |
| AUTOMATION_CHECK_INTERVAL | int | NO | YES | YES |
| CLEANUP_INTERVAL | int | NO | YES | YES |

---

## Recommendation Summary

### Best Practices Observed
✅ Pydantic v2 Settings with proper typing  
✅ Environment variable validation at startup  
✅ Secrets masked in logging (SecretStr)  
✅ Database connection pooling optimized  
✅ Token encryption at rest (Fernet)  
✅ HMAC-signed OAuth state parameters  
✅ Configuration caching for performance  
✅ Comprehensive error messages on startup  

### Configuration Strengths
- **Type Safety**: Full Pydantic validation
- **Security**: SecretStr prevents accidental logging
- **Flexibility**: Works with Supabase, local PostgreSQL, or any PostgreSQL database
- **Scalability**: Connection pooling + background job intervals configurable
- **Observability**: Database initialization validation + health endpoint

### Areas for Enhancement
- Consider adding Supabase Auth integration for passwordless auth
- Add configuration validation schema export (for CI/CD)
- Document environment variable precedence in README
- Add configuration profile support (dev/staging/prod preset configs)

---

## Quick Reference

### Generate Secure Secrets
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Minimal .env File
```env
ENV=dev
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
DATABASE_URL=postgresql://postgres:password@localhost:5432/facebook_automation
OAUTH_STATE_SECRET=<generate-with-python>
MASTER_SECRET_KEY=<generate-with-python>
FB_APP_ID=<your-facebook-app-id>
FB_APP_SECRET=<your-facebook-app-secret>
TIKTOK_CLIENT_KEY=<your-tiktok-client-key>
TIKTOK_CLIENT_SECRET=<your-tiktok-client-secret>
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
```

### Verify Configuration
```bash
# Start app with DEBUG to see loaded settings
python -c "from app.core.config import get_settings; s = get_settings(); print(f'Loaded config: ENV={s.ENV}, DB={s.database_url_safe}')"
```

---

**Document Status**: Complete  
**Last Updated**: 2025-11-14  
**Configuration Version**: 0.2.0
