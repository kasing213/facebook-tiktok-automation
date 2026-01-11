import React from 'react'
import styled from 'styled-components'
import { Invoice } from '../../types/invoice'
import { InvoiceStatusBadge } from './InvoiceStatusBadge'

interface InvoiceTableProps {
  invoices: Invoice[]
  onView: (invoice: Invoice) => void
  onEdit: (invoice: Invoice) => void
  onDelete: (invoice: Invoice) => void
  onDownloadPDF: (invoice: Invoice) => void
  onSendToCustomer?: (invoice: Invoice) => void
  loading?: boolean
  sendingInvoiceId?: string | null
}

const TableWrapper = styled.div`
  overflow-x: auto;
`

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
`

const TableHeader = styled.thead`
  background: #f9fafb;
`

const HeaderCell = styled.th`
  text-align: left;
  padding: 0.875rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
`

const TableBody = styled.tbody``

const TableRow = styled.tr`
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: #f9fafb;
  }

  &:last-child {
    border-bottom: none;
  }
`

const TableCell = styled.td`
  padding: 1rem;
  font-size: 0.875rem;
  color: #1f2937;
  vertical-align: middle;
`

const InvoiceNumber = styled.div`
  font-weight: 600;
  color: #4a90e2;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
`

const CustomerName = styled.div`
  font-weight: 500;
  color: #1f2937;
`

const CustomerEmail = styled.div`
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
`

const Amount = styled.div`
  font-weight: 600;
  color: #1f2937;
  text-align: right;
`

const DateCell = styled.div`
  color: #6b7280;
  white-space: nowrap;
`

const ActionsCell = styled.div`
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
`

const ActionButton = styled.button<{ $variant?: 'danger' | 'primary' }>`
  padding: 0.375rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  ${props => {
    switch (props.$variant) {
      case 'danger':
        return `
          background: white;
          color: #dc3545;
          border: 1px solid #dc3545;

          &:hover {
            background: #dc3545;
            color: white;
          }
        `
      case 'primary':
        return `
          background: #4a90e2;
          color: white;
          border: none;

          &:hover {
            background: #3a7bd5;
          }
        `
      default:
        return `
          background: white;
          color: #6b7280;
          border: 1px solid #e5e7eb;

          &:hover {
            background: #f9fafb;
            border-color: #d1d5db;
          }
        `
    }
  }}
`

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem;
  color: #6b7280;

  h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 0.5rem;
  }

  p {
    font-size: 0.875rem;
  }
`

const LoadingState = styled.div`
  text-align: center;
  padding: 3rem;
  color: #6b7280;
`

export const InvoiceTable: React.FC<InvoiceTableProps> = ({
  invoices,
  onView,
  onEdit,
  onDelete,
  onDownloadPDF,
  onSendToCustomer,
  loading = false,
  sendingInvoiceId = null
}) => {
  const formatCurrency = (amount: number | null | undefined): string => {
    if (amount === null || amount === undefined || isNaN(amount)) {
      return '$0.00'
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (loading) {
    return <LoadingState>Loading invoices...</LoadingState>
  }

  if (invoices.length === 0) {
    return (
      <EmptyState>
        <h3>No invoices yet</h3>
        <p>Create your first invoice to get started.</p>
      </EmptyState>
    )
  }

  return (
    <TableWrapper>
      <Table>
        <TableHeader>
          <tr>
            <HeaderCell>Invoice #</HeaderCell>
            <HeaderCell>Customer</HeaderCell>
            <HeaderCell>Status</HeaderCell>
            <HeaderCell>Due Date</HeaderCell>
            <HeaderCell style={{ textAlign: 'right' }}>Amount</HeaderCell>
            <HeaderCell style={{ textAlign: 'right' }}>Actions</HeaderCell>
          </tr>
        </TableHeader>
        <TableBody>
          {invoices.map(invoice => (
            <TableRow key={invoice.id}>
              <TableCell>
                <InvoiceNumber onClick={() => onView(invoice)}>
                  {invoice.invoice_number}
                </InvoiceNumber>
              </TableCell>
              <TableCell>
                <CustomerName>{invoice.customer?.name || 'Unknown'}</CustomerName>
                {invoice.customer?.email && (
                  <CustomerEmail>{invoice.customer.email}</CustomerEmail>
                )}
              </TableCell>
              <TableCell>
                <InvoiceStatusBadge status={invoice.status} />
              </TableCell>
              <TableCell>
                <DateCell>
                  {invoice.due_date ? formatDate(invoice.due_date) : '-'}
                </DateCell>
              </TableCell>
              <TableCell>
                <Amount>{formatCurrency(invoice.total)}</Amount>
              </TableCell>
              <TableCell>
                <ActionsCell>
                  {onSendToCustomer && (
                    <ActionButton
                      $variant="primary"
                      onClick={() => onSendToCustomer(invoice)}
                      disabled={sendingInvoiceId === invoice.id}
                      title="Send invoice to customer via Telegram"
                    >
                      {sendingInvoiceId === invoice.id ? 'Sending...' : 'Send'}
                    </ActionButton>
                  )}
                  <ActionButton onClick={() => onDownloadPDF(invoice)}>
                    PDF
                  </ActionButton>
                  <ActionButton onClick={() => onEdit(invoice)}>
                    Edit
                  </ActionButton>
                  <ActionButton $variant="danger" onClick={() => onDelete(invoice)}>
                    Delete
                  </ActionButton>
                </ActionsCell>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableWrapper>
  )
}

export default InvoiceTable
