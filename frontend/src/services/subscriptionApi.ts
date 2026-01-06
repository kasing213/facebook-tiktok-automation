import axios from 'axios'
import {
  SubscriptionStatus,
  CheckoutSession,
  PortalSession,
  CreateCheckoutRequest
} from '../types/subscription'

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
    console.error('[Subscription API] Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const subscriptionApi = {
  /**
   * Get current user's subscription status
   */
  async getStatus(): Promise<SubscriptionStatus> {
    const response = await api.get<SubscriptionStatus>('/api/subscriptions/status')
    return response.data
  },

  /**
   * Create a Stripe checkout session for subscription purchase
   */
  async createCheckout(request: CreateCheckoutRequest): Promise<CheckoutSession> {
    const response = await api.post<CheckoutSession>('/api/subscriptions/create-checkout', request)
    return response.data
  },

  /**
   * Create a Stripe billing portal session for subscription management
   */
  async createPortal(): Promise<PortalSession> {
    const response = await api.post<PortalSession>('/api/subscriptions/create-portal')
    return response.data
  },

  /**
   * Redirect to Stripe checkout
   */
  async redirectToCheckout(priceType: 'monthly' | 'yearly'): Promise<void> {
    const session = await this.createCheckout({ price_type: priceType })
    window.location.href = session.checkout_url
  },

  /**
   * Redirect to Stripe billing portal
   */
  async redirectToPortal(): Promise<void> {
    const session = await this.createPortal()
    window.location.href = session.portal_url
  }
}

export default subscriptionApi
