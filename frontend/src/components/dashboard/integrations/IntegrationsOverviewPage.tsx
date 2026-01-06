import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import styled from 'styled-components'
import { useAuth } from '../../../hooks/useAuth'
import { useTelegram } from '../../../hooks/useTelegram'
import { useSubscription } from '../../../hooks/useSubscription'
import { LoadingSpinner } from '../../LoadingSpinner'
import { ErrorMessage } from '../../ErrorMessage'
import SocialIcon from '../../SocialIcon'

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
`

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
`

const RefreshButton = styled.button`
  background: #4a90e2;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:hover:not(:disabled) {
    background: #2a5298;
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const SuccessMessage = styled.div`
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 8px;
  padding: 0.875rem 1.25rem;
  margin-bottom: 1.5rem;
  color: #155724;
  font-size: 0.9375rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`

const IconPlaceholder = styled.div<{ $color?: string }>`
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: ${props => props.$color || '#e5e7eb'};
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  color: white;
  flex-shrink: 0;
`

const IntegrationsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`

const IntegrationCard = styled.div<{ connected: boolean }>`
  border: 2px solid ${props => props.connected ? '#28a745' : '#e5e7eb'};
  border-radius: 12px;
  padding: 1.5rem;
  background: ${props => props.connected ? '#f8fff9' : 'white'};
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
`

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.875rem;
  margin-bottom: 1rem;
`

const PlatformName = styled.h3`
  margin: 0;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
  flex: 1;
`

const StatusBadge = styled.span<{ connected: boolean }>`
  padding: 0.375rem 0.875rem;
  border-radius: 20px;
  font-size: 0.8125rem;
  font-weight: 600;

  ${props => props.connected ? `
    background: #28a745;
    color: white;
  ` : `
    background: #dc3545;
    color: white;
  `}
`

const TierBadge = styled.span<{ tier: 'free' | 'pro' }>`
  padding: 0.375rem 0.875rem;
  border-radius: 20px;
  font-size: 0.8125rem;
  font-weight: 600;
  ${props => props.tier === 'pro' ? `
    background: linear-gradient(135deg, #ffd700 0%, #ff9500 100%);
    color: #1f2937;
  ` : `
    background: #e5e7eb;
    color: #6b7280;
  `}
`

const Description = styled.p`
  margin: 0 0 1rem 0;
  color: #6b7280;
  font-size: 0.9375rem;
  line-height: 1.5;
`

const ViewButton = styled.button`
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  margin-top: 1rem;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
  }
`

const IntegrationsOverviewPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [tenantId, setTenantId] = useState<string>('')
  const [successMessage, setSuccessMessage] = useState<string>('')

  useEffect(() => {
    const storedTenantId = localStorage.getItem('selectedTenantId')
    if (storedTenantId) {
      setTenantId(storedTenantId)
    }
  }, [])

  useEffect(() => {
    const urlParams = new URLSearchParams(location.search)
    const urlSuccess = urlParams.get('success')
    const subscription = urlParams.get('subscription')

    if (urlSuccess) {
      const platform = urlSuccess === 'facebook' ? 'Facebook' : 'TikTok'
      setSuccessMessage(`${platform} account connected successfully!`)
    }

    if (subscription === 'success') {
      setSuccessMessage('Subscription activated successfully! You now have Pro access.')
    } else if (subscription === 'cancelled') {
      setSuccessMessage('Checkout cancelled. You can try again anytime.')
    }

    if (urlSuccess || subscription) {
      const newUrl = new URL(window.location.href)
      newUrl.searchParams.delete('success')
      newUrl.searchParams.delete('subscription')
      window.history.replaceState({}, '', newUrl.pathname)
    }

    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000)
      return () => clearTimeout(timer)
    }
  }, [location.search, successMessage])

  const { authStatus, loading, error, refreshAuthStatus } = useAuth(tenantId || null)
  const { status: telegramStatus, fetchStatus: refreshTelegramStatus } = useTelegram()
  const { tier, isPro, fetchStatus: refreshSubscriptionStatus } = useSubscription()

  const handleRefresh = () => {
    refreshAuthStatus()
    refreshTelegramStatus()
    refreshSubscriptionStatus()
  }

  if (!tenantId) {
    return (
      <Container>
        <Title>Integrations</Title>
        <ErrorMessage message="No workspace selected. Please select a workspace from the header." />
      </Container>
    )
  }

  const integrations = [
    {
      id: 'facebook',
      name: 'Facebook',
      icon: <SocialIcon platform="facebook" size="large" />,
      connected: authStatus?.facebook?.connected || false,
      description: 'Automate posts, manage campaigns, and access Facebook Marketing API.',
      path: '/dashboard/integrations/facebook'
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      icon: <SocialIcon platform="tiktok" size="large" />,
      connected: authStatus?.tiktok?.connected || false,
      description: 'Schedule videos, analyze performance, and leverage TikTok Creator API.',
      path: '/dashboard/integrations/tiktok'
    },
    {
      id: 'telegram',
      name: 'Telegram',
      icon: <IconPlaceholder $color="#0088cc">T</IconPlaceholder>,
      connected: telegramStatus?.connected || false,
      description: 'Receive notifications and interact with the platform via bot.',
      path: '/dashboard/integrations/telegram'
    },
    {
      id: 'invoice',
      name: 'Invoice Generator',
      icon: <IconPlaceholder $color="#6b7280">IN</IconPlaceholder>,
      connected: true,
      description: 'Professional invoicing with customer management and PDF generation.',
      path: '/dashboard/integrations/invoice',
      tier: tier
    },
    {
      id: 'stripe',
      name: 'Stripe Payments',
      icon: <IconPlaceholder $color="#635bff">S</IconPlaceholder>,
      connected: isPro,
      description: 'Manage your subscription and billing through Stripe.',
      path: '/dashboard/integrations/stripe'
    }
  ]

  return (
    <Container>
      <Header>
        <Title>Integrations</Title>
        <RefreshButton onClick={handleRefresh} disabled={loading}>
          {loading && <LoadingSpinner size="small" />}
          Refresh
        </RefreshButton>
      </Header>

      {successMessage && <SuccessMessage>{successMessage}</SuccessMessage>}

      {error && <ErrorMessage message={`Failed to load authentication status: ${error}`} />}

      {loading && !authStatus ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <LoadingSpinner size="large" />
          <p style={{ marginTop: '1rem', color: '#6b7280' }}>Loading integration status...</p>
        </div>
      ) : (
        <IntegrationsGrid>
          {integrations.map(integration => (
            <IntegrationCard
              key={integration.id}
              connected={integration.connected}
              onClick={() => navigate(integration.path)}
            >
              <CardHeader>
                {integration.icon}
                <PlatformName>{integration.name}</PlatformName>
                {integration.tier ? (
                  <TierBadge tier={integration.tier}>
                    {integration.tier === 'pro' ? 'Pro' : 'Free'}
                  </TierBadge>
                ) : (
                  <StatusBadge connected={integration.connected}>
                    {integration.connected ? 'Connected' : 'Disconnected'}
                  </StatusBadge>
                )}
              </CardHeader>
              <Description>{integration.description}</Description>
              <ViewButton>
                View Details →
              </ViewButton>
            </IntegrationCard>
          ))}
        </IntegrationsGrid>
      )}
    </Container>
  )
}

export default IntegrationsOverviewPage
