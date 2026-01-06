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

const FacebookIntegrationPage: React.FC = () => {
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

    if (urlSuccess === 'facebook') {
      setSuccessMessage('Facebook account connected successfully!')
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
  const { initiating, errors: oauthErrors, clearErrors, initiateFacebookOAuth } = useOAuth()

  const handleConnectFacebook = async () => {
    if (!tenantId) return
    clearErrors()
    try {
      await initiateFacebookOAuth(tenantId)
    } catch (error) {
      console.error('Failed to initiate Facebook OAuth:', error)
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

  const isConnected = authStatus?.facebook?.connected || false

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
          <p style={{ marginTop: '1rem', color: '#6b7280' }}>Loading Facebook status...</p>
        </div>
      ) : (
        <IntegrationCard connected={isConnected}>
          <CardHeader>
            <SocialIcon platform="facebook" size="large" />
            <PlatformName>Facebook Integration</PlatformName>
            <StatusBadge connected={isConnected}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </StatusBadge>
          </CardHeader>

          <Description>
            Connect your Facebook account to automate posts, manage campaigns, and access Facebook Marketing API features.
            With Facebook integration, you can schedule posts, analyze engagement, and manage your business pages.
          </Description>

          {isConnected && authStatus?.facebook && (
            <div>
              <InfoText>
                Valid tokens: {authStatus.facebook.valid_tokens}
              </InfoText>

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
                  'Connect Another Account'
                )}
              </ConnectButton>
            </div>
          )}

          {!isConnected && (
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
            <ErrorText>Error: {oauthErrors.facebook}</ErrorText>
          )}
        </IntegrationCard>
      )}
    </Container>
  )
}

export default FacebookIntegrationPage
