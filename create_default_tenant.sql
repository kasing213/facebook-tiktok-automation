-- Create default tenant for user registration
-- Run this in Railway PostgreSQL Query console

-- Check if tenant already exists
SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM tenant LIMIT 1)
        THEN 'Tenant already exists'
        ELSE 'No tenant found'
    END as status;

-- Create tenant if it doesn't exist
INSERT INTO tenant (name, slug, is_active, created_at, updated_at)
SELECT 'Default Organization', 'default', true, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM tenant WHERE slug = 'default');

-- Show the result
SELECT id, name, slug, is_active, created_at
FROM tenant
ORDER BY created_at DESC
LIMIT 1;
