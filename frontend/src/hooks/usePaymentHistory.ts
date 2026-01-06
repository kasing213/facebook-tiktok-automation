import { useState, useEffect, useCallback } from 'react'
import { billingApi, PaginatedPayments } from '../services/billingApi'
import { PaymentRecord } from '../types/billing'

export interface UsePaymentHistoryOptions {
  pageSize?: number
  autoFetch?: boolean
}

export function usePaymentHistory(options: UsePaymentHistoryOptions = {}) {
  const { pageSize = 10, autoFetch = true } = options

  const [payments, setPayments] = useState<PaymentRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  // Fetch payment history
  const fetchPayments = useCallback(async (pageNum: number = 1) => {
    setLoading(true)
    setError(null)
    try {
      const result: PaginatedPayments = await billingApi.getPaymentHistory(pageNum, pageSize)
      setPayments(result.payments)
      setTotal(result.total)
      setPage(result.page)
      setHasMore(result.hasMore)
      return result
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to fetch payment history'
      setError(message)
      setPayments([])
    } finally {
      setLoading(false)
    }
  }, [pageSize])

  // Go to next page
  const nextPage = useCallback(async () => {
    if (hasMore) {
      await fetchPayments(page + 1)
    }
  }, [fetchPayments, page, hasMore])

  // Go to previous page
  const prevPage = useCallback(async () => {
    if (page > 1) {
      await fetchPayments(page - 1)
    }
  }, [fetchPayments, page])

  // Go to specific page
  const goToPage = useCallback(async (pageNum: number) => {
    if (pageNum >= 1 && pageNum <= Math.ceil(total / pageSize)) {
      await fetchPayments(pageNum)
    }
  }, [fetchPayments, total, pageSize])

  // Download invoice PDF
  const downloadInvoice = useCallback(async (payment: PaymentRecord) => {
    if (!payment.invoicePdfUrl && !payment.id) return

    setDownloadingId(payment.id)
    try {
      // If we have a direct PDF URL from Stripe, use it
      if (payment.invoicePdfUrl) {
        window.open(payment.invoicePdfUrl, '_blank')
      } else {
        // Otherwise, download via our API
        const filename = `invoice-${payment.date.split('T')[0]}.pdf`
        await billingApi.downloadInvoice(payment.id, filename)
      }
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to download invoice'
      setError(message)
    } finally {
      setDownloadingId(null)
    }
  }, [])

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Refresh current page
  const refresh = useCallback(async () => {
    await fetchPayments(page)
  }, [fetchPayments, page])

  // Fetch on mount if autoFetch is true
  useEffect(() => {
    if (autoFetch) {
      fetchPayments(1)
    }
  }, [autoFetch, fetchPayments])

  // Computed values
  const totalPages = Math.ceil(total / pageSize)
  const hasPrevPage = page > 1
  const hasNextPage = hasMore

  return {
    // Data
    payments,
    total,
    page,
    totalPages,

    // Loading states
    loading,
    downloadingId,

    // Error
    error,
    clearError,

    // Pagination
    hasPrevPage,
    hasNextPage,
    nextPage,
    prevPage,
    goToPage,

    // Actions
    fetchPayments,
    downloadInvoice,
    refresh
  }
}

export default usePaymentHistory
