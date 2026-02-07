-- Rollback: Disable Comprehensive Row Level Security (RLS) for ALL schemas
-- Description: Removes ALL RLS policies and disables RLS across all schemas
-- WARNING: This will remove tenant isolation at the database level

-- ============================================================================
-- SECTION 1: Drop RLS Policies for PUBLIC SCHEMA
-- ============================================================================

-- Drop policies for core multi-tenant tables (only tables with tenant_id)
DROP POLICY IF EXISTS user_select_policy ON "user";
DROP POLICY IF EXISTS user_insert_policy ON "user";
DROP POLICY IF EXISTS user_update_policy ON "user";
DROP POLICY IF EXISTS user_delete_policy ON "user";

DROP POLICY IF EXISTS ad_token_select_policy ON ad_token;
DROP POLICY IF EXISTS ad_token_insert_policy ON ad_token;
DROP POLICY IF EXISTS ad_token_update_policy ON ad_token;
DROP POLICY IF EXISTS ad_token_delete_policy ON ad_token;

DROP POLICY IF EXISTS social_identity_select_policy ON social_identity;
DROP POLICY IF EXISTS social_identity_insert_policy ON social_identity;
DROP POLICY IF EXISTS social_identity_update_policy ON social_identity;
DROP POLICY IF EXISTS social_identity_delete_policy ON social_identity;

DROP POLICY IF EXISTS destination_select_policy ON destination;
DROP POLICY IF EXISTS destination_insert_policy ON destination;
DROP POLICY IF EXISTS destination_update_policy ON destination;
DROP POLICY IF EXISTS destination_delete_policy ON destination;

DROP POLICY IF EXISTS automation_select_policy ON automation;
DROP POLICY IF EXISTS automation_insert_policy ON automation;
DROP POLICY IF EXISTS automation_update_policy ON automation;
DROP POLICY IF EXISTS automation_delete_policy ON automation;

-- Drop policies for additional public schema tables
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
    -- Drop all policy types for each table
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', table_name || '_select_policy', table_name);
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', table_name || '_insert_policy', table_name);
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', table_name || '_update_policy', table_name);
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', table_name || '_delete_policy', table_name);
  END LOOP;
END $$;

-- ============================================================================
-- SECTION 2: Drop RLS Policies for INVENTORY SCHEMA
-- ============================================================================

DROP POLICY IF EXISTS inventory_products_select_policy ON inventory.products;
DROP POLICY IF EXISTS inventory_products_insert_policy ON inventory.products;
DROP POLICY IF EXISTS inventory_products_update_policy ON inventory.products;
DROP POLICY IF EXISTS inventory_products_delete_policy ON inventory.products;

DROP POLICY IF EXISTS inventory_stock_movements_select_policy ON inventory.stock_movements;
DROP POLICY IF EXISTS inventory_stock_movements_insert_policy ON inventory.stock_movements;
DROP POLICY IF EXISTS inventory_stock_movements_update_policy ON inventory.stock_movements;
DROP POLICY IF EXISTS inventory_stock_movements_delete_policy ON inventory.stock_movements;

-- ============================================================================
-- SECTION 3: Drop RLS Policies for ADS_ALERT SCHEMA
-- ============================================================================

DROP POLICY IF EXISTS ads_alert_chat_select_policy ON ads_alert.chat;
DROP POLICY IF EXISTS ads_alert_chat_insert_policy ON ads_alert.chat;
DROP POLICY IF EXISTS ads_alert_chat_update_policy ON ads_alert.chat;
DROP POLICY IF EXISTS ads_alert_chat_delete_policy ON ads_alert.chat;

DROP POLICY IF EXISTS ads_alert_promotion_select_policy ON ads_alert.promotion;
DROP POLICY IF EXISTS ads_alert_promotion_insert_policy ON ads_alert.promotion;
DROP POLICY IF EXISTS ads_alert_promotion_update_policy ON ads_alert.promotion;
DROP POLICY IF EXISTS ads_alert_promotion_delete_policy ON ads_alert.promotion;

DROP POLICY IF EXISTS ads_alert_promo_status_select_policy ON ads_alert.promo_status;
DROP POLICY IF EXISTS ads_alert_promo_status_insert_policy ON ads_alert.promo_status;
DROP POLICY IF EXISTS ads_alert_promo_status_update_policy ON ads_alert.promo_status;
DROP POLICY IF EXISTS ads_alert_promo_status_delete_policy ON ads_alert.promo_status;

DROP POLICY IF EXISTS ads_alert_media_folder_select_policy ON ads_alert.media_folder;
DROP POLICY IF EXISTS ads_alert_media_folder_insert_policy ON ads_alert.media_folder;
DROP POLICY IF EXISTS ads_alert_media_folder_update_policy ON ads_alert.media_folder;
DROP POLICY IF EXISTS ads_alert_media_folder_delete_policy ON ads_alert.media_folder;

DROP POLICY IF EXISTS ads_alert_media_select_policy ON ads_alert.media;
DROP POLICY IF EXISTS ads_alert_media_insert_policy ON ads_alert.media;
DROP POLICY IF EXISTS ads_alert_media_update_policy ON ads_alert.media;
DROP POLICY IF EXISTS ads_alert_media_delete_policy ON ads_alert.media;

DROP POLICY IF EXISTS ads_alert_broadcast_log_select_policy ON ads_alert.broadcast_log;
DROP POLICY IF EXISTS ads_alert_broadcast_log_insert_policy ON ads_alert.broadcast_log;
DROP POLICY IF EXISTS ads_alert_broadcast_log_update_policy ON ads_alert.broadcast_log;
DROP POLICY IF EXISTS ads_alert_broadcast_log_delete_policy ON ads_alert.broadcast_log;

-- ============================================================================
-- SECTION 4: Drop RLS Policies for INVOICE SCHEMA
-- ============================================================================

DROP POLICY IF EXISTS invoice_customer_select_policy ON invoice.customer;
DROP POLICY IF EXISTS invoice_customer_insert_policy ON invoice.customer;
DROP POLICY IF EXISTS invoice_customer_update_policy ON invoice.customer;
DROP POLICY IF EXISTS invoice_customer_delete_policy ON invoice.customer;

DROP POLICY IF EXISTS invoice_invoice_select_policy ON invoice.invoice;
DROP POLICY IF EXISTS invoice_invoice_insert_policy ON invoice.invoice;
DROP POLICY IF EXISTS invoice_invoice_update_policy ON invoice.invoice;
DROP POLICY IF EXISTS invoice_invoice_delete_policy ON invoice.invoice;

DROP POLICY IF EXISTS invoice_client_link_code_select_policy ON invoice.client_link_code;
DROP POLICY IF EXISTS invoice_client_link_code_insert_policy ON invoice.client_link_code;
DROP POLICY IF EXISTS invoice_client_link_code_update_policy ON invoice.client_link_code;
DROP POLICY IF EXISTS invoice_client_link_code_delete_policy ON invoice.client_link_code;

DROP POLICY IF EXISTS invoice_tenant_client_sequence_select_policy ON invoice.tenant_client_sequence;
DROP POLICY IF EXISTS invoice_tenant_client_sequence_insert_policy ON invoice.tenant_client_sequence;
DROP POLICY IF EXISTS invoice_tenant_client_sequence_update_policy ON invoice.tenant_client_sequence;
DROP POLICY IF EXISTS invoice_tenant_client_sequence_delete_policy ON invoice.tenant_client_sequence;

-- ============================================================================
-- SECTION 5: Drop RLS Policies for SCRIPTCLIENT SCHEMA
-- ============================================================================

DROP POLICY IF EXISTS scriptclient_screenshot_select_policy ON scriptclient.screenshot;
DROP POLICY IF EXISTS scriptclient_screenshot_insert_policy ON scriptclient.screenshot;
DROP POLICY IF EXISTS scriptclient_screenshot_update_policy ON scriptclient.screenshot;
DROP POLICY IF EXISTS scriptclient_screenshot_delete_policy ON scriptclient.screenshot;

-- ============================================================================
-- SECTION 6: Drop RLS Policies for AUDIT_SALES SCHEMA
-- ============================================================================

DROP POLICY IF EXISTS audit_sales_sale_select_policy ON audit_sales.sale;
DROP POLICY IF EXISTS audit_sales_sale_insert_policy ON audit_sales.sale;
DROP POLICY IF EXISTS audit_sales_sale_update_policy ON audit_sales.sale;
DROP POLICY IF EXISTS audit_sales_sale_delete_policy ON audit_sales.sale;

-- ============================================================================
-- SECTION 7: Disable RLS on PUBLIC SCHEMA TABLES
-- ============================================================================

-- Core multi-tenant tables (only tables with tenant_id)
ALTER TABLE "user" DISABLE ROW LEVEL SECURITY;
ALTER TABLE ad_token DISABLE ROW LEVEL SECURITY;
ALTER TABLE social_identity DISABLE ROW LEVEL SECURITY;
ALTER TABLE destination DISABLE ROW LEVEL SECURITY;
ALTER TABLE automation DISABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_link_code DISABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_token DISABLE ROW LEVEL SECURITY;
ALTER TABLE mfa_secret DISABLE ROW LEVEL SECURITY;
ALTER TABLE subscription DISABLE ROW LEVEL SECURITY;

-- Inventory tables (in inventory schema - disabled in SECTION 8)

-- Ads alert tables (in ads_alert schema - disabled in SECTION 8)

-- ============================================================================
-- SECTION 8: Disable RLS on OTHER SCHEMA TABLES
-- ============================================================================

-- Inventory schema
ALTER TABLE inventory.products DISABLE ROW LEVEL SECURITY;
ALTER TABLE inventory.stock_movements DISABLE ROW LEVEL SECURITY;

-- Ads alert schema
ALTER TABLE ads_alert.chat DISABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.promotion DISABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.promo_status DISABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.media_folder DISABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.media DISABLE ROW LEVEL SECURITY;
ALTER TABLE ads_alert.broadcast_log DISABLE ROW LEVEL SECURITY;

-- Invoice schema
ALTER TABLE invoice.customer DISABLE ROW LEVEL SECURITY;
ALTER TABLE invoice.invoice DISABLE ROW LEVEL SECURITY;
ALTER TABLE invoice.client_link_code DISABLE ROW LEVEL SECURITY;
ALTER TABLE invoice.tenant_client_sequence DISABLE ROW LEVEL SECURITY;

-- Scriptclient schema
ALTER TABLE scriptclient.screenshot DISABLE ROW LEVEL SECURITY;

-- Audit sales schema
ALTER TABLE audit_sales.sale DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SECTION 9: Drop helper functions
-- ============================================================================

DROP FUNCTION IF EXISTS public.get_tenant_id();
DROP FUNCTION IF EXISTS public.set_tenant_context(UUID);
DROP FUNCTION IF EXISTS public.verify_rls_status();

-- ============================================================================
-- SECTION 10: Revoke permissions
-- ============================================================================

-- Permissions are automatically revoked when functions are dropped

-- ============================================================================
-- NOTES:
-- ============================================================================
-- RLS has been completely disabled across ALL schemas.
-- Your database is no longer protected by row-level tenant isolation.
-- Use this only for testing or if reverting changes.
-- After rollback, application-level tenant filtering is the only protection.
-- ============================================================================