import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import styled from 'styled-components'
import { useInvoices } from '../../../hooks/useInvoices'
import { useSubscription } from '../../../hooks/useSubscription'
import { InvoiceForm } from '../../invoice'
import { InvoiceStatusBadge } from '../../invoice/InvoiceStatusBadge'
import { LineItemsEditor } from '../../invoice/LineItemsEditor'
import { Invoice, InvoiceUpdate } from '../../../types/invoice'
import { easings, reduceMotion } from '../../../styles/animations'
import { useStaggeredAnimation } from '../../../hooks/useScrollAnimation'

const Container = styled.div`
  max-width: 900px;
  margin: 0 auto;
`

const Header = styled.div`
  margin-bottom: 2rem;
`

const BackLink = styled.button`
  background: none;
  border: none;
  color: ${props => props.theme.accent};
  font-size: 0.875rem;
  cursor: pointer;
  padding: 0;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:hover {
    text-decoration: underline;
  }
`

const TitleRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
`

const TitleSection = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0;
`

const HeaderActions = styled.div`
  display: flex;
  gap: 0.75rem;
`

const Button = styled.button<{ $variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 0.75rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  ${props => {
    switch (props.$variant) {
      case 'primary':
        return `
          background: linear-gradient(135deg, ${props.theme.accent} 0%, ${props.theme.accentDark} 100%);
          color: white;
          border: none;

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px ${props.theme.shadowColor};
          }
        `
      case 'danger':
        return `
          background: ${props.theme.card};
          color: ${props.theme.error};
          border: 1px solid ${props.theme.error};

          &:hover {
            background: ${props.theme.error};
            color: white;
          }
        `
      default:
        return `
          background: ${props.theme.card};
          color: ${props.theme.textSecondary};
          border: 1px solid ${props.theme.border};

          &:hover {
            background: ${props.theme.backgroundTertiary};
          }
        `
    }
  }}

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const Section = styled.section<{ $isVisible?: boolean; $delay?: number }>`
  background: ${props => props.theme.card};
  border: 1px solid ${props => props.theme.border};
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  opacity: ${props => props.$isVisible ? 1 : 0};
  transform: ${props => props.$isVisible ? 'translateY(0)' : 'translateY(20px)'};
  transition: opacity 0.5s ${easings.easeOutCubic},
              transform 0.5s ${easings.easeOutCubic},
              background-color 0.3s ease,
              border-color 0.3s ease;
  transition-delay: ${props => props.$delay || 0}ms;
  ${reduceMotion}
`

const SectionTitle = styled.h2`
  font-size: 1.125rem;
  font-weight: 600;
  color: ${props => props.theme.textPrimary};
  margin: 0 0 1rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid ${props => props.theme.border};
`

const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
`

const InfoItem = styled.div``

const InfoLabel = styled.div`
  font-size: 0.75rem;
  font-weight: 500;
  color: ${props => props.theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
`

const InfoValue = styled.div`
  font-size: 1rem;
  color: ${props => props.theme.textPrimary};
`

const CustomerCard = styled.div`
  background: ${props => props.theme.backgroundTertiary};
  border-radius: 8px;
  padding: 1rem;
`

const CustomerName = styled.div`
  font-weight: 600;
  font-size: 1.125rem;
  color: ${props => props.theme.textPrimary};
  margin-bottom: 0.5rem;
`

const CustomerDetail = styled.div`
  font-size: 0.875rem;
  color: ${props => props.theme.textSecondary};
  margin-bottom: 0.25rem;
`

const TotalsBox = styled.div`
  background: ${props => props.theme.backgroundTertiary};
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
`

const TotalRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.9375rem;
  color: ${props => props.theme.textSecondary};
`

const GrandTotalRow = styled(TotalRow)`
  font-size: 1.25rem;
  font-weight: 700;
  color: ${props => props.theme.textPrimary};
  border-top: 2px solid ${props => props.theme.border};
  padding-top: 1rem;
  margin-top: 0.5rem;
`

const Notes = styled.div`
  background: ${props => props.theme.backgroundTertiary};
  border-radius: 8px;
  padding: 1rem;
  font-size: 0.9375rem;
  color: ${props => props.theme.textSecondary};
  white-space: pre-wrap;
`

const ErrorMessage = styled.div`
  background: ${props => props.theme.errorLight};
  color: ${props => props.theme.error};
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
`

const LoadingState = styled.div`
  text-align: center;
  padding: 3rem;
  color: ${props => props.theme.textSecondary};
`

const InvoiceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const isEditMode = searchParams.get('edit') === 'true'

  // Animation state for sections (4 sections: details, customer, line items, notes)
  const sectionsVisible = useStaggeredAnimation(4, 100)

  const {
    customers,
    error,
    loading,
    saving,
    getInvoice,
    updateInvoice,
    deleteInvoice,
    downloadPDF,
    fetchCustomers,
    clearError
  } = useInvoices()
  const { canAccessPdf, startCheckout, checkoutLoading } = useSubscription()

  const [invoice, setInvoice] = useState<Invoice | null>(null)
  const [editing, setEditing] = useState(isEditMode)

  useEffect(() => {
    if (id) {
      loadInvoice()
      fetchCustomers()
    }
  }, [id])

  const loadInvoice = async () => {
    if (!id) return
    const data = await getInvoice(id)
    setInvoice(data)
  }

  const handleUpdate = async (data: InvoiceUpdate) => {
    if (!id) return
    const updated = await updateInvoice(id, data)
    setInvoice(updated)
    setEditing(false)
    navigate(`/dashboard/invoices/${id}`, { replace: true })
  }

  const handleDelete = async () => {
    if (!id) return
    if (window.confirm('Are you sure you want to delete this invoice?')) {
      await deleteInvoice(id)
      navigate('/dashboard/invoices')
    }
  }

  const handleDownloadPDF = async () => {
    if (!invoice) return
    await downloadPDF(invoice.id, invoice.invoice_number)
  }

  const formatCurrency = (amount: number | null | undefined): string => {
    if (amount === null || amount === undefined || isNaN(amount)) {
      return '$0.00'
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  // Calculate totals from items as fallback when API doesn't provide them
  const calculateSubtotalFromItems = (items: Invoice['items']): number => {
    return items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0)
  }

  const calculateTotalFromItems = (inv: Invoice): number => {
    const subtotal = calculateSubtotalFromItems(inv.items)
    const tax = inv.items.reduce((sum, item) => {
      const itemTotal = item.quantity * item.unit_price
      return sum + (itemTotal * (item.tax_rate || 0) / 100)
    }, 0)
    const discount = inv.discount ? subtotal * (inv.discount / 100) : 0
    return subtotal + tax - discount
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (loading) {
    return <LoadingState>Loading invoice...</LoadingState>
  }

  if (!invoice) {
    return (
      <Container>
        <ErrorMessage>Invoice not found</ErrorMessage>
        <Button onClick={() => navigate('/dashboard/invoices')}>Back to Invoices</Button>
      </Container>
    )
  }

  if (editing) {
    return (
      <Container>
        <Header>
          <BackLink onClick={() => setEditing(false)}>
            ← Cancel Editing
          </BackLink>
          <Title>Edit Invoice {invoice.invoice_number}</Title>
        </Header>

        {error && (
          <ErrorMessage>
            {error}
            <button onClick={clearError} style={{ marginLeft: '1rem' }}>Dismiss</button>
          </ErrorMessage>
        )}

        <InvoiceForm
          invoice={invoice}
          customers={customers}
          onSubmit={handleUpdate}
          onCancel={() => setEditing(false)}
          loading={saving}
          isEdit
        />
      </Container>
    )
  }

  return (
    <Container>
      <Header>
        <BackLink onClick={() => navigate('/dashboard/invoices')}>
          ← Back to Invoices
        </BackLink>
        <TitleRow>
          <TitleSection>
            <Title>{invoice.invoice_number}</Title>
            <InvoiceStatusBadge status={invoice.status} />
          </TitleSection>
          <HeaderActions>
            {canAccessPdf ? (
              <Button onClick={handleDownloadPDF}>Download PDF</Button>
            ) : (
              <Button
                onClick={() => startCheckout('monthly')}
                disabled={checkoutLoading}
                title="Upgrade to Pro to download PDFs"
              >
                {checkoutLoading ? 'Processing...' : 'Download PDF (Pro)'}
              </Button>
            )}
            <Button onClick={() => setEditing(true)}>Edit</Button>
            <Button $variant="danger" onClick={handleDelete}>Delete</Button>
          </HeaderActions>
        </TitleRow>
      </Header>

      {error && (
        <ErrorMessage>
          {error}
          <button onClick={clearError} style={{ marginLeft: '1rem' }}>Dismiss</button>
        </ErrorMessage>
      )}

      <Section $isVisible={sectionsVisible[0]} $delay={0}>
        <SectionTitle>Invoice Details</SectionTitle>
        <InfoGrid>
          <InfoItem>
            <InfoLabel>Invoice Number</InfoLabel>
            <InfoValue>{invoice.invoice_number}</InfoValue>
          </InfoItem>
          <InfoItem>
            <InfoLabel>Status</InfoLabel>
            <InfoValue><InvoiceStatusBadge status={invoice.status} /></InfoValue>
          </InfoItem>
          <InfoItem>
            <InfoLabel>Due Date</InfoLabel>
            <InfoValue>{invoice.due_date ? formatDate(invoice.due_date) : 'Not set'}</InfoValue>
          </InfoItem>
          <InfoItem>
            <InfoLabel>Created</InfoLabel>
            <InfoValue>{formatDate(invoice.created_at)}</InfoValue>
          </InfoItem>
        </InfoGrid>
      </Section>

      <Section $isVisible={sectionsVisible[1]} $delay={100}>
        <SectionTitle>Customer</SectionTitle>
        <CustomerCard>
          <CustomerName>{invoice.customer?.name || 'Unknown Customer'}</CustomerName>
          {invoice.customer?.email && <CustomerDetail>{invoice.customer.email}</CustomerDetail>}
          {invoice.customer?.phone && <CustomerDetail>{invoice.customer.phone}</CustomerDetail>}
          {invoice.customer?.company && <CustomerDetail>{invoice.customer.company}</CustomerDetail>}
          {invoice.customer?.address && <CustomerDetail>{invoice.customer.address}</CustomerDetail>}
        </CustomerCard>
      </Section>

      <Section $isVisible={sectionsVisible[2]} $delay={200}>
        <SectionTitle>Line Items</SectionTitle>
        <LineItemsEditor
          items={invoice.items}
          onChange={() => {}}
          readOnly
        />

        <TotalsBox>
          <TotalRow>
            <span>Subtotal</span>
            <span>{formatCurrency(invoice.subtotal ?? calculateSubtotalFromItems(invoice.items))}</span>
          </TotalRow>
          {invoice.discount && invoice.discount > 0 && (
            <TotalRow>
              <span>Discount ({invoice.discount}%)</span>
              <span>-{formatCurrency(invoice.discount_amount || 0)}</span>
            </TotalRow>
          )}
          {invoice.tax_amount && invoice.tax_amount > 0 && (
            <TotalRow>
              <span>Tax</span>
              <span>{formatCurrency(invoice.tax_amount)}</span>
            </TotalRow>
          )}
          <GrandTotalRow>
            <span>Total</span>
            <span>{formatCurrency(invoice.total ?? calculateTotalFromItems(invoice))}</span>
          </GrandTotalRow>
        </TotalsBox>
      </Section>

      {invoice.notes && (
        <Section $isVisible={sectionsVisible[3]} $delay={300}>
          <SectionTitle>Notes</SectionTitle>
          <Notes>{invoice.notes}</Notes>
        </Section>
      )}
    </Container>
  )
}

export default InvoiceDetailPage
