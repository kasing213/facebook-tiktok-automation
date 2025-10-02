import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import styled from 'styled-components'
import { authService } from '../services/api'
import { LoadingSpinner } from './LoadingSpinner'
import { ErrorMessage } from './ErrorMessage'
import { OAuthResult } from '../types/auth'

const CallbackContainer = styled.div`
  max-width: 500px;
  width: 100%;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  text-align: center;

  @media (max-width: 768px) {
    margin: 1rem;
    padding: 1.5rem;
  }
`

const Title = styled.h1`
  color: #333;
  margin-bottom: 1rem;
  font-size: 1.5rem;
  font-weight: 600;
`

const StatusMessage = styled.p<{ type: 'loading' | 'success' | 'error' }>`
  margin-bottom: 1.5rem;
  font-size: 1rem;
  line-height: 1.5;

  ${props => {
    switch (props.type) {
      case 'success':
        return 'color: #28a745;'
      case 'error':
        return 'color: #dc3545;'
      default:
        return 'color: #666;'
    }
  }}
`

const SuccessIcon = styled.div`
  font-size: 3rem;
  margin-bottom: 1rem;

  &:before {
    content: "✅";
  }
`

const RetryButton = styled.button`
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;
  margin-right: 1rem;

  &:hover {
    background: #0056b3;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const HomeButton = styled.button`
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;

  &:hover {
    background: #545b62;
  }
`

const ResultDetails = styled.div`
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  text-align: left;
  font-size: 0.9rem;

  h4 {
    margin: 0 0 0.5rem 0;
    color: #333;
  }

  p {
    margin: 0.25rem 0;
    color: #666;
  }
`

type CallbackState = 'loading' | 'success' | 'error'

const OAuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [state, setState] = useState<CallbackState>('loading')
  const [result, setResult] = useState<OAuthResult | null>(null)
  const [error, setError] = useState<string>('')
  const [processing, setProcessing] = useState(false)

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code')
      const stateParam = searchParams.get('state')
      const errorParam = searchParams.get('error')
      const errorDescription = searchParams.get('error_description')

      // Check for OAuth errors
      if (errorParam) {
        const errorMsg = errorDescription || errorParam
        setError(`OAuth authentication failed: ${errorMsg}`)
        setState('error')
        return
      }

      // Check for required parameters
      if (!code || !stateParam) {
        setError('Missing required OAuth parameters (code or state)')
        setState('error')
        return
      }

      // Determine platform from current URL or state
      const currentPath = window.location.pathname
      const platform = currentPath.includes('facebook') ? 'facebook' : 'tiktok'

      try {
        setProcessing(true)
        const oauthResult = await authService.handleOAuthCallback(platform, code, stateParam)
        setResult(oauthResult)
        setState('success')

        // Auto-redirect to dashboard after 3 seconds
        setTimeout(() => {
          navigate('/dashboard', {
            state: {
              message: `${platform} account connected successfully!`,
              tenantId: oauthResult.tenant_id
            }
          })
        }, 3000)

      } catch (err) {
        console.error('OAuth callback processing failed:', err)
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
        setError(`Failed to process OAuth callback: ${errorMessage}`)
        setState('error')
      } finally {
        setProcessing(false)
      }
    }

    handleCallback()
  }, [searchParams, navigate])

  const handleRetry = () => {
    setState('loading')
    setError('')
    setResult(null)
    window.location.reload()
  }

  const handleGoHome = () => {
    navigate('/')
  }

  const renderContent = () => {
    switch (state) {
      case 'loading':
        return (
          <>
            <LoadingSpinner size="large" />
            <Title>Processing OAuth Callback</Title>
            <StatusMessage type="loading">
              {processing ? 'Exchanging authorization code for access token...' : 'Initializing OAuth callback...'}
            </StatusMessage>
          </>
        )

      case 'success':
        return (
          <>
            <SuccessIcon />
            <Title>Authentication Successful!</Title>
            <StatusMessage type="success">
              Your {result?.platform} account has been connected successfully.
            </StatusMessage>

            {result && (
              <ResultDetails>
                <h4>Connection Details:</h4>
                <p><strong>Platform:</strong> {result.platform}</p>
                <p><strong>Tenant ID:</strong> {result.tenant_id}</p>
                <p><strong>Token ID:</strong> {result.token_id}</p>
                {result.expires_at && (
                  <p><strong>Expires:</strong> {new Date(result.expires_at).toLocaleString()}</p>
                )}
              </ResultDetails>
            )}

            <StatusMessage type="loading">
              Redirecting to dashboard in a few seconds...
            </StatusMessage>

            <HomeButton onClick={handleGoHome}>
              Go to Dashboard Now
            </HomeButton>
          </>
        )

      case 'error':
        return (
          <>
            <Title>Authentication Failed</Title>
            <ErrorMessage message={error} />
            <div>
              <RetryButton onClick={handleRetry} disabled={processing}>
                {processing ? 'Processing...' : 'Try Again'}
              </RetryButton>
              <HomeButton onClick={handleGoHome}>
                Back to Login
              </HomeButton>
            </div>
          </>
        )
    }
  }

  return (
    <CallbackContainer>
      {renderContent()}
    </CallbackContainer>
  )
}

export default OAuthCallback