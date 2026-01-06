// Types for subscription management

export type SubscriptionTier = 'free' | 'pro'

export type SubscriptionStatusType = 'active' | 'cancelled' | 'past_due' | 'incomplete' | null

export interface SubscriptionStatus {
  tier: SubscriptionTier
  status: SubscriptionStatusType
  stripe_customer_id: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
  can_access_pdf: boolean
  can_access_export: boolean
}

export interface CheckoutSession {
  checkout_url: string
  session_id: string
}

export interface PortalSession {
  portal_url: string
}

export interface CreateCheckoutRequest {
  price_type: 'monthly' | 'yearly'
  success_url?: string
  cancel_url?: string
}

// Feature flags based on tier
export interface TierFeatures {
  createInvoices: boolean
  viewInvoices: boolean
  manageCustomers: boolean
  downloadPdf: boolean
  exportData: boolean
  prioritySupport: boolean
  budgetControls: boolean
  advancedAnalytics: boolean
  usageExport: boolean
}

export const FREE_TIER_FEATURES: TierFeatures = {
  createInvoices: true,
  viewInvoices: true,
  manageCustomers: true,
  downloadPdf: false,
  exportData: false,
  prioritySupport: false,
  budgetControls: false,
  advancedAnalytics: false,
  usageExport: false
}

export const PRO_TIER_FEATURES: TierFeatures = {
  createInvoices: true,
  viewInvoices: true,
  manageCustomers: true,
  downloadPdf: true,
  exportData: true,
  prioritySupport: true,
  budgetControls: true,
  advancedAnalytics: true,
  usageExport: true
}

export function getTierFeatures(tier: SubscriptionTier): TierFeatures {
  return tier === 'pro' ? PRO_TIER_FEATURES : FREE_TIER_FEATURES
}
