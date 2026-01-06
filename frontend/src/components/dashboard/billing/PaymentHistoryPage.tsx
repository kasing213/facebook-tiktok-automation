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
  margin: 0;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
`

export function PaymentHistoryPage() {
  const navigate = useNavigate()

  return (
    <PageContainer>
      <BackLink onClick={() => navigate('/dashboard/billing')}>
        ← Back to Billing
      </BackLink>

      <ComingSoonCard>
        <IconWrapper>📋</IconWrapper>
        <Title>Payment History Coming Soon</Title>
        <Subtitle>
          Your payment history will appear here once billing is enabled.
          Currently all features are free during beta.
        </Subtitle>
      </ComingSoonCard>
    </PageContainer>
  )
}

export default PaymentHistoryPage
