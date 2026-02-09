import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { authService } from '../services/api'
import { createTenant } from '../services/tenant'
import {
  fadeIn,
  fadeInUp,
  fadeInDown,
  shake,
  easings,
  reduceMotion
} from '../styles/animations'

// Modern register page based on Figma design
// Supports light and dark mode via ThemeContext
// Font: Roboto

const PageContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => props.theme.background};
  padding: 2rem;
  position: relative;
  overflow: hidden;
  transition: background-color 0.3s ease;
`

const DecorativeShape1 = styled.div`
  position: absolute;
  top: -50px;
  right: -100px;
  width: 340px;
  height: 245px;
  background: ${props => props.theme.accent};
  border-radius: 26px;
  transform: rotate(-15deg);
  box-shadow: 4px -2px 4px ${props => props.theme.shadowColor};
  animation: ${fadeIn} 0.8s ${easings.easeOutCubic} 0.2s both;
  opacity: 0.8;
  transition: background-color 0.3s ease;
  ${reduceMotion}
`

const DecorativeShape2 = styled.div`
  position: absolute;
  top: -20px;
  right: -150px;
  width: 320px;
  height: 239px;
  background: ${props => props.theme.accentDark};
  border-radius: 26px;
  transform: rotate(-15deg);
  box-shadow: 4px -2px 4px ${props => props.theme.shadowColor};
  animation: ${fadeIn} 0.8s ${easings.easeOutCubic} both;
  opacity: 0.9;
  transition: background-color 0.3s ease;
  ${reduceMotion}
`

const RegisterCard = styled.div`
  background: ${props => props.theme.card};
  border-radius: 0;
  padding: 2rem 2.5rem 3rem;
  width: 100%;
  max-width: 428px;
  position: relative;
  z-index: 1;
  animation: ${fadeInUp} 0.6s ${easings.easeOutCubic} both;
  transition: background-color 0.3s ease;
  ${reduceMotion}

  @media (max-width: 480px) {
    padding: 2rem 1.5rem;
  }
`

const Title = styled.h2`
  font-family: 'Roboto', sans-serif;
  font-weight: 700;
  font-size: 24px;
  color: ${props => props.theme.textPrimary};
  margin: 0 0 0.5rem 0;
  text-align: center;
  line-height: 28px;
  transition: color 0.3s ease;
`

const Subtitle = styled.p`
  font-family: 'Roboto', sans-serif;
  font-weight: 400;
  font-size: 14px;
  color: ${props => props.theme.textSecondary};
  margin: 0 0 2.5rem 0;
  text-align: center;
  line-height: 28px;
  transition: color 0.3s ease;
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
  background: ${props => props.theme.backgroundTertiary};
  border: 2px solid transparent;
  border-radius: 5px;
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  color: ${props => props.theme.textPrimary};
  box-sizing: border-box;
  transition: background-color 0.2s ease,
              border-color 0.2s ease,
              box-shadow 0.2s ease,
              color 0.2s ease;

  &::placeholder {
    color: ${props => props.theme.textSecondary};
  }

  &:focus {
    outline: none;
    background: ${props => props.theme.backgroundSecondary};
    border-color: ${props => props.theme.accent};
    box-shadow: 0 0 0 3px ${props => props.theme.accentLight};
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
  color: ${props => props.theme.textSecondary};
  font-size: 14px;
  pointer-events: none;
  display: flex;
  align-items: center;
  height: 100%;
  transition: color 0.3s ease;

  svg {
    width: 16px;
    height: 16px;
    stroke: ${props => props.theme.textSecondary};
    fill: none;
    stroke-width: 1.3px;
    transition: stroke 0.3s ease;
  }
`

const RegisterButton = styled.button`
  width: 199px;
  height: 53px;
  margin: 1.5rem auto 0;
  border: none;
  border-radius: 5px;
  font-family: 'Roboto', sans-serif;
  font-weight: 700;
  font-size: 16px;
  color: #FFFFFF;
  background: linear-gradient(180deg, ${props => props.theme.accent} 0%, ${props => props.theme.accentDark} 100%);
  cursor: pointer;
  box-shadow: 0px 5px 7px ${props => props.theme.shadowColor};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ${easings.easeOutCubic},
              box-shadow 0.2s ${easings.easeOutCubic},
              background 0.3s ease;

  &:hover:not(:disabled) {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0px 8px 16px ${props => props.theme.shadowColor};
  }

  &:active:not(:disabled) {
    transform: translateY(0) scale(0.98);
    box-shadow: 0px 4px 8px ${props => props.theme.shadowColor};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  ${reduceMotion}
`

const SignInSection = styled.div`
  text-align: center;
  padding-top: 1.5rem;
  border-top: none;

  span {
    font-family: 'Roboto', sans-serif;
    font-size: 16px;
    color: ${props => props.theme.textPrimary};
    transition: color 0.3s ease;
  }

  a {
    font-family: 'Roboto', sans-serif;
    font-weight: 700;
    font-size: 16px;
    color: ${props => props.theme.accent};
    text-decoration: none;
    margin-left: 0.5rem;
    cursor: pointer;
    transition: color 0.3s ease;

    &:hover {
      text-decoration: underline;
    }
  }
`

const ErrorMessage = styled.div`
  background: ${props => props.theme.errorLight};
  color: ${props => props.theme.error};
  padding: 0.75rem 1rem;
  border-radius: 5px;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  border-left: 3px solid ${props => props.theme.error};
  animation: ${shake} 0.4s ease, ${fadeInDown} 0.3s ease;
  transition: background-color 0.3s ease, color 0.3s ease;
  ${reduceMotion}
`

const SuccessMessage = styled.div`
  background: ${props => props.theme.successLight};
  color: ${props => props.theme.success};
  padding: 0.75rem 1rem;
  border-radius: 5px;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  border-left: 3px solid ${props => props.theme.success};
  animation: ${fadeInDown} 0.3s ${easings.easeOutCubic};
  transition: background-color 0.3s ease, color 0.3s ease;
  ${reduceMotion}
`

interface RegisterPageProps {
  onSignIn?: () => void
}

const RegisterPage: React.FC<RegisterPageProps> = ({ onSignIn }) => {
  const navigate = useNavigate()
  const [organizationName, setOrganizationName] = useState('')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    // Validation
    if (!organizationName.trim()) {
      setError('Organization name is required')
      return
    }

    if (!email) {
      setError('Email is required')
      return
    }

    if (!username || !password) {
      setError('Username and password are required')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address')
      return
    }

    setLoading(true)
    try {
      // Step 1: Create a new organization/tenant
      const tenantId = await createTenant(organizationName.trim())
      console.log('[RegisterPage] Created tenant:', tenantId)

      // Step 2: Register user in the new tenant
      await authService.register({
        tenant_id: tenantId,
        username,
        password,
        email
      })
      setSuccess('Account created successfully! Redirecting to login...')
      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageContainer>
      <DecorativeShape2 />
      <DecorativeShape1 />

      <RegisterCard>
        <Title>Let's Get Started!</Title>
        <Subtitle>Create an account on KS to get all features</Subtitle>

        {error && <ErrorMessage role="alert">{error}</ErrorMessage>}
        {success && <SuccessMessage>{success}</SuccessMessage>}

        <Form onSubmit={handleSubmit}>
          <InputGroup>
            <InputWithIcon>
              <InputIcon>
                <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                  <path d="M2 2h12a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1zm1 2v8h10V4H3z" />
                </svg>
              </InputIcon>
              <Input
                type="text"
                placeholder="Organization / Business Name"
                value={organizationName}
                onChange={(e) => setOrganizationName(e.target.value)}
                disabled={loading}
                required
              />
            </InputWithIcon>
          </InputGroup>

          <InputGroup>
            <InputWithIcon>
              <InputIcon>
                <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                  <path d="M2 3h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zm0 2l6 4 6-4" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </InputIcon>
              <Input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                required
              />
            </InputWithIcon>
          </InputGroup>

          <InputGroup>
            <InputWithIcon>
              <InputIcon>
                <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                </svg>
              </InputIcon>
              <Input
                type="text"
                placeholder="Username"
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

          <InputGroup>
            <InputWithIcon>
              <InputIcon>
                <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 6v-2a4 4 0 0 1 8 0v2M3 6h10a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z" />
                </svg>
              </InputIcon>
              <Input
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
              />
            </InputWithIcon>
          </InputGroup>

          <RegisterButton type="submit" disabled={loading}>
            {loading ? 'Creating Account...' : 'REGISTER'}
          </RegisterButton>
        </Form>

        <SignInSection>
          <span>Already have an account?</span>
          <a onClick={onSignIn || (() => navigate('/login'))}>Login</a>
        </SignInSection>
      </RegisterCard>
    </PageContainer>
  )
}

export default RegisterPage
