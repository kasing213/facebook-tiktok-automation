-- Migration: Enable Row Level Security (RLS) for all tables
-- Description: Implements tenant isolation at the database level
-- WARNING: This will restrict access to data based on user context

-- ============================================================================
-- STEP 1: Enable RLS on all tables
-- ============================================================================

ALTER TABLE tenant ENABLE ROW LEVEL SECURITY;
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_token ENABLE ROW LEVEL SECURITY;
ALTER TABLE destination ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_run ENABLE ROW LEVEL SECURITY;
-- Note: alembic_version table should NOT have RLS enabled (migration tracking)

-- ============================================================================
-- STEP 2: Create helper function to get current tenant_id from JWT/session
-- ============================================================================

-- This function extracts the tenant_id from the current user's JWT token
-- Supabase stores JWT claims in current_setting('request.jwt.claims')
-- For local development, you can set this via SET LOCAL
CREATE OR REPLACE FUNCTION public.get_tenant_id()
RETURNS UUID AS $$
DECLARE
  tenant_id_claim TEXT;
BEGIN
  -- Try to get tenant_id from JWT claims (production)
  tenant_id_claim := current_setting('request.jwt.claims', true)::json->>'tenant_id';

  -- If not in JWT, try session variable (development/testing)
  IF tenant_id_claim IS NULL THEN
    tenant_id_claim := current_setting('app.current_tenant_id', true);
  END IF;

  -- Return as UUID or NULL
  RETURN tenant_id_claim::UUID;
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- ============================================================================
-- STEP 3: Create RLS Policies for TENANT table
-- ============================================================================

-- Policy: Users can only view their own tenant
CREATE POLICY tenant_select_policy ON tenant
  FOR SELECT
  USING (id = public.get_tenant_id());

-- Policy: Only admins can insert tenants (handled at application level)
-- For now, disable INSERT via RLS (handle via service role)
CREATE POLICY tenant_insert_policy ON tenant
  FOR INSERT
  WITH CHECK (false);

-- Policy: Users can update their own tenant (admin role check at app level)
CREATE POLICY tenant_update_policy ON tenant
  FOR UPDATE
  USING (id = public.get_tenant_id())
  WITH CHECK (id = public.get_tenant_id());

-- Policy: Prevent tenant deletion via RLS (handle via service role only)
CREATE POLICY tenant_delete_policy ON tenant
  FOR DELETE
  USING (false);

-- ============================================================================
-- STEP 4: Create RLS Policies for USER table
-- ============================================================================

-- Policy: Users can only view users within their tenant
CREATE POLICY user_select_policy ON "user"
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

-- Policy: Users can be created within the current tenant
CREATE POLICY user_insert_policy ON "user"
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

-- Policy: Users can update users within their tenant
CREATE POLICY user_update_policy ON "user"
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

-- Policy: Users can delete users within their tenant (admin check at app level)
CREATE POLICY user_delete_policy ON "user"
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- STEP 5: Create RLS Policies for AD_TOKEN table
-- ============================================================================

-- Policy: Users can only view ad tokens for their tenant
CREATE POLICY ad_token_select_policy ON ad_token
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

-- Policy: Users can create ad tokens for their tenant
CREATE POLICY ad_token_insert_policy ON ad_token
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

-- Policy: Users can update ad tokens for their tenant
CREATE POLICY ad_token_update_policy ON ad_token
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

-- Policy: Users can delete ad tokens for their tenant
CREATE POLICY ad_token_delete_policy ON ad_token
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- STEP 6: Create RLS Policies for DESTINATION table
-- ============================================================================

-- Policy: Users can only view destinations for their tenant
CREATE POLICY destination_select_policy ON destination
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

-- Policy: Users can create destinations for their tenant
CREATE POLICY destination_insert_policy ON destination
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

-- Policy: Users can update destinations for their tenant
CREATE POLICY destination_update_policy ON destination
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

-- Policy: Users can delete destinations for their tenant
CREATE POLICY destination_delete_policy ON destination
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- STEP 7: Create RLS Policies for AUTOMATION table
-- ============================================================================

-- Policy: Users can only view automations for their tenant
CREATE POLICY automation_select_policy ON automation
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

-- Policy: Users can create automations for their tenant
CREATE POLICY automation_insert_policy ON automation
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

-- Policy: Users can update automations for their tenant
CREATE POLICY automation_update_policy ON automation
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

-- Policy: Users can delete automations for their tenant
CREATE POLICY automation_delete_policy ON automation
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- STEP 8: Create RLS Policies for AUTOMATION_RUN table
-- ============================================================================

-- Policy: Users can only view automation runs for their tenant's automations
CREATE POLICY automation_run_select_policy ON automation_run
  FOR SELECT
  USING (
    automation_id IN (
      SELECT id FROM automation WHERE tenant_id = public.get_tenant_id()
    )
  );

-- Policy: Automation runs can be created for tenant's automations
CREATE POLICY automation_run_insert_policy ON automation_run
  FOR INSERT
  WITH CHECK (
    automation_id IN (
      SELECT id FROM automation WHERE tenant_id = public.get_tenant_id()
    )
  );

-- Policy: Users can update automation runs for their tenant's automations
CREATE POLICY automation_run_update_policy ON automation_run
  FOR UPDATE
  USING (
    automation_id IN (
      SELECT id FROM automation WHERE tenant_id = public.get_tenant_id()
    )
  )
  WITH CHECK (
    automation_id IN (
      SELECT id FROM automation WHERE tenant_id = public.get_tenant_id()
    )
  );

-- Policy: Users can delete automation runs for their tenant's automations
CREATE POLICY automation_run_delete_policy ON automation_run
  FOR DELETE
  USING (
    automation_id IN (
      SELECT id FROM automation WHERE tenant_id = public.get_tenant_id()
    )
  );

-- ============================================================================
-- STEP 9: Grant necessary permissions
-- ============================================================================

-- Grant execute permission on the helper function to authenticated users
GRANT EXECUTE ON FUNCTION public.get_tenant_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_tenant_id() TO anon;

-- ============================================================================
-- STEP 10: Create bypass policy for service role (backend API)
-- ============================================================================

-- The service role should bypass RLS for administrative operations
-- This is handled automatically by Supabase when using service_role key

-- For testing purposes, you can create a function to set tenant context:
CREATE OR REPLACE FUNCTION public.set_tenant_context(p_tenant_id UUID)
RETURNS VOID AS $$
BEGIN
  PERFORM set_config('app.current_tenant_id', p_tenant_id::text, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.set_tenant_context(UUID) TO authenticated;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. Your backend API should use the service_role key to bypass RLS
-- 2. The backend should validate tenant_id from JWT/session before operations
-- 3. For Supabase Auth integration, include tenant_id in JWT claims
-- 4. alembic_version table intentionally left without RLS for migrations
-- 5. Test thoroughly before deploying to production!
-- ============================================================================
