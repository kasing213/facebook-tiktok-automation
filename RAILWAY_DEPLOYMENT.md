# Railway Deployment Guide

## Current Status
✅ **Build**: Successful (Python 3.12.3, all dependencies installed)
❌ **Runtime**: Crashed - Missing environment variables

## Issue: API Crash on Startup

### Probable Cause
The application crashes because **required environment variables are not set** in Railway.

### Common Errors to Look For in Railway Logs:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
DATABASE_URL
  Field required [type=missing, input_value={}, input_type=dict]
```

Or:

```
KeyError: 'DATABASE_URL'
ConnectionError: could not connect to server
```

---

## Required Environment Variables

### 1. Database Configuration (CRITICAL)
Railway provides a PostgreSQL database - you need to link it:

```bash
DATABASE_URL=postgresql://user:password@host:port/dbname
```

**In Railway:**
1. Add PostgreSQL database to your project (New → Database → PostgreSQL)
2. In your web service, go to **Variables** tab
3. Add reference: `DATABASE_URL=${{Postgres.DATABASE_URL}}`

---

### 2. Security Keys (CRITICAL)

Generate strong random secrets:
```bash
# Generate secrets locally
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Required variables:**
```bash
MASTER_SECRET_KEY=<your-generated-secret-here>
OAUTH_STATE_SECRET=<your-generated-secret-here>
JWT_SECRET_KEY=<your-generated-secret-here>
```

---

### 3. Facebook OAuth (REQUIRED for Facebook integration)

```bash
FB_APP_ID=your-facebook-app-id
FB_APP_SECRET=your-facebook-app-secret
FB_SCOPES=ads_read,pages_manage_posts,pages_read_engagement
```

Get these from: https://developers.facebook.com/apps

---

### 4. TikTok OAuth (REQUIRED for TikTok integration)

```bash
TIKTOK_CLIENT_KEY=your-tiktok-client-key
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret
TIKTOK_SCOPES=user.info.basic,video.upload,video.publish
```

Get these from: https://developers.tiktok.com/

---

### 5. Application URLs (REQUIRED)

```bash
BASE_URL=https://your-app-name.up.railway.app
FRONTEND_URL=https://your-frontend-url.com
ENV=production
```

**Important:** Update these AFTER Railway generates your domain.

---

### 6. Webhook Verification Tokens (OPTIONAL but recommended)

```bash
FACEBOOK_WEBHOOK_VERIFY_TOKEN=your-random-token-here
TIKTOK_WEBHOOK_VERIFY_TOKEN=your-random-token-here
```

---

### 7. Telegram Bot (OPTIONAL)

```bash
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

Get from: https://t.me/BotFather

---

### 8. Background Jobs Configuration (OPTIONAL)

```bash
AUTOMATION_CHECK_INTERVAL=60
TOKEN_REFRESH_INTERVAL=3600
CLEANUP_INTERVAL=86400
```

---

## Step-by-Step Railway Setup

### Step 1: Add PostgreSQL Database
1. In your Railway project dashboard
2. Click **"New"** → **"Database"** → **"PostgreSQL"**
3. Railway will provision a database

### Step 2: Link Database to Web Service
1. Click on your **web service**
2. Go to **"Variables"** tab
3. Click **"New Variable"**
4. Add: `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
   - This references the PostgreSQL database Railway created

### Step 3: Add All Required Environment Variables

Click **"New Variable"** for each:

#### Minimum Required Variables (to start):
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
MASTER_SECRET_KEY=<generate-with-python>
OAUTH_STATE_SECRET=<generate-with-python>
JWT_SECRET_KEY=<generate-with-python>
BASE_URL=https://your-railway-domain.up.railway.app
FRONTEND_URL=http://localhost:3000
ENV=production
```

#### Add OAuth credentials when ready:
```
FB_APP_ID=<from-facebook>
FB_APP_SECRET=<from-facebook>
FB_SCOPES=ads_read,pages_manage_posts,pages_read_engagement
TIKTOK_CLIENT_KEY=<from-tiktok>
TIKTOK_CLIENT_SECRET=<from-tiktok>
TIKTOK_SCOPES=user.info.basic,video.upload,video.publish
```

### Step 4: Redeploy
After adding variables:
1. Railway will automatically redeploy
2. Monitor the **"Deployments"** tab for logs
3. Look for: `Application startup complete`

---

## Verifying Successful Deployment

### Health Check
Once deployed, visit:
```
https://your-app-name.up.railway.app/health
```

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### Check Logs
In Railway dashboard → Deployments → Latest deployment:

✅ **Success indicators:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

❌ **Failure indicators:**
```
ValidationError: 1 validation error for Settings
KeyError: 'DATABASE_URL'
psycopg2.OperationalError: connection failed
```

---

## Update OAuth Redirect URIs

After Railway generates your domain, update:

### Facebook App Settings
1. Go to https://developers.facebook.com/apps
2. Your App → Settings → Basic
3. Add OAuth Redirect URI:
   ```
   https://your-app-name.up.railway.app/oauth/facebook/callback
   ```

### TikTok App Settings
1. Go to https://developers.tiktok.com/
2. Your App → Manage Apps
3. Add Redirect URI:
   ```
   https://your-app-name.up.railway.app/oauth/tiktok/callback
   ```

---

## Troubleshooting Common Issues

### Issue: "ValidationError for Settings"
**Solution:** Missing required environment variables. Add all variables from Step 3 above.

### Issue: "connection to server failed"
**Solution:** DATABASE_URL not set or incorrect. Verify it references `${{Postgres.DATABASE_URL}}`

### Issue: "Module not found"
**Solution:** Check build logs - dependencies might have failed to install. Verify `runtime.txt` has Python 3.12.3

### Issue: "alembic upgrade head failed"
**Solution:** Database connection failed during migrations. Check DATABASE_URL and ensure PostgreSQL is running.

### Issue: "Health check failed"
**Solution:**
- App might be crashing on startup
- Check logs for specific error
- Verify all REQUIRED variables are set

---

## Production Best Practices

1. **Never commit secrets** to Git (use Railway environment variables)
2. **Use strong random secrets** (at least 32 characters)
3. **Set ENV=production** in Railway
4. **Monitor logs** regularly for errors
5. **Set up alerts** for failed deployments
6. **Backup database** regularly (Railway provides automated backups)

---

## Next Steps After Successful Deployment

1. ✅ Verify health endpoint works
2. ✅ Test user registration and login
3. ✅ Test OAuth flows (Facebook, TikTok)
4. ✅ Configure webhooks for real-time updates
5. ✅ Set up monitoring and logging
6. ✅ Configure custom domain (optional)

---

## Contact Information

- Railway Docs: https://docs.railway.app
- Project Issues: https://github.com/kasing213/facebook-tiktok-automation/issues
