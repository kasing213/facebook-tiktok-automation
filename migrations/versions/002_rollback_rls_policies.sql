-- Rollback: Disable Row Level Security (RLS) for all tables
-- Description: Removes RLS policies and disables RLS
-- WARNING: This will remove tenant isolation at the database level

-- ============================================================================
-- STEP 1: Drop all RLS policies
-- ============================================================================

-- Tenant table policies
DROP POLICY IF EXISTS tenant_select_policy ON tenant;
DROP POLICY IF EXISTS tenant_insert_policy ON tenant;
DROP POLICY IF EXISTS tenant_update_policy ON tenant;
DROP POLICY IF EXISTS tenant_delete_policy ON tenant;

-- User table policies
DROP POLICY IF EXISTS user_select_policy ON "user";
DROP POLICY IF EXISTS user_insert_policy ON "user";
DROP POLICY IF EXISTS user_update_policy ON "user";
DROP POLICY IF EXISTS user_delete_policy ON "user";

-- Ad token table policies
DROP POLICY IF EXISTS ad_token_select_policy ON ad_token;
DROP POLICY IF EXISTS ad_token_insert_policy ON ad_token;
DROP POLICY IF EXISTS ad_token_update_policy ON ad_token;
DROP POLICY IF EXISTS ad_token_delete_policy ON ad_token;

-- Destination table policies
DROP POLICY IF EXISTS destination_select_policy ON destination;
DROP POLICY IF EXISTS destination_insert_policy ON destination;
DROP POLICY IF EXISTS destination_update_policy ON destination;
DROP POLICY IF EXISTS destination_delete_policy ON destination;

-- Automation table policies
DROP POLICY IF EXISTS automation_select_policy ON automation;
DROP POLICY IF EXISTS automation_insert_policy ON automation;
DROP POLICY IF EXISTS automation_update_policy ON automation;
DROP POLICY IF EXISTS automation_delete_policy ON automation;

-- Automation run table policies
DROP POLICY IF EXISTS automation_run_select_policy ON automation_run;
DROP POLICY IF EXISTS automation_run_insert_policy ON automation_run;
DROP POLICY IF EXISTS automation_run_update_policy ON automation_run;
DROP POLICY IF EXISTS automation_run_delete_policy ON automation_run;

-- ============================================================================
-- STEP 2: Disable RLS on all tables
-- ============================================================================

ALTER TABLE tenant DISABLE ROW LEVEL SECURITY;
ALTER TABLE "user" DISABLE ROW LEVEL SECURITY;
ALTER TABLE ad_token DISABLE ROW LEVEL SECURITY;
ALTER TABLE destination DISABLE ROW LEVEL SECURITY;
ALTER TABLE automation DISABLE ROW LEVEL SECURITY;
ALTER TABLE automation_run DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- STEP 3: Drop helper functions
-- ============================================================================

DROP FUNCTION IF EXISTS public.get_tenant_id();
DROP FUNCTION IF EXISTS public.set_tenant_context(UUID);

-- ============================================================================
-- STEP 4: Revoke permissions
-- ============================================================================

-- Permissions are automatically revoked when functions are dropped

-- ============================================================================
-- NOTES:
-- ============================================================================
-- RLS has been disabled. Your database is no longer protected by row-level
-- tenant isolation. Use this only for testing or if reverting changes.
-- ============================================================================
