import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { authService } from '../services/api'

// Styled components matching LoginPageNew design
const PageContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  padding: 2rem;
  position: relative;
  overflow: hidden;
`

const DecorativeShape1 = styled.div`
  position: absolute;
  top: -50px;
  left: -100px;
  width: 340px;
  height: 245px;
  background: #4a90e2;
  border-radius: 26px;
  transform: rotate(15deg);
  opacity: 0.8;
  box-shadow: 4px -2px 4px rgba(0, 0, 0, 0.13);
`

const DecorativeShape2 = styled.div`
  position: absolute;
  top: -20px;
  left: -150px;
  width: 320px;
  height: 239px;
  background: #2a5298;
  border-radius: 26px;
  transform: rotate(15deg);
  opacity: 0.9;
  box-shadow: 4px -2px 4px rgba(0, 0, 0, 0.13);
`

const Card = styled.div`
  background: white;
  border-radius: 0;
  padding: 2rem 2.5rem 3rem;
  width: 100%;
  max-width: 428px;
  position: relative;
  z-index: 1;

  @media (max-width: 480px) {
    padding: 2rem 1.5rem;
  }
`

const Logo = styled.h1`
  font-family: 'Prime', 'Roboto', sans-serif;
  font-size: 80px;
  font-weight: 400;
  background: linear-gradient(180deg, #4a90e2 0%, #2a5298 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 2rem 0;
  text-align: center;
  line-height: 61px;
`

const Title = styled.h2`
  font-family: 'Roboto', sans-serif;
  font-weight: 700;
  font-size: 24px;
  color: #000000;
  margin: 0 0 0.5rem 0;
  text-align: center;
  line-height: 28px;
`

const Subtitle = styled.p`
  font-family: 'Roboto', sans-serif;
  font-weight: 400;
  font-size: 14px;
  color: #515151;
  margin: 0 0 2rem 0;
  text-align: center;
  line-height: 20px;
`

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`

const InputWithIcon = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`

const InputIcon = styled.div`
  position: absolute;
  left: 20px;
  color: #515151;
  font-size: 14px;
  pointer-events: none;
  display: flex;
  align-items: center;
  height: 100%;

  svg {
    width: 16px;
    height: 16px;
    stroke: #515151;
    fill: none;
    stroke-width: 1.3px;
  }
`

const Input = styled.input`
  width: 100%;
  height: 61px;
  padding: 0 1rem 0 3rem;
  background: #F3F3F3;
  border: none;
  border-radius: 5px;
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  color: #515151;
  box-sizing: border-box;

  &::placeholder {
    color: #515151;
  }

  &:focus {
    outline: none;
    background: #EBEBEB;
  }
`

const SubmitButton = styled.button`
  width: 199px;
  height: 53px;
  margin: 1.5rem auto 0;
  border: none;
  border-radius: 5px;
  font-family: 'Roboto', sans-serif;
  font-weight: 700;
  font-size: 16px;
  color: #FFFFFF;
  background: linear-gradient(180deg, #4a90e2 0%, #2a5298 100%);
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0px 5px 7px rgba(0, 0, 0, 0.19);
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0px 7px 10px rgba(0, 0, 0, 0.25);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const BackToLogin = styled.div`
  text-align: center;
  margin-top: 2rem;

  a {
    font-family: 'Roboto', sans-serif;
    font-size: 14px;
    color: #4a90e2;
    text-decoration: none;
    font-weight: 500;

    &:hover {
      text-decoration: underline;
    }
  }
`

const ErrorMessage = styled.div`
  background: #fee2e2;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 5px;
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  text-align: center;
`

const SuccessMessage = styled.div`
  background: #d1fae5;
  color: #059669;
  padding: 1rem;
  border-radius: 5px;
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  text-align: center;
  line-height: 1.5;
`

const SuccessIcon = styled.div`
  font-size: 48px;
  margin-bottom: 1rem;
  text-align: center;
`

const Divider = styled.div`
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
  color: #9ca3af;
  font-family: 'Roboto', sans-serif;
  font-size: 12px;

  &::before,
  &::after {
    content: '';
    flex: 1;
    border-bottom: 1px solid #e5e7eb;
  }

  span {
    padding: 0 1rem;
  }
`

const TokenInputSection = styled.form`
  margin-top: 1rem;
`

const TokenLabel = styled.label`
  display: block;
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  color: #374151;
  margin-bottom: 0.5rem;
  text-align: center;
`

const TokenInput = styled.input`
  width: 100%;
  height: 50px;
  padding: 0 1rem;
  background: #F3F3F3;
  border: none;
  border-radius: 5px;
  font-family: 'Roboto Mono', monospace;
  font-size: 13px;
  color: #515151;
  text-align: center;
  letter-spacing: 0.5px;
  box-sizing: border-box;

  &::placeholder {
    color: #9ca3af;
    font-family: 'Roboto', sans-serif;
  }

  &:focus {
    outline: none;
    background: #EBEBEB;
  }
`

const TokenSubmitButton = styled.button`
  width: 100%;
  height: 45px;
  margin-top: 0.75rem;
  border: none;
  border-radius: 5px;
  font-family: 'Roboto', sans-serif;
  font-weight: 600;
  font-size: 14px;
  color: #FFFFFF;
  background: linear-gradient(180deg, #4a90e2 0%, #2a5298 100%);
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0px 3px 5px rgba(0, 0, 0, 0.15);

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0px 5px 8px rgba(0, 0, 0, 0.2);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [manualToken, setManualToken] = useState('')
  const [tokenError, setTokenError] = useState('')

  const handleTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setTokenError('')

    if (!manualToken.trim()) {
      setTokenError('Please enter the verification code')
      return
    }

    if (manualToken.trim().length < 32) {
      setTokenError('Invalid verification code format')
      return
    }

    // Navigate to reset password page with the token
    navigate(`/reset-password?token=${encodeURIComponent(manualToken.trim())}`)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      await authService.forgotPassword(email)
      setIsSubmitted(true)
    } catch (err: any) {
      setError(err.message || 'Failed to send reset email')
    } finally {
      setIsLoading(false)
    }
  }

  if (isSubmitted) {
    return (
      <PageContainer>
        <DecorativeShape1 />
        <DecorativeShape2 />
        <Card>
          <Logo>KS</Logo>
          <SuccessIcon>📧</SuccessIcon>
          <Title>Check Your Email</Title>
          <SuccessMessage>
            If an account exists with <strong>{email}</strong>, you will receive a password reset link shortly.
            <br /><br />
            The link will expire in 1 hour for security reasons.
          </SuccessMessage>

          <Divider><span>OR</span></Divider>

          <TokenInputSection onSubmit={handleTokenSubmit}>
            <TokenLabel>Enter the verification code from your email:</TokenLabel>
            <TokenInput
              type="text"
              placeholder="Paste your verification code here"
              value={manualToken}
              onChange={(e) => setManualToken(e.target.value)}
            />
            {tokenError && <ErrorMessage style={{ marginTop: '0.5rem' }}>{tokenError}</ErrorMessage>}
            <TokenSubmitButton type="submit" disabled={!manualToken.trim()}>
              Reset Password
            </TokenSubmitButton>
          </TokenInputSection>

          <BackToLogin>
            <Link to="/login">Back to Login</Link>
          </BackToLogin>
        </Card>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <DecorativeShape1 />
      <DecorativeShape2 />
      <Card>
        <Logo>KS</Logo>
        <Title>Forgot Password?</Title>
        <Subtitle>
          Enter your email address and we'll send you a link to reset your password.
        </Subtitle>

        {error && <ErrorMessage>{error}</ErrorMessage>}

        <Form onSubmit={handleSubmit}>
          <InputWithIcon>
            <InputIcon>
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                <polyline points="22,6 12,13 2,6" />
              </svg>
            </InputIcon>
            <Input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </InputWithIcon>

          <SubmitButton type="submit" disabled={isLoading || !email}>
            {isLoading ? 'Sending...' : 'Send Reset Link'}
          </SubmitButton>
        </Form>

        <BackToLogin>
          <Link to="/login">Back to Login</Link>
        </BackToLogin>
      </Card>
    </PageContainer>
  )
}

export default ForgotPasswordPage
