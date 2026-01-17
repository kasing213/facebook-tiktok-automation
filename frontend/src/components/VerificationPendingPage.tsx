import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { authService } from '../services/api'

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  padding: 1rem;
`

const Card = styled.div`
  background: white;
  border-radius: 16px;
  padding: 3rem;
  max-width: 500px;
  width: 100%;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
`

const IconWrapper = styled.div`
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 2rem;
  position: relative;
`

const Icon = styled.span`
  font-size: 3rem;
  color: white;
`

const PulsingDot = styled.div`
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse 2s infinite;

  @keyframes pulse {
    0% {
      transform: scale(0.8);
      opacity: 1;
    }
    50% {
      transform: scale(1.2);
      opacity: 0.7;
    }
    100% {
      transform: scale(0.8);
      opacity: 1;
    }
  }
`

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 1rem;
`

const Subtitle = styled.p`
  font-size: 1.125rem;
  color: #6b7280;
  margin-bottom: 2rem;
  line-height: 1.6;
`

const EmailDisplay = styled.div`
  background: #f3f4f6;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 2rem;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 0.875rem;
  color: #374151;
`

const Actions = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
`

const Button = styled.button<{ $variant?: 'primary' | 'secondary' }>`
  background: ${props =>
    props.$variant === 'secondary'
      ? 'transparent'
      : 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
  };
  color: ${props =>
    props.$variant === 'secondary'
      ? '#6b7280'
      : 'white'
  };
  border: ${props =>
    props.$variant === 'secondary'
      ? '2px solid #e5e7eb'
      : 'none'
  };
  padding: 0.875rem 2rem;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;

  &:hover {
    transform: translateY(-2px);
    box-shadow: ${props =>
      props.$variant === 'secondary'
        ? '0 4px 12px rgba(0, 0, 0, 0.1)'
        : '0 4px 12px rgba(245, 158, 11, 0.4)'
    };
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`

const LoadingSpinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`

const Instructions = styled.div`
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: left;
`

const InstructionTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`

const InstructionList = styled.ol`
  margin: 0;
  padding-left: 1.25rem;
  color: #0c4a6e;
  line-height: 1.5;

  li {
    margin-bottom: 0.5rem;

    &:last-child {
      margin-bottom: 0;
    }
  }
`

const Footer = styled.div`
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
  font-size: 0.875rem;
  color: #6b7280;
`

interface VerificationPendingPageProps {
  userEmail?: string
}

const VerificationPendingPage: React.FC<VerificationPendingPageProps> = ({
  userEmail: propEmail
}) => {
  const navigate = useNavigate()
  const [userEmail, setUserEmail] = useState(propEmail || '')
  const [isLoading, setIsLoading] = useState(false)
  const [lastResendTime, setLastResendTime] = useState<Date | null>(null)
  const [cooldownSeconds, setCooldownSeconds] = useState(0)

  useEffect(() => {
    // Get user's email if not provided
    if (!userEmail) {
      getUserEmail()
    }
  }, [userEmail])

  useEffect(() => {
    // Cooldown timer
    let interval: number | null = null
    if (cooldownSeconds > 0) {
      interval = setInterval(() => {
        setCooldownSeconds(prev => prev - 1)
      }, 1000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [cooldownSeconds])

  const getUserEmail = async () => {
    try {
      const status = await authService.getVerificationStatus()
      setUserEmail(status.email || 'your email')

      // If already verified, redirect to dashboard
      if (status.is_verified) {
        navigate('/dashboard')
      }
    } catch (error) {
      console.error('Failed to get user email:', error)
    }
  }

  const handleResendEmail = async () => {
    setIsLoading(true)
    try {
      const result = await authService.requestVerification()

      if (result.success) {
        setLastResendTime(new Date())
        setCooldownSeconds(60) // 1 minute cooldown
      }
    } catch (error) {
      console.error('Failed to resend verification email:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoToLogin = () => {
    navigate('/login')
  }

  const canResend = cooldownSeconds === 0

  return (
    <Container>
      <Card>
        <IconWrapper>
          <Icon>📧</Icon>
          <PulsingDot />
        </IconWrapper>

        <Title>Check Your Email</Title>
        <Subtitle>
          We've sent a verification link to your email address. Please click the link to activate your account.
        </Subtitle>

        <EmailDisplay>
          {userEmail}
        </EmailDisplay>

        <Actions>
          <Button
            onClick={handleResendEmail}
            disabled={!canResend || isLoading}
          >
            {isLoading && <LoadingSpinner />}
            {isLoading
              ? 'Sending...'
              : canResend
                ? 'Resend Verification Email'
                : `Resend in ${cooldownSeconds}s`
            }
          </Button>

          <Button
            $variant="secondary"
            onClick={handleGoToLogin}
          >
            Back to Login
          </Button>
        </Actions>

        <Instructions>
          <InstructionTitle>
            <span>💡</span>
            Next Steps:
          </InstructionTitle>
          <InstructionList>
            <li>Check your inbox (and spam folder)</li>
            <li>Look for an email from "KS Automation"</li>
            <li>Click the "Verify Email Address" button</li>
            <li>Return to this page to access your dashboard</li>
          </InstructionList>
        </Instructions>

        <Footer>
          {lastResendTime && (
            <p>
              ✅ Verification email sent at {lastResendTime.toLocaleTimeString()}
            </p>
          )}
          <p>
            Didn't receive the email? Check your spam folder or contact support.
          </p>
        </Footer>
      </Card>
    </Container>
  )
}

export default VerificationPendingPage