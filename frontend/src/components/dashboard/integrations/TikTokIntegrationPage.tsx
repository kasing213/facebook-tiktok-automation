import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth, useOAuth } from '../../../hooks/useAuth'
import { LoadingSpinner } from '../../LoadingSpinner'
import { ErrorMessage } from '../../ErrorMessage'
import SocialIcon from '../../SocialIcon'
import {
  Container,
  Header,
  BackButton,
  IntegrationCard,
  CardHeader,
  PlatformName,
  StatusBadge,
  Description,
  TokensList,
  TokenItem,
  TokenMeta,
  ConnectButton,
  ErrorText,
  SuccessMessage,
  InfoText
} from './shared/styles'

const TikTokIntegrationPage: React.FC = () => {
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

    if (urlSuccess === 'tiktok') {
      setSuccessMessage('TikTok account connected successfully!')
      const newUrl = new URL(window.location.href)
      newUrl.searchParams.delete('success')
      window.history.replaceState({}, '', newUrl.pathname)
    }

    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000)
      return () => clearTimeout(timer)
    }
  }, [location.search, successMessage])

  const { authStatus, loading, error } = useAuth(tenantId || null)
  const { initiating, errors: oauthErrors, clearErrors, initiateTikTokOAuth } = useOAuth()

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
        <Header>
          <BackButton onClick={() => navigate('/dashboard/integrations')}>
            ← Back to Integrations
          </BackButton>
        </Header>
        <ErrorMessage message="No workspace selected. Please select a workspace from the header." />
      </Container>
    )
  }

  const isConnected = authStatus?.tiktok?.connected || false

  return (
    <Container>
      <Header>
        <BackButton onClick={() => navigate('/dashboard/integrations')}>
          ← Back to Integrations
        </BackButton>
      </Header>

      {successMessage && <SuccessMessage>{successMessage}</SuccessMessage>}

      {error && <ErrorMessage message={`Failed to load status: ${error}`} />}

      {loading && !authStatus ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <LoadingSpinner size="large" />
          <p style={{ marginTop: '1rem', color: '#6b7280' }}>Loading TikTok status...</p>
        </div>
      ) : (
        <IntegrationCard connected={isConnected}>
          <CardHeader>
            <SocialIcon platform="tiktok" size="large" />
            <PlatformName>TikTok Integration</PlatformName>
            <StatusBadge connected={isConnected}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </StatusBadge>
          </CardHeader>

          <Description>
            Connect your TikTok account to schedule videos, analyze performance, and leverage TikTok Creator API capabilities.
            Manage your content calendar and track engagement metrics all in one place.
          </Description>

          {isConnected && authStatus?.tiktok && (
            <div>
              <InfoText>
                Valid tokens: {authStatus.tiktok.valid_tokens}
              </InfoText>

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
                  'Connect Another Account'
                )}
              </ConnectButton>
            </div>
          )}

          {!isConnected && (
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
            <ErrorText>Error: {oauthErrors.tiktok}</ErrorText>
          )}
        </IntegrationCard>
      )}
    </Container>
  )
}

export default TikTokIntegrationPage
