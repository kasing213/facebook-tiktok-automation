import { useNavigate } from 'react-router-dom'
import { usePaymentHistory } from '../../../hooks/usePaymentHistory'
import {
  PageContainer,
  PageHeader,
  PageTitle,
  BackLink,
  Card,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableCell,
  StatusBadge,
  DownloadLink,
  Pagination,
  PaginationInfo,
  PaginationButtons,
  PaginationButton,
  EmptyState,
  EmptyIcon,
  EmptyText,
  LoadingSpinner,
  ErrorMessage
} from './shared/styles'

export function PaymentHistoryPage() {
  const navigate = useNavigate()
  const {
    payments,
    total,
    page,
    totalPages,
    loading,
    error,
    hasPrevPage,
    hasNextPage,
    nextPage,
    prevPage,
    downloadInvoice,
    downloadingId
  } = usePaymentHistory({ pageSize: 10 })

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  return (
    <PageContainer>
      <BackLink onClick={() => navigate('/dashboard/billing')}>
        ← Back to Billing
      </BackLink>

      <PageHeader>
        <PageTitle>Payment History</PageTitle>
      </PageHeader>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      <Card>
        {loading ? (
          <LoadingSpinner />
        ) : payments.length === 0 ? (
          <EmptyState>
            <EmptyIcon>--</EmptyIcon>
            <EmptyText>No payment history yet</EmptyText>
            <p style={{ color: '#9ca3af', fontSize: '0.875rem', marginTop: '0.5rem' }}>
              When you make a purchase, your payments will appear here.
            </p>
          </EmptyState>
        ) : (
          <>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>Date</TableHeader>
                  <TableHeader>Description</TableHeader>
                  <TableHeader>Amount</TableHeader>
                  <TableHeader>Status</TableHeader>
                  <TableHeader>Invoice</TableHeader>
                </TableRow>
              </TableHead>
              <tbody>
                {payments.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell>{formatDate(payment.date)}</TableCell>
                    <TableCell>{payment.description}</TableCell>
                    <TableCell style={{ fontWeight: 600 }}>
                      {formatCurrency(payment.amount)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge $status={payment.status}>
                        {payment.status}
                      </StatusBadge>
                    </TableCell>
                    <TableCell>
                      {payment.invoicePdfUrl || payment.invoiceUrl ? (
                        <DownloadLink
                          onClick={() => downloadInvoice(payment)}
                          disabled={downloadingId === payment.id}
                        >
                          {downloadingId === payment.id ? 'Opening...' : 'Download PDF'}
                        </DownloadLink>
                      ) : (
                        <span style={{ color: '#9ca3af' }}>-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </tbody>
            </Table>

            {totalPages > 1 && (
              <Pagination>
                <PaginationInfo>
                  Showing {(page - 1) * 10 + 1} - {Math.min(page * 10, total)} of {total} payments
                </PaginationInfo>
                <PaginationButtons>
                  <PaginationButton
                    onClick={prevPage}
                    disabled={!hasPrevPage}
                  >
                    Previous
                  </PaginationButton>
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter(p => {
                      // Show first, last, and pages around current
                      if (p === 1 || p === totalPages) return true
                      if (Math.abs(p - page) <= 1) return true
                      return false
                    })
                    .map((p, idx, arr) => {
                      // Add ellipsis if there's a gap
                      const prev = arr[idx - 1]
                      const showEllipsis = prev && p - prev > 1

                      return (
                        <span key={p}>
                          {showEllipsis && (
                            <span style={{ padding: '0 0.5rem', color: '#6b7280' }}>...</span>
                          )}
                          <PaginationButton
                            $active={p === page}
                            onClick={() => {
                              if (p !== page) {
                                // Use goToPage from hook if needed
                              }
                            }}
                          >
                            {p}
                          </PaginationButton>
                        </span>
                      )
                    })}
                  <PaginationButton
                    onClick={nextPage}
                    disabled={!hasNextPage}
                  >
                    Next
                  </PaginationButton>
                </PaginationButtons>
              </Pagination>
            )}
          </>
        )}
      </Card>
    </PageContainer>
  )
}

export default PaymentHistoryPage
