# Deployment Guide - Facebook/TikTok Automation Platform

## 📦 Docker Deployment Overview

This project uses **multi-stage Docker builds** for production deployments with optimized image sizes, enhanced security, and better performance.

### Architecture
```
┌─────────────────────────────────────────────┐
│  VERCEL (Frontend - React/Vite)             │
│  https://facebooktiktokautomation.vercel.app│
└────────────────┬────────────────────────────┘
                 │
    ┌────────────┴───────────────┐
    │                            │
┌───▼────────────────┐  ┌────────▼──────────┐
│ RAILWAY            │  │ RAILWAY            │
│ facebook-automation│  │ api-gateway        │
│ (Main Backend)     │  │ (Telegram Bot)     │
│ Port: 8000         │  │ Port: 8001         │
│ Dockerfile (root)  │  │ Dockerfile (./api) │
└───────┬────────────┘  └────────┬───────────┘
        │                        │
        └────────────┬───────────┘
                     │
            ┌────────▼──────────┐
            │ SUPABASE          │
            │ PostgreSQL        │
            │ (6 schemas)       │
            └───────────────────┘
```

---

## 🐳 Dockerfile Features

### Main Backend (`Dockerfile`)
✅ **Multi-stage build** - Smaller final image (~300MB vs ~1GB)
✅ **Python 3.12** - Latest stable with security patches
✅ **Non-root user** - Security best practice (UID 1000)
✅ **Health checks** - Automatic container monitoring
✅ **Optimized layers** - Better caching and faster rebuilds
✅ **Production uvicorn** - 2 workers, keep-alive timeout 65s

### API Gateway (`api-gateway/Dockerfile`)
✅ **Multi-stage build** - Reduced attack surface
✅ **Isolated bot service** - Separate concerns
✅ **Health monitoring** - Kubernetes/Railway compatible
✅ **Security hardened** - Non-root execution

---

## 🚀 Quick Start

### Local Development with Docker Compose

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your credentials
# Required: DATABASE_URL, MASTER_SECRET_KEY, TELEGRAM_BOT_TOKEN

# 3. Build and run all services
docker-compose up --build

# 4. Access services
# Backend: http://localhost:8000
# API Gateway: http://localhost:8001
# Docs: http://localhost:8000/docs
```

### Build Individual Services

```bash
# Main backend
docker build -t facebook-automation:latest .

# API Gateway
docker build -t api-gateway:latest ./api-gateway

# Run backend container
docker run -p 8000:8000 --env-file .env facebook-automation:latest

# Run API Gateway container
docker run -p 8001:8001 --env-file .env api-gateway:latest
```

---

## 🏗️ Railway Deployment (Production)

### Prerequisites
- Railway account connected to GitHub
- Supabase PostgreSQL database
- Environment variables configured

### Deploy Main Backend (facebook-automation)

1. **Create New Service on Railway**
   ```
   Project: Facebook-TikTok-Automation
   Service Name: facebook-automation
   Source: GitHub repo (root directory)
   ```

2. **Configure Build**
   ```
   Build Command: (auto-detected from Dockerfile)
   Start Command: (auto-detected from Dockerfile CMD)
   ```

3. **Set Environment Variables**
   ```bash
   DATABASE_URL=postgresql://...
   MASTER_SECRET_KEY=your-secret-key
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_BOT_USERNAME=KS_automations_bot
   FB_APP_ID=your-fb-app-id
   FB_APP_SECRET=your-fb-secret
   TIKTOK_CLIENT_KEY=your-tiktok-key
   TIKTOK_CLIENT_SECRET=your-tiktok-secret
   BASE_URL=https://facebook-automation-production.up.railway.app
   FRONTEND_URL=https://facebooktiktokautomation.vercel.app
   INVOICE_API_KEY=invoice_api_xxx
   OCR_API_KEY=ocr_api_xxx
   ```

4. **Deploy**
   - Railway auto-deploys on git push to main branch
   - Monitor logs: `railway logs`

### Deploy API Gateway (Telegram Bot)

1. **Create Second Service on Railway**
   ```
   Service Name: api-gateway
   Source: GitHub repo (api-gateway directory)
   Root Directory: /api-gateway
   ```

2. **Set Environment Variables**
   ```bash
   DATABASE_URL=postgresql://...
   TELEGRAM_BOT_TOKEN=your-bot-token
   CORE_API_URL=https://facebook-automation-production.up.railway.app
   MASTER_SECRET_KEY=your-secret-key
   OCR_API_KEY=ocr_api_xxx
   ```

3. **Deploy**
   - Auto-deploys with main backend
   - Bot starts automatically

---

## 🔧 Environment Variables Reference

### Required (Both Services)
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:6543/db` |
| `MASTER_SECRET_KEY` | JWT signing secret | `your-256-bit-secret` |
| `TELEGRAM_BOT_TOKEN` | Bot API token from @BotFather | `123456:ABC-DEF...` |

### Backend Only
| Variable | Description | Example |
|----------|-------------|---------|
| `FB_APP_ID` | Facebook App ID | `1234567890` |
| `FB_APP_SECRET` | Facebook App Secret | `abc123...` |
| `TIKTOK_CLIENT_KEY` | TikTok API client key | `awx123...` |
| `TIKTOK_CLIENT_SECRET` | TikTok API secret | `xyz789...` |
| `BASE_URL` | Backend URL | `https://api.example.com` |
| `FRONTEND_URL` | Frontend URL | `https://app.example.com` |
| `INVOICE_API_KEY` | Invoice service API key | `invoice_api_xxx` |
| `OCR_API_KEY` | OCR service API key | `ocr_api_xxx` |

### API Gateway Only
| Variable | Description | Example |
|----------|-------------|---------|
| `CORE_API_URL` | Main backend URL | `https://api.example.com` |

---

## 📊 Image Size Comparison

### Before Optimization (Single-stage)
```
facebook-automation:  ~1.2 GB
api-gateway:          ~950 MB
```

### After Optimization (Multi-stage)
```
facebook-automation:  ~320 MB  (73% reduction)
api-gateway:          ~280 MB  (70% reduction)
```

**Benefits:**
- Faster deployment times (less to download)
- Reduced bandwidth costs
- Smaller attack surface
- Better layer caching

---

## 🔒 Security Features

### Container Security
✅ **Non-root execution** - Runs as `appuser` (UID 1000)
✅ **Minimal base image** - `python:3.12-slim` (security patches only)
✅ **No secrets in images** - Environment variables only
✅ **Read-only filesystem** - Application files owned by appuser
✅ **Health checks** - Automatic restart on failure

### Network Security
✅ **Private networking** - Services communicate via internal network
✅ **HTTPS only** - Railway provides automatic SSL/TLS
✅ **CORS configured** - Frontend whitelist only

### Application Security
✅ **JWT authentication** - Service-to-service auth with rotation
✅ **Row-level security** - Database-level tenant isolation
✅ **Input validation** - Pydantic models enforce schemas
✅ **Rate limiting** - API endpoint protection

---

## 🧪 Testing Deployment

### Health Checks
```bash
# Backend health
curl https://facebook-automation-production.up.railway.app/health

# API Gateway health
curl https://api-gateway-production.up.railway.app/health

# Expected response
{"status": "healthy", "version": "1.0.0"}
```

### API Endpoints
```bash
# Test authentication
curl -X POST https://your-backend.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Test Telegram bot
# Send /start to @KS_automations_bot
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions (Future Enhancement)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push Docker image
        # Railway auto-deploys from GitHub

  deploy-api-gateway:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      # Railway handles deployment
```

---

## 📝 Troubleshooting

### Build Failures

**Error: `psycopg-binary version not found`**
```bash
# Solution: Update requirements.txt
psycopg[binary]==3.2.13  # Use latest compatible version
```

**Error: `SQLAlchemy Python 3.13 incompatible`**
```bash
# Solution: Use Python 3.12 in Dockerfile
FROM python:3.12-slim
```

### Runtime Issues

**Container exits immediately**
```bash
# Check logs
railway logs --service facebook-automation

# Common cause: Missing environment variables
# Solution: Verify all required env vars are set
```

**Health check failing**
```bash
# Check if port is correct
# Railway sets PORT env var automatically
# Ensure app listens on 0.0.0.0:${PORT}
```

**Database connection timeout**
```bash
# Solution: Use connection pooler (pgbouncer)
# DATABASE_URL should use port 6543 (transaction mode)
```

---

## 🎯 Performance Tuning

### Uvicorn Workers
```python
# Production settings (Dockerfile)
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \           # CPU cores
     "--timeout-keep-alive", "65"]  # Keep-alive timeout
```

### Database Connection Pool
```python
# app/core/db.py
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Railway handles pooling via pgbouncer
    connect_args={
        "connect_timeout": 30,
        "prepare_threshold": 0
    }
)
```

---

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Supabase Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)

---

## 🆘 Support

For deployment issues:
1. Check Railway logs: `railway logs`
2. Review environment variables
3. Verify database connectivity
4. Check GitHub Actions (if configured)
5. Contact DevOps team

---

**Last Updated:** February 7, 2026
**Version:** 2.0.0 (Multi-stage Docker deployment)
