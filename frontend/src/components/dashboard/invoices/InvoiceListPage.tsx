import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import styled from 'styled-components'
import { useInvoices } from '../../../hooks/useInvoices'
import { useSubscription } from '../../../hooks/useSubscription'
import { InvoiceTable } from '../../invoice'
import { Invoice, InvoiceStatus } from '../../../types/invoice'
import { easings, reduceMotion } from '../../../styles/animations'
import { useStaggeredAnimation } from '../../../hooks/useScrollAnimation'
import { LoadingButton } from '../../common/LoadingButton'
import { RefreshButton } from '../../common/RefreshButton'
import { useAsyncAction } from '../../../hooks/useAsyncAction'
import { useExportOperation } from '../../../hooks/useEnhancedAsyncAction'
import { LoadingOverlay } from '../../common/LoadingOverlay'

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
  background: linear-gradient(135deg, ${props => props.theme.accent} 0%, ${props => props.theme.accentDark} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
`

const HeaderActions = styled.div`
  display: flex;
  gap: 0.75rem;
  align-items: center;
`


const Button = styled.button<{ $variant?: 'primary' | 'secondary' }>`
  padding: 0.75rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  ${props => props.$variant === 'primary' ? `
    background: linear-gradient(135deg, ${props.theme.accent} 0%, ${props.theme.accentDark} 100%);
    color: white;
    border: none;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 8px ${props.theme.shadowColor};
    }
  ` : `
    background: ${props.theme.card};
    color: ${props.theme.textSecondary};
    border: 1px solid ${props.theme.border};

    &:hover {
      background: ${props.theme.cardHover};
    }
  `}
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`

const StatCard = styled.div<{ $isVisible?: boolean; $delay?: number }>`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  padding: 1.25rem;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(20px)'};
  transition: opacity 0.5s ${easings.easeOutCubic},
              transform 0.5s ${easings.easeOutCubic},
              background-color 0.3s ease,
              border-color 0.3s ease;
  transition-delay: ${props => props.$delay || 0}ms;

  &:hover {
    box-shadow: 0 4px 12px ${props => props.theme.shadowColor};
  }

  ${reduceMotion}
`

const StatLabel = styled.div`
  font-size: 0.75rem;
  font-weight: 500;
  color: ${props => props.theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
`

const StatValue = styled.div<{ $color?: string }>`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => props.$color || props.theme.textPrimary};
`

const FilterToolbar = styled.div`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
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
  color: ${props => props.theme.textMuted};
  display: flex;
  align-items: center;
  justify-content: center;

  svg {
    width: 16px;
    height: 16px;
  }
`

const SearchInput = styled.input`
  width: 100%;
  padding: 0.625rem 1rem 0.625rem 2.5rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  font-size: 0.9375rem;
  color: ${props => props.theme.textPrimary};
  background: ${props => props.theme.card};

  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent};
  }

  &::placeholder {
    color: ${props => props.theme.textMuted};
  }
`

const FilterSelect = styled.select`
  padding: 0.625rem 2.5rem 0.625rem 1rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 6px;
  font-size: 0.9375rem;
  color: ${props => props.theme.textPrimary};
  background: ${props => props.theme.card};
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M10.293 3.293L6 7.586 1.707 3.293A1 1 0 00.293 4.707l5 5a1 1 0 001.414 0l5-5a1 1 0 10-1.414-1.414z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent};
  }
`

const TableSection = styled.section`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  padding: 1.5rem;
`

const ErrorMessage = styled.div`
  background: ${props => props.theme.errorLight};
  color: ${props => props.theme.error};
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
`

const SuccessMessage = styled.div`
  background: ${props => props.theme.successLight};
  color: ${props => props.theme.success};
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`

const ConfirmModal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: ${props => props.theme.overlay};
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`

const ModalContent = styled.div`
  background: ${props => props.theme.card};
  border-radius: 12px;
  padding: 2rem;
  max-width: 400px;
  width: 90%;

  h3 {
    margin: 0 0 1rem 0;
    color: ${props => props.theme.textPrimary};
  }

  p {
    color: ${props => props.theme.textSecondary};
    margin-bottom: 1.5rem;
  }
`

const ModalActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
`

const InvoiceListPage: React.FC = () => {
  const { t } = useTranslation()
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
    sendToCustomer,
    clearError
  } = useInvoices()
  const { canAccessExport } = useSubscription()

  // Animation state for stat cards
  const statsVisible = useStaggeredAnimation(4, 100)

  const [statusFilter, setStatusFilter] = useState<InvoiceStatus | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<Invoice | null>(null)
  const [sendingInvoiceId, setSendingInvoiceId] = useState<string | null>(null)
  const [sendSuccess, setSendSuccess] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // Enhanced async actions for exports and operations
  const exportAction = useExportOperation({
    onSuccess: (result) => {
      if (result?.filename) {
        setSendSuccess(`${result.format.toUpperCase()} export complete: ${result.filename}`)
        setTimeout(() => setSendSuccess(null), 3000)
      }
    },
    onError: (error) => {
      console.error('Export failed:', error)
      setError(error.message || 'Export failed. Please try again.')
    },
    progressTitle: 'Exporting Invoices',
    progressMessage: 'Preparing your invoice export...'
  })

  useEffect(() => {
    fetchInvoices()
    fetchStats()
    setLastUpdated(new Date())
  }, [fetchInvoices, fetchStats])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await Promise.all([
        fetchInvoices(),
        fetchStats()
      ])
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Refresh failed:', error)
    } finally {
      setRefreshing(false)
    }
  }

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
    await exportAction.executeWithSteps(async (progress) => {
      progress.setCurrentStep('prepare', `Preparing ${format.toUpperCase()} export...`)
      await new Promise(resolve => setTimeout(resolve, 300))
      progress.completeStep('prepare')

      progress.setCurrentStep('format', 'Formatting data...')
      await new Promise(resolve => setTimeout(resolve, 200))
      progress.completeStep('format')

      progress.setCurrentStep('generate', 'Generating file...')
      const result = await exportInvoices(format)
      progress.completeStep('generate')

      progress.setCurrentStep('download', 'Preparing download...')
      await new Promise(resolve => setTimeout(resolve, 100))
      progress.completeStep('download')

      return result
    })
  }

  const handleSendToCustomer = async (invoice: Invoice) => {
    setSendingInvoiceId(invoice.id)
    setSendSuccess(null)
    try {
      const result = await sendToCustomer(invoice.id)
      setSendSuccess(`Invoice ${result.invoice_number} sent to ${result.telegram_username || 'customer'}`)
      // Clear success message after 3 seconds
      setTimeout(() => setSendSuccess(null), 3000)
    } catch (err) {
      // Error handled by hook
    } finally {
      setSendingInvoiceId(null)
    }
  }

  const handleDuplicate = (invoice: Invoice) => {
    // Navigate to create page with invoice data as state for duplication
    navigate('/dashboard/invoices/new', {
      state: {
        duplicate: true,
        sourceInvoice: invoice
      }
    })
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
        <Title>{t('invoices.title')}</Title>
        <HeaderActions>
          <RefreshButton
            onRefresh={handleRefresh}
            refreshing={refreshing}
            disabled={loading}
            lastUpdated={lastUpdated}
          />
          <LoadingButton
            variant="secondary"
            loading={exportAction.state.loading}
            disabled={!canAccessExport}
            onClick={() => handleExport('csv')}
          >
            {t('invoices.exportCsv')} {!canAccessExport && '(Pro)'}
          </LoadingButton>
          <LoadingButton
            variant="secondary"
            loading={exportAction.state.loading}
            disabled={!canAccessExport}
            onClick={() => handleExport('xlsx')}
          >
            {t('invoices.exportExcel')} {!canAccessExport && '(Pro)'}
          </LoadingButton>
          <LoadingButton
            variant="primary"
            onClick={() => navigate('/dashboard/invoices/new')}
          >
            + {t('invoices.createNew')}
          </LoadingButton>
        </HeaderActions>
      </Header>

      {error && (
        <ErrorMessage>
          {error}
          <button onClick={clearError} style={{ marginLeft: '1rem' }}>{t('invoices.dismiss')}</button>
        </ErrorMessage>
      )}

      <StatsGrid>
        <StatCard $isVisible={statsVisible[0]} $delay={0}>
          <StatLabel>{t('invoices.totalInvoices')}</StatLabel>
          <StatValue>{stats?.total_invoices || invoices.length}</StatValue>
        </StatCard>
        <StatCard $isVisible={statsVisible[1]} $delay={100}>
          <StatLabel>{t('invoices.totalRevenue')}</StatLabel>
          <StatValue $color="#28a745">{formatCurrency(stats?.total_revenue || 0)}</StatValue>
        </StatCard>
        <StatCard $isVisible={statsVisible[2]} $delay={200}>
          <StatLabel>{t('invoices.pendingAmount')}</StatLabel>
          <StatValue $color="#ffc107">{formatCurrency(stats?.pending_amount || 0)}</StatValue>
        </StatCard>
        <StatCard $isVisible={statsVisible[3]} $delay={300}>
          <StatLabel>{t('invoices.overdue')}</StatLabel>
          <StatValue $color="#dc3545">{stats?.overdue_count || 0}</StatValue>
        </StatCard>
      </StatsGrid>

      <FilterToolbar>
        <SearchBox>
          <SearchIcon>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </SearchIcon>
          <SearchInput
            type="text"
            placeholder={t('invoices.searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </SearchBox>
        <FilterSelect
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as InvoiceStatus | 'all')}
        >
          <option value="all">{t('invoices.allStatuses')}</option>
          <option value="draft">{t('invoices.draft')}</option>
          <option value="pending">{t('invoices.pending')}</option>
          <option value="paid">{t('invoices.paid')}</option>
          <option value="overdue">{t('invoices.overdue')}</option>
          <option value="cancelled">{t('invoices.cancelled')}</option>
        </FilterSelect>
      </FilterToolbar>

      {sendSuccess && (
        <SuccessMessage>{sendSuccess}</SuccessMessage>
      )}

      <TableSection>
        <InvoiceTable
          invoices={filteredInvoices}
          onView={handleView}
          onEdit={handleEdit}
          onDelete={(invoice) => setDeleteTarget(invoice)}
          onDownloadPDF={handleDownloadPDF}
          onSendToCustomer={handleSendToCustomer}
          onDuplicate={handleDuplicate}
          sendingInvoiceId={sendingInvoiceId}
          loading={loading}
        />
      </TableSection>

      {deleteTarget && (
        <ConfirmModal onClick={() => setDeleteTarget(null)}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <h3>{t('invoices.deleteInvoice')}</h3>
            <p>
              {t('invoices.deleteConfirmation')} <strong>{deleteTarget.invoice_number}</strong>?
              {t('invoices.cannotUndo')}
            </p>
            <ModalActions>
              <Button onClick={() => setDeleteTarget(null)}>{t('common.cancel')}</Button>
              <Button
                $variant="primary"
                onClick={handleDelete}
                disabled={deleting}
                style={{ background: '#dc3545' }}
              >
                {deleting ? t('invoices.deleting') : t('common.delete')}
              </Button>
            </ModalActions>
          </ModalContent>
        </ConfirmModal>
      )}

      {/* Loading Overlay for Exports */}
      <LoadingOverlay
        visible={exportAction.state.showOverlay}
        title="Exporting Invoices"
        message="Please wait while we prepare your export..."
        variant="steps"
        steps={[
          { id: 'prepare', label: 'Preparing data...' },
          { id: 'format', label: 'Formatting export...' },
          { id: 'generate', label: 'Generating file...' },
          { id: 'download', label: 'Preparing download...' }
        ]}
        currentStep={exportAction.state.currentStep}
        onCancel={() => exportAction.hideOverlay()}
        cancelLabel="Close"
      />
    </Container>
  )
}

export default InvoiceListPage
