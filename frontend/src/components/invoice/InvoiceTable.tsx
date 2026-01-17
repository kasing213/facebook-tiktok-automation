import React, { useState, useRef, useEffect } from 'react'
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
  onDuplicate?: (invoice: Invoice) => void
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
  align-items: center;
`

const SendButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #22c55e;
  color: white;
  border: none;

  &:hover {
    background: #16a34a;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  svg {
    width: 14px;
    height: 14px;
  }
`

const IconButton = styled.button`
  padding: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    color: #6b7280;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  svg {
    width: 18px;
    height: 18px;
  }
`

const MenuButton = styled.button`
  padding: 0.375rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: #f9fafb;
    border-color: #d1d5db;
  }

  svg {
    width: 18px;
    height: 18px;
  }
`

const DropdownMenu = styled.div<{ $visible: boolean }>`
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 0.25rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 140px;
  z-index: 100;
  display: ${props => props.$visible ? 'block' : 'none'};
`

const DropdownItem = styled.button<{ $danger?: boolean }>`
  width: 100%;
  padding: 0.625rem 1rem;
  text-align: left;
  background: transparent;
  border: none;
  font-size: 0.875rem;
  color: ${props => props.$danger ? '#dc3545' : '#374151'};
  cursor: pointer;
  transition: background 0.2s ease;

  &:hover {
    background: ${props => props.$danger ? '#fef2f2' : '#f9fafb'};
  }

  &:first-child {
    border-radius: 8px 8px 0 0;
  }

  &:last-child {
    border-radius: 0 0 8px 8px;
  }
`

const MenuWrapper = styled.div`
  position: relative;
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
  onDuplicate,
  loading = false,
  sendingInvoiceId = null
}) => {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpenMenuId(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

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

  // Check if invoice needs "Send" button (not paid)
  const showSendButton = (invoice: Invoice) => {
    return invoice.status !== 'paid' && invoice.status !== 'cancelled'
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
                  {/* Send Button - only for unpaid invoices */}
                  {onSendToCustomer && showSendButton(invoice) && (
                    <SendButton
                      onClick={() => onSendToCustomer(invoice)}
                      disabled={sendingInvoiceId === invoice.id}
                      title="Send invoice to customer via Telegram"
                    >
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      {sendingInvoiceId === invoice.id ? 'Sending...' : 'Send'}
                    </SendButton>
                  )}

                  {/* Copy/Duplicate Icon */}
                  {onDuplicate && (
                    <IconButton
                      title="Duplicate invoice"
                      onClick={() => onDuplicate(invoice)}
                    >
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </IconButton>
                  )}

                  {/* Edit Icon */}
                  <IconButton title="Edit invoice" onClick={() => onEdit(invoice)}>
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </IconButton>

                  {/* Three-dot Menu */}
                  <MenuWrapper ref={openMenuId === invoice.id ? menuRef : null}>
                    <MenuButton
                      onClick={() => setOpenMenuId(openMenuId === invoice.id ? null : invoice.id)}
                      title="More options"
                    >
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                      </svg>
                    </MenuButton>
                    <DropdownMenu $visible={openMenuId === invoice.id}>
                      <DropdownItem onClick={() => {
                        onView(invoice)
                        setOpenMenuId(null)
                      }}>
                        View Details
                      </DropdownItem>
                      <DropdownItem onClick={() => {
                        onDownloadPDF(invoice)
                        setOpenMenuId(null)
                      }}>
                        Download PDF
                      </DropdownItem>
                      <DropdownItem
                        $danger
                        onClick={() => {
                          onDelete(invoice)
                          setOpenMenuId(null)
                        }}
                      >
                        Delete
                      </DropdownItem>
                    </DropdownMenu>
                  </MenuWrapper>
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
