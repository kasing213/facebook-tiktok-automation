import api from './api'
import {
  Invoice,
  InvoiceCreate,
  InvoiceUpdate,
  Customer,
  CustomerCreate,
  CustomerUpdate,
  InvoiceStats,
  InvoiceListParams,
  CustomerListParams,
  InvoiceExportParams,
  InvoiceHealthStatus
} from '../types/invoice'

const BASE_PATH = '/api/integrations/invoice'

export const invoiceService = {
  // Health check
  async getHealth(): Promise<InvoiceHealthStatus> {
    const response = await api.get(`${BASE_PATH}/health`)
    return response.data
  },

  // Statistics
  async getStats(): Promise<InvoiceStats> {
    const response = await api.get(`${BASE_PATH}/stats`)
    return response.data
  },

  // Customer endpoints
  async listCustomers(params?: CustomerListParams): Promise<Customer[]> {
    const response = await api.get(`${BASE_PATH}/customers`, { params })
    return response.data
  },

  async getCustomer(customerId: string): Promise<Customer> {
    const response = await api.get(`${BASE_PATH}/customers/${customerId}`)
    return response.data
  },

  async createCustomer(data: CustomerCreate): Promise<Customer> {
    const response = await api.post(`${BASE_PATH}/customers`, data)
    return response.data
  },

  async updateCustomer(customerId: string, data: CustomerUpdate): Promise<Customer> {
    const response = await api.put(`${BASE_PATH}/customers/${customerId}`, data)
    return response.data
  },

  async deleteCustomer(customerId: string): Promise<void> {
    await api.delete(`${BASE_PATH}/customers/${customerId}`)
  },

  // Invoice endpoints
  async listInvoices(params?: InvoiceListParams): Promise<Invoice[]> {
    const response = await api.get(`${BASE_PATH}/invoices`, { params })
    return response.data
  },

  async getInvoice(invoiceId: string): Promise<Invoice> {
    const response = await api.get(`${BASE_PATH}/invoices/${invoiceId}`)
    return response.data
  },

  async createInvoice(data: InvoiceCreate): Promise<Invoice> {
    const response = await api.post(`${BASE_PATH}/invoices`, data)
    return response.data
  },

  async updateInvoice(invoiceId: string, data: InvoiceUpdate): Promise<Invoice> {
    const response = await api.put(`${BASE_PATH}/invoices/${invoiceId}`, data)
    return response.data
  },

  async deleteInvoice(invoiceId: string): Promise<void> {
    await api.delete(`${BASE_PATH}/invoices/${invoiceId}`)
  },

  // PDF download
  async downloadPDF(invoiceId: string): Promise<Blob> {
    const response = await api.get(`${BASE_PATH}/invoices/${invoiceId}/pdf`, {
      responseType: 'blob'
    })
    return response.data
  },

  // Export invoices
  async exportInvoices(params: InvoiceExportParams): Promise<Blob> {
    const response = await api.get(`${BASE_PATH}/invoices/export`, {
      params,
      responseType: 'blob'
    })
    return response.data
  },

  // Helper to trigger file download
  downloadFile(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }
}

export default invoiceService
