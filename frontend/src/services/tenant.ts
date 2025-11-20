import api from './api'
import { Tenant } from '../types/auth'

/**
 * Get or create a default tenant for user registration
 * This is a temporary solution until we implement proper tenant selection
 */
export const getDefaultTenant = async (): Promise<string> => {
  try {
    // Try to get list of tenants
    const response = await api.get<Tenant[]>('/api/tenants')

    // If we have tenants, return the first one
    if (response.data && response.data.length > 0) {
      return response.data[0].id
    }

    // If no tenants exist, we need to create one
    // For now, we'll throw an error as tenant creation should be done via admin
    throw new Error('No tenants available. Please contact administrator.')

  } catch (error) {
    console.error('Failed to get default tenant:', error)
    throw new Error('Failed to get organization. Please try again later.')
  }
}
