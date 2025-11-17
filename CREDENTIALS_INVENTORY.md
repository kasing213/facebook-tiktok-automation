# Credentials Inventory - Railway Deployment

## ✅ CREDENTIALS YOU HAVE (Ready to Deploy)

### 1. Database
- ✅ `DATABASE_URL` - Supabase PostgreSQL connection
  - **Value**: `postgresql://postgres:kasingchan223699.@db.wsqwoeqetggqkktkgoxo.supabase.co:5432/postgres`
  - **Status**: Ready to use in Railway

### 2. Security Keys
- ✅ `OAUTH_STATE_SECRET` - OAuth CSRF protection
  - **Current Value**: `change_me_long_random_secret_key_for_oauth_state_validation`
  - **Status**: ⚠️ Should be changed to more secure random value

- ✅ `MASTER_SECRET_KEY` - Token encryption master key
  - **Value**: `1ufwp2kU8UShokdA-TaD_kAXJGCr9OGr9Jyhza6eJ9s=`
  - **Status**: ✅ Good - Fernet key format

- ✅ `SECRET_KEY` - General application secret
  - **Value**: `HRUiqBNfMuqjTyNiG2ncpacIL6oNfkuPYUZgHLXxzQ8=`
  - **Status**: ✅ Good

### 3. Facebook/Meta Integration
- ✅ `FB_APP_ID` - Facebook App ID
  - **Value**: `1536800164835472`
  - **Status**: ✅ Ready

- ✅ `FB_APP_SECRET` - Facebook App Secret
  - **Value**: `d1bfce9e058edbb1a660cf74ecb26b2b`
  - **Status**: ✅ Ready

- ✅ `FB_SCOPES` - Facebook permissions
  - **Value**: `ads_read,pages_show_list,pages_read_engagement,business_management`
  - **Status**: ✅ Ready

- ✅ `FACEBOOK_WEBHOOK_VERIFY_TOKEN` - Webhook verification
  - **Value**: `my_fb_verify_token_change_me_in_production`
  - **Status**: ⚠️ Should be changed to secure random value

### 4. TikTok Integration
- ✅ `TIKTOK_CLIENT_KEY` - TikTok Client Key
  - **Value**: `sbawmkkkttd6nwy6yn`
  - **Status**: ✅ Ready

- ✅ `TIKTOK_CLIENT_SECRET` - TikTok Client Secret
  - **Value**: `Y22NSqJWsYiUnL11T4OoUCQgkOqxVJJQ`
  - **Status**: ✅ Ready

- ✅ `TIKTOK_SCOPES` - TikTok permissions
  - **Value**: `user.info.basic,user.info.profile,user.info.stats`
  - **Status**: ✅ Ready

- ✅ `TIKTOK_WEBHOOK_VERIFY_TOKEN` - Webhook verification
  - **Value**: `my_tt_verify_token_change_me_in_production`
  - **Status**: ⚠️ Should be changed to secure random value

### 5. Telegram Bot
- ✅ `TELEGRAM_BOT_TOKEN` - Telegram Bot API token
  - **Value**: `8331745179:AAFbjfvcXh2jiiOxiAxWGjzll37eB5WRSN0`
  - **Status**: ✅ Ready

### 6. Application Configuration
- ✅ `ENV` - Environment mode
  - **Value**: `dev` (should be `prod` for Railway)

- ✅ `BASE_URL` - Backend URL
  - **Current**: `https://ed4b0e938597.ngrok-free.app`
  - **Need**: Railway deployment URL (e.g., `https://your-app.up.railway.app`)

- ✅ `FRONTEND_URL` - Frontend URL
  - **Current**: `http://localhost:3000`
  - **Need**: Production frontend URL if deploying separately

---

## 🎯 WHAT YOU NEED TO DO FOR RAILWAY

### Option 1: Deploy with Current Credentials ✅ RECOMMENDED

**You have ALL the required credentials!** Just need to add them to Railway.

#### Steps:
1. Go to Railway Dashboard → Your Project → Variables
2. Add these environment variables:

```bash
# Core Required (7 variables needed by config.py)
DATABASE_URL=postgresql://postgres:kasingchan223699.@db.wsqwoeqetggqkktkgoxo.supabase.co:5432/postgres
OAUTH_STATE_SECRET=change_me_long_random_secret_key_for_oauth_state_validation
MASTER_SECRET_KEY=1ufwp2kU8UShokdA-TaD_kAXJGCr9OGr9Jyhza6eJ9s=
FB_APP_ID=1536800164835472
FB_APP_SECRET=d1bfce9e058edbb1a660cf74ecb26b2b
TIKTOK_CLIENT_KEY=sbawmkkkttd6nwy6yn
TIKTOK_CLIENT_SECRET=Y22NSqJWsYiUnL11T4OoUCQgkOqxVJJQ
TELEGRAM_BOT_TOKEN=8331745179:AAFbjfvcXh2jiiOxiAxWGjzll37eB5WRSN0

# Application Config
ENV=prod
BASE_URL=${{RAILWAY_PUBLIC_DOMAIN}}
FRONTEND_URL=http://localhost:3000

# Facebook Config
FB_SCOPES=ads_read,pages_show_list,pages_read_engagement,business_management
FACEBOOK_WEBHOOK_VERIFY_TOKEN=my_fb_verify_token_change_me_in_production

# TikTok Config
TIKTOK_SCOPES=user.info.basic,user.info.profile,user.info.stats
TIKTOK_WEBHOOK_VERIFY_TOKEN=my_tt_verify_token_change_me_in_production

# Optional
API_HOST=0.0.0.0
API_PORT=8000
```

3. Click "Deploy" or wait for auto-deploy

**Time to deploy**: 5 minutes ✅

---

### Option 2: Improve Security First (Recommended for Production)

#### Generate Better Secrets:

**Run this locally:**
```bash
python -c "import secrets; print('OAUTH_STATE_SECRET=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('FACEBOOK_WEBHOOK_VERIFY_TOKEN=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('TIKTOK_WEBHOOK_VERIFY_TOKEN=' + secrets.token_urlsafe(32))"
```

**Then use the generated values in Railway instead of:**
- `change_me_long_random_secret_key_for_oauth_state_validation`
- `my_fb_verify_token_change_me_in_production`
- `my_tt_verify_token_change_me_in_production`

**Time to deploy**: 10 minutes

---

## 📊 Summary

| Credential | Status | Action Needed |
|------------|--------|---------------|
| DATABASE_URL | ✅ Have it | Copy to Railway |
| OAUTH_STATE_SECRET | ⚠️ Weak | Use as-is OR generate new |
| MASTER_SECRET_KEY | ✅ Good | Copy to Railway |
| FB_APP_ID | ✅ Have it | Copy to Railway |
| FB_APP_SECRET | ✅ Have it | Copy to Railway |
| TIKTOK_CLIENT_KEY | ✅ Have it | Copy to Railway |
| TIKTOK_CLIENT_SECRET | ✅ Have it | Copy to Railway |
| TELEGRAM_BOT_TOKEN | ✅ Have it | Copy to Railway |

**Result**: 🎉 **You have 100% of required credentials!**

---

## ⚠️ SECURITY WARNINGS

### 1. Your .env file contains real credentials
**CRITICAL**: These credentials are now exposed in this file. You should:
- ✅ Verify `.env` is in `.gitignore`
- ✅ Never commit this file to GitHub
- ⚠️ Consider rotating Facebook/TikTok secrets if they were ever committed
- ⚠️ Your GitHub token is also visible (line 81)

### 2. Weak webhook tokens
The current webhook verify tokens should be replaced with secure random strings:
- Current: `my_fb_verify_token_change_me_in_production`
- Better: `Xg7k2_9pRLmN4vT8qWcZ3hYbUj5sKe1f`

### 3. BASE_URL needs updating
- Current: ngrok URL (temporary)
- Need: Railway public domain (e.g., `https://facebook-automation-production.up.railway.app`)

---

## 🚀 NEXT STEPS

### Immediate (to fix crashes):
1. ✅ **Add all 7 required variables to Railway** (see Option 1 above)
2. ✅ **Deploy and test** - app should start successfully

### Short-term (improve security):
1. Generate better webhook tokens
2. Update BASE_URL with Railway domain
3. Set ENV=prod

### Long-term (production hardening):
1. Enable SSL/HTTPS
2. Configure CORS for production frontend
3. Set up monitoring
4. Rotate sensitive credentials
5. Enable Railway's secret scanning

---

## 📝 Railway Variable Setup Script

You can copy-paste this into Railway's bulk variable editor:

```
DATABASE_URL=postgresql://postgres:kasingchan223699.@db.wsqwoeqetggqkktkgoxo.supabase.co:5432/postgres
OAUTH_STATE_SECRET=change_me_long_random_secret_key_for_oauth_state_validation
MASTER_SECRET_KEY=1ufwp2kU8UShokdA-TaD_kAXJGCr9OGr9Jyhza6eJ9s=
FB_APP_ID=1536800164835472
FB_APP_SECRET=d1bfce9e058edbb1a660cf74ecb26b2b
FB_SCOPES=ads_read,pages_show_list,pages_read_engagement,business_management
TIKTOK_CLIENT_KEY=sbawmkkkttd6nwy6yn
TIKTOK_CLIENT_SECRET=Y22NSqJWsYiUnL11T4OoUCQgkOqxVJJQ
TIKTOK_SCOPES=user.info.basic,user.info.profile,user.info.stats
TELEGRAM_BOT_TOKEN=8331745179:AAFbjfvcXh2jiiOxiAxWGjzll37eB5WRSN0
ENV=prod
FRONTEND_URL=http://localhost:3000
FACEBOOK_WEBHOOK_VERIFY_TOKEN=my_fb_verify_token_change_me_in_production
TIKTOK_WEBHOOK_VERIFY_TOKEN=my_tt_verify_token_change_me_in_production
API_HOST=0.0.0.0
API_PORT=8000
```

---

**Last Updated**: 2025-11-17
**Status**: ✅ All credentials available - Ready to deploy!
