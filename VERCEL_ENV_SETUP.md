# Vercel Environment Variable Setup

## 🚨 Critical Fix: Backend Connection

Your frontend on Vercel needs to know where your Railway backend is located.

## ✅ Automatic Setup (via .env.production)

The file `frontend/.env.production` has been created with:
```
VITE_API_URL=https://web-production-3ed15.up.railway.app
```

This will be automatically used by Vercel on the next deployment.

## 🔧 Manual Setup (Vercel Dashboard)

If the automatic setup doesn't work, configure it manually:

### Step 1: Go to Vercel Dashboard
1. Visit: https://vercel.com/dashboard
2. Select your project: `facebooktiktokautomation`
3. Go to **Settings** → **Environment Variables**

### Step 2: Add Environment Variable

| Field | Value |
|-------|-------|
| **Key** | `VITE_API_URL` |
| **Value** | `https://web-production-3ed15.up.railway.app` |
| **Environment** | ✅ Production ✅ Preview ✅ Development |

### Step 3: Redeploy
1. Go to **Deployments** tab
2. Click the three dots on the latest deployment
3. Click **Redeploy**
4. Check "Use existing build cache" → **Redeploy**

---

## 🧪 Verify It Works

After redeployment, test:

1. **Visit**: https://facebooktiktokautomation.vercel.app/register
2. Open browser DevTools (F12) → **Console** tab
3. Look for: `[API] Base URL configured as: https://web-production-3ed15.up.railway.app`
4. Try registration → Should work now!

---

## 🔍 Troubleshooting

### Issue: Still seeing "Network Error"

**Check console output:**
```javascript
[API] Base URL configured as: http://localhost:8000  ❌ WRONG
[API] Base URL configured as: https://web-production-3ed15.up.railway.app  ✅ CORRECT
```

**If showing localhost:**
1. Verify `.env.production` file exists in `frontend/` folder
2. Check Vercel environment variables are set correctly
3. Force redeploy (don't use cache)

### Issue: CORS Error

**Error message:** `Access to XMLHttpRequest at 'https://web-production-3ed15.up.railway.app' from origin 'https://facebooktiktokautomation.vercel.app' has been blocked by CORS policy`

**Fix:**
Check Railway environment variable `FRONTEND_URL` includes your Vercel domain:
```bash
railway variables | grep FRONTEND_URL
```

Should show:
```
FRONTEND_URL=https://facebooktiktokautomation.vercel.app
```

---

## 📊 Current Configuration

| Service | URL | Status |
|---------|-----|--------|
| Frontend (Vercel) | https://facebooktiktokautomation.vercel.app | ✅ Deployed |
| Backend (Railway) | https://web-production-3ed15.up.railway.app | ✅ Deployed |
| Database (Supabase) | (connection string in Railway) | ✅ Connected |

---

**Next Steps After Fix:**
1. Commit `.env.production` → triggers Vercel redeploy
2. Wait ~2 minutes for build
3. Test registration at https://facebooktiktokautomation.vercel.app/register
4. Test login
5. Test OAuth buttons (Facebook/TikTok)

---

**Last Updated:** 2025-11-20
**Status:** Ready to deploy
