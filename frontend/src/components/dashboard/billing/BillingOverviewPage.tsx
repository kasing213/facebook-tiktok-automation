import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { useSubscription } from '../../../hooks/useSubscription'
import { usePaymentHistory } from '../../../hooks/usePaymentHistory'
import { billingApi } from '../../../services/billingApi'
import { PaymentMethod } from '../../../types/billing'
import {
  PageContainer,
  PageHeader,
  PageTitle,
  Card,
  CardTitle,
  CardGrid,
  SummaryCard,
  SummaryLabel,
  SummaryValue,
  SummarySubtext,
  PaymentMethodCard,
  CardBrandIcon,
  CardDetails,
  CardNumber,
  CardExpiry,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableCell,
  StatusBadge,
  DownloadLink,
  PrimaryButton,
  SecondaryButton,
  TierBadge,
  EmptyState,
  EmptyIcon,
  EmptyText,
  LoadingSpinner,
  ErrorMessage
} from './shared/styles'

const HeaderActions = styled.div`
  display: flex;
  gap: 0.75rem;
`

const QuickLinks = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
`

const QuickLink = styled.button`
  background: transparent;
  border: none;
  color: #4a90e2;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 0.25rem;

  &:hover {
    text-decoration: underline;
  }
`

const PaymentMethodSection = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: stretch;
  }
`

const NoPaymentMethod = styled.div`
  color: #6b7280;
  font-size: 0.9375rem;
`

export function BillingOverviewPage() {
  const navigate = useNavigate()
  const {
    status,
    tier,
    isPro,
    loading: subscriptionLoading,
    error: subscriptionError,
    openBillingPortal,
    portalLoading
  } = useSubscription()

  const {
    payments,
    loading: paymentsLoading,
    downloadInvoice,
    downloadingId
  } = usePaymentHistory({ pageSize: 5 })

  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | null>(null)
  const [paymentMethodLoading, setPaymentMethodLoading] = useState(true)

  // Fetch payment method
  useEffect(() => {
    async function fetchPaymentMethod() {
      try {
        const method = await billingApi.getPaymentMethod()
        setPaymentMethod(method)
      } catch {
        // Silently fail - payment method is optional
      } finally {
        setPaymentMethodLoading(false)
      }
    }
    fetchPaymentMethod()
  }, [])

  // Format date
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
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

  // Get plan name
  const getPlanName = () => {
    if (!isPro) return 'Free'
    if (status?.current_period_end) {
      // Check if yearly based on period length
      const periodEnd = new Date(status.current_period_end)
      const now = new Date()
      const daysRemaining = Math.ceil((periodEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
      return daysRemaining > 35 ? 'Pro Yearly' : 'Pro Monthly'
    }
    return 'Pro'
  }

  // Get next payment info
  const getNextPayment = () => {
    if (!isPro || !status?.current_period_end) {
      return { date: null, amount: null }
    }
    if (status.cancel_at_period_end) {
      return { date: status.current_period_end, amount: null }
    }
    // Assume monthly price for simplicity
    return { date: status.current_period_end, amount: 9.99 }
  }

  const nextPayment = getNextPayment()

  if (subscriptionLoading) {
    return (
      <PageContainer>
        <LoadingSpinner />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader>
        <PageTitle>Billing</PageTitle>
        <HeaderActions>
          <SecondaryButton
            onClick={() => navigate('/dashboard/billing/payments')}
          >
            View All Payments
          </SecondaryButton>
          {isPro && (
            <PrimaryButton
              onClick={openBillingPortal}
              disabled={portalLoading}
            >
              {portalLoading ? 'Loading...' : 'Manage Subscription'}
            </PrimaryButton>
          )}
        </HeaderActions>
      </PageHeader>

      {subscriptionError && (
        <ErrorMessage>{subscriptionError}</ErrorMessage>
      )}

      {/* Summary Cards */}
      <CardGrid>
        <SummaryCard>
          <SummaryLabel>Current Plan</SummaryLabel>
          <SummaryValue style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {getPlanName()}
            <TierBadge $tier={tier}>{tier.toUpperCase()}</TierBadge>
          </SummaryValue>
          {!isPro && (
            <SummarySubtext>
              <QuickLink onClick={() => navigate('/dashboard/billing/pricing')}>
                Upgrade to Pro →
              </QuickLink>
            </SummarySubtext>
          )}
          {isPro && status?.cancel_at_period_end && (
            <SummarySubtext style={{ color: '#dc3545' }}>
              Cancels on {formatDate(status.current_period_end)}
            </SummarySubtext>
          )}
        </SummaryCard>

        <SummaryCard>
          <SummaryLabel>Next Payment</SummaryLabel>
          {nextPayment.date ? (
            <>
              <SummaryValue>
                {status?.cancel_at_period_end ? 'Cancelled' : formatCurrency(nextPayment.amount || 0)}
              </SummaryValue>
              <SummarySubtext>
                {status?.cancel_at_period_end
                  ? `Access until ${formatDate(nextPayment.date)}`
                  : `Due ${formatDate(nextPayment.date)}`}
              </SummarySubtext>
            </>
          ) : (
            <>
              <SummaryValue>-</SummaryValue>
              <SummarySubtext>No upcoming payments</SummarySubtext>
            </>
          )}
        </SummaryCard>

        <SummaryCard>
          <SummaryLabel>Payment Method</SummaryLabel>
          {paymentMethodLoading ? (
            <SummarySubtext>Loading...</SummarySubtext>
          ) : paymentMethod ? (
            <>
              <SummaryValue style={{ fontSize: '1.25rem' }}>
                {paymentMethod.brand?.toUpperCase() || 'Card'} •••• {paymentMethod.last4}
              </SummaryValue>
              <SummarySubtext>
                Expires {paymentMethod.expiryMonth}/{paymentMethod.expiryYear}
              </SummarySubtext>
            </>
          ) : (
            <>
              <SummaryValue style={{ fontSize: '1.25rem', color: '#6b7280' }}>
                No card on file
              </SummaryValue>
              {isPro && (
                <SummarySubtext>
                  <QuickLink onClick={openBillingPortal}>
                    Add payment method →
                  </QuickLink>
                </SummarySubtext>
              )}
            </>
          )}
        </SummaryCard>
      </CardGrid>

      {/* Payment Method Card (detailed view) */}
      <Card>
        <CardTitle>Payment Method</CardTitle>
        <PaymentMethodSection>
          {paymentMethod ? (
            <PaymentMethodCard>
              <CardBrandIcon $brand={paymentMethod.brand}>
                {paymentMethod.brand?.slice(0, 4) || 'CARD'}
              </CardBrandIcon>
              <CardDetails>
                <CardNumber>
                  {paymentMethod.brand?.charAt(0).toUpperCase()}{paymentMethod.brand?.slice(1)} ending in {paymentMethod.last4}
                </CardNumber>
                <CardExpiry>
                  Expires {paymentMethod.expiryMonth?.toString().padStart(2, '0')}/{paymentMethod.expiryYear}
                </CardExpiry>
              </CardDetails>
            </PaymentMethodCard>
          ) : (
            <NoPaymentMethod>
              {isPro
                ? 'No payment method on file. Add one to ensure uninterrupted service.'
                : 'Add a payment method when you upgrade to Pro.'}
            </NoPaymentMethod>
          )}
          <SecondaryButton
            onClick={openBillingPortal}
            disabled={portalLoading}
          >
            {paymentMethod ? 'Update' : 'Add Card'}
          </SecondaryButton>
        </PaymentMethodSection>
      </Card>

      {/* Recent Payments */}
      <Card>
        <CardTitle>Recent Payments</CardTitle>
        {paymentsLoading ? (
          <LoadingSpinner />
        ) : payments.length === 0 ? (
          <EmptyState>
            <EmptyIcon>--</EmptyIcon>
            <EmptyText>No payment history yet</EmptyText>
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
                  <TableHeader></TableHeader>
                </TableRow>
              </TableHead>
              <tbody>
                {payments.slice(0, 5).map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell>{formatDate(payment.date)}</TableCell>
                    <TableCell>{payment.description}</TableCell>
                    <TableCell>{formatCurrency(payment.amount)}</TableCell>
                    <TableCell>
                      <StatusBadge $status={payment.status}>
                        {payment.status}
                      </StatusBadge>
                    </TableCell>
                    <TableCell>
                      {(payment.invoicePdfUrl || payment.invoiceUrl) && (
                        <DownloadLink
                          onClick={() => downloadInvoice(payment)}
                          disabled={downloadingId === payment.id}
                        >
                          {downloadingId === payment.id ? 'Downloading...' : 'PDF'}
                        </DownloadLink>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </tbody>
            </Table>
            <QuickLinks>
              <QuickLink onClick={() => navigate('/dashboard/billing/payments')}>
                View all payments →
              </QuickLink>
            </QuickLinks>
          </>
        )}
      </Card>

      {/* Upgrade CTA for free users */}
      {!isPro && (
        <Card style={{ background: 'linear-gradient(135deg, #f0f7ff 0%, #e8f4ff 100%)', border: '2px solid #4a90e2' }}>
          <CardTitle style={{ color: '#2a5298' }}>Upgrade to Pro</CardTitle>
          <p style={{ color: '#4a90e2', margin: '0 0 1rem 0' }}>
            Unlock PDF downloads, data exports, priority support, and more.
          </p>
          <PrimaryButton onClick={() => navigate('/dashboard/billing/pricing')}>
            View Pricing Plans →
          </PrimaryButton>
        </Card>
      )}
    </PageContainer>
  )
}

export default BillingOverviewPage
