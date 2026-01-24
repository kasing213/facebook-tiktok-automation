import api from './api'

/**
 * Create a new tenant/organization for user registration
 * Each new user gets their own organization with isolated data
 */
export const createTenant = async (name: string): Promise<string> => {
  try {
    const response = await api.post<{ id: string; name: string; slug: string }>(
      '/api/tenants/register',
      { name }
    )

    if (response.data && response.data.id) {
      return response.data.id
    }

    throw new Error('Failed to create organization')

  } catch (error: any) {
    console.error('Failed to create tenant:', error)
    const message = error.response?.data?.detail || 'Failed to create organization. Please try again later.'
    throw new Error(message)
  }
}

// Keep the old function name for backwards compatibility during transition
// TODO: Remove after all usages are updated
export const getDefaultTenant = async (): Promise<string> => {
  console.warn('getDefaultTenant is deprecated. Use createTenant(name) instead.')
  return createTenant('My Organization')
}
