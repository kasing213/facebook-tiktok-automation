-- Migration: Fix Function Search Path Security Warning
-- Description: Add SET search_path to SECURITY DEFINER functions
-- Fixes: Supabase Security Advisor warnings about mutable search_path

-- ============================================================================
-- Fix public.get_tenant_id() search path
-- ============================================================================

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
-- Fix public.set_tenant_context() search path
-- ============================================================================

CREATE OR REPLACE FUNCTION public.set_tenant_context(p_tenant_id UUID)
RETURNS VOID AS $$
BEGIN
  PERFORM set_config('app.current_tenant_id', p_tenant_id::text, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- This migration fixes the security warnings about mutable search_path
-- in SECURITY DEFINER functions. Setting an explicit search_path prevents
-- potential SQL injection attacks via search path manipulation.
-- ============================================================================
