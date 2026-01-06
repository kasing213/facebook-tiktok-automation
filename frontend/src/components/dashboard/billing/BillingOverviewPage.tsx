import styled from 'styled-components'

const PageContainer = styled.div`
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
`

const ComingSoonCard = styled.div`
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px dashed #cbd5e1;
  border-radius: 16px;
  padding: 4rem 2rem;
  text-align: center;
`

const IconWrapper = styled.div`
  font-size: 4rem;
  margin-bottom: 1.5rem;
`

const Title = styled.h1`
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.75rem 0;
`

const Subtitle = styled.p`
  font-size: 1.125rem;
  color: #64748b;
  margin: 0 0 2rem 0;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
`

const BetaBadge = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  font-weight: 600;
  font-size: 0.9375rem;
`

const FeatureList = styled.div`
  margin-top: 2.5rem;
  padding-top: 2rem;
  border-top: 1px solid #e2e8f0;
`

const FeatureTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: #475569;
  margin: 0 0 1rem 0;
`

const FeatureGrid = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
`

const FeatureTag = styled.span`
  background: #e0f2fe;
  color: #0369a1;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
`

export function BillingOverviewPage() {
  return (
    <PageContainer>
      <ComingSoonCard>
        <IconWrapper>💳</IconWrapper>
        <Title>Billing Coming Soon</Title>
        <Subtitle>
          We're working on bringing payment processing to Cambodia.
          Until then, enjoy all Pro features for free!
        </Subtitle>
        <BetaBadge>
          <span>✓</span>
          All Features Free During Beta
        </BetaBadge>

        <FeatureList>
          <FeatureTitle>Currently included for free:</FeatureTitle>
          <FeatureGrid>
            <FeatureTag>Unlimited Invoices</FeatureTag>
            <FeatureTag>PDF Downloads</FeatureTag>
            <FeatureTag>Data Export</FeatureTag>
            <FeatureTag>Facebook Integration</FeatureTag>
            <FeatureTag>TikTok Integration</FeatureTag>
            <FeatureTag>Telegram Notifications</FeatureTag>
          </FeatureGrid>
        </FeatureList>
      </ComingSoonCard>
    </PageContainer>
  )
}

export default BillingOverviewPage
