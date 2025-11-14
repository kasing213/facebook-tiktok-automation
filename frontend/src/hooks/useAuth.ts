import axios from 'axios'
import { useState, useEffect, useCallback } from 'react'
import { authService } from '../services/api'
import { AuthStatus, Tenant } from '../types/auth'

const DEMO_TENANTS: Tenant[] = [
  {
    id: 'demo-tenant',
    name: 'Demo Organization',
    slug: 'demo-organization',
    is_active: true,
    created_at: '2024-01-01T00:00:00.000Z'
  }
]

export const useAuth = (tenantId: string | null) => {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAuthStatus = useCallback(async () => {
    if (!tenantId) return

    setLoading(true)
    setError(null)

    try {
      // Use the main API endpoint which provides proper data format
      const status = await authService.getTenantAuthStatus(tenantId)
      setAuthStatus(status)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch auth status'
      setError(errorMessage)
      console.error('Error fetching auth status:', err)
    } finally {
      setLoading(false)
    }
  }, [tenantId])

  useEffect(() => {
    fetchAuthStatus()
  }, [fetchAuthStatus])

  const refreshAuthStatus = useCallback(() => {
    fetchAuthStatus()
  }, [fetchAuthStatus])

  return {
    authStatus,
    loading,
    error,
    refreshAuthStatus
  }
}

export const useTenants = () => {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTenants = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const tenantsData = await authService.getTenants()
      setTenants(tenantsData)
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (!err.response) {
          setTenants(DEMO_TENANTS)
          setError('Backend API is unreachable. Using demo organization data until the server is available.')
        } else if (err.response.status === 404) {
          setError('No tenants found. Create an organization in the backend to continue.')
        } else {
          const detail = (err.response.data as { detail?: string })?.detail
          setError(detail || err.message || 'Failed to fetch tenants')
        }
      } else {
        setError(err instanceof Error ? err.message : 'Failed to fetch tenants')
      }
      console.error('Error fetching tenants:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTenants()
  }, [fetchTenants])

  return {
    tenants,
    loading,
    error,
    refreshTenants: fetchTenants
  }
}

export const useOAuth = () => {
  const [initiating, setInitiating] = useState<{facebook: boolean, tiktok: boolean}>({
    facebook: false,
    tiktok: false
  })
  const [errors, setErrors] = useState<{facebook: string | null, tiktok: string | null}>({
    facebook: null,
    tiktok: null
  })

  const initiateFacebookOAuth = useCallback(async (tenantId: string) => {
    setInitiating(prev => ({ ...prev, facebook: true }))
    setErrors(prev => ({ ...prev, facebook: null }))

    try {
      await authService.initiateFacebookOAuth(tenantId)
      // Note: If successful, user will be redirected and this component will unmount
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to initiate Facebook OAuth'
      console.error('Failed to initiate Facebook OAuth:', err)
      setErrors(prev => ({ ...prev, facebook: errorMessage }))
      setInitiating(prev => ({ ...prev, facebook: false }))
      throw err
    }
  }, [])

  const initiateTikTokOAuth = useCallback(async (tenantId: string) => {
    setInitiating(prev => ({ ...prev, tiktok: true }))
    setErrors(prev => ({ ...prev, tiktok: null }))

    try {
      await authService.initiateTikTokOAuth(tenantId)
      // Note: If successful, user will be redirected and this component will unmount
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to initiate TikTok OAuth'
      console.error('Failed to initiate TikTok OAuth:', err)
      setErrors(prev => ({ ...prev, tiktok: errorMessage }))
      setInitiating(prev => ({ ...prev, tiktok: false }))
      throw err
    }
  }, [])

  const clearErrors = useCallback(() => {
    setErrors({ facebook: null, tiktok: null })
  }, [])

  return {
    initiating,
    errors,
    clearErrors,
    initiateFacebookOAuth,
    initiateTikTokOAuth
  }
}

/**
 * Hook to check OAuth credentials configuration status
 * TODO: Remove this hook when credentials are properly configured
 */
export const useCredentialsStatus = () => {
  const [status, setStatus] = useState<{
    facebook: { appId: boolean; appSecret: boolean }
    tiktok: { clientId: boolean; clientSecret: boolean }
  } | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const checkStatus = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const credentialsStatus = await authService.checkCredentialsStatus()
      setStatus(credentialsStatus)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to check credentials status'
      setError(errorMessage)
      console.error('Error checking credentials status:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    checkStatus()
  }, [checkStatus])

  const isConfigured = status ?
    (status.facebook.appId && status.facebook.appSecret &&
     status.tiktok.clientId && status.tiktok.clientSecret) : false

  return {
    status,
    loading,
    error,
    isConfigured,
    recheckStatus: checkStatus
  }
}
