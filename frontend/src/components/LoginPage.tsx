import React, { useState } from 'react'
import styled from 'styled-components'
import { LoadingSpinner } from './LoadingSpinner'
import { ErrorMessage } from './ErrorMessage'
import SocialIcon from './SocialIcon'

// Modern login page with gradient background inspired by ColorLib design
// Supports username/password authentication and social OAuth

const PageContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  padding: 2rem;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
    animation: gradientShift 15s ease infinite;
  }

  @keyframes gradientShift {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }
`

const LoginCard = styled.div`
  background: white;
  border-radius: 20px;
  padding: 3rem 2.5rem;
  width: 100%;
  max-width: 450px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
  animation: slideUp 0.5s ease-out;

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @media (max-width: 768px) {
    padding: 2.5rem 2rem;
    border-radius: 16px;
  }

  @media (max-width: 480px) {
    padding: 2rem 1.5rem;
    border-radius: 12px;
  }
`

const Title = styled.h1`
  color: #333;
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: 700;
  text-align: center;
  letter-spacing: -0.5px;
`

const Subtitle = styled.p`
  color: #666;
  margin: 0 0 2rem 0;
  font-size: 0.95rem;
  text-align: center;
  line-height: 1.5;
`

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
`

const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`

const Label = styled.label`
  color: #555;
  font-size: 0.9rem;
  font-weight: 500;
  margin-left: 0.25rem;
`

const InputWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`

const InputIcon = styled.span`
  position: absolute;
  left: 1rem;
  color: #9ca3af;
  pointer-events: none;
  display: flex;
  align-items: center;

  svg {
    width: 18px;
    height: 18px;
  }
`

const Input = styled.input`
  width: 100%;
  padding: 0.875rem 1rem 0.875rem 2.75rem;
  border: 2px solid #e1e5e9;
  border-radius: 10px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: white;

  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  &::placeholder {
    color: #aaa;
  }

  &:disabled {
    background: #f8f9fa;
    cursor: not-allowed;
  }
`

const ForgotPassword = styled.a`
  color: #667eea;
  font-size: 0.85rem;
  text-decoration: none;
  text-align: right;
  cursor: pointer;
  transition: color 0.2s ease;

  &:hover {
    color: #764ba2;
    text-decoration: underline;
  }
`

const LoginButton = styled.button`
  padding: 1rem;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 50px;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`

const Divider = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #e1e5e9;
  }

  span {
    color: #999;
    font-size: 0.85rem;
    font-weight: 500;
  }
`

const SocialButtons = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
`

const SocialButton = styled.button<{ platform: 'facebook' | 'twitter' | 'google' }>`
  flex: 1;
  padding: 0.875rem;
  border: none;
  border-radius: 50px;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  ${props => {
    switch (props.platform) {
      case 'facebook':
        return `
          background: #4267b2;
          color: white;
          &:hover:not(:disabled) {
            background: #365899;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(66, 103, 178, 0.4);
          }
        `
      case 'twitter':
        return `
          background: #1da1f2;
          color: white;
          &:hover:not(:disabled) {
            background: #1a91da;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(29, 161, 242, 0.4);
          }
        `
      case 'google':
        return `
          background: #db4437;
          color: white;
          &:hover:not(:disabled) {
            background: #c23321;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(219, 68, 55, 0.4);
          }
        `
    }
  }}

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }
`

const SignUpSection = styled.div`
  text-align: center;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e1e5e9;

  span {
    color: #666;
    font-size: 0.9rem;
  }

  a {
    color: #667eea;
    font-weight: 600;
    text-decoration: none;
    margin-left: 0.5rem;
    cursor: pointer;
    transition: color 0.2s ease;

    &:hover {
      color: #764ba2;
      text-decoration: underline;
    }
  }
`

interface LoginPageProps {
  onLogin?: (username: string, password: string) => Promise<void>
  onSocialLogin?: (provider: 'facebook' | 'twitter' | 'google') => void
  onSignUp?: () => void
  onForgotPassword?: () => void
}

const LoginPage: React.FC<LoginPageProps> = ({
  onLogin,
  onSocialLogin,
  onSignUp,
  onForgotPassword
}) => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!username || !password) {
      setError('Please enter both username and password')
      return
    }

    if (onLogin) {
      setLoading(true)
      try {
        await onLogin(username, password)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Login failed')
      } finally {
        setLoading(false)
      }
    }
  }

  const handleSocialLogin = (provider: 'facebook' | 'twitter' | 'google') => {
    if (onSocialLogin) {
      onSocialLogin(provider)
    }
  }

  return (
    <PageContainer>
      <LoginCard>
        <Title>Login</Title>
        <Subtitle>Welcome back! Please login to your account</Subtitle>

        {error && <ErrorMessage message={error} />}

        <Form onSubmit={handleSubmit}>
          <InputGroup>
            <Label htmlFor="username">Username</Label>
            <InputWrapper>
              <InputIcon>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </InputIcon>
              <Input
                id="username"
                type="text"
                placeholder="Type your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                autoComplete="username"
              />
            </InputWrapper>
          </InputGroup>

          <InputGroup>
            <Label htmlFor="password">Password</Label>
            <InputWrapper>
              <InputIcon>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </InputIcon>
              <Input
                id="password"
                type="password"
                placeholder="Type your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                autoComplete="current-password"
              />
            </InputWrapper>
          </InputGroup>

          <ForgotPassword onClick={onForgotPassword}>
            Forgot password?
          </ForgotPassword>

          <LoginButton type="submit" disabled={loading}>
            {loading ? (
              <>
                <LoadingSpinner size="small" />
                Logging in...
              </>
            ) : (
              'LOGIN'
            )}
          </LoginButton>
        </Form>

        <Divider>
          <span>Or Sign Up Using</span>
        </Divider>

        <SocialButtons>
          <SocialButton
            platform="facebook"
            onClick={() => handleSocialLogin('facebook')}
            title="Login with Facebook"
            type="button"
          >
            <SocialIcon platform="facebook" size="medium" />
          </SocialButton>
          <SocialButton
            platform="twitter"
            onClick={() => handleSocialLogin('twitter')}
            title="Login with Twitter"
            type="button"
          >
            🐦
          </SocialButton>
          <SocialButton
            platform="google"
            onClick={() => handleSocialLogin('google')}
            title="Login with Google"
            type="button"
          >
            🔴
          </SocialButton>
        </SocialButtons>

        <SignUpSection>
          <span>Or Sign Up Using</span>
          <a onClick={onSignUp}>SIGN UP</a>
        </SignUpSection>
      </LoginCard>
    </PageContainer>
  )
}

export default LoginPage
