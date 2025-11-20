# Quick Fix Guide - Registration & Login Issues

## 🔴 Issues Identified

From Railway logs:
```
INFO: "POST /auth/register HTTP/1.1" 422 Unprocessable Entity
INFO: "POST /auth/login HTTP/1.1" 401 Unauthorized
```

## ✅ Fixes Applied

### 1. **Registration Requirements Fixed** (Commit: `7e196b0`)

**Backend Requirements:**
- `tenant_id`: UUID (required)
- `email`: EmailStr (required, not optional)
- `password`: minimum 8 characters (not 6)

**Frontend Changes:**
- ✅ Added `tenant_id` field (auto-fetched from default tenant)
- ✅ Made `email` required
- ✅ Increased password minimum to 8 characters
- ✅ Created `tenant.ts` service to fetch default organization

---

## 🚀 How to Fix Backend (Create Default Tenant)

### Option 1: Using Railway CLI (Recommended)

```bash
# Connect to Railway database and create default tenant
railway run python create_default_tenant_direct.py
```

### Option 2: Using Railway Dashboard SQL Console

1. Go to Railway Dashboard → Your Project → PostgreSQL
2. Click "Query" tab
3. Run this SQL:

```sql
INSERT INTO tenant (name, slug, is_active, created_at, updated_at)
VALUES ('Default Organization', 'default', true, NOW(), NOW())
RETURNING id, name, slug;
```

### Option 3: Using psql directly

```bash
# Get your DATABASE_URL from Railway
railway variables

# Connect with psql
psql <DATABASE_URL>

# Run the insert
INSERT INTO tenant (name, slug, is_active, created_at, updated_at)
VALUES ('Default Organization', 'default', true, NOW(), NOW());
```

---

## 🧪 Test Registration After Fix

### Frontend will deploy automatically from Vercel

Once Vercel finishes building (commit `7e196b0`):

1. **Visit your Vercel URL**
2. **Click "Get Started" or "Sign Up"**
3. **Fill the form:**
   - Email: test@example.com (required now)
   - Username: testuser
   - Password: password123 (min 8 chars)
   - Confirm Password: password123

4. **Click "REGISTER"**
   - Should see: "Account created successfully!"
   - Auto-redirect to login after 2 seconds

5. **Login:**
   - Username: testuser
   - Password: password123

6. **Expected result:** Redirect to dashboard

---

## 📊 What Changed in the Code

### [frontend/src/services/tenant.ts](frontend/src/services/tenant.ts) - NEW
```typescript
// Fetches default tenant from backend
export const getDefaultTenant = async (): Promise<string> => {
  const response = await api.get<Tenant[]>('/api/tenants')
  if (response.data && response.data.length > 0) {
    return response.data[0].id
  }
  throw new Error('No tenants available')
}
```

### [frontend/src/components/RegisterPage.tsx](frontend/src/components/RegisterPage.tsx) - UPDATED
```typescript
// Now fetches tenant_id on mount
useEffect(() => {
  const fetchTenant = async () => {
    const defaultTenantId = await getDefaultTenant()
    setTenantId(defaultTenantId)
  }
  fetchTenant()
}, [])

// Updated validation
- if (password.length < 6) ❌
+ if (password.length < 8) ✅

+ if (!email) {
+   setError('Email is required')
+ }

// Now sends tenant_id to backend
await authService.register({
  tenant_id: tenantId, // ✅ Added
  username,
  password,
  email // ✅ Now required
})
```

---

## 🔍 Verify Everything Works

### Check Railway Logs
```bash
railway logs
```

**Expected logs after successful registration:**
```
INFO: "POST /auth/register HTTP/1.1" 201 Created
```

**Expected logs after successful login:**
```
INFO: "POST /auth/login HTTP/1.1" 200 OK
```

---

## ❓ Troubleshooting

### If registration still fails with 422:

1. **Check if tenant exists:**
   ```bash
   railway run python -c "
   from app.core.db import get_db
   db = next(get_db())
   result = db.execute('SELECT COUNT(*) FROM tenant')
   print(f'Tenants: {result.fetchone()[0]}')
   "
   ```

2. **Check frontend is calling `/api/tenants`:**
   - Open browser DevTools (F12)
   - Go to Network tab
   - Register → Should see GET `/api/tenants`
   - Check response has tenant data

### If login fails with 401:

1. **Check user was created:**
   ```bash
   railway run python -c "
   from app.core.db import get_db
   db = next(get_db())
   result = db.execute('SELECT username, email FROM \"user\" LIMIT 5')
   for row in result:
       print(f'User: {row[0]}, Email: {row[1]}')
   "
   ```

2. **Verify password:**
   - Make sure you're using the same password you registered with
   - Minimum 8 characters

---

## 📝 Summary

### Commits
- `7e196b0` - Fix registration requirements (tenant_id, email required, password min 8)
- `9166b42` - Fix unused variable TypeScript error
- `b3282d6` - Original frontend implementation

### Files Changed
- ✅ `frontend/src/components/RegisterPage.tsx`
- ✅ `frontend/src/services/tenant.ts` (new)

### Backend Status
- ✅ Running on Railway
- ⚠️ Needs default tenant created

### Frontend Status
- ✅ Deploying on Vercel
- ✅ Will work once backend has tenant

---

**Next Step:** Create the default tenant using one of the options above, then test registration!
