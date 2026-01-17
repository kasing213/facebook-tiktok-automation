import React, { useState, useEffect } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
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

const PasswordRequirements = styled.ul`
  font-family: 'Roboto', sans-serif;
  font-size: 12px;
  color: #6b7280;
  margin: 0.5rem 0 0 0;
  padding-left: 1.5rem;
  line-height: 1.6;

  li {
    margin-bottom: 0.25rem;
  }
`

const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isSuccess, setIsSuccess] = useState(false)

  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      setError('Invalid reset link. Please request a new password reset.')
    }
  }, [token])

  const validatePassword = () => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters long'
    }
    if (password !== confirmPassword) {
      return 'Passwords do not match'
    }
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const validationError = validatePassword()
    if (validationError) {
      setError(validationError)
      return
    }

    if (!token) {
      setError('Invalid reset link')
      return
    }

    setIsLoading(true)

    try {
      await authService.resetPassword(token, password)
      setIsSuccess(true)
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login')
      }, 3000)
    } catch (err: any) {
      setError(err.message || 'Failed to reset password')
    } finally {
      setIsLoading(false)
    }
  }

  if (isSuccess) {
    return (
      <PageContainer>
        <DecorativeShape1 />
        <DecorativeShape2 />
        <Card>
          <Logo>KS</Logo>
          <SuccessIcon>✓</SuccessIcon>
          <Title>Password Reset!</Title>
          <SuccessMessage>
            Your password has been successfully reset.
            <br /><br />
            Redirecting you to login...
          </SuccessMessage>
          <BackToLogin>
            <Link to="/login">Go to Login</Link>
          </BackToLogin>
        </Card>
      </PageContainer>
    )
  }

  if (!token) {
    return (
      <PageContainer>
        <DecorativeShape1 />
        <DecorativeShape2 />
        <Card>
          <Logo>KS</Logo>
          <SuccessIcon>⚠️</SuccessIcon>
          <Title>Invalid Reset Link</Title>
          <ErrorMessage>
            This password reset link is invalid or has expired.
            Please request a new password reset.
          </ErrorMessage>
          <BackToLogin>
            <Link to="/forgot-password">Request New Reset Link</Link>
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
        <Title>Reset Password</Title>
        <Subtitle>
          Enter your new password below.
        </Subtitle>

        {error && <ErrorMessage>{error}</ErrorMessage>}

        <Form onSubmit={handleSubmit}>
          <InputWithIcon>
            <InputIcon>
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </InputIcon>
            <Input
              type="password"
              placeholder="New password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </InputWithIcon>

          <InputWithIcon>
            <InputIcon>
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </InputIcon>
            <Input
              type="password"
              placeholder="Confirm new password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
            />
          </InputWithIcon>

          <PasswordRequirements>
            <li>At least 8 characters long</li>
            <li>Both passwords must match</li>
          </PasswordRequirements>

          <SubmitButton type="submit" disabled={isLoading || !password || !confirmPassword}>
            {isLoading ? 'Resetting...' : 'Reset Password'}
          </SubmitButton>
        </Form>

        <BackToLogin>
          <Link to="/login">Back to Login</Link>
        </BackToLogin>
      </Card>
    </PageContainer>
  )
}

export default ResetPasswordPage
