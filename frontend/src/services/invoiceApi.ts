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
  InvoiceHealthStatus,
  RegisteredClient,
  RegisteredClientListResponse,
  ClientLinkCodeResponse
} from '../types/invoice'

const BASE_PATH = '/api/integrations/invoice'

// Helper function to extract error message
function getErrorMessage(error: unknown, defaultMessage: string): string {
  if (error instanceof Error) {
    const axiosError = error as { response?: { data?: { detail?: string } } }
    return axiosError.response?.data?.detail || error.message || defaultMessage
  }
  return defaultMessage
}

export const invoiceService = {
  // Health check
  async getHealth(): Promise<InvoiceHealthStatus> {
    try {
      const response = await api.get(`${BASE_PATH}/health`)
      return response.data
    } catch (error) {
      console.error('Failed to get invoice health status:', error)
      throw new Error(getErrorMessage(error, 'Failed to check invoice service health'))
    }
  },

  // Statistics
  async getStats(): Promise<InvoiceStats> {
    try {
      const response = await api.get(`${BASE_PATH}/stats`)
      return response.data
    } catch (error) {
      console.error('Failed to get invoice stats:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch invoice statistics'))
    }
  },

  // Customer endpoints
  async listCustomers(params?: CustomerListParams): Promise<Customer[]> {
    try {
      const response = await api.get(`${BASE_PATH}/customers`, { params })
      return response.data
    } catch (error) {
      console.error('Failed to list customers:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch customers'))
    }
  },

  async getCustomer(customerId: string): Promise<Customer> {
    try {
      const response = await api.get(`${BASE_PATH}/customers/${customerId}`)
      return response.data
    } catch (error) {
      console.error('Failed to get customer:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch customer details'))
    }
  },

  async createCustomer(data: CustomerCreate): Promise<Customer> {
    try {
      const response = await api.post(`${BASE_PATH}/customers`, data)
      return response.data
    } catch (error) {
      console.error('Failed to create customer:', error)
      throw new Error(getErrorMessage(error, 'Failed to create customer'))
    }
  },

  async updateCustomer(customerId: string, data: CustomerUpdate): Promise<Customer> {
    try {
      const response = await api.put(`${BASE_PATH}/customers/${customerId}`, data)
      return response.data
    } catch (error) {
      console.error('Failed to update customer:', error)
      throw new Error(getErrorMessage(error, 'Failed to update customer'))
    }
  },

  async deleteCustomer(customerId: string): Promise<void> {
    try {
      await api.delete(`${BASE_PATH}/customers/${customerId}`)
    } catch (error) {
      console.error('Failed to delete customer:', error)
      throw new Error(getErrorMessage(error, 'Failed to delete customer'))
    }
  },

  // Invoice endpoints
  async listInvoices(params?: InvoiceListParams): Promise<Invoice[]> {
    try {
      const response = await api.get(`${BASE_PATH}/invoices`, { params })
      return response.data
    } catch (error) {
      console.error('Failed to list invoices:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch invoices'))
    }
  },

  async getInvoice(invoiceId: string): Promise<Invoice> {
    try {
      const response = await api.get(`${BASE_PATH}/invoices/${invoiceId}`)
      return response.data
    } catch (error) {
      console.error('Failed to get invoice:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch invoice details'))
    }
  },

  async createInvoice(data: InvoiceCreate): Promise<Invoice> {
    try {
      const response = await api.post(`${BASE_PATH}/invoices`, data)
      return response.data
    } catch (error) {
      console.error('Failed to create invoice:', error)
      throw new Error(getErrorMessage(error, 'Failed to create invoice'))
    }
  },

  async updateInvoice(invoiceId: string, data: InvoiceUpdate): Promise<Invoice> {
    try {
      const response = await api.put(`${BASE_PATH}/invoices/${invoiceId}`, data)
      return response.data
    } catch (error) {
      console.error('Failed to update invoice:', error)
      throw new Error(getErrorMessage(error, 'Failed to update invoice'))
    }
  },

  async deleteInvoice(invoiceId: string): Promise<void> {
    try {
      await api.delete(`${BASE_PATH}/invoices/${invoiceId}`)
    } catch (error) {
      console.error('Failed to delete invoice:', error)
      throw new Error(getErrorMessage(error, 'Failed to delete invoice'))
    }
  },

  // PDF download
  async downloadPDF(invoiceId: string): Promise<Blob> {
    try {
      const response = await api.get(`${BASE_PATH}/invoices/${invoiceId}/pdf`, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Failed to download PDF:', error)
      throw new Error(getErrorMessage(error, 'Failed to download invoice PDF'))
    }
  },

  // Export invoices
  async exportInvoices(params: InvoiceExportParams): Promise<Blob> {
    try {
      const response = await api.get(`${BASE_PATH}/invoices/export`, {
        params,
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Failed to export invoices:', error)
      throw new Error(getErrorMessage(error, 'Failed to export invoices'))
    }
  },

  // Helper to trigger file download
  downloadFile(blob: Blob, filename: string): void {
    try {
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download file:', error)
      throw new Error('Failed to download file. Please try again.')
    }
  },

  // Registered Clients (from Telegram Bot)
  async listRegisteredClients(params?: {
    limit?: number
    skip?: number
    telegram_linked?: boolean
  }): Promise<RegisteredClientListResponse> {
    try {
      const response = await api.get(`${BASE_PATH}/registered-clients`, { params })
      return response.data
    } catch (error) {
      console.error('Failed to list registered clients:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch registered clients'))
    }
  },

  async getRegisteredClient(clientId: string, includePendingInvoices = false): Promise<RegisteredClient> {
    try {
      const response = await api.get(`${BASE_PATH}/registered-clients/${clientId}`, {
        params: { include_pending_invoices: includePendingInvoices }
      })
      return response.data
    } catch (error) {
      console.error('Failed to get registered client:', error)
      throw new Error(getErrorMessage(error, 'Failed to fetch client details'))
    }
  },

  async generateClientLinkCode(clientId: string): Promise<ClientLinkCodeResponse> {
    try {
      const response = await api.post(`${BASE_PATH}/registered-clients/${clientId}/generate-link`)
      return response.data
    } catch (error) {
      console.error('Failed to generate link code:', error)
      throw new Error(getErrorMessage(error, 'Failed to generate registration link'))
    }
  },

  // Send invoice to customer via Telegram
  async sendToCustomer(invoiceId: string): Promise<{
    success: boolean
    message: string
    invoice_number: string
    telegram_username?: string
  }> {
    try {
      const response = await api.post(`${BASE_PATH}/invoices/${invoiceId}/send`)
      return response.data
    } catch (error) {
      console.error('Failed to send invoice to customer:', error)
      throw new Error(getErrorMessage(error, 'Failed to send invoice to customer'))
    }
  }
}

export default invoiceService
