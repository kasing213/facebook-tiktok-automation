import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import styled from 'styled-components'
import { useInvoices } from '../../../hooks/useInvoices'
import { useSubscription } from '../../../hooks/useSubscription'
import { InvoiceForm } from '../../invoice'
import { InvoiceStatusBadge } from '../../invoice/InvoiceStatusBadge'
import { LineItemsEditor } from '../../invoice/LineItemsEditor'
import { Invoice, InvoiceUpdate } from '../../../types/invoice'

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
  color: #4a90e2;
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
  color: #1f2937;
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
          background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
          color: white;
          border: none;

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
          }
        `
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
      default:
        return `
          background: white;
          color: #6b7280;
          border: 1px solid #e5e7eb;

          &:hover {
            background: #f9fafb;
          }
        `
    }
  }}

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const Section = styled.section`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
`

const SectionTitle = styled.h2`
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
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
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
`

const InfoValue = styled.div`
  font-size: 1rem;
  color: #1f2937;
`

const CustomerCard = styled.div`
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
`

const CustomerName = styled.div`
  font-weight: 600;
  font-size: 1.125rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
`

const CustomerDetail = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
`

const TotalsBox = styled.div`
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
`

const TotalRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.9375rem;
  color: #6b7280;
`

const GrandTotalRow = styled(TotalRow)`
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  border-top: 2px solid #e5e7eb;
  padding-top: 1rem;
  margin-top: 0.5rem;
`

const Notes = styled.div`
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
  font-size: 0.9375rem;
  color: #6b7280;
  white-space: pre-wrap;
`

const ErrorMessage = styled.div`
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
`

const LoadingState = styled.div`
  text-align: center;
  padding: 3rem;
  color: #6b7280;
`

const InvoiceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const isEditMode = searchParams.get('edit') === 'true'

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

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
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

      <Section>
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

      <Section>
        <SectionTitle>Customer</SectionTitle>
        <CustomerCard>
          <CustomerName>{invoice.customer?.name || 'Unknown Customer'}</CustomerName>
          {invoice.customer?.email && <CustomerDetail>{invoice.customer.email}</CustomerDetail>}
          {invoice.customer?.phone && <CustomerDetail>{invoice.customer.phone}</CustomerDetail>}
          {invoice.customer?.company && <CustomerDetail>{invoice.customer.company}</CustomerDetail>}
          {invoice.customer?.address && <CustomerDetail>{invoice.customer.address}</CustomerDetail>}
        </CustomerCard>
      </Section>

      <Section>
        <SectionTitle>Line Items</SectionTitle>
        <LineItemsEditor
          items={invoice.items}
          onChange={() => {}}
          readOnly
        />

        <TotalsBox>
          <TotalRow>
            <span>Subtotal</span>
            <span>{formatCurrency(invoice.subtotal)}</span>
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
            <span>{formatCurrency(invoice.total)}</span>
          </GrandTotalRow>
        </TotalsBox>
      </Section>

      {invoice.notes && (
        <Section>
          <SectionTitle>Notes</SectionTitle>
          <Notes>{invoice.notes}</Notes>
        </Section>
      )}
    </Container>
  )
}

export default InvoiceDetailPage
