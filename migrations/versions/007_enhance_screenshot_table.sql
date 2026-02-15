-- Migration: Enhanced Screenshot Table for Payment Verification
-- Purpose: Add indexes and optimize the scriptclient.screenshot table for OCR payment verification
-- Date: February 2026

-- ============================================================================
-- SECTION 1: Add indexes for performance optimization
-- ============================================================================

-- Index for invoice lookup (fast queries by invoice_id stored in meta JSON)
CREATE INDEX IF NOT EXISTS idx_screenshot_invoice_id
ON scriptclient.screenshot USING GIN ((meta->>'invoice_id'));

-- Index for customer lookup (fast queries by customer_id stored in meta JSON)
CREATE INDEX IF NOT EXISTS idx_screenshot_customer_id
ON scriptclient.screenshot USING GIN ((meta->>'customer_id'));

-- Index for verification status lookup (find pending verifications)
CREATE INDEX IF NOT EXISTS idx_screenshot_verification_status
ON scriptclient.screenshot USING GIN ((meta->>'verification_status'));

-- Index for OCR processing status (find unprocessed screenshots)
CREATE INDEX IF NOT EXISTS idx_screenshot_ocr_processed
ON scriptclient.screenshot USING GIN ((meta->>'ocr_processed'));

-- Index for pending manual verifications (very common query)
CREATE INDEX IF NOT EXISTS idx_screenshot_pending_manual_review
ON scriptclient.screenshot (verified, created_at)
WHERE verified = false;

-- Index for cleanup queries (find old screenshots for deletion)
CREATE INDEX IF NOT EXISTS idx_screenshot_cleanup
ON scriptclient.screenshot (created_at)
WHERE verified = true OR created_at < (NOW() - INTERVAL '30 days');

-- ============================================================================
-- SECTION 2: Add helpful functions for screenshot queries
-- ============================================================================

-- Function to get pending screenshots for a tenant (for manual review)
CREATE OR REPLACE FUNCTION get_pending_screenshots_for_tenant(tenant_uuid UUID)
RETURNS TABLE (
    screenshot_id UUID,
    invoice_id TEXT,
    customer_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    ocr_confidence NUMERIC,
    verification_status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.meta->>'invoice_id' as invoice_id,
        s.meta->>'customer_id' as customer_id,
        s.created_at,
        (s.meta->>'ocr_confidence')::NUMERIC as ocr_confidence,
        s.meta->>'verification_status' as verification_status
    FROM scriptclient.screenshot s
    WHERE s.tenant_id = tenant_uuid
      AND s.verified = false
      AND (s.meta->>'verification_status' = 'pending' OR s.meta->>'verification_status' IS NULL)
    ORDER BY s.created_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get screenshot statistics for a tenant
CREATE OR REPLACE FUNCTION get_screenshot_stats_for_tenant(tenant_uuid UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_screenshots', COUNT(*),
        'verified_screenshots', COUNT(*) FILTER (WHERE verified = true),
        'pending_screenshots', COUNT(*) FILTER (WHERE verified = false),
        'auto_approved', COUNT(*) FILTER (WHERE meta->>'verification_method' = 'ocr_auto'),
        'manually_verified', COUNT(*) FILTER (WHERE meta->>'verification_method' = 'manual_telegram'),
        'high_confidence_ocr', COUNT(*) FILTER (WHERE (meta->>'ocr_confidence')::NUMERIC >= 0.80),
        'low_confidence_ocr', COUNT(*) FILTER (WHERE (meta->>'ocr_confidence')::NUMERIC < 0.80),
        'total_file_size_mb', ROUND(SUM((meta->>'file_size')::BIGINT) / (1024.0 * 1024.0), 2)
    )
    INTO result
    FROM scriptclient.screenshot
    WHERE tenant_id = tenant_uuid;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- SECTION 3: Add constraints and data validation
-- ============================================================================

-- Ensure meta JSON contains required fields for new screenshots
-- Note: This is a check constraint, not enforced on existing records
ALTER TABLE scriptclient.screenshot
ADD CONSTRAINT check_screenshot_meta_structure
CHECK (
    meta IS NOT NULL OR
    (meta ? 'invoice_id' AND meta ? 'customer_id') OR
    created_at < '2026-02-01'::timestamp  -- Allow existing records without validation
);

-- ============================================================================
-- SECTION 4: Update table comments for documentation
-- ============================================================================

COMMENT ON TABLE scriptclient.screenshot IS
'Payment verification screenshots stored in MongoDB GridFS. file_path contains GridFS file_id, meta contains invoice/customer linkage and OCR results.';

COMMENT ON COLUMN scriptclient.screenshot.file_path IS
'Contains MongoDB GridFS file_id for retrieving the actual screenshot image';

COMMENT ON COLUMN scriptclient.screenshot.file_url IS
'API URL path for accessing the screenshot (e.g., /api/gateway/screenshots/{id}/view)';

COMMENT ON COLUMN scriptclient.screenshot.meta IS
'JSON metadata containing: invoice_id, customer_id, filename, file_size, content_type, ocr_results, verification_method';

COMMENT ON COLUMN scriptclient.screenshot.verified IS
'True if screenshot has been manually verified by merchant, false if pending review';

COMMENT ON COLUMN scriptclient.screenshot.verified_by IS
'User ID of merchant who manually verified this screenshot via Telegram';

-- ============================================================================
-- SECTION 5: Performance optimization - update table statistics
-- ============================================================================

-- Update table statistics for better query planning
ANALYZE scriptclient.screenshot;

-- ============================================================================
-- SECTION 6: Add row-level security policies for screenshot access
-- ============================================================================

-- Note: RLS is already enabled on this table from migration 003
-- Add specific policies for screenshot access patterns

-- Policy for getting screenshots by invoice (merchants accessing their own invoices)
CREATE POLICY screenshot_invoice_access_policy ON scriptclient.screenshot
  FOR SELECT
  USING (
    tenant_id = public.get_tenant_id() AND
    meta->>'invoice_id' IN (
      SELECT i.id::text
      FROM invoice.invoice i
      WHERE i.tenant_id = public.get_tenant_id()
    )
  );

-- Policy for updating screenshot verification status (merchants verifying payments)
CREATE POLICY screenshot_verification_update_policy ON scriptclient.screenshot
  FOR UPDATE
  USING (tenant_id = public.get_tenant_id())
  WITH CHECK (tenant_id = public.get_tenant_id());