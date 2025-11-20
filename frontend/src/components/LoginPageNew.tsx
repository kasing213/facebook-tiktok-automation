import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { authService } from '../services/api'

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
  background: #8CD6F7;
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
  background: #769EAD;
  border-radius: 26px;
  transform: rotate(15deg);
  opacity: 0.9;
  box-shadow: 4px -2px 4px rgba(0, 0, 0, 0.13);
`

const LoginCard = styled.div`
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
  background: linear-gradient(180deg, #91DDFF 0%, #7A9EAE 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 3rem 0;
  text-align: left;
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
  background: linear-gradient(180deg, #8EDDFF 0%, #769DAD 100%);
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

const Divider = styled.div`
  display: flex;
  align-items: center;
  margin: 2rem 0 1.5rem;
  text-align: center;

  span {
    font-family: 'Helvetica', sans-serif;
    font-size: 15px;
    color: #282828;
    white-space: nowrap;
  }
`

const SocialButtons = styled.div`
  display: flex;
  gap: 1.25rem;
  justify-content: center;
  margin-bottom: 2rem;
`

const SocialButton = styled.button`
  width: 50px;
  height: 50px;
  border: none;
  border-radius: 50%;
  background: #F9F9F6;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
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
      // Redirect to dashboard on successful login
      navigate('/dashboard')
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
        <Logo>LOGO</Logo>

        <Title>Welcome back!</Title>
        <Subtitle>Log in to existing LOGO account</Subtitle>

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

          <ForgotPassword href="/forgot-password">
            Forgot Password?
          </ForgotPassword>

          <LoginButton type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'LOG IN'}
          </LoginButton>
        </Form>

        <Divider>
          <span>Or sign up using</span>
        </Divider>

        <SocialButtons>
          <SocialButton type="button" title="Login with Facebook" disabled>
            {/* Facebook icon - blue */}
            <svg width="24" height="24" viewBox="0 0 24 24" fill="#1877F2">
              <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
            </svg>
          </SocialButton>

          <SocialButton type="button" title="Login with Google" disabled>
            {/* Google icon - multicolor */}
            <svg width="24" height="24" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          </SocialButton>

          <SocialButton type="button" title="Login with Apple" disabled>
            {/* Apple icon - black */}
            <svg width="24" height="24" viewBox="0 0 24 24" fill="#28354B">
              <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
            </svg>
          </SocialButton>
        </SocialButtons>

        <SignUpSection>
          <span>Don't have an account?</span>
          <a onClick={onSignUp || (() => navigate('/register'))}>Sign Up</a>
        </SignUpSection>
      </LoginCard>
    </PageContainer>
  )
}

export default LoginPageNew
