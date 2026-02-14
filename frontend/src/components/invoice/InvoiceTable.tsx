import React, { useState, useRef, useEffect } from 'react'
import styled from 'styled-components'
import { Invoice } from '../../types/invoice'
import { InvoiceStatusBadge } from './InvoiceStatusBadge'
import { easings, reduceMotion } from '../../styles/animations'
import { useStaggeredAnimation } from '../../hooks/useScrollAnimation'

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

  @media (max-width: 768px) {
    display: none;
  }
`

const TableHeader = styled.thead`
  background: ${props => props.theme.backgroundTertiary};
`

const HeaderCell = styled.th`
  text-align: left;
  padding: 0.875rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: ${props => props.theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid ${props => props.theme.border};
  white-space: nowrap;
`

const TableBody = styled.tbody``

const TableRow = styled.tr<{ $isVisible?: boolean; $delay?: number }>`
  border-bottom: 1px solid ${props => props.theme.border};
  opacity: ${props => props.$isVisible !== undefined ? (props.$isVisible ? 1 : 0) : 1};
  transform: ${props => props.$isVisible !== undefined ? (props.$isVisible ? 'translateX(0)' : 'translateX(-8px)') : 'translateX(0)'};
  transition: opacity 0.3s ${easings.easeOutCubic},
              transform 0.3s ${easings.easeOutCubic},
              background-color 0.15s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    background-color: ${props => props.theme.backgroundTertiary};
  }

  &:last-child {
    border-bottom: none;
  }

  ${reduceMotion}
`

const TableCell = styled.td`
  padding: 1rem;
  font-size: 0.875rem;
  color: ${props => props.theme.textPrimary};
  vertical-align: middle;
`

const InvoiceNumber = styled.div`
  font-weight: 600;
  color: ${props => props.theme.accent};
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
`

const CustomerName = styled.div`
  font-weight: 500;
  color: ${props => props.theme.textPrimary};
`

const CustomerEmail = styled.div`
  font-size: 0.75rem;
  color: ${props => props.theme.textSecondary};
  margin-top: 0.25rem;
`

const Amount = styled.div`
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  text-align: right;
`

const DateCell = styled.div`
  color: ${props => props.theme.textSecondary};
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
  transition: background 0.2s ease,
              transform 0.15s ${easings.easeOutCubic},
              box-shadow 0.2s ease;
  background: #22c55e;
  color: white;
  border: none;

  &:hover:not(:disabled) {
    background: #16a34a;
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(34, 197, 94, 0.3);
  }

  &:active:not(:disabled) {
    transform: translateY(0) scale(0.98);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  svg {
    width: 14px;
    height: 14px;
  }

  ${reduceMotion}
`

const IconButton = styled.button`
  padding: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 0.2s ease,
              transform 0.15s ${easings.easeOutCubic},
              background 0.15s ease;
  color: ${props => props.theme.textMuted};
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;

  &:hover:not(:disabled) {
    color: ${props => props.theme.accent};
    background: ${props => props.theme.mode === 'dark' ? 'rgba(62, 207, 142, 0.1)' : 'rgba(74, 144, 226, 0.08)'};
    transform: scale(1.1);
  }

  &:active:not(:disabled) {
    transform: scale(0.95);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  svg {
    width: 18px;
    height: 18px;
  }

  ${reduceMotion}
`

const MenuButton = styled.button`
  padding: 0.375rem;
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: ${props => props.theme.textSecondary};
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: ${props => props.theme.backgroundTertiary};
    border-color: ${props => props.theme.textMuted};
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
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  box-shadow: 0 4px 12px ${props => props.theme.mode === 'dark' ? 'rgba(0, 0, 0, 0.4)' : 'rgba(0, 0, 0, 0.15)'};
  min-width: 140px;
  z-index: 100;
  opacity: ${props => props.$visible ? 1 : 0};
  transform: ${props => props.$visible ? 'translateY(0) scale(1)' : 'translateY(-8px) scale(0.95)'};
  transform-origin: top right;
  pointer-events: ${props => props.$visible ? 'auto' : 'none'};
  transition: opacity 0.15s ${easings.easeOutCubic},
              transform 0.2s ${easings.easeOutCubic};

  ${reduceMotion}
`

const DropdownItem = styled.button<{ $danger?: boolean }>`
  width: 100%;
  padding: 0.625rem 1rem;
  text-align: left;
  background: transparent;
  border: none;
  font-size: 0.875rem;
  color: ${props => props.$danger ? props.theme.error : props.theme.textPrimary};
  cursor: pointer;
  transition: background 0.2s ease;

  &:hover {
    background: ${props => props.$danger
      ? (props.theme.mode === 'dark' ? 'rgba(239, 68, 68, 0.1)' : '#fef2f2')
      : props.theme.backgroundTertiary};
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

/* Mobile card view - shown only on small screens */
const MobileCardList = styled.div`
  display: none;

  @media (max-width: 768px) {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
`

const MobileCard = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 10px;
  padding: 1rem;
  opacity: ${props => props.$isVisible !== undefined ? (props.$isVisible ? 1 : 0) : 1};
  transform: ${props => props.$isVisible !== undefined ? (props.$isVisible ? 'translateY(0)' : 'translateY(8px)') : 'translateY(0)'};
  transition: opacity 0.3s ${easings.easeOutCubic},
              transform 0.3s ${easings.easeOutCubic};
  transition-delay: ${props => props.$delay || 0}ms;

  ${reduceMotion}
`

const MobileCardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
`

const MobileCardBody = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.875rem;
`

const MobileCardRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`

const MobileCardLabel = styled.span`
  font-size: 0.75rem;
  color: ${props => props.theme.textMuted};
`

const MobileCardActions = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid ${props => props.theme.border};
  flex-wrap: wrap;
  align-items: center;
`

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem;
  color: ${props => props.theme.textSecondary};

  h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: ${props => props.theme.textPrimary};
    margin-bottom: 0.5rem;
  }

  p {
    font-size: 0.875rem;
  }
`

const LoadingState = styled.div`
  text-align: center;
  padding: 3rem;
  color: ${props => props.theme.textSecondary};
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

  // Animation hook for table rows
  const rowsVisible = useStaggeredAnimation(invoices.length, 50)

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
          {invoices.map((invoice, index) => (
            <TableRow key={invoice.id} $isVisible={rowsVisible[index]} $delay={index * 50}>
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

      {/* Mobile card view */}
      <MobileCardList>
        {invoices.map((invoice, index) => (
          <MobileCard key={invoice.id} $isVisible={rowsVisible[index]} $delay={index * 50}>
            <MobileCardHeader>
              <InvoiceNumber onClick={() => onView(invoice)}>
                {invoice.invoice_number}
              </InvoiceNumber>
              <InvoiceStatusBadge status={invoice.status} />
            </MobileCardHeader>
            <MobileCardBody>
              <CustomerName>{invoice.customer?.name || 'Unknown'}</CustomerName>
              <MobileCardRow>
                <MobileCardLabel>Due</MobileCardLabel>
                <DateCell>{invoice.due_date ? formatDate(invoice.due_date) : '-'}</DateCell>
              </MobileCardRow>
              <MobileCardRow>
                <MobileCardLabel>Amount</MobileCardLabel>
                <Amount style={{ textAlign: 'left' }}>{formatCurrency(invoice.total)}</Amount>
              </MobileCardRow>
            </MobileCardBody>
            <MobileCardActions>
              {onSendToCustomer && showSendButton(invoice) && (
                <SendButton
                  onClick={() => onSendToCustomer(invoice)}
                  disabled={sendingInvoiceId === invoice.id}
                >
                  {sendingInvoiceId === invoice.id ? 'Sending...' : 'Send'}
                </SendButton>
              )}
              {onDuplicate && (
                <IconButton title="Duplicate" onClick={() => onDuplicate(invoice)}>
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </IconButton>
              )}
              <IconButton title="Edit" onClick={() => onEdit(invoice)}>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </IconButton>
              <IconButton title="Download PDF" onClick={() => onDownloadPDF(invoice)}>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </IconButton>
              <IconButton title="Delete" onClick={() => onDelete(invoice)}>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </IconButton>
            </MobileCardActions>
          </MobileCard>
        ))}
      </MobileCardList>
    </TableWrapper>
  )
}

export default InvoiceTable
