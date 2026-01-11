import axios from 'axios'
import {
  PaymentRecord,
  PaymentRecordResponse,
  BillingOverview,
  BillingOverviewResponse,
  PaymentMethod,
  mapPaymentRecordResponse,
  mapBillingOverviewResponse
} from '../types/billing'

// Use same API URL as main api.ts
const API_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? 'https://web-production-3ed15.up.railway.app' : 'http://localhost:8000')

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[Billing API] Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export interface PaginatedPayments {
  payments: PaymentRecord[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

// Helper function to extract error message
function getErrorMessage(error: unknown, defaultMessage: string): string {
  if (error instanceof Error) {
    const axiosError = error as { response?: { data?: { detail?: string } } }
    return axiosError.response?.data?.detail || error.message || defaultMessage
  }
  return defaultMessage
}

export const billingApi = {
  /**
   * Get billing overview (current plan, next payment, payment method)
   */
  async getOverview(): Promise<BillingOverview> {
    try {
      const response = await api.get<BillingOverviewResponse>('/api/billing/overview')
      return mapBillingOverviewResponse(response.data)
    } catch (error) {
      console.error('Failed to get billing overview:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch billing overview'))
    }
  },

  /**
   * Get payment history with pagination
   */
  async getPaymentHistory(page: number = 1, pageSize: number = 10): Promise<PaginatedPayments> {
    try {
      const response = await api.get<{
        payments: PaymentRecordResponse[]
        total: number
        page: number
        page_size: number
        has_more: boolean
      }>('/api/billing/payments', {
        params: { page, page_size: pageSize }
      })

      return {
        payments: response.data.payments.map(mapPaymentRecordResponse),
        total: response.data.total,
        page: response.data.page,
        pageSize: response.data.page_size,
        hasMore: response.data.has_more
      }
    } catch (error) {
      console.error('Failed to get payment history:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch payment history'))
    }
  },

  /**
   * Get a single payment detail
   */
  async getPayment(paymentId: string): Promise<PaymentRecord> {
    try {
      const response = await api.get<PaymentRecordResponse>(`/api/billing/payments/${paymentId}`)
      return mapPaymentRecordResponse(response.data)
    } catch (error) {
      console.error('Failed to get payment details:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch payment details'))
    }
  },

  /**
   * Download invoice PDF from Stripe
   */
  async downloadInvoicePdf(invoiceId: string): Promise<Blob> {
    try {
      const response = await api.get(`/api/billing/invoices/${invoiceId}/pdf`, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Failed to download invoice PDF:', error)
      throw new Error(getErrorMessage(error, 'Failed to download invoice PDF'))
    }
  },

  /**
   * Get current payment method on file
   */
  async getPaymentMethod(): Promise<PaymentMethod | null> {
    try {
      const response = await api.get<{
        id: string
        type: 'card' | 'bank_account'
        brand?: string
        last4: string
        expiry_month?: number
        expiry_year?: number
        is_default: boolean
      } | null>('/api/billing/payment-method')

      if (!response.data) return null

      return {
        id: response.data.id,
        type: response.data.type,
        brand: response.data.brand,
        last4: response.data.last4,
        expiryMonth: response.data.expiry_month,
        expiryYear: response.data.expiry_year,
        isDefault: response.data.is_default
      }
    } catch (error) {
      console.error('Failed to get payment method:', error)
      return null
    }
  },

  /**
   * Helper to download invoice as file
   */
  async downloadInvoice(invoiceId: string, filename: string = 'invoice.pdf'): Promise<void> {
    try {
      const blob = await this.downloadInvoicePdf(invoiceId)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download invoice:', error)
      throw new Error(getErrorMessage(error, 'Failed to download invoice'))
    }
  }
}

export default billingApi
