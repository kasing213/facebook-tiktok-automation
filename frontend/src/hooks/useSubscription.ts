import { useState, useEffect, useCallback } from 'react'
import { subscriptionApi } from '../services/subscriptionApi'
import {
  SubscriptionStatus,
  SubscriptionTier,
  TierFeatures,
  getTierFeatures
} from '../types/subscription'

export function useSubscription() {
  const [status, setStatus] = useState<SubscriptionStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [portalLoading, setPortalLoading] = useState(false)

  // Fetch subscription status
  const fetchStatus = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await subscriptionApi.getStatus()
      setStatus(data)
      return data
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to fetch subscription status'
      setError(message)
      // Default to free tier on error
      setStatus({
        tier: 'free',
        status: null,
        stripe_customer_id: null,
        current_period_end: null,
        cancel_at_period_end: false,
        can_access_pdf: false,
        can_access_export: false
      })
    } finally {
      setLoading(false)
    }
  }, [])

  // Start checkout session and redirect to Stripe
  const startCheckout = useCallback(async (priceType: 'monthly' | 'yearly') => {
    setCheckoutLoading(true)
    setError(null)
    try {
      await subscriptionApi.redirectToCheckout(priceType)
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to start checkout'
      setError(message)
      throw err
    } finally {
      setCheckoutLoading(false)
    }
  }, [])

  // Open billing portal and redirect to Stripe
  const openBillingPortal = useCallback(async () => {
    setPortalLoading(true)
    setError(null)
    try {
      await subscriptionApi.redirectToPortal()
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to open billing portal'
      setError(message)
      throw err
    } finally {
      setPortalLoading(false)
    }
  }, [])

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Fetch status on mount
  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  // Computed properties
  const tier: SubscriptionTier = status?.tier || 'free'
  const isPro = tier === 'pro'
  const features: TierFeatures = getTierFeatures(tier)

  return {
    // Status
    status,
    tier,
    isPro,
    features,

    // Loading states
    loading,
    checkoutLoading,
    portalLoading,

    // Error
    error,
    clearError,

    // Actions
    fetchStatus,
    startCheckout,
    openBillingPortal,

    // Convenience accessors
    canAccessPdf: status?.can_access_pdf || false,
    canAccessExport: status?.can_access_export || false,
    isSubscriptionActive: status?.status === 'active',
    cancelAtPeriodEnd: status?.cancel_at_period_end || false,
    periodEnd: status?.current_period_end || null
  }
}

export default useSubscription
