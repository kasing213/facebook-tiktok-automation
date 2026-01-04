# Commands Reference

Quick reference for all commands needed to run and manage the Facebook-automation platform.

---

## Development

### Backend (FastAPI)

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with specific env file
ENV=dev uvicorn app.main:app --reload

# Run tests
pytest
pytest -v  # verbose
pytest tests/test_oauth.py  # specific test file
```

### Frontend (React + Vite)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### API Gateway (FastAPI + Telegram Bot)

```bash
# Navigate to api-gateway
cd api-gateway

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001

# Run with Docker
docker build -t api-gateway .
docker run -p 8001:8001 --env-file .env api-gateway
```

---

## Database

### Alembic Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --indicate-current
```

### PostgreSQL Direct Access

```bash
# Connect via psql (if installed)
psql $DATABASE_URL

# Using Docker
docker exec -it <container_name> psql -U postgres -d database_name

# Common SQL commands
\dt                    # List tables
\d table_name          # Describe table
\du                    # List users
\l                     # List databases
\c database_name       # Connect to database
```

---

## Docker

### Building Images

```bash
# Build backend
docker build -t facebook-automation .

# Build frontend
docker build -t facebook-automation-frontend ./frontend

# Build API Gateway
docker build -t api-gateway ./api-gateway
```

### Running Containers

```bash
# Run backend
docker run -p 8000:8000 --env-file .env facebook-automation

# Run with docker-compose (if available)
docker-compose up -d
docker-compose down
docker-compose logs -f
```

---

## Git Workflow

```bash
# Check status
git status

# Create feature branch
git checkout -b feature/my-feature

# Stage and commit
git add .
git commit -m "feat: description"

# Push to remote
git push origin feature/my-feature

# Merge to main
git checkout main
git pull origin main
git merge feature/my-feature
git push origin main
```

### Commit Message Prefixes
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

---

## Railway Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up

# View logs
railway logs

# Open dashboard
railway open

# Set environment variables
railway variables set KEY=value
```

---

## Telegram Bot Commands

### User Commands (in Telegram)
```
/start              # Start bot / show welcome
/start <code>       # Link account with code
/status             # View all systems status
/help               # Show all commands

# Invoice Generator
/invoice            # Invoice menu
/invoice_list       # List recent invoices
/invoice_stats      # Invoice statistics

# Screenshot Verifier
/verify             # Verification menu
/verify_pending     # List pending screenshots
/verify_stats       # Verification statistics

# Sales Reports
/sales              # Sales menu
/sales_today        # Today's sales summary
/sales_stats        # Sales statistics

# Promotions
/promo              # Promotion menu
/promo_status       # Current promotion status
/promo_chats        # Registered chats
```

---

## API Endpoints Reference

### Authentication
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "...", "username": "user", "email": "user@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password123"

# Get current user
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <token>"
```

### OAuth
```bash
# Get Facebook OAuth URL
curl "http://localhost:8000/auth/facebook/authorize-url?tenant_id=<id>"

# Get TikTok OAuth URL
curl "http://localhost:8000/auth/tiktok/authorize-url?tenant_id=<id>"

# Get auth status
curl "http://localhost:8000/api/tenants/<id>/auth-status" \
  -H "Authorization: Bearer <token>"
```

### Telegram Integration
```bash
# Generate link code
curl -X POST http://localhost:8000/telegram/generate-code \
  -H "Authorization: Bearer <token>"

# Get telegram status
curl http://localhost:8000/telegram/status \
  -H "Authorization: Bearer <token>"

# Disconnect telegram
curl -X POST http://localhost:8000/telegram/disconnect \
  -H "Authorization: Bearer <token>"
```

### Health Checks
```bash
# Main API health
curl http://localhost:8000/health

# API Gateway health
curl http://localhost:8001/health

# Individual service health (via gateway)
curl http://localhost:8001/api/invoice/health
curl http://localhost:8001/api/scriptclient/health
curl http://localhost:8001/api/audit-sales/health
curl http://localhost:8001/api/ads-alert/health
```

---

## Environment Variables

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Security
OAUTH_STATE_SECRET=your-secret-key
MASTER_SECRET_KEY=your-master-key

# Facebook
FB_APP_ID=your-app-id
FB_APP_SECRET=your-app-secret
FB_SCOPES=public_profile

# TikTok
TIKTOK_CLIENT_KEY=your-client-key
TIKTOK_CLIENT_SECRET=your-client-secret
TIKTOK_SCOPES=user.info.basic

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_BOT_USERNAME=your_bot_username

# URLs
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### API Gateway Variables

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token

# PostgreSQL
DATABASE_URL=postgresql://...

# Core API
CORE_API_URL=http://localhost:8000

# MongoDB connections (optional)
MONGO_URL_INVOICE=mongodb+srv://...
MONGO_URL_SCRIPTCLIENT=mongodb+srv://...
MONGO_URL_AUDIT_SALES=mongodb+srv://...
MONGO_URL_ADS_ALERT=mongodb+srv://...
```

---

## Troubleshooting

### Common Issues

```bash
# Port already in use
lsof -i :8000
kill -9 <PID>

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Reset node_modules
cd frontend && rm -rf node_modules && npm install

# Check PostgreSQL connection
psql $DATABASE_URL -c "SELECT 1"

# Check logs
tail -f logs/app.log
```

### Database Reset (Development Only!)

```bash
# Drop all tables and recreate
alembic downgrade base
alembic upgrade head

# Or via psql
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

---

## Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd Facebook-automation
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your values

# 3. Run migrations
alembic upgrade head

# 4. Start backend
uvicorn app.main:app --reload

# 5. Start frontend (new terminal)
cd frontend
npm install
npm run dev

# 6. (Optional) Start API Gateway
cd api-gateway
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8001
```

---

## Useful Links

- Backend API Docs: http://localhost:8000/docs
- Frontend Dev: http://localhost:3000
- API Gateway Docs: http://localhost:8001/docs
- Railway Dashboard: https://railway.app/dashboard
- Vercel Dashboard: https://vercel.com/dashboard
