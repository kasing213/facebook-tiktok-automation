import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { useTenants, useAuth, useOAuth, useCredentialsStatus } from '../hooks/useAuth'
import { LoadingSpinner } from './LoadingSpinner'
import { ErrorMessage } from './ErrorMessage'

// TODO: Remove when OAuth credentials are properly configured
// This component currently works in demo mode with placeholder functionality
// When FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, TIKTOK_CLIENT_ID, and TIKTOK_CLIENT_SECRET
// are properly configured in .env, the OAuth flows will work with real APIs

const LoginContainer = styled.div`
  max-width: 600px;
  width: 100%;
  padding: 2.5rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  text-align: center;
  margin: 2rem auto;

  @media (max-width: 768px) {
    margin: 1rem;
    padding: 2rem;
    border-radius: 12px;
  }

  @media (max-width: 480px) {
    margin: 0.5rem;
    padding: 1.5rem;
    border-radius: 8px;
  }
`

const Title = styled.h1`
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 2rem;
  font-weight: 600;
`

const Subtitle = styled.p`
  color: #666;
  margin-bottom: 2rem;
  font-size: 1rem;
  line-height: 1.5;
`

const TenantSelector = styled.div`
  margin-bottom: 2rem;
`

const Label = styled.label`
  display: block;
  color: #333;
  font-weight: 500;
  margin-bottom: 0.5rem;
  text-align: left;
`

const Select = styled.select`
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
  transition: border-color 0.3s ease;

  &:focus {
    outline: none;
    border-color: #4267b2;
  }

  &:disabled {
    background: #f8f9fa;
    cursor: not-allowed;
  }
`

const OAuthButtonsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
`

const OAuthButton = styled.button<{ platform: 'facebook' | 'tiktok'; demoMode?: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.875rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  min-height: 50px;

  /* Add visual indicator for demo mode */
  ${props => props.demoMode ? `
    border: 2px dashed rgba(255, 255, 255, 0.5);
    background: linear-gradient(135deg, ${props.platform === 'facebook' ? '#4267b2' : '#000'} 0%, ${props.platform === 'facebook' ? '#365899' : '#333'} 100%);
  ` : ''}

  ${props => props.platform === 'facebook' ? `
    background: ${props.demoMode ? 'linear-gradient(135deg, #4267b2 0%, #365899 100%)' : '#4267b2'};
    color: white;

    &:hover:not(:disabled) {
      background: ${props.demoMode ? 'linear-gradient(135deg, #365899 0%, #2d4373 100%)' : '#365899'};
      transform: translateY(-1px);
    }
  ` : `
    background: ${props.demoMode ? 'linear-gradient(135deg, #000 0%, #333 100%)' : '#000'};
    color: white;

    &:hover:not(:disabled) {
      background: ${props.demoMode ? 'linear-gradient(135deg, #333 0%, #555 100%)' : '#333'};
      transform: translateY(-1px);
    }
  `}

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  &:active {
    transform: translateY(0);
  }
`

const PlatformIcon = styled.span<{ platform: 'facebook' | 'tiktok' }>`
  font-size: 1.25rem;

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

const StatusSection = styled.div`
  margin-top: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: left;
`

const DemoModeNotice = styled.div`
  margin-bottom: 2rem;
  padding: 1rem;
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  color: #856404;
  font-size: 0.9rem;
  line-height: 1.5;

  h4 {
    margin: 0 0 0.5rem 0;
    color: #664d03;
    font-size: 1rem;
  }

  p {
    margin: 0.5rem 0;
  }

  ul {
    margin: 0.5rem 0;
    padding-left: 1.2rem;
  }

  li {
    margin: 0.25rem 0;
  }

  .credential-name {
    font-family: 'Courier New', monospace;
    background: rgba(0, 0, 0, 0.1);
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
    font-size: 0.85em;
  }
`

const CredentialStatus = styled.div`
  margin-top: 1rem;
  padding: 1.25rem;
  background: #f8f9fa;
  border-radius: 12px;
  border-left: 4px solid #dc3545;
  text-align: left;

  h4 {
    color: #dc3545;
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0.5rem 0;
    font-size: 0.95rem;
    padding: 0.5rem;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.5);

    &.missing {
      color: #dc3545;

      &::before {
        content: '❌';
        font-size: 1rem;
      }
    }

    &.configured {
      color: #28a745;

      &::before {
        content: '✅';
        font-size: 1rem;
      }
    }
  }

  @media (max-width: 480px) {
    padding: 1rem;

    .status-item {
      font-size: 0.9rem;
      gap: 0.5rem;
    }
  }
`

const StatusTitle = styled.h3`
  color: #333;
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
`

const StatusItem = styled.div<{ connected: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;

  &:before {
    content: "${props => props.connected ? '✅' : '❌'}";
  }

  color: ${props => props.connected ? '#28a745' : '#dc3545'};
`

const OAuthLoginPage: React.FC = () => {
  const [selectedTenantId, setSelectedTenantId] = useState<string>('')

  const { tenants, loading: tenantsLoading, error: tenantsError } = useTenants()
  const { authStatus, loading: authLoading } = useAuth(selectedTenantId || null)
  const { initiating, errors: oauthErrors, clearErrors, initiateFacebookOAuth, initiateTikTokOAuth } = useOAuth()
  const { status: credentialsStatus, loading: credentialsLoading, isConfigured } = useCredentialsStatus()

  // Demo mode is active when credentials are not properly configured
  const demoMode = !isConfigured

  // Generate demo tenant if none exist (for demo purposes)
  const effectiveTenants = tenants.length > 0 ? tenants : [
    { id: 'demo-tenant', name: 'Demo Organization', created_at: new Date().toISOString() }
  ]

  // Auto-select first tenant if available (including demo tenant)
  useEffect(() => {
    if (effectiveTenants.length > 0 && !selectedTenantId) {
      setSelectedTenantId(effectiveTenants[0].id)
    }
  }, [effectiveTenants, selectedTenantId])

  const handleFacebookLogin = async () => {
    if (!selectedTenantId) return

    // Clear any previous errors
    clearErrors()

    // In demo mode, show a placeholder alert instead of real OAuth
    if (demoMode) {
      alert(
        '🔧 Demo Mode: Facebook OAuth\n\n' +
        'This would normally redirect to Facebook for authentication.\n\n' +
        'To enable real OAuth:\n' +
        '1. Configure FACEBOOK_APP_ID in .env\n' +
        '2. Configure FACEBOOK_APP_SECRET in .env\n' +
        '3. Restart the backend server\n\n' +
        'The button will then connect to Facebook\'s real OAuth API.'
      )
      return
    }

    try {
      await initiateFacebookOAuth(selectedTenantId)
    } catch (error) {
      console.error('Facebook OAuth failed:', error)
      // Error is already handled by the useOAuth hook
    }
  }

  const handleTikTokLogin = async () => {
    if (!selectedTenantId) return

    // Clear any previous errors
    clearErrors()

    // In demo mode, show a placeholder alert instead of real OAuth
    if (demoMode) {
      alert(
        '🔧 Demo Mode: TikTok OAuth\n\n' +
        'This would normally redirect to TikTok for authentication.\n\n' +
        'To enable real OAuth:\n' +
        '1. Configure TIKTOK_CLIENT_ID in .env\n' +
        '2. Configure TIKTOK_CLIENT_SECRET in .env\n' +
        '3. Restart the backend server\n\n' +
        'The button will then connect to TikTok\'s real OAuth API.'
      )
      return
    }

    try {
      await initiateTikTokOAuth(selectedTenantId)
    } catch (error) {
      console.error('TikTok OAuth failed:', error)
      // Error is already handled by the useOAuth hook
    }
  }

  const isLoading = tenantsLoading || authLoading || credentialsLoading
  const canInitiateOAuth = selectedTenantId && !isLoading

  return (
    <LoginContainer>
      <Title>Social Media Automation</Title>
      <Subtitle>
        Connect your Facebook and TikTok accounts to start automating your social media campaigns
      </Subtitle>

      {tenantsError && (
        <ErrorMessage message={`Failed to load tenants: ${tenantsError}`} />
      )}

      {demoMode && (
        <DemoModeNotice>
          <h4>🔧 Demo Mode Active</h4>
          <p>OAuth credentials are not configured yet. The login buttons will show demo functionality.</p>
          <p>To enable real OAuth integration, configure these environment variables:</p>
          <ul>
            <li><span className="credential-name">FACEBOOK_APP_ID</span> - Your Facebook App ID</li>
            <li><span className="credential-name">FACEBOOK_APP_SECRET</span> - Your Facebook App Secret</li>
            <li><span className="credential-name">TIKTOK_CLIENT_ID</span> - Your TikTok Client ID</li>
            <li><span className="credential-name">TIKTOK_CLIENT_SECRET</span> - Your TikTok Client Secret</li>
          </ul>
          <p>Once configured, restart the backend server and refresh this page.</p>
        </DemoModeNotice>
      )}

      <TenantSelector>
        <Label htmlFor="tenant-select">Select Organization:</Label>
        <Select
          id="tenant-select"
          value={selectedTenantId}
          onChange={(e) => setSelectedTenantId(e.target.value)}
          disabled={tenantsLoading || effectiveTenants.length === 0}
        >
          <option value="" disabled>
            {tenantsLoading ? 'Loading organizations...' : 'Select an organization'}
          </option>
          {effectiveTenants.map((tenant) => (
            <option key={tenant.id} value={tenant.id}>
              {tenant.name} {tenant.id === 'demo-tenant' ? '(Demo)' : ''}
            </option>
          ))}
        </Select>
      </TenantSelector>

      <OAuthButtonsContainer>
        <OAuthButton
          platform="facebook"
          demoMode={demoMode}
          onClick={handleFacebookLogin}
          disabled={!canInitiateOAuth || initiating.facebook}
          title={demoMode ? 'Click to see demo functionality' : 'Connect your Facebook account'}
        >
          <PlatformIcon platform="facebook" />
          {initiating.facebook ? (
            <>
              <LoadingSpinner size="small" />
              Connecting to Facebook...
            </>
          ) : (
            `${demoMode ? 'Try ' : ''}Connect Facebook${demoMode ? ' (Demo)' : ''}`
          )}
        </OAuthButton>

        <OAuthButton
          platform="tiktok"
          demoMode={demoMode}
          onClick={handleTikTokLogin}
          disabled={!canInitiateOAuth || initiating.tiktok}
          title={demoMode ? 'Click to see demo functionality' : 'Connect your TikTok account'}
        >
          <PlatformIcon platform="tiktok" />
          {initiating.tiktok ? (
            <>
              <LoadingSpinner size="small" />
              Connecting to TikTok...
            </>
          ) : (
            `${demoMode ? 'Try ' : ''}Connect TikTok${demoMode ? ' (Demo)' : ''}`
          )}
        </OAuthButton>
      </OAuthButtonsContainer>

      {/* OAuth Error Messages */}
      {oauthErrors.facebook && (
        <ErrorMessage message={`Facebook OAuth Error: ${oauthErrors.facebook}`} />
      )}
      {oauthErrors.tiktok && (
        <ErrorMessage message={`TikTok OAuth Error: ${oauthErrors.tiktok}`} />
      )}

      {demoMode && credentialsStatus && (
        <CredentialStatus>
          <h4>OAuth Credentials Status</h4>
          <div className={`status-item ${credentialsStatus.facebook.appId ? 'configured' : 'missing'}`}>
            Facebook App ID: {credentialsStatus.facebook.appId ? 'Configured' : 'Not configured'}
          </div>
          <div className={`status-item ${credentialsStatus.facebook.appSecret ? 'configured' : 'missing'}`}>
            Facebook App Secret: {credentialsStatus.facebook.appSecret ? 'Configured' : 'Not configured'}
          </div>
          <div className={`status-item ${credentialsStatus.tiktok.clientId ? 'configured' : 'missing'}`}>
            TikTok Client ID: {credentialsStatus.tiktok.clientId ? 'Configured' : 'Not configured'}
          </div>
          <div className={`status-item ${credentialsStatus.tiktok.clientSecret ? 'configured' : 'missing'}`}>
            TikTok Client Secret: {credentialsStatus.tiktok.clientSecret ? 'Configured' : 'Not configured'}
          </div>
        </CredentialStatus>
      )}

      {!demoMode && selectedTenantId && authStatus && (
        <StatusSection>
          <StatusTitle>Connection Status</StatusTitle>
          <StatusItem connected={authStatus.facebook?.connected || false}>
            Facebook: {authStatus.facebook?.connected ?
              `Connected (${authStatus.facebook.valid_tokens} valid tokens)` :
              'Not connected'
            }
          </StatusItem>
          <StatusItem connected={authStatus.tiktok?.connected || false}>
            TikTok: {authStatus.tiktok?.connected ?
              `Connected (${authStatus.tiktok.valid_tokens} valid tokens)` :
              'Not connected'
            }
          </StatusItem>
        </StatusSection>
      )}

      {isLoading && (
        <div style={{ marginTop: '1rem' }}>
          <LoadingSpinner />
        </div>
      )}
    </LoginContainer>
  )
}

export default OAuthLoginPage