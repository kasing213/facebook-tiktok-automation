import axios from 'axios'
import { AuthStatus, Tenant } from '../types/auth'

// Create axios instance with base configuration
// Use environment variable if available, fallback to localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
console.log('[API] Base URL configured as:', API_URL)

const api = axios.create({
  baseURL: API_URL,
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
   */
  async checkCredentialsStatus(): Promise<{
    facebook: { appId: boolean; appSecret: boolean }
    tiktok: { clientId: boolean; clientSecret: boolean }
  }> {
    try {
      // Get health check data which includes service configuration status
      const response = await api.get('/health')
      const services = response.data.services || {}

      return {
        facebook: {
          appId: services.facebook_integration === 'configured',
          appSecret: services.facebook_integration === 'configured'
        },
        tiktok: {
          clientId: services.tiktok_integration === 'configured',
          clientSecret: services.tiktok_integration === 'configured'
        }
      }
    } catch (error) {
      console.warn('Could not check credentials status:', error)
      // Return true for all credentials to disable demo mode by default
      // This will allow OAuth flow to proceed normally
      return {
        facebook: { appId: true, appSecret: true },
        tiktok: { clientId: true, clientSecret: true }
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
    try {
      const response = await api.get(`/auth/status/${tenantId}`)
      return response.data
    } catch (error: any) {
      console.error('Failed to get OAuth status:', error)
      throw new Error(`Failed to get OAuth status: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Get OAuth status from main API endpoint
   */
  async getTenantAuthStatus(tenantId: string): Promise<AuthStatus> {
    try {
      const response = await api.get(`/api/tenants/${tenantId}/auth-status`)
      // Transform the response to match the expected AuthStatus interface
      const data = response.data
      return {
        tenant_id: data.tenant_id,
        facebook: data.platforms?.facebook ? {
          connected: data.platforms.facebook.connected,
          valid_tokens: data.platforms.facebook.valid_tokens,
          accounts: data.platforms.facebook.accounts
        } : { connected: false, valid_tokens: 0, accounts: [] },
        tiktok: data.platforms?.tiktok ? {
          connected: data.platforms.tiktok.connected,
          valid_tokens: data.platforms.tiktok.valid_tokens,
          accounts: data.platforms.tiktok.accounts
        } : { connected: false, valid_tokens: 0, accounts: [] }
      }
    } catch (error: any) {
      console.error('Failed to get tenant auth status:', error)
      throw new Error(`Failed to get tenant auth status: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Initiate Facebook OAuth flow
   */
  async initiateFacebookOAuth(tenantId: string): Promise<void> {
    try {
      // This will redirect, so we construct the URL manually
      const url = `/auth/facebook/authorize?tenant_id=${encodeURIComponent(tenantId)}`
      window.location.href = `${api.defaults.baseURL}${url}`
    } catch (error: any) {
      console.error('Failed to initiate Facebook OAuth:', error)
      throw new Error(`Failed to initiate Facebook OAuth: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Initiate TikTok OAuth flow
   */
  async initiateTikTokOAuth(tenantId: string): Promise<void> {
    try {
      // This will redirect, so we construct the URL manually
      const url = `/auth/tiktok/authorize?tenant_id=${encodeURIComponent(tenantId)}`
      window.location.href = `${api.defaults.baseURL}${url}`
    } catch (error: any) {
      console.error('Failed to initiate TikTok OAuth:', error)
      throw new Error(`Failed to initiate TikTok OAuth: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Handle OAuth callback (mock implementation - actual OAuth is handled by backend redirect)
   */
  async handleOAuthCallback(platform: string, code: string, state: string): Promise<any> {
    try {
      // The backend already handles the OAuth callback and redirects
      // This is a placeholder for any frontend processing needed
      return {
        success: true,
        platform,
        message: `${platform} OAuth completed successfully`
      }
    } catch (error: any) {
      console.error('Failed to handle OAuth callback:', error)
      throw new Error(`Failed to handle OAuth callback: ${error.response?.data?.detail || error.message}`)
    }
  }

}

export default api