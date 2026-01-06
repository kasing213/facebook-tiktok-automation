// Types for billing, payments, and budget management

export type PaymentStatus = 'paid' | 'pending' | 'failed' | 'refunded'

export interface PaymentRecord {
  id: string
  date: string                    // ISO date
  description: string             // 'Pro Monthly Subscription', 'Pro Yearly Subscription'
  amount: number                  // Amount in dollars
  currency: string                // 'usd'
  status: PaymentStatus
  invoiceUrl: string | null       // Stripe invoice URL
  invoicePdfUrl: string | null    // Direct PDF download URL
  receiptUrl: string | null       // Stripe receipt URL
}

export interface PaymentMethod {
  id: string
  type: 'card' | 'bank_account'
  brand?: string                  // 'visa', 'mastercard', etc.
  last4: string                   // Last 4 digits
  expiryMonth?: number
  expiryYear?: number
  isDefault: boolean
}

export interface BillingOverview {
  currentPlan: {
    name: string                  // 'Free', 'Pro Monthly', 'Pro Yearly'
    price: number                 // Monthly equivalent price
    billingInterval: 'month' | 'year' | null
  }
  thisMonthCost: number           // Total cost this month
  budgetLimit: number | null      // Monthly budget limit
  budgetUsedPercent: number       // Percentage of budget used
  nextPayment: {
    date: string | null           // Next payment date
    amount: number | null         // Next payment amount
  }
  paymentMethod: PaymentMethod | null
}

// Budget configuration
export interface BudgetConfig {
  monthlyLimit: number | null     // Monthly spend limit in dollars
  alertAt50: boolean              // Alert when 50% reached
  alertAt80: boolean              // Alert when 80% reached
  alertAt100: boolean             // Alert when 100% reached
  pauseAtLimit: boolean           // Pause service when limit reached
  alertEmail: string              // Email for alerts
}

export interface SpendAlert {
  id: string
  thresholdPercent: number        // 50, 80, or 100
  amountAtAlert: number           // Amount when alert triggered
  sentAt: string                  // ISO timestamp
  deliveryMethod: 'email' | 'telegram'
}

// Pricing tiers
export interface PricingTier {
  id: string
  name: string                    // 'Free', 'Pro'
  monthlyPrice: number            // Price per month
  yearlyPrice: number             // Price per year
  yearlyDiscount: number          // Percentage saved with yearly
  features: PricingFeature[]
  isPopular: boolean
  isCurrent: boolean
}

export interface PricingFeature {
  name: string
  included: boolean
  tooltip?: string
}

// API response types
export interface PaymentRecordResponse {
  id: string
  date: string
  description: string
  amount: number
  currency: string
  status: PaymentStatus
  invoice_url: string | null
  invoice_pdf_url: string | null
  receipt_url: string | null
}

export interface BillingOverviewResponse {
  current_plan: {
    name: string
    price: number
    billing_interval: 'month' | 'year' | null
  }
  this_month_cost: number
  budget_limit: number | null
  budget_used_percent: number
  next_payment: {
    date: string | null
    amount: number | null
  }
  payment_method: {
    id: string
    type: 'card' | 'bank_account'
    brand?: string
    last4: string
    expiry_month?: number
    expiry_year?: number
    is_default: boolean
  } | null
}

export interface BudgetConfigResponse {
  monthly_limit: number | null
  alert_at_50: boolean
  alert_at_80: boolean
  alert_at_100: boolean
  pause_at_limit: boolean
  alert_email: string
}

export interface SpendAlertResponse {
  id: string
  threshold_percent: number
  amount_at_alert: number
  sent_at: string
  delivery_method: 'email' | 'telegram'
}

// Mappers
export function mapPaymentRecordResponse(response: PaymentRecordResponse): PaymentRecord {
  return {
    id: response.id,
    date: response.date,
    description: response.description,
    amount: response.amount,
    currency: response.currency,
    status: response.status,
    invoiceUrl: response.invoice_url,
    invoicePdfUrl: response.invoice_pdf_url,
    receiptUrl: response.receipt_url
  }
}

export function mapBillingOverviewResponse(response: BillingOverviewResponse): BillingOverview {
  return {
    currentPlan: {
      name: response.current_plan.name,
      price: response.current_plan.price,
      billingInterval: response.current_plan.billing_interval
    },
    thisMonthCost: response.this_month_cost,
    budgetLimit: response.budget_limit,
    budgetUsedPercent: response.budget_used_percent,
    nextPayment: {
      date: response.next_payment.date,
      amount: response.next_payment.amount
    },
    paymentMethod: response.payment_method ? {
      id: response.payment_method.id,
      type: response.payment_method.type,
      brand: response.payment_method.brand,
      last4: response.payment_method.last4,
      expiryMonth: response.payment_method.expiry_month,
      expiryYear: response.payment_method.expiry_year,
      isDefault: response.payment_method.is_default
    } : null
  }
}

export function mapBudgetConfigResponse(response: BudgetConfigResponse): BudgetConfig {
  return {
    monthlyLimit: response.monthly_limit,
    alertAt50: response.alert_at_50,
    alertAt80: response.alert_at_80,
    alertAt100: response.alert_at_100,
    pauseAtLimit: response.pause_at_limit,
    alertEmail: response.alert_email
  }
}

export function mapSpendAlertResponse(response: SpendAlertResponse): SpendAlert {
  return {
    id: response.id,
    thresholdPercent: response.threshold_percent,
    amountAtAlert: response.amount_at_alert,
    sentAt: response.sent_at,
    deliveryMethod: response.delivery_method
  }
}

// Pricing constants
export const PRICING_TIERS: Omit<PricingTier, 'isCurrent'>[] = [
  {
    id: 'free',
    name: 'Free',
    monthlyPrice: 0,
    yearlyPrice: 0,
    yearlyDiscount: 0,
    isPopular: false,
    features: [
      { name: 'Create invoices', included: true },
      { name: 'View invoices', included: true },
      { name: 'Manage customers', included: true },
      { name: 'PDF downloads', included: false },
      { name: 'Data export (CSV/Excel)', included: false },
      { name: 'Budget controls', included: false },
      { name: 'Advanced analytics', included: false },
      { name: 'Priority support', included: false }
    ]
  },
  {
    id: 'pro',
    name: 'Pro',
    monthlyPrice: 9.99,
    yearlyPrice: 99,
    yearlyDiscount: 17,
    isPopular: true,
    features: [
      { name: 'Create invoices', included: true },
      { name: 'View invoices', included: true },
      { name: 'Manage customers', included: true },
      { name: 'PDF downloads', included: true },
      { name: 'Data export (CSV/Excel)', included: true },
      { name: 'Budget controls', included: true },
      { name: 'Advanced analytics', included: true },
      { name: 'Priority support', included: true }
    ]
  }
]
