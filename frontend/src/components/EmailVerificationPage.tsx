import React, { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { authService } from '../services/api'

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  padding: 1rem;
`

const Card = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2.5rem;
  max-width: 420px;
  width: 100%;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
`

const IconWrapper = styled.div<{ $status: 'verifying' | 'success' | 'error' }>`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  background: ${props => {
    switch (props.$status) {
      case 'success': return 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
      case 'error': return 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
      default: return 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)'
    }
  }};
`

const Icon = styled.span`
  font-size: 2rem;
`

const Title = styled.h1`
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.75rem;
`

const Message = styled.p`
  font-size: 1rem;
  color: #6b7280;
  margin-bottom: 2rem;
  line-height: 1.6;
`

const Button = styled.button`
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 0.875rem 2rem;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
  }

  &:active {
    transform: translateY(0);
  }
`

const Spinner = styled.div`
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`

const EmailVerificationPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) {
      setStatus('error')
      setMessage('Invalid verification link. The link may be incomplete or corrupted.')
      return
    }

    const verifyEmail = async () => {
      try {
        const response = await authService.verifyEmail(token)
        setStatus('success')
        setMessage(response.message || 'Your email has been verified successfully!')
      } catch (error: any) {
        setStatus('error')
        setMessage(error.message || 'Email verification failed. The link may have expired.')
      }
    }

    verifyEmail()
  }, [searchParams])

  const handleNavigate = () => {
    if (authService.isAuthenticated()) {
      navigate('/dashboard/settings')
    } else {
      navigate('/login')
    }
  }

  return (
    <Container>
      <Card>
        <IconWrapper $status={status}>
          {status === 'verifying' && <Spinner />}
          {status === 'success' && <Icon>✓</Icon>}
          {status === 'error' && <Icon>✕</Icon>}
        </IconWrapper>

        <Title>
          {status === 'verifying' && 'Verifying Email...'}
          {status === 'success' && 'Email Verified!'}
          {status === 'error' && 'Verification Failed'}
        </Title>

        <Message>
          {status === 'verifying' && 'Please wait while we verify your email address.'}
          {status === 'success' && message}
          {status === 'error' && message}
        </Message>

        {status !== 'verifying' && (
          <Button onClick={handleNavigate}>
            {authService.isAuthenticated() ? 'Go to Settings' : 'Go to Login'}
          </Button>
        )}
      </Card>
    </Container>
  )
}

export default EmailVerificationPage
