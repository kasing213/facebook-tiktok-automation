import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import styled from 'styled-components'
import { useAuth, useOAuth } from '../../hooks/useAuth'
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
    content: "✅";
    font-size: 1.125rem;
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

const IntegrationsPage: React.FC = () => {
  const location = useLocation()
  const [tenantId, setTenantId] = useState<string>('')
  const [successMessage, setSuccessMessage] = useState<string>('')

  // Get tenant ID from localStorage (set by DashboardHeader)
  useEffect(() => {
    const storedTenantId = localStorage.getItem('selectedTenantId')
    if (storedTenantId) {
      setTenantId(storedTenantId)
    }
  }, [])

  // Handle OAuth redirect success message
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search)
    const urlSuccess = urlParams.get('success')

    if (urlSuccess) {
      const platform = urlSuccess === 'facebook' ? 'Facebook' : 'TikTok'
      setSuccessMessage(`${platform} account connected successfully!`)

      // Clean up URL parameters
      const newUrl = new URL(window.location.href)
      newUrl.searchParams.delete('success')
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

  const handleRefresh = () => {
    refreshAuthStatus()
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
          {loading ? <LoadingSpinner size="small" /> : '🔄'}
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
                  ✅ Valid tokens: {authStatus.facebook.valid_tokens}
                </p>

                {authStatus.facebook.accounts && authStatus.facebook.accounts.length > 0 && (
                  <TokensList>
                    {authStatus.facebook.accounts.map((account, index) => (
                      <TokenItem key={index}>
                        <div><strong>Account:</strong> {account.account_name || account.account_ref}</div>
                        <TokenMeta>
                          Valid: {account.is_valid ? 'Yes ✓' : 'No ✗'} |
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
                  ✅ Valid tokens: {authStatus.tiktok.valid_tokens}
                </p>

                {authStatus.tiktok.accounts && authStatus.tiktok.accounts.length > 0 && (
                  <TokensList>
                    {authStatus.tiktok.accounts.map((account, index) => (
                      <TokenItem key={index}>
                        <div><strong>Account:</strong> {account.account_name || account.account_ref}</div>
                        <TokenMeta>
                          Valid: {account.is_valid ? 'Yes ✓' : 'No ✗'} |
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

          {/* Future Integrations Placeholders */}
          <IntegrationCard connected={false}>
            <CardHeader>
              <span style={{ fontSize: '2rem' }}>📄</span>
              <PlatformName>Invoice Generator</PlatformName>
              <StatusBadge connected={false}>Coming Soon</StatusBadge>
            </CardHeader>
            <Description>
              Generate professional invoices automatically. Integration coming soon.
            </Description>
          </IntegrationCard>

          <IntegrationCard connected={false}>
            <CardHeader>
              <span style={{ fontSize: '2rem' }}>📊</span>
              <PlatformName>Analytics API</PlatformName>
              <StatusBadge connected={false}>Coming Soon</StatusBadge>
            </CardHeader>
            <Description>
              Advanced analytics and reporting API. Integration coming soon.
            </Description>
          </IntegrationCard>
        </IntegrationsGrid>
      )}
    </Container>
  )
}

export default IntegrationsPage
