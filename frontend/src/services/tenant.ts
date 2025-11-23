import api from './api'

/**
 * Get or create a default tenant for user registration
 * This will automatically create a default tenant if none exists
 */
export const getDefaultTenant = async (): Promise<string> => {
  try {
    // Use the new default tenant endpoint that auto-creates if needed
    const response = await api.get<{ id: string; name: string; slug: string }>('/api/tenants/default')

    if (response.data && response.data.id) {
      return response.data.id
    }

    throw new Error('Failed to get default tenant ID')

  } catch (error) {
    console.error('Failed to get default tenant:', error)
    throw new Error('Failed to get organization. Please try again later.')
  }
}
