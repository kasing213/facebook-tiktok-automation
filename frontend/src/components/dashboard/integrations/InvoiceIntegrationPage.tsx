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
  TierBadge,
  Description,
  FeatureList,
  FeatureItem,
  UpgradeButton,
  OpenButton,
  ErrorText
} from './shared/styles'

const InvoiceIntegrationPage: React.FC = () => {
  const navigate = useNavigate()

  const {
    tier,
    isPro,
    features,
    checkoutLoading,
    error: subscriptionError,
    startCheckout
  } = useSubscription()

  return (
    <Container>
      <Header>
        <BackButton onClick={() => navigate('/dashboard/integrations')}>
          ← Back to Integrations
        </BackButton>
      </Header>

      <IntegrationCard connected={true}>
        <CardHeader>
          <PlatformName>Invoice Generator</PlatformName>
          <TierBadge tier={tier}>
            {isPro ? 'Pro' : 'Free'}
          </TierBadge>
        </CardHeader>

        <Description>
          Professional invoicing with customer management, PDF generation, and export features.
          Create beautiful invoices, track payments, and manage your customer database all in one place.
        </Description>

        <FeatureList>
          <FeatureItem available={features.createInvoices}>Create & View Invoices</FeatureItem>
          <FeatureItem available={features.manageCustomers}>Manage Customers</FeatureItem>
          <FeatureItem available={features.downloadPdf}>PDF Download</FeatureItem>
          <FeatureItem available={features.exportData}>Excel/CSV Export</FeatureItem>
        </FeatureList>

        {!isPro && (
          <>
            <Description style={{ marginTop: '1rem', color: '#6b7280', fontSize: '0.9375rem' }}>
              Upgrade to Pro for full access to PDF downloads and data exports.
            </Description>
            <UpgradeButton
              onClick={() => startCheckout('monthly')}
              disabled={checkoutLoading}
            >
              {checkoutLoading ? (
                <>
                  <LoadingSpinner size="small" />
                  Processing...
                </>
              ) : (
                'Upgrade to Pro - $9.99/mo'
              )}
            </UpgradeButton>
          </>
        )}

        <OpenButton onClick={() => navigate('/dashboard/invoices')}>
          Open Invoice Generator
        </OpenButton>

        {subscriptionError && (
          <ErrorText>Error: {subscriptionError}</ErrorText>
        )}
      </IntegrationCard>
    </Container>
  )
}

export default InvoiceIntegrationPage
