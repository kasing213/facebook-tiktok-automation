import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { authService } from '../services/api'
import {
  fadeIn,
  fadeInUp,
  fadeInDown,
  shake,
  easings,
  reduceMotion
} from '../styles/animations'

// Modern login page based on Figma design
// Colors: Light blue (#91DDFF to #769EAD gradient), White background
// Font: Roboto

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
  box-shadow: 4px -2px 4px rgba(0, 0, 0, 0.13);
  animation: ${fadeIn} 0.8s ${easings.easeOutCubic} 0.2s both;
  opacity: 0.8;
  ${reduceMotion}
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
  box-shadow: 4px -2px 4px rgba(0, 0, 0, 0.13);
  animation: ${fadeIn} 0.8s ${easings.easeOutCubic} both;
  opacity: 0.9;
  ${reduceMotion}
`

const LoginCard = styled.div`
  background: white;
  border-radius: 0;
  padding: 2rem 2.5rem 3rem;
  width: 100%;
  max-width: 428px;
  position: relative;
  z-index: 1;
  animation: ${fadeInUp} 0.6s ${easings.easeOutCubic} both;
  ${reduceMotion}

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
  margin: 0 0 3rem 0;
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
  margin: 0 0 2.5rem 0;
  text-align: center;
  line-height: 18px;
`

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`

const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0;
`

const Input = styled.input`
  width: 100%;
  height: 61px;
  padding: 0 1rem 0 3rem;
  background: #F3F3F3;
  border: 2px solid transparent;
  border-radius: 5px;
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  color: #515151;
  box-sizing: border-box;
  transition: background-color 0.2s ease,
              border-color 0.2s ease,
              box-shadow 0.2s ease;

  &::placeholder {
    color: #515151;
  }

  &:focus {
    outline: none;
    background: #EBEBEB;
    border-color: #4a90e2;
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
  }

  ${reduceMotion}
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

const ForgotPassword = styled.a`
  font-family: 'Roboto', sans-serif;
  font-weight: 500;
  font-size: 14px;
  color: #515151;
  text-decoration: none;
  text-align: right;
  cursor: pointer;
  margin-top: 0.5rem;

  &:hover {
    text-decoration: underline;
  }
`

const LoginButton = styled.button`
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
  box-shadow: 0px 5px 7px rgba(0, 0, 0, 0.19);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ${easings.easeOutCubic},
              box-shadow 0.2s ${easings.easeOutCubic};

  &:hover:not(:disabled) {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0px 8px 16px rgba(74, 144, 226, 0.35);
  }

  &:active:not(:disabled) {
    transform: translateY(0) scale(0.98);
    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  ${reduceMotion}
`

const SignUpSection = styled.div`
  text-align: center;
  padding-top: 1.5rem;
  border-top: none;

  span {
    font-family: 'Roboto', sans-serif;
    font-size: 16px;
    color: #000000;
  }

  a {
    font-family: 'Roboto', sans-serif;
    font-weight: 700;
    font-size: 16px;
    color: #000000;
    text-decoration: none;
    margin-left: 0.5rem;
    cursor: pointer;

    &:hover {
      text-decoration: underline;
    }
  }
`

const ErrorMessage = styled.div`
  background: #fee;
  color: #c33;
  padding: 0.75rem 1rem;
  border-radius: 5px;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  border-left: 3px solid #c33;
  animation: ${shake} 0.4s ease, ${fadeInDown} 0.3s ease;
  ${reduceMotion}
`

interface LoginPageNewProps {
  onSignUp?: () => void
}

const LoginPageNew: React.FC<LoginPageNewProps> = ({ onSignUp }) => {
  const navigate = useNavigate()
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

    setLoading(true)
    try {
      await authService.login({ username, password })
      // Get user info to extract tenant_id
      const user = await authService.getCurrentUser()

      // Store tenant_id in localStorage for persistent access
      if (user.tenant_id) {
        localStorage.setItem('selectedTenantId', user.tenant_id)
      }

      // Redirect to dashboard with tenant_id
      navigate('/dashboard', {
        state: { tenantId: user.tenant_id }
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageContainer>
      <DecorativeShape2 />
      <DecorativeShape1 />

      <LoginCard>
        <Logo>KS</Logo>

        <Title>Welcome back!</Title>
        <Subtitle>Log in to existing KS account</Subtitle>

        {error && <ErrorMessage>{error}</ErrorMessage>}

        <Form onSubmit={handleSubmit}>
          <InputGroup>
            <InputWithIcon>
              <InputIcon>
                <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                </svg>
              </InputIcon>
              <Input
                type="text"
                placeholder="Username or Email"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
              />
            </InputWithIcon>
          </InputGroup>

          <InputGroup>
            <InputWithIcon>
              <InputIcon>
                <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 6v-2a4 4 0 0 1 8 0v2M3 6h10a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z" />
                </svg>
              </InputIcon>
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </InputWithIcon>
          </InputGroup>

          <ForgotPassword href="/forgot-password">
            Forgot Password?
          </ForgotPassword>

          <LoginButton type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'LOG IN'}
          </LoginButton>
        </Form>

        <SignUpSection>
          <span>Don't have an account?</span>
          <a onClick={onSignUp || (() => navigate('/register'))}>Sign Up</a>
        </SignUpSection>
      </LoginCard>
    </PageContainer>
  )
}

export default LoginPageNew
