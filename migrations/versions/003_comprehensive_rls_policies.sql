-- Migration: Comprehensive Row Level Security (RLS) Implementation
-- Description: Implements tenant isolation at the database level for ALL schemas
-- Schemas covered: public, invoice, scriptclient, audit_sales, ads_alert, inventory (products/stock_movements)
-- WARNING: This will restrict access to data based on user context

-- ============================================================================
-- SECTION 1: Enable RLS on PUBLIC SCHEMA TABLES
-- ============================================================================

-- Core multi-tenant tables in public schema (only tables with tenant_id column)
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_token ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_identity ENABLE ROW LEVEL SECURITY;
ALTER TABLE destination ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_link_code ENABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_token ENABLE ROW LEVEL SECURITY;
ALTER TABLE mfa_secret ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription ENABLE ROW LEVEL SECURITY;

-- Inventory tables (in inventory schema)
ALTER TABLE inventory.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory.stock_movements ENABLE ROW LEVEL SECURITY;

-- Ads alert tables (in ads_alert schema)
ALTER TABLE ads_alert.chat ENABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.promotion ENABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.promo_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.media_folder ENABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.media ENABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.broadcast_log ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SECTION 2: Enable RLS on INVOICE SCHEMA TABLES
-- ============================================================================

ALTER TABLE invoice.customer ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice.invoice ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice.client_link_code ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice.tenant_client_sequence ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SECTION 3: Enable RLS on SCRIPTCLIENT SCHEMA TABLES
-- ============================================================================

ALTER TABLE scriptclient.screenshot ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SECTION 4: Enable RLS on AUDIT_SALES SCHEMA TABLES
-- ============================================================================

ALTER TABLE audit_sales.sale ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SECTION 5: Enable RLS on ADS_ALERT SCHEMA TABLES (if using separate schema)
-- ============================================================================

-- Note: These may be in public schema based on models.py, but including for completeness
-- ALTER TABLE ads_alert.chat ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ads_alert.promotion ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ads_alert.promo_status ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SECTION 6: Create helper function to get current tenant_id from JWT/session
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
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = public;

-- ============================================================================
-- SECTION 7: Create RLS Policies for PUBLIC SCHEMA CORE TABLES
-- ============================================================================

-- USER table policies
CREATE POLICY user_select_policy ON "user"
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY user_insert_policy ON "user"
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY user_update_policy ON "user"
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY user_delete_policy ON "user"
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- AD_TOKEN table policies
CREATE POLICY ad_token_select_policy ON ad_token
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY ad_token_insert_policy ON ad_token
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ad_token_update_policy ON ad_token
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ad_token_delete_policy ON ad_token
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- SOCIAL_IDENTITY table policies
CREATE POLICY social_identity_select_policy ON social_identity
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY social_identity_insert_policy ON social_identity
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY social_identity_update_policy ON social_identity
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY social_identity_delete_policy ON social_identity
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- DESTINATION table policies
CREATE POLICY destination_select_policy ON destination
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY destination_insert_policy ON destination
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY destination_update_policy ON destination
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY destination_delete_policy ON destination
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- AUTOMATION table policies
CREATE POLICY automation_select_policy ON automation
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY automation_insert_policy ON automation
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY automation_update_policy ON automation
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY automation_delete_policy ON automation
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- SECTION 8: Create RLS Policies for ADDITIONAL PUBLIC SCHEMA TABLES
-- ============================================================================

-- Template for all tenant_id-based tables
DO $$
DECLARE
  table_name text;
  policy_name text;
BEGIN
  FOR table_name IN
    SELECT unnest(ARRAY[
      'telegram_link_code', 'refresh_token', 'mfa_secret', 'subscription'
    ])
  LOOP
    -- SELECT policy
    policy_name := table_name || '_select_policy';
    EXECUTE format('
      CREATE POLICY %I ON %I
      FOR SELECT
      USING (tenant_id = public.get_tenant_id())
    ', policy_name, table_name);

    -- INSERT policy
    policy_name := table_name || '_insert_policy';
    EXECUTE format('
      CREATE POLICY %I ON %I
      FOR INSERT
      WITH CHECK (tenant_id = public.get_tenant_id())
    ', policy_name, table_name);

    -- UPDATE policy
    policy_name := table_name || '_update_policy';
    EXECUTE format('
      CREATE POLICY %I ON %I
      FOR UPDATE
      USING (tenant_id = public.get_tenant_id())
      WITH CHECK (tenant_id = public.get_tenant_id())
    ', policy_name, table_name);

    -- DELETE policy
    policy_name := table_name || '_delete_policy';
    EXECUTE format('
      CREATE POLICY %I ON %I
      FOR DELETE
      USING (tenant_id = public.get_tenant_id())
    ', policy_name, table_name);
  END LOOP;
END $$;

-- ============================================================================
-- SECTION 9: Create RLS Policies for INVENTORY SCHEMA
-- ============================================================================

-- PRODUCTS table policies
CREATE POLICY inventory_products_select_policy ON inventory.products
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY inventory_products_insert_policy ON inventory.products
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY inventory_products_update_policy ON inventory.products
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY inventory_products_delete_policy ON inventory.products
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- STOCK_MOVEMENTS table policies
CREATE POLICY inventory_stock_movements_select_policy ON inventory.stock_movements
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY inventory_stock_movements_insert_policy ON inventory.stock_movements
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY inventory_stock_movements_update_policy ON inventory.stock_movements
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY inventory_stock_movements_delete_policy ON inventory.stock_movements
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- SECTION 10: Create RLS Policies for ADS_ALERT SCHEMA
-- ============================================================================

-- CHAT table policies
CREATE POLICY ads_alert_chat_select_policy ON ads_alert.chat
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_chat_insert_policy ON ads_alert.chat
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_chat_update_policy ON ads_alert.chat
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_chat_delete_policy ON ads_alert.chat
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- PROMOTION table policies
CREATE POLICY ads_alert_promotion_select_policy ON ads_alert.promotion
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_promotion_insert_policy ON ads_alert.promotion
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_promotion_update_policy ON ads_alert.promotion
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_promotion_delete_policy ON ads_alert.promotion
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- PROMO_STATUS table policies
CREATE POLICY ads_alert_promo_status_select_policy ON ads_alert.promo_status
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_promo_status_insert_policy ON ads_alert.promo_status
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_promo_status_update_policy ON ads_alert.promo_status
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_promo_status_delete_policy ON ads_alert.promo_status
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- MEDIA_FOLDER table policies
CREATE POLICY ads_alert_media_folder_select_policy ON ads_alert.media_folder
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_media_folder_insert_policy ON ads_alert.media_folder
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_media_folder_update_policy ON ads_alert.media_folder
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_media_folder_delete_policy ON ads_alert.media_folder
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- MEDIA table policies
CREATE POLICY ads_alert_media_select_policy ON ads_alert.media
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_media_insert_policy ON ads_alert.media
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_media_update_policy ON ads_alert.media
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_media_delete_policy ON ads_alert.media
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- BROADCAST_LOG table policies
CREATE POLICY ads_alert_broadcast_log_select_policy ON ads_alert.broadcast_log
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_broadcast_log_insert_policy ON ads_alert.broadcast_log
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_broadcast_log_update_policy ON ads_alert.broadcast_log
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY ads_alert_broadcast_log_delete_policy ON ads_alert.broadcast_log
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- SECTION 11: Create RLS Policies for INVOICE SCHEMA
-- ============================================================================

-- CUSTOMER table policies
CREATE POLICY invoice_customer_select_policy ON invoice.customer
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_customer_insert_policy ON invoice.customer
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_customer_update_policy ON invoice.customer
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_customer_delete_policy ON invoice.customer
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- INVOICE table policies
CREATE POLICY invoice_invoice_select_policy ON invoice.invoice
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_invoice_insert_policy ON invoice.invoice
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_invoice_update_policy ON invoice.invoice
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_invoice_delete_policy ON invoice.invoice
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- CLIENT_LINK_CODE table policies
CREATE POLICY invoice_client_link_code_select_policy ON invoice.client_link_code
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_client_link_code_insert_policy ON invoice.client_link_code
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_client_link_code_update_policy ON invoice.client_link_code
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_client_link_code_delete_policy ON invoice.client_link_code
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- TENANT_CLIENT_SEQUENCE table policies
CREATE POLICY invoice_tenant_client_sequence_select_policy ON invoice.tenant_client_sequence
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_tenant_client_sequence_insert_policy ON invoice.tenant_client_sequence
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_tenant_client_sequence_update_policy ON invoice.tenant_client_sequence
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY invoice_tenant_client_sequence_delete_policy ON invoice.tenant_client_sequence
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- SECTION 12: Create RLS Policies for SCRIPTCLIENT SCHEMA
-- ============================================================================

-- SCREENSHOT table policies
CREATE POLICY scriptclient_screenshot_select_policy ON scriptclient.screenshot
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY scriptclient_screenshot_insert_policy ON scriptclient.screenshot
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY scriptclient_screenshot_update_policy ON scriptclient.screenshot
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY scriptclient_screenshot_delete_policy ON scriptclient.screenshot
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- SECTION 13: Create RLS Policies for AUDIT_SALES SCHEMA
-- ============================================================================

-- SALE table policies
CREATE POLICY audit_sales_sale_select_policy ON audit_sales.sale
  FOR SELECT
  USING (tenant_id = public.get_tenant_id());

CREATE POLICY audit_sales_sale_insert_policy ON audit_sales.sale
  FOR INSERT
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY audit_sales_sale_update_policy ON audit_sales.sale
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY audit_sales_sale_delete_policy ON audit_sales.sale
  FOR DELETE
  USING (tenant_id = public.get_tenant_id());

-- ============================================================================
-- SECTION 14: Grant necessary permissions
-- ============================================================================

-- Grant execute permission on the helper function to authenticated users
GRANT EXECUTE ON FUNCTION public.get_tenant_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_tenant_id() TO anon;

-- ============================================================================
-- SECTION 15: Create bypass policy for service role (backend API)
-- ============================================================================

-- The service role should bypass RLS for administrative operations
-- This is handled automatically by Supabase when using service_role key

-- For testing purposes, you can create a function to set tenant context:
CREATE OR REPLACE FUNCTION public.set_tenant_context(p_tenant_id UUID)
RETURNS VOID AS $$
BEGIN
  PERFORM set_config('app.current_tenant_id', p_tenant_id::text, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

GRANT EXECUTE ON FUNCTION public.set_tenant_context(UUID) TO authenticated;

-- ============================================================================
-- VERIFICATION: Check RLS status
-- ============================================================================

-- Function to verify RLS is enabled on all tables
CREATE OR REPLACE FUNCTION public.verify_rls_status()
RETURNS TABLE(
  schema_name text,
  table_name text,
  rls_enabled boolean,
  policy_count bigint
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    schemaname::text,
    tablename::text,
    rowsecurity,
    (SELECT count(*) FROM pg_policy WHERE polrelid = (schemaname||'.'||tablename)::regclass)
  FROM pg_tables
  WHERE schemaname IN ('public', 'invoice', 'scriptclient', 'audit_sales', 'ads_alert')
    AND tablename NOT IN ('alembic_version')  -- Skip migration table
  ORDER BY schemaname, tablename;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. Your backend API should use the service_role key to bypass RLS
-- 2. The backend should validate tenant_id from JWT/session before operations
-- 3. For Supabase Auth integration, include tenant_id in JWT claims
-- 4. alembic_version table intentionally left without RLS for migrations
-- 5. Test thoroughly before deploying to production!
-- 6. Run SELECT * FROM public.verify_rls_status(); to check implementation
-- ============================================================================