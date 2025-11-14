# Claude Code Project Configuration

## Project Info
- **Name**: Facebook/TikTok Automation Project
- **Type**: FastAPI backend + React frontend + Telegram bot
- **Working Directory**: `d:\Facebook-automation`
- **Version**: 0.2.0

## Development Setup
- **Python Environment**: Use the existing `.venv/`
- **Activate venv (Windows)**: `.\.venv\Scripts\activate`
- **Activate venv (WSL/Linux/macOS)**: `source .venv/bin/activate`
- **Dependencies**: `pip install -r app/tests/requirements.txt`
- **Database**: PostgreSQL managed through SQLAlchemy and Alembic

## Key Commands
```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Telegram bot
python -m app.bot

# Apply database migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "Description"
```

## Project Structure
- `app/main.py` - FastAPI application entrypoint with CORS, routers, and lifespan management
- `app/bot.py` - Telegram bot entrypoint
- `app/core/` - Configuration, database session management, models, and security utilities
  - `config.py` - Pydantic settings with environment variable validation
  - `db.py` - Database engine, session management, and connection pooling
  - `models.py` - SQLAlchemy ORM models (Tenant, User, AdToken, Destination, Automation)
  - `crypto.py` - Token encryption/decryption using Fernet
  - `security.py` - Password hashing (bcrypt) and JWT token generation
  - `rate_limit.py` - Rate limiting middleware for API protection
- `app/routes/` - API route handlers
  - `auth.py` - User registration, login, password management
  - `oauth.py` - Facebook and TikTok OAuth flows
  - `webhooks.py` - Webhook handlers for Facebook and TikTok events
- `app/services/` - Business logic layer
  - `auth_service.py` - OAuth token storage, validation, and retrieval
- `app/repositories/` - Data access layer (Repository pattern)
  - `user.py` - User CRUD operations
  - `tenant.py` - Tenant management
  - `ad_token.py` - Token storage and retrieval
  - `destination.py` - Destination management
  - `automation.py` - Automation CRUD
- `app/integrations/` - External API clients
  - `oauth.py` - Facebook/TikTok OAuth client implementations
  - `tiktok.py` - TikTok API client
- `app/jobs/` - Background tasks
  - `token_refresh.py` - Automated token refresh and cleanup scheduler
- `frontend/` - React single-page application
  - `src/components/LoginPage.tsx` - Modern login UI with gradient background
  - `src/components/OAuthLoginPage.tsx` - OAuth social media connection UI
  - `src/components/Dashboard.tsx` - Main dashboard
- `migrations/` - Alembic migration history

## Database Schema

### Multi-Tenant Architecture
All core entities are scoped to a `Tenant` for complete data isolation:

#### **Tenant** (tenant)
- `id` (UUID, PK) - Unique tenant identifier
- `name` (String) - Organization name
- `slug` (String, unique) - URL-friendly identifier
- `is_active` (Boolean) - Active status
- `settings` (JSON) - Tenant-specific configuration
- `created_at`, `updated_at` (DateTime)

#### **User** (user)
Multi-user support per tenant with flexible authentication:
- `id` (UUID, PK) - Unique user identifier
- `tenant_id` (UUID, FK) - Parent tenant
- `telegram_user_id` (String, nullable) - Telegram authentication
- `email` (String, nullable) - Email address
- `username` (String, nullable) - Username for login
- `password_hash` (String, nullable) - Bcrypt password hash
- `email_verified` (Boolean) - Email verification status
- `role` (Enum) - admin, user, viewer
- `is_active` (Boolean) - Account status
- `last_login` (DateTime) - Last login timestamp
- `profile_data` (JSON) - Additional profile information
- **Unique Constraints**: (tenant_id, telegram_user_id), (tenant_id, email)

#### **AdToken** (ad_token)
OAuth tokens for social media platforms:
- `id` (UUID, PK)
- `tenant_id` (UUID, FK)
- `platform` (Enum) - facebook, tiktok
- `account_ref` (String) - Platform account ID (e.g., act_123, open_id)
- `account_name` (String) - Human-readable account name
- `access_token_enc` (String) - Encrypted access token (Fernet)
- `refresh_token_enc` (String, nullable) - Encrypted refresh token
- `scope` (String) - OAuth scopes granted
- `expires_at` (DateTime, nullable) - Token expiration (UTC)
- `is_valid` (Boolean) - Validation status
- `last_validated` (DateTime) - Last validation check
- `meta` (JSON) - Raw OAuth response data
- **Unique Constraint**: (tenant_id, platform, account_ref)

#### **Destination** (destination)
Output targets for reports and alerts:
- `id` (UUID, PK)
- `tenant_id` (UUID, FK)
- `name` (String) - Destination name
- `type` (Enum) - telegram_chat, webhook, email
- `config` (JSON) - Type-specific configuration
- `is_active` (Boolean)

#### **Automation** (automation)
Scheduled automation rules:
- `id` (UUID, PK)
- `tenant_id` (UUID, FK)
- `destination_id` (UUID, FK)
- `name` (String) - Automation name
- `type` (Enum) - scheduled_report, alert, data_sync
- `status` (Enum) - active, paused, stopped, error
- `schedule_config` (JSON) - Cron-like scheduling
- `automation_config` (JSON) - Automation-specific settings
- `platforms` (JSON) - Platforms to include
- `last_run`, `next_run` (DateTime)
- `run_count`, `error_count` (Integer)

#### **AutomationRun** (automation_run)
Execution history and logs:
- `id` (UUID, PK)
- `automation_id` (UUID, FK)
- `started_at`, `completed_at` (DateTime)
- `status` (String) - running, completed, failed
- `result` (JSON) - Execution results
- `error_message` (Text)
- `logs` (JSON) - Detailed execution logs

## Authentication & Security

### User Authentication
1. **Username/Password** - JWT-based authentication with bcrypt password hashing
   - Registration: `POST /auth/register`
   - Login: `POST /auth/login` (returns JWT access token)
   - Get current user: `GET /auth/me`
   - Change password: `POST /auth/change-password`
   - Logout: `POST /auth/logout` (client-side token discard)

2. **Social OAuth** - Facebook, TikTok integration for account linking
   - Authorization: `GET /oauth/{platform}/authorize`
   - Callback: `GET /oauth/{platform}/callback`

3. **Telegram Bot** - Telegram user ID authentication

### Security Features
- **Password Security**: Bcrypt hashing with automatic salt generation
- **JWT Tokens**: HS256 algorithm, 30-minute expiration
- **Token Encryption**: Fernet symmetric encryption for OAuth tokens
- **Rate Limiting**: API endpoint protection against abuse
- **CORS**: Configured for localhost development
- **Environment Variables**: Sensitive credentials via `.env` file

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Security Keys
OAUTH_STATE_SECRET=your-oauth-state-secret-here
MASTER_SECRET_KEY=your-master-secret-key-for-encryption

# Facebook
FB_APP_ID=your-facebook-app-id
FB_APP_SECRET=your-facebook-app-secret
FB_SCOPES=ads_read,pages_manage_posts,pages_read_engagement

# TikTok
TIKTOK_CLIENT_KEY=your-tiktok-client-key
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret
TIKTOK_SCOPES=user.info.basic,video.upload,video.publish

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Webhooks
FACEBOOK_WEBHOOK_VERIFY_TOKEN=my_facebook_verify_token_change_me
TIKTOK_WEBHOOK_VERIFY_TOKEN=my_tiktok_verify_token_change_me

# Application
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
ENV=dev

# Background Job Configuration (Optional)
AUTOMATION_CHECK_INTERVAL=60    # Check for due automations every 60 seconds
TOKEN_REFRESH_INTERVAL=3600     # Check token expiry every hour
CLEANUP_INTERVAL=86400          # Run cleanup daily
```

## Progress Summary (Updated 2025-10-25)

### ✅ Completed Features

1. **Database Architecture**
   - Multi-tenant data isolation with complete schema
   - Repository pattern for clean data access
   - Alembic migrations for schema versioning
   - Encrypted token storage with Fernet

2. **OAuth Integration**
   - Facebook OAuth 2.0 flow with page token management
   - TikTok OAuth 2.0 flow with creator info
   - Token refresh and validation scheduling
   - State parameter CSRF protection

3. **User Authentication**
   - Username/password registration and login
   - JWT-based session management
   - Password hashing with bcrypt
   - Social OAuth account linking
   - Role-based access control (admin, user, viewer)

4. **Frontend UI**
   - Modern login page with gradient background (ColorLib-inspired)
   - OAuth connection page for Facebook/TikTok
   - Dashboard with tenant selection
   - Responsive design for mobile/tablet/desktop

5. **API Endpoints**
   - `/health` - System health check
   - `/auth/*` - User authentication
   - `/oauth/*` - Social media OAuth flows
   - `/api/tenants/*` - Tenant management
   - `/api/webhooks/*` - Facebook/TikTok webhooks

6. **Background Jobs & Automation Scheduler**
   - ✅ Automation scheduler - executes automations on schedule
   - ✅ Scheduled report handler - generates periodic reports
   - ✅ Alert handler - monitors thresholds and sends notifications
   - ✅ Data sync handler - syncs data to external systems
   - ✅ Automated token refresh (configurable interval)
   - ✅ Daily cleanup of expired tokens
   - ✅ Configurable scheduler intervals via environment variables
   - See [SCHEDULER.md](SCHEDULER.md) for detailed documentation

7. **Security & Rate Limiting**
   - Rate limiting middleware
   - CORS configuration
   - JWT token validation
   - Encrypted credential storage

## Current Status
- **Backend API**: ✅ Running on `http://localhost:8000`
- **Frontend React**: ✅ Running on `http://localhost:3000`
- **Database**: ✅ PostgreSQL with complete schema
- **OAuth Flows**: ✅ Facebook and TikTok working end-to-end
- **Authentication**: ✅ Username/password + JWT + OAuth
- **Webhooks**: ✅ Configured and ready for events
- **Automation Scheduler**: ✅ Running and executing automations

## Next Steps & Improvements

1. **Email Verification**
   - Implement email verification flow
   - Send verification emails on registration
   - Add email templates

2. **Password Reset**
   - Forgot password functionality
   - Password reset tokens
   - Email-based reset flow

3. **Testing**
   - Unit tests for authentication
   - Integration tests for OAuth flows
   - E2E tests for user flows

4. **Production Deployment**
   - Set up proper MASTER_SECRET_KEY
   - Configure production database
   - Set up SSL/HTTPS
   - Configure production CORS origins
   - Set up monitoring and logging

5. **UI Enhancements**
   - Connect LoginPage to backend
   - Add form validation
   - Improve error handling
   - Add loading states

6. **Documentation**
   - API documentation with Swagger/OpenAPI
   - User guide
   - Deployment guide
