import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { useAuth, useOAuth } from '../hooks/useAuth'
import { LoadingSpinner } from './LoadingSpinner'
import { ErrorMessage } from './ErrorMessage'

const DashboardContainer = styled.div`
  max-width: 800px;
  width: 100%;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);

  @media (max-width: 768px) {
    margin: 1rem;
    padding: 1.5rem;
  }
`

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e1e5e9;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
`

const Title = styled.h1`
  color: #333;
  margin: 0;
  font-size: 2rem;
  font-weight: 600;
`

const BackButton = styled.button`
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.3s ease;

  &:hover {
    background: #545b62;
  }
`

const SuccessMessage = styled.div`
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.5rem;
  color: #155724;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:before {
    content: "✅";
    font-size: 1rem;
  }
`

const StatusGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`

const PlatformCard = styled.div<{ connected: boolean }>`
  border: 2px solid ${props => props.connected ? '#28a745' : '#dc3545'};
  border-radius: 12px;
  padding: 1.5rem;
  background: ${props => props.connected ? '#f8fff9' : '#fff8f8'};
`

const PlatformHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
`

const PlatformIcon = styled.span<{ platform: 'facebook' | 'tiktok' }>`
  font-size: 1.5rem;

  ${props => props.platform === 'facebook' ? `
    &:before {
      content: "📘";
    }
  ` : `
    &:before {
      content: "🎵";
    }
  `}
`

const PlatformName = styled.h3`
  margin: 0;
  color: #333;
  font-size: 1.2rem;
  text-transform: capitalize;
`

const StatusBadge = styled.span<{ connected: boolean }>`
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-left: auto;

  ${props => props.connected ? `
    background: #28a745;
    color: white;
  ` : `
    background: #dc3545;
    color: white;
  `}
`

const TokensList = styled.div`
  margin-top: 1rem;
`

const TokenItem = styled.div`
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;

  &:last-child {
    margin-bottom: 0;
  }
`

const TokenMeta = styled.div`
  color: #666;
  font-size: 0.8rem;
  margin-top: 0.25rem;
`

const RefreshButton = styled.button`
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:hover:not(:disabled) {
    background: #0056b3;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const ConnectButton = styled.button<{ platform: 'facebook' | 'tiktok' }>`
  ${props => props.platform === 'facebook' ? `
    background: #4267b2;
    &:hover:not(:disabled) {
      background: #365899;
    }
  ` : `
    background: #000;
    &:hover:not(:disabled) {
      background: #333;
    }
  `}
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    transform: translateY(-1px);
  }
`

const Dashboard: React.FC = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const [tenantId, setTenantId] = useState<string>('')
  const [successMessage, setSuccessMessage] = useState<string>('')

  // Extract tenant ID and success message from navigation state or URL params
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search)
    const urlTenantId = urlParams.get('tenant_id')
    const urlSuccess = urlParams.get('success')

    if (location.state) {
      const { tenantId: stateTenantId, message } = location.state as any
      if (stateTenantId) setTenantId(stateTenantId)
      if (message) setSuccessMessage(message)
    } else if (urlTenantId) {
      // Handle OAuth redirect from backend
      setTenantId(urlTenantId)
      if (urlSuccess) {
        const platform = urlSuccess === 'facebook' ? 'Facebook' : 'TikTok'
        setSuccessMessage(`${platform} account connected successfully!`)

        // Clean up URL parameters
        const newUrl = new URL(window.location.href)
        newUrl.searchParams.delete('success')
        newUrl.searchParams.delete('tenant_id')
        window.history.replaceState({}, '', newUrl.pathname)
      }
    }

    // Clear success message after 5 seconds
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000)
      return () => clearTimeout(timer)
    }
  }, [location.state, location.search, successMessage])

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

  const handleBackToLogin = () => {
    navigate('/')
  }

  if (!tenantId) {
    return (
      <DashboardContainer>
        <Header>
          <Title>Dashboard</Title>
          <BackButton onClick={handleBackToLogin}>
            Back to Login
          </BackButton>
        </Header>
        <ErrorMessage message="No tenant ID provided. Please go back to login and select an organization." />
      </DashboardContainer>
    )
  }

  return (
    <DashboardContainer>
      <Header>
        <Title>Dashboard</Title>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <RefreshButton onClick={handleRefresh} disabled={loading}>
            {loading ? <LoadingSpinner size="small" /> : '🔄'}
            Refresh
          </RefreshButton>
          <BackButton onClick={handleBackToLogin}>
            Back to Login
          </BackButton>
        </div>
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
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <LoadingSpinner size="large" />
          <p style={{ marginTop: '1rem', color: '#666' }}>Loading authentication status...</p>
        </div>
      )}

      {authStatus && (
        <StatusGrid>
          <PlatformCard connected={authStatus.facebook?.connected || false}>
            <PlatformHeader>
              <PlatformIcon platform="facebook" />
              <PlatformName>Facebook</PlatformName>
              <StatusBadge connected={authStatus.facebook?.connected || false}>
                {authStatus.facebook?.connected ? 'Connected' : 'Not Connected'}
              </StatusBadge>
            </PlatformHeader>

            {authStatus.facebook?.connected && (
              <div>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: '#666' }}>
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
              <div>
                <p style={{ margin: '0 0 1rem 0', color: '#666', fontSize: '0.9rem' }}>
                  Connect your Facebook account to manage Facebook campaigns.
                </p>
                <ConnectButton
                  platform="facebook"
                  onClick={handleConnectFacebook}
                  disabled={initiating.facebook}
                >
                  <span>📘</span>
                  {initiating.facebook ? (
                    <>
                      <LoadingSpinner size="small" />
                      Connecting...
                    </>
                  ) : (
                    'Connect Facebook'
                  )}
                </ConnectButton>
                {oauthErrors.facebook && (
                  <div style={{ marginTop: '0.5rem', color: '#dc3545', fontSize: '0.8rem' }}>
                    Error: {oauthErrors.facebook}
                  </div>
                )}
              </div>
            )}
          </PlatformCard>

          <PlatformCard connected={authStatus.tiktok?.connected || false}>
            <PlatformHeader>
              <PlatformIcon platform="tiktok" />
              <PlatformName>TikTok</PlatformName>
              <StatusBadge connected={authStatus.tiktok?.connected || false}>
                {authStatus.tiktok?.connected ? 'Connected' : 'Not Connected'}
              </StatusBadge>
            </PlatformHeader>

            {authStatus.tiktok?.connected && (
              <div>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: '#666' }}>
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
              <div>
                <p style={{ margin: '0 0 1rem 0', color: '#666', fontSize: '0.9rem' }}>
                  Connect your TikTok account to manage TikTok campaigns.
                </p>
                <ConnectButton
                  platform="tiktok"
                  onClick={handleConnectTikTok}
                  disabled={initiating.tiktok}
                >
                  <span>🎵</span>
                  {initiating.tiktok ? (
                    <>
                      <LoadingSpinner size="small" />
                      Connecting...
                    </>
                  ) : (
                    'Connect TikTok'
                  )}
                </ConnectButton>
                {oauthErrors.tiktok && (
                  <div style={{ marginTop: '0.5rem', color: '#dc3545', fontSize: '0.8rem' }}>
                    Error: {oauthErrors.tiktok}
                  </div>
                )}
              </div>
            )}
          </PlatformCard>
        </StatusGrid>
      )}
    </DashboardContainer>
  )
}

export default Dashboard