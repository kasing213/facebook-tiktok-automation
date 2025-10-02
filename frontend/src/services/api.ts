import axios from 'axios'
import { AuthStatus, Tenant, OAuthResult } from '../types/auth'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens or headers here if needed
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const authService = {
  /**
   * Check if backend is healthy
   */
  async healthCheck() {
    const response = await api.get('/health')
    return response.data
  },

  /**
   * Check OAuth credentials configuration status
   * TODO: Implement this endpoint in the backend when credentials are configured
   */
  async checkCredentialsStatus(): Promise<{
    facebook: { appId: boolean; appSecret: boolean }
    tiktok: { clientId: boolean; clientSecret: boolean }
  }> {
    try {
      // TODO: Replace with actual backend endpoint
      // const response = await api.get('/oauth/credentials/status')
      // return response.data

      // For now, return demo status (all credentials missing)
      return {
        facebook: { appId: false, appSecret: false },
        tiktok: { clientId: false, clientSecret: false }
      }
    } catch (error) {
      console.warn('Could not check credentials status:', error)
      // Default to missing credentials if check fails
      return {
        facebook: { appId: false, appSecret: false },
        tiktok: { clientId: false, clientSecret: false }
      }
    }
  },

  /**
   * Get list of tenants
   */
  async getTenants(): Promise<Tenant[]> {
    const response = await api.get('/api/tenants')
    return response.data
  },

  /**
   * Get tenant details by ID
   */
  async getTenant(tenantId: string): Promise<Tenant> {
    const response = await api.get(`/api/tenants/${tenantId}`)
    return response.data
  },

  /**
   * Get OAuth status for a tenant
   */
  async getAuthStatus(tenantId: string): Promise<AuthStatus> {
    const response = await api.get(`/oauth/status/${tenantId}`)
    return response.data
  },

  /**
   * Get OAuth status from main API endpoint
   */
  async getTenantAuthStatus(tenantId: string): Promise<AuthStatus> {
    const response = await api.get(`/api/tenants/${tenantId}/auth-status`)
    return response.data
  },

  /**
   * Initiate Facebook OAuth flow
   */
  async initiateFacebookOAuth(tenantId: string): Promise<void> {
    // This will redirect, so we construct the URL manually
    const url = `/oauth/facebook/authorize?tenant_id=${encodeURIComponent(tenantId)}`
    window.location.href = `${api.defaults.baseURL}${url}`
  },

  /**
   * Initiate TikTok OAuth flow
   */
  async initiateTikTokOAuth(tenantId: string): Promise<void> {
    // This will redirect, so we construct the URL manually
    const url = `/oauth/tiktok/authorize?tenant_id=${encodeURIComponent(tenantId)}`
    window.location.href = `${api.defaults.baseURL}${url}`
  },

  /**
   * Handle OAuth callback (for manual processing if needed)
   */
  async handleOAuthCallback(
    platform: 'facebook' | 'tiktok',
    code: string,
    state: string
  ): Promise<OAuthResult> {
    const response = await api.get(`/oauth/${platform}/callback`, {
      params: { code, state }
    })
    return response.data
  }
}

export default api