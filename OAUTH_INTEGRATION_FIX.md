# OAuth Integration Fix

## 🐛 Problem Identified

OAuth buttons on Dashboard were not working because:
1. **Missing `tenant_id`** - Dashboard component didn't have the tenant_id needed for OAuth flows
2. **Login flow incomplete** - After login, user was redirected to Dashboard without passing tenant_id

## 🔍 Root Cause

### Login Flow Before Fix:
```
User logs in
  ↓
Backend returns JWT token (contains tenant_id in claims)
  ↓
Frontend stores token in localStorage
  ↓
Frontend redirects to /dashboard
  ↓
Dashboard: tenant_id = undefined ❌
  ↓
OAuth buttons can't initiate (need tenant_id parameter)
```

### OAuth Endpoint Requirements:
- **Facebook OAuth**: `GET /auth/facebook/authorize?tenant_id=<UUID>`
- **TikTok OAuth**: `GET /auth/tiktok/authorize?tenant_id=<UUID>`

Both require `tenant_id` as a query parameter to associate the OAuth token with the correct organization.

## ✅ Solution Applied

### Updated Login Flow:
```
User logs in
  ↓
Backend returns JWT token
  ↓
Frontend stores token
  ↓
Frontend calls GET /auth/me (uses JWT from localStorage)
  ↓
Backend returns user info including tenant_id
  ↓
Frontend redirects to /dashboard with tenant_id in state
  ↓
Dashboard: tenant_id = <UUID> ✅
  ↓
OAuth buttons work! Can initiate Facebook/TikTok OAuth
```

### Code Changes:

#### [frontend/src/components/LoginPageNew.tsx](frontend/src/components/LoginPageNew.tsx)

**Before:**
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  // ...
  await authService.login({ username, password })
  navigate('/dashboard')  // ❌ No tenant_id
}
```

**After:**
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  // ...
  await authService.login({ username, password })
  // Get user info to extract tenant_id
  const user = await authService.getCurrentUser()  // ✅ Fetch user info
  // Redirect to dashboard with tenant_id
  navigate('/dashboard', {
    state: { tenantId: user.tenant_id }  // ✅ Pass tenant_id
  })
}
```

## 📊 How It Works Now

### 1. User Authentication Flow:
```
POST /auth/login
  ├─ Username: testuser
  ├─ Password: testpassword123
  └─ Response: { access_token: "eyJ..." }
       ↓
GET /auth/me (with Authorization: Bearer eyJ...)
  └─ Response: {
       id: "user-uuid",
       tenant_id: "1bdbca28-46a1-4102-8686-a6e93ecd9052",  ← This!
       username: "testuser",
       email: "test@example.com",
       role: "user"
     }
       ↓
Navigate to /dashboard with state: { tenantId: "1bdbca28-..." }
```

### 2. OAuth Initiation Flow:
```
Dashboard component receives tenantId from navigation state
  ↓
User clicks "Connect Facebook"
  ↓
handleConnectFacebook() calls:
  authService.initiateFacebookOAuth(tenantId)
  ↓
Frontend redirects to:
  https://web-production-3ed15.up.railway.app/auth/facebook/authorize?tenant_id=1bdbca28-...
  ↓
Backend generates Facebook OAuth URL with state parameter
  ↓
Redirects user to Facebook for authorization
  ↓
Facebook redirects back to:
  /auth/facebook/callback?code=...&state=...
  ↓
Backend stores token and redirects to frontend:
  https://facebooktiktokautomation.vercel.app/dashboard?tenant_id=...&success=facebook
  ↓
Dashboard shows success message and refreshes auth status
```

## 🧪 Testing After Fix

### Step 1: Login
1. Go to: https://facebooktiktokautomation.vercel.app/login
2. Login with:
   - Username: `testuser`
   - Password: `testpassword123`
3. ✅ Should redirect to Dashboard

### Step 2: Verify Tenant ID Passed
1. Open DevTools (F12) → **Network** tab
2. Look for `GET /auth/me` request
3. Check response contains `tenant_id`
4. Dashboard should show Platform Cards (Facebook/TikTok)

### Step 3: Test OAuth Buttons
1. Click "Connect Facebook" button
2. Should redirect to Railway backend OAuth URL
3. Check URL contains `tenant_id` parameter
4. If Facebook credentials configured: redirects to Facebook
5. If not configured: shows error from backend

## 📝 Related Files

| File | Change | Purpose |
|------|--------|---------|
| [LoginPageNew.tsx](frontend/src/components/LoginPageNew.tsx) | Added getCurrentUser() call | Fetch tenant_id after login |
| [Dashboard.tsx](frontend/src/components/Dashboard.tsx) | Already receives state | Extract tenant_id from navigation state |
| [api.ts](frontend/src/services/api.ts) | No change needed | OAuth methods already expect tenant_id |

## 🔗 Backend OAuth Endpoints

| Platform | Authorize URL | Callback URL |
|----------|--------------|--------------|
| Facebook | `/auth/facebook/authorize?tenant_id=<UUID>` | `/auth/facebook/callback` |
| TikTok | `/auth/tiktok/authorize?tenant_id=<UUID>` | `/auth/tiktok/callback` |

Both endpoints:
- **Require**: `tenant_id` query parameter
- **Return**: Redirect to platform OAuth page
- **Callback**: Stores token in database, redirects to frontend with success

## ⚙️ Required Environment Variables

### Railway Backend:
```bash
# OAuth Credentials (required for OAuth to work)
FB_APP_ID=<your-facebook-app-id>
FB_APP_SECRET=<your-facebook-app-secret>
TIKTOK_CLIENT_KEY=<your-tiktok-client-key>
TIKTOK_CLIENT_SECRET=<your-tiktok-client-secret>

# OAuth Configuration
BASE_URL=https://web-production-3ed15.up.railway.app
FRONTEND_URL=https://facebooktiktokautomation.vercel.app
OAUTH_STATE_SECRET=<your-state-secret>
```

### Vercel Frontend:
```bash
VITE_API_URL=https://web-production-3ed15.up.railway.app
```

## 🚨 Important Notes

1. **OAuth credentials required**: OAuth flows won't work without Facebook/TikTok app credentials in Railway
2. **Redirect URIs**: Must be configured in Facebook/TikTok developer consoles
3. **CORS**: Backend must allow Vercel domain in FRONTEND_URL
4. **HTTPS required**: OAuth flows require HTTPS (Railway provides this automatically)

## 🎯 Next Steps

1. **Wait for Vercel deployment** (~2 minutes)
2. **Test login** → should redirect to dashboard with tenant_id
3. **Test OAuth buttons** → should redirect to OAuth authorization pages
4. **Configure OAuth apps** (if not already done):
   - Set up Facebook App with redirect URI
   - Set up TikTok App with redirect URI
   - Add credentials to Railway environment variables

---

**Status:** ✅ Fixed - Vercel deploying
**Commit:** c0d6448
**Deployment:** https://facebooktiktokautomation.vercel.app
