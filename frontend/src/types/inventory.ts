// Inventory types for the Inventory Management system

export interface Product {
  id: string
  tenant_id: string
  name: string
  sku?: string
  description?: string
  unit_price: number
  cost_price?: number
  currency: string
  current_stock: number
  low_stock_threshold: number
  track_stock: boolean
  is_active: boolean
  image_id?: string
  image_url?: string
  created_at: string
  updated_at: string
}

export interface ProductCreate {
  name: string
  sku?: string
  description?: string
  unit_price: number
  cost_price?: number
  currency?: string
  current_stock?: number
  low_stock_threshold?: number
  track_stock?: boolean
}

export interface ProductUpdate {
  name?: string
  sku?: string
  description?: string
  unit_price?: number
  cost_price?: number
  currency?: string
  low_stock_threshold?: number
  track_stock?: boolean
}

export type MovementType = 'in' | 'out' | 'adjustment'

export interface StockMovement {
  id: string
  tenant_id: string
  product_id: string
  movement_type: MovementType
  quantity: number
  reference_type?: string
  reference_id?: string
  notes?: string
  created_by?: string
  created_at: string
}

export interface StockAdjustmentRequest {
  product_id: string
  new_stock_level: number
  notes?: string
}

export interface MovementSummary {
  product_id: string
  product_name: string
  product_sku?: string
  total_in: number
  total_out: number
  total_adjustments: number
  movement_count: number
}

export interface InventoryStats {
  total_products: number
  active_products: number
  low_stock_count: number
  total_stock_value: number
  total_movements: number
}

export interface ProductListParams {
  active_only?: boolean
  search?: string
  low_stock_only?: boolean
}

export interface ProductImageUploadResponse {
  product_id: string
  image_id: string
  image_url: string
}
