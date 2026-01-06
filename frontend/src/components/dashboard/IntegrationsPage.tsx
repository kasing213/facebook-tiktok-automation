import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { useAuth, useOAuth } from '../../hooks/useAuth'
import { useTelegram } from '../../hooks/useTelegram'
import { useSubscription } from '../../hooks/useSubscription'
import { LoadingSpinner } from '../LoadingSpinner'
import { ErrorMessage } from '../ErrorMessage'
import SocialIcon from '../SocialIcon'

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

  &:before {
    content: "\\2713";
    font-size: 1.125rem;
    font-weight: 700;
    color: #28a745;
  }
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

const Description = styled.p`
  margin: 0 0 1rem 0;
  color: #6b7280;
  font-size: 0.9375rem;
  line-height: 1.5;
`

const TokensList = styled.div`
  margin: 1rem 0;
`

const TokenItem = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.875rem;
  margin-bottom: 0.625rem;
  font-size: 0.9375rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const TokenMeta = styled.div`
  color: #6b7280;
  font-size: 0.8125rem;
  margin-top: 0.375rem;
`

const ConnectButton = styled.button<{ platform: 'facebook' | 'tiktok' }>`
  ${props => props.platform === 'facebook' ? `
    background: linear-gradient(135deg, #4267b2 0%, #365899 100%);
  ` : `
    background: linear-gradient(135deg, #000 0%, #333 100%);
  `}
  color: white;
  border: none;
  padding: 0.875rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  width: 100%;
  margin-top: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
`

const ErrorText = styled.div`
  margin-top: 0.625rem;
  color: #dc3545;
  font-size: 0.8125rem;
`

const TelegramButton = styled.button`
  background: linear-gradient(135deg, #0088cc 0%, #229ED9 100%);
  color: white;
  border: none;
  padding: 0.875rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  width: 100%;
  margin-top: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 136, 204, 0.3);
  }
`

const DisconnectButton = styled.button`
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    background: #c82333;
  }
`

const LinkCodeBox = styled.div`
  background: #f0f9ff;
  border: 1px solid #0088cc;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
  text-align: center;
`

const LinkCode = styled.code`
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0088cc;
  letter-spacing: 0.1em;
  margin: 0.5rem 0;
`

const DeepLinkButton = styled.a`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #0088cc;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 600;
  margin-top: 0.5rem;
  transition: all 0.2s ease;

  &:hover {
    background: #006699;
    transform: translateY(-1px);
  }
`

const ExpiryText = styled.p`
  font-size: 0.8125rem;
  color: #6b7280;
  margin-top: 0.5rem;
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

const FeatureList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 1rem 0;
`

const FeatureItem = styled.li<{ available: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0;
  font-size: 0.9375rem;
  color: ${props => props.available ? '#1f2937' : '#9ca3af'};

  &:before {
    content: "${props => props.available ? '✓' : '✗'}";
    color: ${props => props.available ? '#28a745' : '#dc3545'};
    font-weight: 700;
  }
`

const UpgradeButton = styled.button`
  background: linear-gradient(135deg, #ffd700 0%, #ff9500 100%);
  color: #1f2937;
  border: none;
  padding: 0.875rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  width: 100%;
  margin-top: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 149, 0, 0.3);
  }
`

const OpenButton = styled.button`
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  color: white;
  border: none;
  padding: 0.875rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  width: 100%;
  margin-top: 0.75rem;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
  }
`

const PricingOptions = styled.div`
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
`

const PriceButton = styled.button<{ recommended?: boolean }>`
  flex: 1;
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;

  ${props => props.recommended ? `
    background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
    color: white;
    border: none;
  ` : `
    background: white;
    color: #4a90e2;
    border: 2px solid #4a90e2;
  `}

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  small {
    display: block;
    font-weight: 400;
    font-size: 0.75rem;
    margin-top: 0.25rem;
    opacity: 0.8;
  }
`

const SubscriptionInfo = styled.div`
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
`

const SubscriptionDetail = styled.p`
  margin: 0.25rem 0;
  font-size: 0.875rem;
  color: #6b7280;
`

const ManageButton = styled.button`
  background: white;
  color: #4a90e2;
  border: 2px solid #4a90e2;
  padding: 0.625rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 0.75rem;

  &:hover:not(:disabled) {
    background: #f0f7ff;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const IntegrationsPage: React.FC = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const [tenantId, setTenantId] = useState<string>('')
  const [successMessage, setSuccessMessage] = useState<string>('')

  // Get tenant ID from localStorage (set by DashboardHeader)
  useEffect(() => {
    const storedTenantId = localStorage.getItem('selectedTenantId')
    if (storedTenantId) {
      setTenantId(storedTenantId)
    }
  }, [])

  // Handle OAuth redirect and subscription success messages
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
      refreshSubscriptionStatus()
    } else if (subscription === 'cancelled') {
      setSuccessMessage('Checkout cancelled. You can try again anytime.')
    }

    // Clean up URL parameters
    if (urlSuccess || subscription) {
      const newUrl = new URL(window.location.href)
      newUrl.searchParams.delete('success')
      newUrl.searchParams.delete('subscription')
      window.history.replaceState({}, '', newUrl.pathname)
    }

    // Clear success message after 5 seconds
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000)
      return () => clearTimeout(timer)
    }
  }, [location.search, successMessage])

  const { authStatus, loading, error, refreshAuthStatus } = useAuth(tenantId || null)
  const { initiating, errors: oauthErrors, clearErrors, initiateFacebookOAuth, initiateTikTokOAuth } = useOAuth()
  const {
    status: telegramStatus,
    linkCode,
    generating: telegramGenerating,
    disconnecting: telegramDisconnecting,
    error: telegramError,
    generateLinkCode,
    disconnect: disconnectTelegram,
    fetchStatus: refreshTelegramStatus,
    clearError: clearTelegramError
  } = useTelegram()
  const {
    tier,
    isPro,
    features,
    checkoutLoading,
    portalLoading,
    error: subscriptionError,
    startCheckout,
    openBillingPortal,
    fetchStatus: refreshSubscriptionStatus,
    periodEnd,
    cancelAtPeriodEnd
  } = useSubscription()

  const handleRefresh = () => {
    refreshAuthStatus()
    refreshTelegramStatus()
    refreshSubscriptionStatus()
  }

  const handleConnectTelegram = async () => {
    clearTelegramError()
    try {
      await generateLinkCode()
    } catch (error) {
      console.error('Failed to generate Telegram link code:', error)
    }
  }

  const handleDisconnectTelegram = async () => {
    clearTelegramError()
    try {
      await disconnectTelegram()
      setSuccessMessage('Telegram account disconnected successfully!')
    } catch (error) {
      console.error('Failed to disconnect Telegram:', error)
    }
  }

  const handleConnectFacebook = async () => {
    if (!tenantId) return
    clearErrors()
    try {
      await initiateFacebookOAuth(tenantId)
    } catch (error) {
      console.error('Failed to initiate Facebook OAuth:', error)
    }
  }

  const handleConnectTikTok = async () => {
    if (!tenantId) return
    clearErrors()
    try {
      await initiateTikTokOAuth(tenantId)
    } catch (error) {
      console.error('Failed to initiate TikTok OAuth:', error)
    }
  }

  if (!tenantId) {
    return (
      <Container>
        <Title>Integrations</Title>
        <ErrorMessage message="No workspace selected. Please select a workspace from the header." />
      </Container>
    )
  }

  return (
    <Container>
      <Header>
        <Title>Integrations</Title>
        <RefreshButton onClick={handleRefresh} disabled={loading}>
          {loading && <LoadingSpinner size="small" />}
          Refresh
        </RefreshButton>
      </Header>

      {successMessage && (
        <SuccessMessage>
          {successMessage}
        </SuccessMessage>
      )}

      {error && (
        <ErrorMessage message={`Failed to load authentication status: ${error}`} />
      )}

      {loading && !authStatus && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <LoadingSpinner size="large" />
          <p style={{ marginTop: '1rem', color: '#6b7280' }}>Loading integration status...</p>
        </div>
      )}

      {authStatus && (
        <IntegrationsGrid>
          {/* Facebook Integration */}
          <IntegrationCard connected={authStatus.facebook?.connected || false}>
            <CardHeader>
              <SocialIcon platform="facebook" size="large" />
              <PlatformName>Facebook</PlatformName>
              <StatusBadge connected={authStatus.facebook?.connected || false}>
                {authStatus.facebook?.connected ? 'Connected' : 'Disconnected'}
              </StatusBadge>
            </CardHeader>

            <Description>
              Connect your Facebook account to automate posts, manage campaigns, and access Facebook Marketing API features.
            </Description>

            {authStatus.facebook?.connected && (
              <div>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9375rem', color: '#6b7280', fontWeight: 500 }}>
                  Valid tokens: {authStatus.facebook.valid_tokens}
                </p>

                {authStatus.facebook.accounts && authStatus.facebook.accounts.length > 0 && (
                  <TokensList>
                    {authStatus.facebook.accounts.map((account, index) => (
                      <TokenItem key={index}>
                        <div><strong>Account:</strong> {account.account_name || account.account_ref}</div>
                        <TokenMeta>
                          Valid: {account.is_valid ? 'Yes' : 'No'} |
                          {account.expires_at ?
                            ` Expires: ${new Date(account.expires_at).toLocaleDateString()}` :
                            ' No expiration'
                          }
                        </TokenMeta>
                      </TokenItem>
                    ))}
                  </TokensList>
                )}
              </div>
            )}

            {!authStatus.facebook?.connected && (
              <ConnectButton
                platform="facebook"
                onClick={handleConnectFacebook}
                disabled={initiating.facebook}
              >
                <SocialIcon platform="facebook" size="small" />
                {initiating.facebook ? (
                  <>
                    <LoadingSpinner size="small" />
                    Connecting...
                  </>
                ) : (
                  'Connect Facebook'
                )}
              </ConnectButton>
            )}

            {oauthErrors.facebook && (
              <ErrorText>
                Error: {oauthErrors.facebook}
              </ErrorText>
            )}
          </IntegrationCard>

          {/* TikTok Integration */}
          <IntegrationCard connected={authStatus.tiktok?.connected || false}>
            <CardHeader>
              <SocialIcon platform="tiktok" size="large" />
              <PlatformName>TikTok</PlatformName>
              <StatusBadge connected={authStatus.tiktok?.connected || false}>
                {authStatus.tiktok?.connected ? 'Connected' : 'Disconnected'}
              </StatusBadge>
            </CardHeader>

            <Description>
              Connect your TikTok account to schedule videos, analyze performance, and leverage TikTok Creator API capabilities.
            </Description>

            {authStatus.tiktok?.connected && (
              <div>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9375rem', color: '#6b7280', fontWeight: 500 }}>
                  Valid tokens: {authStatus.tiktok.valid_tokens}
                </p>

                {authStatus.tiktok.accounts && authStatus.tiktok.accounts.length > 0 && (
                  <TokensList>
                    {authStatus.tiktok.accounts.map((account, index) => (
                      <TokenItem key={index}>
                        <div><strong>Account:</strong> {account.account_name || account.account_ref}</div>
                        <TokenMeta>
                          Valid: {account.is_valid ? 'Yes' : 'No'} |
                          {account.expires_at ?
                            ` Expires: ${new Date(account.expires_at).toLocaleDateString()}` :
                            ' No expiration'
                          }
                        </TokenMeta>
                      </TokenItem>
                    ))}
                  </TokensList>
                )}
              </div>
            )}

            {!authStatus.tiktok?.connected && (
              <ConnectButton
                platform="tiktok"
                onClick={handleConnectTikTok}
                disabled={initiating.tiktok}
              >
                <SocialIcon platform="tiktok" size="small" />
                {initiating.tiktok ? (
                  <>
                    <LoadingSpinner size="small" />
                    Connecting...
                  </>
                ) : (
                  'Connect TikTok'
                )}
              </ConnectButton>
            )}

            {oauthErrors.tiktok && (
              <ErrorText>
                Error: {oauthErrors.tiktok}
              </ErrorText>
            )}
          </IntegrationCard>

          {/* Telegram Integration */}
          <IntegrationCard connected={telegramStatus?.connected || false}>
            <CardHeader>
              <span style={{
                width: '28px',
                height: '28px',
                background: '#0088cc',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '0.75rem',
                fontWeight: 700
              }}>TG</span>
              <PlatformName>Telegram</PlatformName>
              <StatusBadge connected={telegramStatus?.connected || false}>
                {telegramStatus?.connected ? 'Connected' : 'Disconnected'}
              </StatusBadge>
            </CardHeader>

            <Description>
              Connect your Telegram account to receive notifications, run commands, and interact with the platform via bot.
            </Description>

            {telegramStatus?.connected && (
              <div>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9375rem', color: '#6b7280', fontWeight: 500 }}>
                  Connected as @{telegramStatus.telegram_username || telegramStatus.telegram_user_id}
                </p>
                {telegramStatus.linked_at && (
                  <TokenMeta>
                    Linked: {new Date(telegramStatus.linked_at).toLocaleDateString()}
                  </TokenMeta>
                )}
                <DisconnectButton
                  onClick={handleDisconnectTelegram}
                  disabled={telegramDisconnecting}
                >
                  {telegramDisconnecting ? 'Disconnecting...' : 'Disconnect Telegram'}
                </DisconnectButton>
              </div>
            )}

            {!telegramStatus?.connected && !linkCode && (
              <TelegramButton
                onClick={handleConnectTelegram}
                disabled={telegramGenerating}
              >
                {telegramGenerating ? (
                  <>
                    <LoadingSpinner size="small" />
                    Generating...
                  </>
                ) : (
                  'Connect Telegram'
                )}
              </TelegramButton>
            )}

            {!telegramStatus?.connected && linkCode && (
              <LinkCodeBox>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>
                  Click the button below or send this code to the bot:
                </p>
                <LinkCode>{linkCode.code}</LinkCode>
                <DeepLinkButton
                  href={linkCode.deep_link}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open Telegram Bot
                </DeepLinkButton>
                <ExpiryText>
                  Code expires: {new Date(linkCode.expires_at).toLocaleTimeString()}
                </ExpiryText>
              </LinkCodeBox>
            )}

            {telegramError && (
              <ErrorText>
                Error: {telegramError}
              </ErrorText>
            )}
          </IntegrationCard>

          {/* Invoice Generator Integration */}
          <IntegrationCard connected={true}>
            <CardHeader>
              <span style={{
                width: '28px',
                height: '28px',
                background: 'linear-gradient(135deg, #4a90e2 0%, #2a5298 100%)',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '0.75rem',
                fontWeight: 700
              }}>INV</span>
              <PlatformName>Invoice Generator</PlatformName>
              <TierBadge tier={tier}>
                {isPro ? 'Pro' : 'Free'}
              </TierBadge>
            </CardHeader>

            <Description>
              Professional invoicing with customer management, PDF generation, and export features.
            </Description>

            <FeatureList>
              <FeatureItem available={features.createInvoices}>Create & View Invoices</FeatureItem>
              <FeatureItem available={features.manageCustomers}>Manage Customers</FeatureItem>
              <FeatureItem available={features.downloadPdf}>PDF Download</FeatureItem>
              <FeatureItem available={features.exportData}>Excel/CSV Export</FeatureItem>
            </FeatureList>

            {!isPro && (
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
                  'Upgrade to Pro'
                )}
              </UpgradeButton>
            )}

            <OpenButton onClick={() => navigate('/dashboard/invoices')}>
              Open Invoice Generator
            </OpenButton>

            {subscriptionError && (
              <ErrorText>Error: {subscriptionError}</ErrorText>
            )}
          </IntegrationCard>

          {/* Stripe Payments / Subscription Management */}
          <IntegrationCard connected={isPro}>
            <CardHeader>
              <span style={{
                width: '28px',
                height: '28px',
                background: 'linear-gradient(135deg, #635bff 0%, #7a73ff 100%)',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '0.625rem',
                fontWeight: 700
              }}>PAY</span>
              <PlatformName>Stripe Payments</PlatformName>
              <StatusBadge connected={isPro}>
                {isPro ? 'Active' : 'Not Subscribed'}
              </StatusBadge>
            </CardHeader>

            <Description>
              Manage your subscription and billing through Stripe's secure payment platform.
            </Description>

            {isPro && (
              <SubscriptionInfo>
                <SubscriptionDetail>
                  <strong>Status:</strong> Active
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
                <Description style={{ marginTop: '1rem' }}>
                  Upgrade to Pro for full access to PDF downloads and data exports.
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
              </>
            )}
          </IntegrationCard>
        </IntegrationsGrid>
      )}
    </Container>
  )
}

export default IntegrationsPage
