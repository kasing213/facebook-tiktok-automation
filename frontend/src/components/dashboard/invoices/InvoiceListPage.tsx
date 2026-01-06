import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { useInvoices } from '../../../hooks/useInvoices'
import { useSubscription } from '../../../hooks/useSubscription'
import { InvoiceTable } from '../../invoice'
import { Invoice, InvoiceStatus } from '../../../types/invoice'

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
`

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
`

const HeaderActions = styled.div`
  display: flex;
  gap: 0.75rem;
`

const Button = styled.button<{ $variant?: 'primary' | 'secondary' }>`
  padding: 0.75rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  ${props => props.$variant === 'primary' ? `
    background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
    color: white;
    border: none;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
    }
  ` : `
    background: white;
    color: #6b7280;
    border: 1px solid #e5e7eb;

    &:hover {
      background: #f9fafb;
    }
  `}
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`

const StatCard = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.25rem;
`

const StatLabel = styled.div`
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
`

const StatValue = styled.div<{ $color?: string }>`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => props.$color || '#1f2937'};
`

const FilterToolbar = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: center;
`

const SearchBox = styled.div`
  flex: 1;
  min-width: 200px;
  position: relative;
`

const SearchIcon = styled.span`
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #6b7280;
`

const SearchInput = styled.input`
  width: 100%;
  padding: 0.625rem 1rem 0.625rem 2.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }
`

const FilterSelect = styled.select`
  padding: 0.625rem 2.5rem 0.625rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9375rem;
  color: #1f2937;
  background: white;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M10.293 3.293L6 7.586 1.707 3.293A1 1 0 00.293 4.707l5 5a1 1 0 001.414 0l5-5a1 1 0 10-1.414-1.414z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;

  &:focus {
    outline: none;
    border-color: #4a90e2;
  }
`

const TableSection = styled.section`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
`

const ErrorMessage = styled.div`
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
`

const ConfirmModal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`

const ModalContent = styled.div`
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 400px;
  width: 90%;

  h3 {
    margin: 0 0 1rem 0;
    color: #1f2937;
  }

  p {
    color: #6b7280;
    margin-bottom: 1.5rem;
  }
`

const ModalActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
`

const InvoiceListPage: React.FC = () => {
  const navigate = useNavigate()
  const {
    invoices,
    stats,
    loading,
    error,
    deleting,
    fetchInvoices,
    fetchStats,
    deleteInvoice,
    downloadPDF,
    exportInvoices,
    clearError
  } = useInvoices()
  const { canAccessExport, canAccessPdf } = useSubscription()

  const [statusFilter, setStatusFilter] = useState<InvoiceStatus | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<Invoice | null>(null)

  useEffect(() => {
    fetchInvoices()
    fetchStats()
  }, [fetchInvoices, fetchStats])

  const handleView = (invoice: Invoice) => {
    navigate(`/dashboard/invoices/${invoice.id}`)
  }

  const handleEdit = (invoice: Invoice) => {
    navigate(`/dashboard/invoices/${invoice.id}?edit=true`)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteInvoice(deleteTarget.id)
      setDeleteTarget(null)
    } catch (err) {
      // Error handled by hook
    }
  }

  const handleDownloadPDF = async (invoice: Invoice) => {
    try {
      await downloadPDF(invoice.id, invoice.invoice_number)
    } catch (err) {
      // Error handled by hook
    }
  }

  const handleExport = async (format: 'csv' | 'xlsx') => {
    try {
      await exportInvoices(format)
    } catch (err) {
      // Error handled by hook
    }
  }

  const filteredInvoices = invoices.filter(invoice => {
    if (statusFilter !== 'all' && invoice.status !== statusFilter) {
      return false
    }
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        invoice.invoice_number.toLowerCase().includes(query) ||
        invoice.customer?.name.toLowerCase().includes(query) ||
        invoice.customer?.email?.toLowerCase().includes(query)
      )
    }
    return true
  })

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  return (
    <Container>
      <Header>
        <Title>Invoices</Title>
        <HeaderActions>
          <Button
            onClick={() => handleExport('csv')}
            disabled={!canAccessExport}
            title={!canAccessExport ? 'Upgrade to Pro for export access' : undefined}
          >
            Export CSV {!canAccessExport && '(Pro)'}
          </Button>
          <Button
            onClick={() => handleExport('xlsx')}
            disabled={!canAccessExport}
            title={!canAccessExport ? 'Upgrade to Pro for export access' : undefined}
          >
            Export Excel {!canAccessExport && '(Pro)'}
          </Button>
          <Button $variant="primary" onClick={() => navigate('/dashboard/invoices/new')}>
            + Create Invoice
          </Button>
        </HeaderActions>
      </Header>

      {error && (
        <ErrorMessage>
          {error}
          <button onClick={clearError} style={{ marginLeft: '1rem' }}>Dismiss</button>
        </ErrorMessage>
      )}

      <StatsGrid>
        <StatCard>
          <StatLabel>Total Invoices</StatLabel>
          <StatValue>{stats?.total_invoices || invoices.length}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>Total Revenue</StatLabel>
          <StatValue $color="#28a745">{formatCurrency(stats?.total_revenue || 0)}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>Pending Amount</StatLabel>
          <StatValue $color="#ffc107">{formatCurrency(stats?.pending_amount || 0)}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>Overdue</StatLabel>
          <StatValue $color="#dc3545">{stats?.overdue_count || 0}</StatValue>
        </StatCard>
      </StatsGrid>

      <FilterToolbar>
        <SearchBox>
          <SearchIcon>🔍</SearchIcon>
          <SearchInput
            type="text"
            placeholder="Search invoices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </SearchBox>
        <FilterSelect
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as InvoiceStatus | 'all')}
        >
          <option value="all">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="pending">Pending</option>
          <option value="paid">Paid</option>
          <option value="overdue">Overdue</option>
          <option value="cancelled">Cancelled</option>
        </FilterSelect>
      </FilterToolbar>

      <TableSection>
        <InvoiceTable
          invoices={filteredInvoices}
          onView={handleView}
          onEdit={handleEdit}
          onDelete={(invoice) => setDeleteTarget(invoice)}
          onDownloadPDF={handleDownloadPDF}
          loading={loading}
        />
      </TableSection>

      {deleteTarget && (
        <ConfirmModal onClick={() => setDeleteTarget(null)}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <h3>Delete Invoice</h3>
            <p>
              Are you sure you want to delete invoice <strong>{deleteTarget.invoice_number}</strong>?
              This action cannot be undone.
            </p>
            <ModalActions>
              <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
              <Button
                $variant="primary"
                onClick={handleDelete}
                disabled={deleting}
                style={{ background: '#dc3545' }}
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </Button>
            </ModalActions>
          </ModalContent>
        </ConfirmModal>
      )}
    </Container>
  )
}

export default InvoiceListPage
