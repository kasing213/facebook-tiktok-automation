import React from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'

const PageContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
`

const Header = styled.header`
  padding: 1.5rem 3rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);

  @media (max-width: 768px) {
    padding: 1rem 1.5rem;
  }
`

const Logo = styled.h1`
  font-family: 'Roboto', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: white;
  margin: 0;
`

const Nav = styled.nav`
  display: flex;
  gap: 1.5rem;
  align-items: center;

  @media (max-width: 480px) {
    gap: 1rem;
  }
`

const NavButton = styled.button<{ primary?: boolean }>`
  padding: ${props => props.primary ? '0.75rem 2rem' : '0.75rem 1.5rem'};
  border: ${props => props.primary ? 'none' : '2px solid white'};
  border-radius: 50px;
  font-family: 'Roboto', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  color: ${props => props.primary ? '#667eea' : 'white'};
  background: ${props => props.primary ? 'white' : 'transparent'};
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    background: ${props => props.primary ? '#f8f8f8' : 'rgba(255, 255, 255, 0.1)'};
  }

  @media (max-width: 480px) {
    padding: ${props => props.primary ? '0.6rem 1.5rem' : '0.6rem 1rem'};
    font-size: 0.9rem;
  }
`

const Main = styled.main`
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  text-align: center;
`

const Hero = styled.div`
  max-width: 800px;
  animation: fadeIn 0.8s ease-out;

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`

const Title = styled.h2`
  font-family: 'Roboto', sans-serif;
  font-size: 3.5rem;
  font-weight: 700;
  color: white;
  margin: 0 0 1.5rem 0;
  line-height: 1.2;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);

  @media (max-width: 768px) {
    font-size: 2.5rem;
  }

  @media (max-width: 480px) {
    font-size: 2rem;
  }
`

const Subtitle = styled.p`
  font-family: 'Roboto', sans-serif;
  font-size: 1.25rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 3rem 0;
  line-height: 1.6;

  @media (max-width: 768px) {
    font-size: 1.1rem;
  }

  @media (max-width: 480px) {
    font-size: 1rem;
  }
`

const CTAButtons = styled.div`
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  margin-bottom: 4rem;

  @media (max-width: 480px) {
    flex-direction: column;
    gap: 1rem;
  }
`

const CTAButton = styled.button<{ primary?: boolean }>`
  padding: 1rem 2.5rem;
  border: ${props => props.primary ? 'none' : '2px solid white'};
  border-radius: 50px;
  font-family: 'Roboto', sans-serif;
  font-size: 1.1rem;
  font-weight: 600;
  color: ${props => props.primary ? '#667eea' : 'white'};
  background: ${props => props.primary ? 'white' : 'transparent'};
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: ${props => props.primary ? '0 4px 15px rgba(0, 0, 0, 0.2)' : 'none'};

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    background: ${props => props.primary ? '#f8f8f8' : 'rgba(255, 255, 255, 0.1)'};
  }

  @media (max-width: 480px) {
    width: 100%;
  }
`

const Features = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  max-width: 1000px;
  width: 100%;
`

const FeatureCard = styled.div`
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 2rem;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    background: rgba(255, 255, 255, 0.2);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  }
`

const FeatureIcon = styled.div`
  font-size: 3rem;
  margin-bottom: 1rem;
`

const FeatureTitle = styled.h3`
  font-family: 'Roboto', sans-serif;
  font-size: 1.5rem;
  font-weight: 600;
  color: white;
  margin: 0 0 0.75rem 0;
`

const FeatureDescription = styled.p`
  font-family: 'Roboto', sans-serif;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  line-height: 1.5;
`

const HomePage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <PageContainer>
      <Header>
        <Logo>LOGO</Logo>
        <Nav>
          <NavButton onClick={() => navigate('/login')}>Login</NavButton>
          <NavButton primary onClick={() => navigate('/register')}>Sign Up</NavButton>
        </Nav>
      </Header>

      <Main>
        <Hero>
          <Title>Automate Your Social Media Marketing</Title>
          <Subtitle>
            Streamline your Facebook and TikTok advertising campaigns with powerful automation tools.
            Save time, increase efficiency, and grow your business.
          </Subtitle>

          <CTAButtons>
            <CTAButton primary onClick={() => navigate('/register')}>
              Get Started Free
            </CTAButton>
            <CTAButton onClick={() => navigate('/login')}>
              Sign In
            </CTAButton>
          </CTAButtons>

          <Features>
            <FeatureCard>
              <FeatureIcon>📘</FeatureIcon>
              <FeatureTitle>Facebook Integration</FeatureTitle>
              <FeatureDescription>
                Connect your Facebook Ads account and manage campaigns with ease
              </FeatureDescription>
            </FeatureCard>

            <FeatureCard>
              <FeatureIcon>🎵</FeatureIcon>
              <FeatureTitle>TikTok Automation</FeatureTitle>
              <FeatureDescription>
                Automate your TikTok content and advertising strategies
              </FeatureDescription>
            </FeatureCard>

            <FeatureCard>
              <FeatureIcon>📊</FeatureIcon>
              <FeatureTitle>Analytics & Reports</FeatureTitle>
              <FeatureDescription>
                Track performance with detailed analytics and automated reporting
              </FeatureDescription>
            </FeatureCard>
          </Features>
        </Hero>
      </Main>
    </PageContainer>
  )
}

export default HomePage
