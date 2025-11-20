-- =====================================================
-- Create Test Tenant in Supabase
-- Run this in your Supabase SQL Editor
-- =====================================================

-- Step 1: Check if tenant table exists and has correct structure
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'tenant'
ORDER BY ordinal_position;

-- Step 2: Check if any tenants already exist
SELECT COUNT(*) as tenant_count FROM tenant;

-- Step 3: Create a test tenant if none exists
-- This will be the default tenant for user registration
INSERT INTO tenant (id, name, slug, is_active, settings, created_at, updated_at)
SELECT
    gen_random_uuid(),  -- Generate UUID for id
    'Test Organization',
    'test-org',
    true,
    '{}'::jsonb,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM tenant WHERE slug = 'test-org'
)
RETURNING id, name, slug, is_active, created_at;

-- Step 4: Show all tenants
SELECT
    id,
    name,
    slug,
    is_active,
    created_at,
    updated_at
FROM tenant
ORDER BY created_at DESC;

-- Step 5: Get the tenant ID (you'll need this for testing)
SELECT
    id as tenant_id,
    name,
    slug,
    '✅ Use this tenant_id for manual testing if needed' as note
FROM tenant
LIMIT 1;

-- =====================================================
-- Expected Output:
-- You should see one tenant with:
-- - name: 'Test Organization'
-- - slug: 'test-org'
-- - is_active: true
-- - A UUID for the tenant_id
-- =====================================================

-- =====================================================
-- Next Step: Create a test user (optional)
-- =====================================================
-- Uncomment the following to create a test user:

/*
-- Replace <TENANT_ID> with the tenant_id from Step 5
-- Replace <PASSWORD_HASH> with a bcrypt hash of your password

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
    '<TENANT_ID>'::uuid,  -- Replace with actual tenant_id
    'testuser',
    'test@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OfmcQ8vDGW6u',  -- Password: "testpassword123"
    false,
    'user',
    true,
    NOW(),
    NOW()
)
RETURNING id, tenant_id, username, email, role;
*/

-- =====================================================
-- Verification Queries
-- =====================================================

-- Count users
SELECT COUNT(*) as user_count FROM "user";

-- Show all users (without password hash for security)
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
ORDER BY created_at DESC
LIMIT 10;
