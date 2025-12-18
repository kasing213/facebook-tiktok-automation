# Row Level Security (RLS) Implementation Guide

## 🔒 What is RLS?

Row Level Security (RLS) is a PostgreSQL feature that restricts which rows users can access in database tables. For your multi-tenant application, RLS ensures that:

- **Tenant A cannot see Tenant B's data**
- **Users can only access their own tenant's resources**
- **Database-level security prevents data leaks**

## 🚨 Current Security Issues

Your Supabase database currently has **7 critical security warnings**:
- ❌ RLS Disabled on `public.ad_token`
- ❌ RLS Disabled on `public.alembic_version`
- ❌ RLS Disabled on `public.automation_run`
- ❌ RLS Disabled on `public.automation`
- ❌ RLS Disabled on `public.destination`
- ❌ RLS Disabled on `public.tenant`
- ❌ RLS Disabled on `public.user`

**Risk:** Without RLS, anyone with database access can query ALL tenant data.

## 📋 What This Migration Does

### Tables Protected
1. **tenant** - Only view your own tenant
2. **user** - Only see users in your tenant
3. **ad_token** - Isolated Facebook/TikTok tokens per tenant
4. **destination** - Tenant-specific destinations
5. **automation** - Tenant-specific automations
6. **automation_run** - Runs belong to tenant's automations

### Table NOT Protected
- **alembic_version** - Migration tracking (intentionally skipped)

### Security Functions Created
- `auth.get_tenant_id()` - Extracts tenant_id from JWT or session
- `auth.set_tenant_context()` - For testing/development

## 🚀 How to Apply RLS

### Option 1: Using Python Script (Recommended)

```bash
# 1. Make sure your .env has database credentials
# 2. Run the migration script
python apply_rls_migration.py
```

The script will:
- Connect to your Supabase database
- Show what will change
- Ask for confirmation
- Apply all RLS policies
- Verify RLS is enabled

### Option 2: Manual SQL Execution

1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `migrations/versions/002_enable_rls_policies.sql`
3. Paste and execute
4. Verify in Table Editor that RLS warnings are gone

## ⚙️ Backend Configuration

### Important: Use Service Role Key

Your FastAPI backend must use the **service_role** key to bypass RLS:

```python
# app/core/database.py
from supabase import create_client
import os

# Use SERVICE_ROLE_KEY for backend operations
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # ⚠️ NOT anon key!
)
```

### Why Service Role?

- **Anon Key**: Respects RLS policies (for frontend)
- **Service Role**: Bypasses RLS (for backend admin operations)

Your backend already validates tenant_id in the application layer, so it's safe to use service_role.

## 🧪 Testing RLS

### Test 1: Verify RLS is Enabled

```sql
-- Run in Supabase SQL Editor
SELECT
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('tenant', 'user', 'ad_token', 'destination', 'automation', 'automation_run');
```

Expected: `rowsecurity` = `true` for all tables

### Test 2: Test Tenant Isolation

```sql
-- Set tenant context (simulating user logged in as tenant X)
SELECT auth.set_tenant_context('129ce388-9d85-44fb-a815-6c4cf6a1d010');

-- Try to query users (should only see users from this tenant)
SELECT id, username, tenant_id FROM "user";

-- Switch to another tenant
SELECT auth.set_tenant_context('1fbe5b4c-2eff-4db1-8fd5-d9a8238e2d55');

-- Query again (should see different users)
SELECT id, username, tenant_id FROM "user";
```

### Test 3: API Endpoint Testing

```bash
# Test login and data access
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# Use the token to access tenant-specific data
curl http://localhost:8000/api/v1/automations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔄 How It Works

### Flow Diagram

```
┌─────────────┐
│   Frontend  │
│  (React)    │
└──────┬──────┘
       │ JWT with tenant_id
       ▼
┌─────────────┐
│   Backend   │
│  (FastAPI)  │ ← Uses service_role key (bypasses RLS)
└──────┬──────┘
       │ Validates tenant_id
       ▼
┌─────────────┐
│  Supabase   │
│  Database   │ ← RLS enabled (protects direct access)
└─────────────┘
```

### Key Points

1. **Frontend → Backend**: JWT contains `tenant_id`
2. **Backend Validates**: Checks user belongs to tenant
3. **Backend → Database**: Uses service_role (bypasses RLS)
4. **Direct Database Access**: RLS blocks unauthorized queries

## 🔙 Rollback (If Needed)

If something goes wrong:

```sql
-- Execute in Supabase SQL Editor
\i migrations/versions/002_rollback_rls_policies.sql
```

Or via psql:
```bash
psql $DATABASE_URL -f migrations/versions/002_rollback_rls_policies.sql
```

## ⚠️ Important Warnings

### Before Applying

1. **Backup your database** (Supabase → Database → Backups)
2. **Test in development first** (don't apply to production directly)
3. **Ensure service_role key is configured** in your backend

### After Applying

1. **Test all API endpoints** - make sure CRUD operations work
2. **Verify tenant isolation** - users can't see other tenant's data
3. **Check for errors** in Supabase logs
4. **Monitor performance** - RLS adds overhead (usually negligible)

## 🐛 Troubleshooting

### Problem: "permission denied" errors

**Solution**: Make sure your backend uses `SUPABASE_SERVICE_ROLE_KEY`, not `SUPABASE_ANON_KEY`

### Problem: Can't see any data

**Solution**: Check that `tenant_id` is properly set in JWT claims or session

### Problem: RLS still showing as disabled

**Solution**: Refresh Supabase dashboard, or run verification query

### Problem: Application stopped working

**Solution**: Apply rollback script immediately:
```sql
\i migrations/versions/002_rollback_rls_policies.sql
```

## 📚 Additional Resources

- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Supabase RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Multi-tenant Security Best Practices](https://supabase.com/docs/guides/database/multi-tenancy)

## ✅ Checklist

- [ ] Backup database
- [ ] Review migration SQL file
- [ ] Confirm service_role key is in .env
- [ ] Apply RLS migration
- [ ] Verify RLS is enabled (check dashboard)
- [ ] Test API endpoints
- [ ] Test tenant isolation
- [ ] Monitor for errors
- [ ] Celebrate 🎉 (your database is now secure!)

## 🆘 Need Help?

If you encounter issues:
1. Check Supabase logs (Dashboard → Logs)
2. Review FastAPI logs (`uvicorn` output)
3. Test with rollback script first
4. Contact support with specific error messages

---

**Last Updated**: 2025-12-08
**Migration Version**: 002_enable_rls_policies
