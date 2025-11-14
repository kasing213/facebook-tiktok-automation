import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { useTenants, useAuth, useOAuth } from '../hooks/useAuth'
import { LoadingSpinner } from './LoadingSpinner'
import { ErrorMessage } from './ErrorMessage'

// OAuth login page for Facebook and TikTok integration
// Connects to FastAPI backend OAuth endpoints

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

const OAuthButton = styled.button<{ platform: 'facebook' | 'tiktok' }>`
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

  ${props => props.platform === 'facebook' ? `
    background: #4267b2;
    color: white;

    &:hover:not(:disabled) {
      background: #365899;
      transform: translateY(-1px);
    }
  ` : `
    background: #000;
    color: white;

    &:hover:not(:disabled) {
      background: #333;
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
  const { initiating, errors: oauthErrors, clearErrors, initiateFacebookOAuth, initiateTikTokOAuth} = useOAuth()

  // Auto-select first tenant if available
  useEffect(() => {
    if (tenants.length > 0 && !selectedTenantId) {
      setSelectedTenantId(tenants[0].id)
    }
  }, [tenants, selectedTenantId])

  const handleFacebookLogin = async () => {
    if (!selectedTenantId) return

    // Clear any previous errors
    clearErrors()

    try {
      await initiateFacebookOAuth(selectedTenantId)
      // If we reach here without redirect, something went wrong
      console.warn('Facebook OAuth initiation completed but no redirect occurred')
    } catch (error) {
      console.error('Facebook OAuth failed:', error)
      // Error is already handled by the useOAuth hook
    }
  }

  const handleTikTokLogin = async () => {
    if (!selectedTenantId) return

    // Clear any previous errors
    clearErrors()

    try {
      await initiateTikTokOAuth(selectedTenantId)
      // If we reach here without redirect, something went wrong
      console.warn('TikTok OAuth initiation completed but no redirect occurred')
    } catch (error) {
      console.error('TikTok OAuth failed:', error)
      // Error is already handled by the useOAuth hook
    }
  }

  const isLoading = tenantsLoading || authLoading
  const canInitiateOAuth = selectedTenantId && !isLoading

  return (
    <LoginContainer>
      <Title>Social Media Automation</Title>
      <Subtitle>
        Connect your Facebook and TikTok accounts to start automating your social media campaigns
      </Subtitle>

      {tenantsError && (
        <ErrorMessage message={tenantsError} />
      )}


      <TenantSelector>
        <Label htmlFor="tenant-select">Select Organization:</Label>
        <Select
          id="tenant-select"
          value={selectedTenantId}
          onChange={(e) => setSelectedTenantId(e.target.value)}
          disabled={tenantsLoading || tenants.length === 0}
        >
          <option value="" disabled>
            {tenantsLoading ? 'Loading organizations...' : 'Select an organization'}
          </option>
          {tenants.map((tenant) => (
            <option key={tenant.id} value={tenant.id}>
              {tenant.name}
            </option>
          ))}
        </Select>
      </TenantSelector>

      <OAuthButtonsContainer>
        <OAuthButton
          platform="facebook"
          onClick={handleFacebookLogin}
          disabled={!canInitiateOAuth || initiating.facebook}
          title="Connect your Facebook account"
        >
          <PlatformIcon platform="facebook" />
          {initiating.facebook ? (
            <>
              <LoadingSpinner size="small" />
              Connecting to Facebook...
            </>
          ) : (
            'Connect Facebook'
          )}
        </OAuthButton>

        <OAuthButton
          platform="tiktok"
          onClick={handleTikTokLogin}
          disabled={!canInitiateOAuth || initiating.tiktok}
          title="Connect your TikTok account"
        >
          <PlatformIcon platform="tiktok" />
          {initiating.tiktok ? (
            <>
              <LoadingSpinner size="small" />
              Connecting to TikTok...
            </>
          ) : (
            'Connect TikTok'
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


      {selectedTenantId && authStatus && (
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
