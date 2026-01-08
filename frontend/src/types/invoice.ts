// Invoice types for the Invoice API integration

export type InvoiceStatus = 'draft' | 'pending' | 'paid' | 'overdue' | 'cancelled'

export type VerificationStatus = 'pending' | 'verified' | 'rejected'

export type Currency = 'KHR' | 'USD'

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
  // Payment verification fields
  bank?: string
  expected_account?: string
  currency: Currency
  verification_status: VerificationStatus
  verified_at?: string
  verified_by?: string
  verification_note?: string
  created_at: string
  updated_at: string
}

export interface InvoiceCreate {
  customer_id: string
  items: LineItem[]
  due_date?: string
  notes?: string
  discount?: number
  // Payment verification fields
  bank?: string
  expected_account?: string
  currency?: Currency
}

export interface InvoiceUpdate {
  items?: LineItem[]
  due_date?: string
  notes?: string
  discount?: number
  status?: InvoiceStatus
  // Payment verification fields
  bank?: string
  expected_account?: string
  currency?: Currency
}

export interface InvoiceVerify {
  verification_status: VerificationStatus
  verified_by?: string
  verification_note?: string
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

// Registered Clients (from Telegram Bot)
export interface RegisteredClient {
  id: string
  name: string
  email?: string
  phone?: string
  address?: string
  telegram_chat_id?: string
  telegram_username?: string
  telegram_linked: boolean
  telegram_linked_at?: string
  created_at?: string
  updated_at?: string
  pending_invoices?: PendingInvoice[]
}

export interface PendingInvoice {
  id: string
  invoice_number: string
  amount: number
  currency: Currency
  bank?: string
  expected_account?: string
  status: InvoiceStatus
  verification_status: VerificationStatus
  created_at?: string
}

export interface RegisteredClientListResponse {
  clients: RegisteredClient[]
  total: number
  limit: number
  skip: number
}

export interface ClientLinkCodeResponse {
  client_id: string
  client_name: string
  code: string
  link: string
  expires_at?: string
}
