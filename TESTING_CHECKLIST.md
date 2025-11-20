# 🧪 Testing Checklist - Frontend Authentication

## ⚡ Quick Start (5 minutes)

### ✅ Step 1: Create Test Tenant in Supabase

**Time:** 2 minutes

1. Open [Supabase Dashboard](https://supabase.com/dashboard)
2. Go to **SQL Editor** → **New Query**
3. Copy paste from [supabase_create_test_tenant.sql](supabase_create_test_tenant.sql)
4. Click **Run** (Ctrl+Enter)
5. ✅ Verify you see: `Test Organization` created

---

### ✅ Step 2: Test Registration

**Time:** 1 minute

1. Open: https://facebooktiktokautomation.vercel.app
2. Click **"Get Started"** or **"Sign Up"**
3. Fill form:
   ```
   📧 Email:    test@example.com
   👤 Username: testuser
   🔒 Password: testpassword123
   ✅ Confirm:  testpassword123
   ```
4. Click **"REGISTER"**
5. ✅ See: "Account created successfully!"
6. ✅ Auto-redirect to login

---

### ✅ Step 3: Test Login

**Time:** 30 seconds

1. Enter credentials:
   ```
   👤 Username: testuser
   🔒 Password: testpassword123
   ```
2. Click **"LOG IN"**
3. ✅ Redirect to **Dashboard**
4. ✅ See OAuth connection buttons

---

### ✅ Step 4: Verify in Database

**Time:** 1 minute

Run in Supabase SQL Editor:

```sql
-- Check tenant exists
SELECT id, name, slug FROM tenant;

-- Check user was created
SELECT id, username, email, role FROM "user";
```

✅ You should see:
- 1 tenant: "Test Organization"
- 1 user: "testuser" with "test@example.com"

---

## 🔍 Extended Testing (Optional)

### Test Multiple Users

1. Logout (or open incognito)
2. Register second user:
   ```
   Email:    user2@example.com
   Username: testuser2
   Password: password12345678
   ```
3. ✅ Both users should have same `tenant_id`

### Test Invalid Inputs

**Registration:**
- ❌ Short password (< 8 chars) → "Password must be at least 8 characters"
- ❌ Passwords don't match → "Passwords do not match"
- ❌ Invalid email → "Please enter a valid email"
- ❌ Missing fields → Appropriate error messages

**Login:**
- ❌ Wrong password → "Login failed"
- ❌ Non-existent user → "Login failed"

### Test Protected Routes

1. Logout (clear token)
2. Try to access: https://facebooktiktokautomation.vercel.app/dashboard
3. ✅ Should redirect to `/login`

---

## 📊 Check Backend Logs

```bash
railway logs
```

**Success Pattern:**
```
✅ GET  /api/tenants HTTP/1.1 200 OK
✅ POST /auth/register HTTP/1.1 201 Created
✅ POST /auth/login HTTP/1.1 200 OK
✅ GET  /auth/me HTTP/1.1 200 OK
```

**Error Pattern:**
```
❌ 422 Unprocessable Entity → Check request format
❌ 401 Unauthorized         → Check credentials
❌ 404 Not Found            → Check endpoint exists
```

---

## 🐛 Common Issues & Fixes

### Issue: "No tenants available"
**Fix:** Run Step 1 again (create tenant in Supabase)

### Issue: "Registration failed: 422"
**Fix:** Check Railway logs for details
- Ensure email is valid format
- Ensure password is 8+ characters
- Check tenant_id is being sent

### Issue: "Login failed: 401"
**Fix:**
- Verify user exists in database
- Check password is correct (case-sensitive)
- Ensure you registered successfully first

### Issue: CORS error
**Fix:** Check Railway environment variable:
```bash
railway variables | grep FRONTEND_URL
```
Should include: `https://facebooktiktokautomation.vercel.app`

---

## ✅ Success Criteria

Mark each as complete:

- [ ] Tenant created in Supabase ✓
- [ ] Registration works (201 response) ✓
- [ ] Login works (200 response) ✓
- [ ] Dashboard accessible after login ✓
- [ ] Protected routes redirect when not logged in ✓
- [ ] User data visible in Supabase ✓
- [ ] Backend logs show success messages ✓

---

## 🎉 All Tests Passed?

Congratulations! Your authentication system is working perfectly!

### Next Steps:

1. **Test OAuth Integration**
   - Add Facebook credentials to Railway
   - Test Facebook connection from dashboard
   - Verify token stored in `ad_token` table

2. **Test TikTok OAuth**
   - Add TikTok credentials
   - Connect TikTok account
   - Verify token storage

3. **Production Deployment**
   - Configure production environment variables
   - Set up monitoring
   - Enable SSL/HTTPS

---

## 📚 Additional Resources

- [SUPABASE_TESTING_GUIDE.md](SUPABASE_TESTING_GUIDE.md) - Detailed testing guide
- [QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md) - Troubleshooting guide
- [FRONTEND_IMPLEMENTATION.md](FRONTEND_IMPLEMENTATION.md) - Implementation details
- [CLAUDE.md](CLAUDE.md) - Project overview

---

**Total Time:** ~5 minutes
**Status:** Ready to test!
**Last Updated:** 2025-11-20
