import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { AuthStatus, Tenant, LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, User } from '../types/auth'

// Create axios instance with base configuration
// Use environment variable if available, fallback to production backend
const API_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? 'https://web-production-3ed15.up.railway.app' : 'http://localhost:8000')
console.log('[API] Base URL configured as:', API_URL)
console.log('[API] Environment:', import.meta.env.MODE)

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookies for cross-origin requests (refresh token)
})

// Extend AxiosRequestConfig to include _retry flag
interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
}

// Token utilities
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    // Check if token expires within the next 30 seconds (buffer)
    return payload.exp * 1000 < Date.now() + 30000
  } catch {
    return true
  }
}

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(callback => callback(token))
  refreshSubscribers = []
}

/**
 * Refresh the access token using the httpOnly refresh token cookie
 */
async function refreshAccessToken(): Promise<string | null> {
  try {
    const response = await axios.post(
      `${API_URL}/auth/refresh`,
      {},
      { withCredentials: true }
    )
    const newToken = response.data.access_token
    if (newToken) {
      localStorage.setItem('access_token', newToken)
      return newToken
    }
    return null
  } catch (error) {
    console.error('[API] Token refresh failed:', error)
    localStorage.removeItem('access_token')
    return null
  }
}

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add JWT token to requests if available
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor with automatic token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequest

    // Handle 401 errors with automatic token refresh
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Skip refresh for login/register/refresh endpoints
      const skipRefreshPaths = ['/auth/login', '/auth/register', '/auth/refresh']
      if (skipRefreshPaths.some(path => originalRequest.url?.includes(path))) {
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // Wait for ongoing refresh to complete
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((token: string) => {
            if (token) {
              originalRequest.headers.Authorization = `Bearer ${token}`
              resolve(api(originalRequest))
            } else {
              reject(error)
            }
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const newToken = await refreshAccessToken()
        isRefreshing = false

        if (newToken) {
          onTokenRefreshed(newToken)
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return api(originalRequest)
        } else {
          // Refresh failed - redirect to login
          onTokenRefreshed('')
          window.location.href = '/login'
          return Promise.reject(error)
        }
      } catch (refreshError) {
        isRefreshing = false
        onTokenRefreshed('')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

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
      const response = await api.get('/auth/facebook/authorize-url', {
        params: { tenant_id: tenantId }
      })
      const authUrl = response.data?.auth_url
      if (!authUrl) {
        throw new Error('Facebook OAuth URL missing from response')
      }
      window.location.href = authUrl
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
      const response = await api.get('/auth/tiktok/authorize-url', {
        params: { tenant_id: tenantId }
      })
      const authUrl = response.data?.auth_url
      if (!authUrl) {
        throw new Error('TikTok OAuth URL missing from response')
      }
      window.location.href = authUrl
    } catch (error: any) {
      console.error('Failed to initiate TikTok OAuth:', error)
      throw new Error(`Failed to initiate TikTok OAuth: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Handle OAuth callback (mock implementation - actual OAuth is handled by backend redirect)
   */
  async handleOAuthCallback(platform: string, _code: string, _state: string): Promise<any> {
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
  },

  /**
   * Login with username and password
   * Access token is returned in response, refresh token is set as httpOnly cookie
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      // Backend expects form data for OAuth2 password flow
      const formData = new URLSearchParams()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        withCredentials: true, // Accept refresh token cookie
      })

      // Store access token in localStorage
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token)
      }

      return response.data
    } catch (error: any) {
      console.error('Login failed:', error)
      throw new Error(`Login failed: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Register a new user
   */
  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    try {
      const response = await api.post('/auth/register', userData)
      return response.data
    } catch (error: any) {
      console.error('Registration failed:', error)
      throw new Error(`Registration failed: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await api.get('/auth/me')
      return response.data
    } catch (error: any) {
      console.error('Failed to get current user:', error)
      throw new Error(`Failed to get current user: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Logout - revoke tokens on backend and clear local storage
   */
  async logout(): Promise<void> {
    try {
      // Call backend to blacklist access token and revoke refresh token
      await api.post('/auth/logout', {}, { withCredentials: true })
    } catch (error) {
      // Logout should succeed even if backend call fails
      console.error('Backend logout failed:', error)
    } finally {
      // Always clear local storage
      localStorage.removeItem('access_token')
    }
  },

  /**
   * Check if user is authenticated (has valid, non-expired token)
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token')
    if (!token) return false
    return !isTokenExpired(token)
  },

  /**
   * Manually refresh the access token
   */
  async refreshToken(): Promise<string | null> {
    return refreshAccessToken()
  },

  /**
   * Revoke all sessions (logout from all devices)
   */
  async revokeAllSessions(): Promise<{ message: string; revoked_count: number }> {
    try {
      const response = await api.post('/auth/revoke-all-sessions', {}, { withCredentials: true })
      localStorage.removeItem('access_token')
      return response.data
    } catch (error: any) {
      console.error('Failed to revoke sessions:', error)
      throw new Error(`Failed to revoke sessions: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Get all active sessions for the current user
   */
  async getActiveSessions(): Promise<{
    sessions: Array<{
      id: string
      device_info: string
      ip_address: string
      created_at: string
      expires_at: string
    }>
    count: number
  }> {
    try {
      const response = await api.get('/auth/sessions')
      return response.data
    } catch (error: any) {
      console.error('Failed to get sessions:', error)
      throw new Error(`Failed to get sessions: ${error.response?.data?.detail || error.message}`)
    }
  }

}

// Telegram service
export const telegramService = {
  /**
   * Generate a link code for connecting Telegram
   */
  async generateLinkCode(): Promise<{
    code: string
    expires_at: string
    bot_url: string
    deep_link: string
  }> {
    try {
      const response = await api.post('/telegram/generate-code')
      return response.data
    } catch (error: any) {
      console.error('Failed to generate Telegram link code:', error)
      throw new Error(`Failed to generate link code: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Get Telegram connection status
   */
  async getStatus(): Promise<{
    connected: boolean
    telegram_user_id?: string
    telegram_username?: string
    linked_at?: string
  }> {
    try {
      const response = await api.get('/telegram/status')
      return response.data
    } catch (error: any) {
      console.error('Failed to get Telegram status:', error)
      throw new Error(`Failed to get Telegram status: ${error.response?.data?.detail || error.message}`)
    }
  },

  /**
   * Disconnect Telegram account
   */
  async disconnect(): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.post('/telegram/disconnect')
      return response.data
    } catch (error: any) {
      console.error('Failed to disconnect Telegram:', error)
      throw new Error(`Failed to disconnect: ${error.response?.data?.detail || error.message}`)
    }
  }
}

export default api
