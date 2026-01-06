// Invoice types for the Invoice API integration

export type InvoiceStatus = 'draft' | 'pending' | 'paid' | 'overdue' | 'cancelled'

export interface Customer {
  id: string
  name: string
  email?: string
  phone?: string
  address?: string
  company?: string
  notes?: string
  created_at?: string
  updated_at?: string
}

export interface CustomerCreate {
  name: string
  email?: string
  phone?: string
  address?: string
  company?: string
  notes?: string
}

export interface CustomerUpdate {
  name?: string
  email?: string
  phone?: string
  address?: string
  company?: string
  notes?: string
}

export interface LineItem {
  id?: string
  description: string
  quantity: number
  unit_price: number
  tax_rate?: number
  total?: number
}

export interface Invoice {
  id: string
  invoice_number: string
  customer_id: string
  customer?: Customer
  items: LineItem[]
  subtotal: number
  tax_rate?: number
  tax_amount?: number
  discount?: number
  discount_amount?: number
  total: number
  status: InvoiceStatus
  due_date?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface InvoiceCreate {
  customer_id: string
  items: LineItem[]
  due_date?: string
  notes?: string
  discount?: number
}

export interface InvoiceUpdate {
  items?: LineItem[]
  due_date?: string
  notes?: string
  discount?: number
  status?: InvoiceStatus
}

export interface InvoiceStats {
  total_invoices: number
  total_revenue: number
  pending_amount: number
  paid_amount: number
  overdue_count: number
  customers_count: number
}

export interface InvoiceListParams {
  limit?: number
  skip?: number
  customer_id?: string
  status?: InvoiceStatus
}

export interface CustomerListParams {
  limit?: number
  skip?: number
  search?: string
}

export interface InvoiceExportParams {
  format: 'csv' | 'xlsx'
  start_date?: string
  end_date?: string
}

export interface InvoiceHealthStatus {
  configured: boolean
  url: string
  api_status?: string
}
