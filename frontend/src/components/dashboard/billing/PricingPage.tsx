import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'

const PageContainer = styled.div`
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
`

const BackLink = styled.button`
  background: none;
  border: none;
  color: #4a90e2;
  font-size: 0.9375rem;
  cursor: pointer;
  padding: 0;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;

  &:hover {
    text-decoration: underline;
  }
`

const ComingSoonCard = styled.div`
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px dashed #cbd5e1;
  border-radius: 16px;
  padding: 4rem 2rem;
  text-align: center;
`

const IconWrapper = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
  color: #64748b;

  svg {
    width: 64px;
    height: 64px;
  }
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
  margin: 0;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
`

export function PricingPage() {
  const navigate = useNavigate()

  return (
    <PageContainer>
      <BackLink onClick={() => navigate('/dashboard/billing')}>
        ← Back to Billing
      </BackLink>

      <ComingSoonCard>
        <IconWrapper>
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
        </IconWrapper>
        <Title>Pricing Coming Soon</Title>
        <Subtitle>
          All features are currently free during our beta period.
          We'll announce pricing plans when payment processing becomes available.
        </Subtitle>
      </ComingSoonCard>
    </PageContainer>
  )
}

export default PricingPage
