import axios from 'axios'
import {
  Product,
  ProductCreate,
  ProductUpdate,
  StockMovement,
  StockAdjustmentRequest,
  MovementSummary,
  ProductListParams,
  ProductImageUploadResponse
} from '../types/inventory'

// Use same API base URL as main api.ts
const API_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? 'https://web-production-3ed15.up.railway.app' : 'http://localhost:8000')

const inventoryApi = axios.create({
  baseURL: `${API_URL}/inventory`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth interceptor
inventoryApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors by redirecting to login
inventoryApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const inventoryService = {
  // Products
  async listProducts(params?: ProductListParams): Promise<Product[]> {
    const response = await inventoryApi.get('/products', { params })
    return response.data
  },

  async getProduct(id: string): Promise<Product> {
    const response = await inventoryApi.get(`/products/${id}`)
    return response.data
  },

  async createProduct(data: ProductCreate): Promise<Product> {
    const response = await inventoryApi.post('/products', data)
    return response.data
  },

  async updateProduct(id: string, data: ProductUpdate): Promise<Product> {
    const response = await inventoryApi.put(`/products/${id}`, data)
    return response.data
  },

  async deleteProduct(id: string): Promise<{ message: string }> {
    const response = await inventoryApi.delete(`/products/${id}`)
    return response.data
  },

  // Stock Management
  async adjustStock(data: StockAdjustmentRequest): Promise<{
    message: string
    movement_id: string
    new_stock_level: number
  }> {
    const response = await inventoryApi.post('/adjust-stock', data)
    return response.data
  },

  async getLowStockProducts(): Promise<Product[]> {
    const response = await inventoryApi.get('/low-stock')
    return response.data
  },

  // Stock Movements
  async listMovements(params?: {
    product_id?: string
    limit?: number
  }): Promise<StockMovement[]> {
    const response = await inventoryApi.get('/movements', { params })
    return response.data
  },

  async getMovementSummary(params?: {
    start_date?: string
    end_date?: string
  }): Promise<{
    period: { start_date?: string; end_date?: string }
    summary: MovementSummary[]
  }> {
    const response = await inventoryApi.get('/movements/summary', { params })
    return response.data
  },

  // Product Images (MongoDB GridFS)
  async uploadProductImage(productId: string, file: File): Promise<ProductImageUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await inventoryApi.post(
      `/products/${productId}/image`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 second timeout for uploads
      }
    )
    return response.data
  },

  async deleteProductImage(productId: string): Promise<{ message: string }> {
    const response = await inventoryApi.delete(`/products/${productId}/image`)
    return response.data
  },

  /**
   * Get the full URL for a product image
   * Constructs the URL based on the image_id
   */
  getProductImageUrl(imageId: string): string {
    return `${API_URL}/inventory/products/image/${imageId}`
  },

  /**
   * Fetch authenticated product image as blob URL for img tags.
   * Converts internal API URLs to blob URLs that can be used in <img> src.
   */
  async getImageBlobUrl(imageUrl: string): Promise<string> {
    // Return empty for no URL
    if (!imageUrl) return ''

    // Return external URLs as-is
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      // Check if it's our API URL that needs auth
      if (!imageUrl.includes('/inventory/products/image/')) {
        return imageUrl
      }
    }

    try {
      // Extract the image path and fetch with auth
      let apiPath = imageUrl
      if (imageUrl.includes('/inventory/products/image/')) {
        apiPath = imageUrl.substring(imageUrl.indexOf('/inventory/products/image/') + '/inventory'.length)
      } else if (imageUrl.startsWith('/products/image/')) {
        apiPath = imageUrl
      }

      const response = await inventoryApi.get(apiPath, {
        responseType: 'blob'
      })
      return URL.createObjectURL(response.data)
    } catch (error) {
      console.error('Failed to fetch product image:', error)
      return ''
    }
  }
}

// Invoice integration - get products for invoice line items
// This uses the invoice integration endpoint, not the inventory endpoint
const invoiceApi = axios.create({
  baseURL: `${API_URL}/api/integrations/invoice`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

invoiceApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const invoiceProductService = {
  /**
   * Get products available for invoice line items
   * Returns products with stock info for the invoice product picker
   */
  async getProductsForInvoice(search?: string): Promise<Array<{
    id: string
    name: string
    sku?: string
    unit_price: number
    currency: string
    current_stock: number
    track_stock: boolean
  }>> {
    const response = await invoiceApi.get('/products', {
      params: search ? { search } : undefined
    })
    return response.data
  }
}

export default inventoryService
