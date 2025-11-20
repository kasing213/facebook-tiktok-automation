# Supabase Testing Guide

## 🎯 Quick Setup for Testing

### Step 1: Create Test Tenant in Supabase

1. **Open Supabase Dashboard**
   - Go to https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor**
   - Click "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Run the SQL Script**
   - Copy and paste the content from [supabase_create_test_tenant.sql](supabase_create_test_tenant.sql)
   - Click "Run" or press `Ctrl+Enter`

4. **Verify Tenant Created**
   - You should see output showing:
     - tenant_id (UUID)
     - name: "Test Organization"
     - slug: "test-org"
   - **Save this tenant_id** - you'll need it if testing manually

---

## 🧪 Test Registration Flow (Recommended)

### Option A: Test via Frontend (Easiest)

1. **Visit your Vercel URL**
   ```
   https://facebooktiktokautomation.vercel.app
   ```

2. **Click "Get Started" or "Sign Up"**

3. **Fill the registration form:**
   ```
   Email:    test@example.com
   Username: testuser
   Password: testpassword123  (min 8 chars)
   Confirm:  testpassword123
   ```

4. **Click "REGISTER"**
   - Should see: ✅ "Account created successfully!"
   - Auto-redirect to login page

5. **Login with the credentials:**
   ```
   Username: testuser
   Password: testpassword123
   ```

6. **Expected Result:**
   - ✅ Redirect to dashboard
   - ✅ Can see OAuth connection options

---

## 🔍 Verify in Supabase

### Check if User Was Created

Run this in Supabase SQL Editor:

```sql
-- Show all users
SELECT
    id,
    tenant_id,
    username,
    email,
    role,
    is_active,
    email_verified,
    created_at
FROM "user"
ORDER BY created_at DESC;
```

**Expected Output:**
```
id        | tenant_id | username  | email              | role | is_active | email_verified
----------|-----------|-----------|--------------------|----- |-----------|---------------
<uuid>    | <uuid>    | testuser  | test@example.com   | user | true      | false
```

---

## 🔧 Manual Testing (Advanced)

If you want to create a test user manually without using the frontend:

### Step 1: Get Tenant ID

```sql
SELECT id FROM tenant LIMIT 1;
```

### Step 2: Generate Password Hash

The password "testpassword123" has this bcrypt hash:
```
$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OfmcQ8vDGW6u
```

Or generate a new one with Python:
```python
from passlib.hash import bcrypt
print(bcrypt.hash("your-password-here"))
```

### Step 3: Insert Test User

```sql
INSERT INTO "user" (
    tenant_id,
    username,
    email,
    password_hash,
    email_verified,
    role,
    is_active,
    created_at,
    updated_at
)
VALUES (
    '<TENANT_ID>'::uuid,  -- Replace with tenant_id from Step 1
    'manualuser',
    'manual@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OfmcQ8vDGW6u',
    false,
    'user',
    true,
    NOW(),
    NOW()
)
RETURNING id, username, email;
```

---

## 📊 Check Railway/Backend Logs

After testing registration/login, check the logs:

```bash
railway logs
```

**Success Logs:**
```
✅ POST /api/tenants HTTP/1.1 200 OK
✅ POST /auth/register HTTP/1.1 201 Created
✅ POST /auth/login HTTP/1.1 200 OK
```

**Error Logs (if something fails):**
```
❌ POST /auth/register HTTP/1.1 422 Unprocessable Entity  → Check request body
❌ POST /auth/login HTTP/1.1 401 Unauthorized            → Check password
❌ POST /api/tenants HTTP/1.1 404 Not Found              → Create tenant first
```

---

## 🐛 Troubleshooting

### Issue 1: "No tenants available"

**Cause:** Frontend can't fetch tenant from `/api/tenants`

**Fix:**
1. Verify tenant exists in Supabase:
   ```sql
   SELECT COUNT(*) FROM tenant;
   ```
2. Check Railway backend is connected to correct database
3. Check backend logs for errors

### Issue 2: "Registration failed: 422"

**Cause:** Request body doesn't match backend requirements

**Debug:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Look for POST to `/auth/register`
4. Check Request Payload:
   ```json
   {
     "tenant_id": "uuid-here",
     "username": "testuser",
     "email": "test@example.com",
     "password": "testpassword123"
   }
   ```
5. All fields should be present and valid

### Issue 3: "Login failed: 401"

**Cause:** Wrong password or user doesn't exist

**Debug:**
1. Check user exists in Supabase:
   ```sql
   SELECT username, email FROM "user" WHERE username = 'testuser';
   ```
2. Verify you're using the correct password
3. Try resetting password in database (see Manual Testing section)

### Issue 4: CORS Error

**Cause:** Backend not allowing requests from Vercel domain

**Fix:**
Check Railway environment variable `FRONTEND_URL`:
```bash
railway variables
```

Should include:
```
FRONTEND_URL=https://facebooktiktokautomation.vercel.app
```

---

## ✅ Success Criteria

After running the tests, you should have:

- ✅ Tenant created in Supabase
- ✅ User registered via frontend
- ✅ User can login successfully
- ✅ User redirected to dashboard
- ✅ Backend logs show 200/201 responses
- ✅ Data visible in Supabase tables

---

## 🎉 Next Steps After Successful Testing

1. **Test OAuth Connections**
   - Login to dashboard
   - Click "Connect Facebook"
   - Go through OAuth flow
   - Verify token stored in `ad_token` table

2. **Test Multi-User**
   - Register second user
   - Verify tenant isolation

3. **Test API Endpoints**
   - GET `/auth/me` - Get current user
   - GET `/api/tenants/{tenant_id}/auth-status` - Check OAuth status

4. **Setup Production**
   - Add real OAuth credentials to Railway
   - Configure production database
   - Set up monitoring

---

## 📝 Quick Reference

### Important Tables
- `tenant` - Organizations
- `user` - User accounts
- `ad_token` - OAuth tokens
- `destination` - Notification targets
- `automation` - Scheduled tasks

### Important Endpoints
- `POST /auth/register` - Create user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user
- `GET /api/tenants` - List tenants
- `GET /api/tenants/{id}/auth-status` - OAuth status

### Environment Variables (Railway)
- `DATABASE_URL` - Supabase connection string
- `FRONTEND_URL` - Vercel URL for CORS
- `MASTER_SECRET_KEY` - Token encryption key
- `OAUTH_STATE_SECRET` - OAuth CSRF protection

---

**Last Updated:** 2025-11-20
**Status:** ✅ Ready for Testing
