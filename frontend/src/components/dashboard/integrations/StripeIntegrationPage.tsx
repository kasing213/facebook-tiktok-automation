import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useSubscription } from '../../../hooks/useSubscription'
import { LoadingSpinner } from '../../LoadingSpinner'
import {
  Container,
  Header,
  BackButton,
  IntegrationCard,
  CardHeader,
  PlatformName,
  StatusBadge,
  Description,
  PricingOptions,
  PriceButton,
  SubscriptionInfo,
  SubscriptionDetail,
  ManageButton,
  ErrorText
} from './shared/styles'

const StripeIntegrationPage: React.FC = () => {
  const navigate = useNavigate()

  const {
    isPro,
    checkoutLoading,
    portalLoading,
    error: subscriptionError,
    startCheckout,
    openBillingPortal,
    periodEnd,
    cancelAtPeriodEnd
  } = useSubscription()

  return (
    <Container>
      <Header>
        <BackButton onClick={() => navigate('/dashboard/integrations')}>
          ← Back to Integrations
        </BackButton>
      </Header>

      <IntegrationCard connected={isPro}>
        <CardHeader>
          <PlatformName>Stripe Payments</PlatformName>
          <StatusBadge connected={isPro}>
            {isPro ? 'Active' : 'Not Subscribed'}
          </StatusBadge>
        </CardHeader>

        <Description>
          Manage your subscription and billing through Stripe's secure payment platform.
          All payments are processed securely with industry-standard encryption.
        </Description>

        {isPro && (
          <SubscriptionInfo>
            <SubscriptionDetail>
              <strong>Status:</strong> Active Subscription
            </SubscriptionDetail>
            {periodEnd && (
              <SubscriptionDetail>
                <strong>{cancelAtPeriodEnd ? 'Expires' : 'Renews'}:</strong>{' '}
                {new Date(periodEnd).toLocaleDateString()}
              </SubscriptionDetail>
            )}
            {cancelAtPeriodEnd && (
              <SubscriptionDetail style={{ color: '#dc3545' }}>
                Your subscription will not renew
              </SubscriptionDetail>
            )}
            <ManageButton
              onClick={openBillingPortal}
              disabled={portalLoading}
            >
              {portalLoading ? 'Loading...' : 'Manage Billing'}
            </ManageButton>
          </SubscriptionInfo>
        )}

        {!isPro && (
          <>
            <Description style={{ marginTop: '1rem', fontWeight: 500, color: '#1f2937' }}>
              Choose your plan:
            </Description>
            <PricingOptions>
              <PriceButton
                onClick={() => startCheckout('monthly')}
                disabled={checkoutLoading}
              >
                $9.99/mo
                <small>Monthly billing</small>
              </PriceButton>
              <PriceButton
                recommended
                onClick={() => startCheckout('yearly')}
                disabled={checkoutLoading}
              >
                $99/year
                <small>Save 17%</small>
              </PriceButton>
            </PricingOptions>
            {checkoutLoading && (
              <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                <LoadingSpinner size="small" />
                <p style={{ margin: '0.5rem 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
                  Preparing checkout...
                </p>
              </div>
            )}
          </>
        )}

        {subscriptionError && (
          <ErrorText>Error: {subscriptionError}</ErrorText>
        )}
      </IntegrationCard>
    </Container>
  )
}

export default StripeIntegrationPage
