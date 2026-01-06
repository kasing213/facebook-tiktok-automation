import { useState, useCallback } from 'react'
import { invoiceService } from '../services/invoiceApi'
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
  InvoiceHealthStatus
} from '../types/invoice'

export function useInvoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [stats, setStats] = useState<InvoiceStats | null>(null)
  const [health, setHealth] = useState<InvoiceHealthStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Check health
  const checkHealth = useCallback(async () => {
    try {
      const data = await invoiceService.getHealth()
      setHealth(data)
      return data
    } catch (err: any) {
      setError(err.message || 'Failed to check invoice API health')
      return null
    }
  }, [])

  // Fetch statistics
  const fetchStats = useCallback(async () => {
    try {
      const data = await invoiceService.getStats()
      setStats(data)
      return data
    } catch (err: any) {
      setError(err.message || 'Failed to fetch statistics')
      return null
    }
  }, [])

  // Fetch invoices
  const fetchInvoices = useCallback(async (params?: InvoiceListParams) => {
    setLoading(true)
    setError(null)
    try {
      const data = await invoiceService.listInvoices(params)
      setInvoices(data)
      return data
    } catch (err: any) {
      setError(err.message || 'Failed to fetch invoices')
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  // Get single invoice
  const getInvoice = useCallback(async (invoiceId: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await invoiceService.getInvoice(invoiceId)
      return data
    } catch (err: any) {
      setError(err.message || 'Failed to fetch invoice')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  // Create invoice
  const createInvoice = useCallback(async (data: InvoiceCreate) => {
    setSaving(true)
    setError(null)
    try {
      const invoice = await invoiceService.createInvoice(data)
      setInvoices(prev => [invoice, ...prev])
      return invoice
    } catch (err: any) {
      setError(err.message || 'Failed to create invoice')
      throw err
    } finally {
      setSaving(false)
    }
  }, [])

  // Update invoice
  const updateInvoice = useCallback(async (invoiceId: string, data: InvoiceUpdate) => {
    setSaving(true)
    setError(null)
    try {
      const invoice = await invoiceService.updateInvoice(invoiceId, data)
      setInvoices(prev => prev.map(inv => inv.id === invoiceId ? invoice : inv))
      return invoice
    } catch (err: any) {
      setError(err.message || 'Failed to update invoice')
      throw err
    } finally {
      setSaving(false)
    }
  }, [])

  // Delete invoice
  const deleteInvoice = useCallback(async (invoiceId: string) => {
    setDeleting(true)
    setError(null)
    try {
      await invoiceService.deleteInvoice(invoiceId)
      setInvoices(prev => prev.filter(inv => inv.id !== invoiceId))
    } catch (err: any) {
      setError(err.message || 'Failed to delete invoice')
      throw err
    } finally {
      setDeleting(false)
    }
  }, [])

  // Download PDF
  const downloadPDF = useCallback(async (invoiceId: string, invoiceNumber?: string) => {
    try {
      const blob = await invoiceService.downloadPDF(invoiceId)
      const filename = `invoice-${invoiceNumber || invoiceId}.pdf`
      invoiceService.downloadFile(blob, filename)
    } catch (err: any) {
      setError(err.message || 'Failed to download PDF')
      throw err
    }
  }, [])

  // Export invoices
  const exportInvoices = useCallback(async (format: 'csv' | 'xlsx', startDate?: string, endDate?: string) => {
    try {
      const blob = await invoiceService.exportInvoices({ format, start_date: startDate, end_date: endDate })
      const filename = `invoices.${format}`
      invoiceService.downloadFile(blob, filename)
    } catch (err: any) {
      setError(err.message || 'Failed to export invoices')
      throw err
    }
  }, [])

  // Fetch customers
  const fetchCustomers = useCallback(async (params?: CustomerListParams) => {
    setLoading(true)
    setError(null)
    try {
      const data = await invoiceService.listCustomers(params)
      setCustomers(data)
      return data
    } catch (err: any) {
      setError(err.message || 'Failed to fetch customers')
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  // Get single customer
  const getCustomer = useCallback(async (customerId: string) => {
    try {
      const data = await invoiceService.getCustomer(customerId)
      return data
    } catch (err: any) {
      setError(err.message || 'Failed to fetch customer')
      return null
    }
  }, [])

  // Create customer
  const createCustomer = useCallback(async (data: CustomerCreate) => {
    setSaving(true)
    setError(null)
    try {
      const customer = await invoiceService.createCustomer(data)
      setCustomers(prev => [customer, ...prev])
      return customer
    } catch (err: any) {
      setError(err.message || 'Failed to create customer')
      throw err
    } finally {
      setSaving(false)
    }
  }, [])

  // Update customer
  const updateCustomer = useCallback(async (customerId: string, data: CustomerUpdate) => {
    setSaving(true)
    setError(null)
    try {
      const customer = await invoiceService.updateCustomer(customerId, data)
      setCustomers(prev => prev.map(c => c.id === customerId ? customer : c))
      return customer
    } catch (err: any) {
      setError(err.message || 'Failed to update customer')
      throw err
    } finally {
      setSaving(false)
    }
  }, [])

  // Delete customer
  const deleteCustomer = useCallback(async (customerId: string) => {
    setDeleting(true)
    setError(null)
    try {
      await invoiceService.deleteCustomer(customerId)
      setCustomers(prev => prev.filter(c => c.id !== customerId))
    } catch (err: any) {
      setError(err.message || 'Failed to delete customer')
      throw err
    } finally {
      setDeleting(false)
    }
  }, [])

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    // State
    invoices,
    customers,
    stats,
    health,
    loading,
    error,
    saving,
    deleting,

    // Invoice actions
    fetchInvoices,
    getInvoice,
    createInvoice,
    updateInvoice,
    deleteInvoice,
    downloadPDF,
    exportInvoices,

    // Customer actions
    fetchCustomers,
    getCustomer,
    createCustomer,
    updateCustomer,
    deleteCustomer,

    // Utility
    checkHealth,
    fetchStats,
    clearError,
  }
}

export default useInvoices
