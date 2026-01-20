import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { authService } from '../services/api'

const BannerContainer = styled.div<{ $visible: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  padding: 1rem;
  z-index: 1000;
  transform: translateY(${props => props.$visible ? '0' : '-100%'});
  transition: transform 0.3s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`

const BannerContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: between;
  gap: 1rem;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    flex-direction: column;
    text-align: center;
  }
`

const MessageSection = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
`

const Icon = styled.span`
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.9;

  svg {
    width: 24px;
    height: 24px;
  }
`

const TextContent = styled.div`
  flex: 1;
`

const Title = styled.h3`
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  opacity: 1;
`

const Description = styled.p`
  margin: 0;
  font-size: 0.875rem;
  opacity: 0.9;
  line-height: 1.4;
`

const Actions = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    justify-content: center;
  }
`

const Button = styled.button<{ $variant?: 'primary' | 'secondary' }>`
  background: ${props =>
    props.$variant === 'secondary'
      ? 'rgba(255, 255, 255, 0.2)'
      : 'rgba(255, 255, 255, 1)'
  };
  color: ${props =>
    props.$variant === 'secondary'
      ? 'white'
      : '#d97706'
  };
  border: ${props =>
    props.$variant === 'secondary'
      ? '1px solid rgba(255, 255, 255, 0.4)'
      : 'none'
  };
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: ${props =>
      props.$variant === 'secondary'
        ? 'rgba(255, 255, 255, 0.3)'
        : 'rgba(255, 255, 255, 0.9)'
    };
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`

const CloseButton = styled.button`
  background: none;
  border: none;
  color: white;
  font-size: 1.25rem;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
  padding: 0.25rem;
  border-radius: 4px;

  &:hover {
    opacity: 1;
    background: rgba(255, 255, 255, 0.1);
  }
`

const LoadingSpinner = styled.div`
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`

interface EmailVerificationBannerProps {
  onVerificationChange?: (verified: boolean) => void
}

const EmailVerificationBanner: React.FC<EmailVerificationBannerProps> = ({
  onVerificationChange
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [isVerified, setIsVerified] = useState(false)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)

  useEffect(() => {
    checkVerificationStatus()
  }, [])

  const checkVerificationStatus = async () => {
    try {
      if (!authService.isAuthenticated()) return

      const status = await authService.getVerificationStatus()
      setIsVerified(status.is_verified)
      setUserEmail(status.email)

      // Show banner if not verified and not dismissed
      setIsVisible(!status.is_verified && !isDismissed)

      onVerificationChange?.(status.is_verified)
    } catch (error) {
      console.error('Failed to check verification status:', error)
    }
  }

  const handleRequestVerification = async () => {
    setIsLoading(true)
    try {
      const result = await authService.requestVerification()

      if (result.success) {
        // Show success state temporarily
        setTimeout(() => {
          setIsLoading(false)
        }, 2000)
      } else {
        setIsLoading(false)
      }
    } catch (error) {
      console.error('Failed to request verification:', error)
      setIsLoading(false)
    }
  }

  const handleDismiss = () => {
    setIsVisible(false)
    setIsDismissed(true)
    // Store dismissal in localStorage to persist across page loads
    localStorage.setItem('email_verification_dismissed', 'true')
  }

  // Check if user has previously dismissed the banner
  useEffect(() => {
    const dismissed = localStorage.getItem('email_verification_dismissed')
    setIsDismissed(dismissed === 'true')
  }, [])

  // Don't render if verified or dismissed
  if (isVerified || isDismissed) {
    return null
  }

  return (
    <BannerContainer $visible={isVisible}>
      <BannerContent>
        <MessageSection>
          <Icon>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </Icon>
          <TextContent>
            <Title>Email Verification Required</Title>
            <Description>
              Please verify your email address ({userEmail}) to access all features.
              Check your inbox for our verification email.
            </Description>
          </TextContent>
        </MessageSection>

        <Actions>
          <Button
            onClick={handleRequestVerification}
            disabled={isLoading}
            $variant="primary"
          >
            {isLoading && <LoadingSpinner />}
            {isLoading ? 'Sending...' : 'Resend Email'}
          </Button>

          <Button
            onClick={handleDismiss}
            $variant="secondary"
          >
            Dismiss
          </Button>

          <CloseButton onClick={handleDismiss}>
            ×
          </CloseButton>
        </Actions>
      </BannerContent>
    </BannerContainer>
  )
}

export default EmailVerificationBanner