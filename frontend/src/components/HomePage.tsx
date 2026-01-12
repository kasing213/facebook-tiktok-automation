import React from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import SocialIcon from './SocialIcon'

// OpenAI-style landing page with blue color scheme
// Colors: #4a90e2 (light blue), #2a5298 (dark blue), #1e3c72 (deeper blue)

const PageWrapper = styled.div`
  min-height: 100vh;
  background: #ffffff;
`

const StickyHeader = styled.header`
  position: sticky;
  top: 0;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  z-index: 100;
  padding: 1rem 2rem;

  @media (max-width: 768px) {
    padding: 1rem 1.5rem;
  }
`

const NavContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 48px;
`

const NavLogo = styled.h1`
  font-family: 'Roboto', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(180deg, #4a90e2 0%, #2a5298 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  cursor: pointer;
`

const NavCenter = styled.div`
  display: flex;
  gap: 2rem;
  align-items: center;

  @media (max-width: 768px) {
    display: none;
  }
`

const NavLink = styled.a`
  font-family: 'Roboto', sans-serif;
  font-size: 0.95rem;
  font-weight: 500;
  color: #6b7280;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s ease;

  &:hover {
    color: #2a5298;
  }
`

const AuthButtons = styled.div`
  display: flex;
  gap: 1rem;
  align-items: center;
`

const LoginButton = styled.button`
  padding: 0.625rem 1.25rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-family: 'Roboto', sans-serif;
  font-size: 0.95rem;
  font-weight: 500;
  color: #6b7280;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #2a5298;
    color: #2a5298;
  }

  @media (max-width: 480px) {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
`

const SignUpButton = styled.button`
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 6px;
  font-family: 'Roboto', sans-serif;
  font-size: 0.95rem;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
  }

  @media (max-width: 480px) {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
`

const HeroSection = styled.section`
  max-width: 900px;
  margin: 0 auto;
  padding: 4rem 2rem 3rem;
  text-align: center;

  @media (max-width: 768px) {
    padding: 3rem 1.5rem 2rem;
  }
`

const HeroTitle = styled.h2`
  font-family: 'Roboto', sans-serif;
  font-size: 3.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 1rem 0;
  line-height: 1.1;

  @media (max-width: 768px) {
    font-size: 2.5rem;
  }

  @media (max-width: 480px) {
    font-size: 2rem;
  }
`

const HeroSubtitle = styled.p`
  font-family: 'Roboto', sans-serif;
  font-size: 1.25rem;
  font-weight: 400;
  color: #6b7280;
  margin: 0;
  line-height: 1.6;
  max-width: 700px;
  margin: 0 auto;

  @media (max-width: 768px) {
    font-size: 1.1rem;
  }

  @media (max-width: 480px) {
    font-size: 1rem;
  }
`

const QuickstartSection = styled.section`
  max-width: 900px;
  margin: 2rem auto;
  padding: 3rem 2rem;
  background: #f5f8fb;
  border-radius: 12px;

  @media (max-width: 768px) {
    padding: 2rem 1.5rem;
    margin: 2rem 1.5rem;
  }
`

const SectionTitle = styled.h3`
  font-family: 'Roboto', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 1rem 0;
  text-align: center;

  @media (max-width: 768px) {
    font-size: 1.75rem;
  }

  @media (max-width: 480px) {
    font-size: 1.5rem;
  }
`

const Description = styled.p`
  font-family: 'Roboto', sans-serif;
  font-size: 1.125rem;
  font-weight: 400;
  color: #4b5563;
  margin: 0 0 1.5rem 0;
  line-height: 1.7;
  text-align: center;

  @media (max-width: 480px) {
    font-size: 1rem;
  }
`

const CTAButton = styled.button`
  padding: 0.875rem 2rem;
  border: none;
  border-radius: 8px;
  font-family: 'Roboto', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
  display: block;
  margin: 0 auto;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(74, 144, 226, 0.4);
  }

  @media (max-width: 480px) {
    padding: 0.75rem 1.5rem;
    font-size: 0.95rem;
  }
`

const ExampleSection = styled.section`
  max-width: 900px;
  margin: 3rem auto;
  padding: 0 2rem;

  @media (max-width: 768px) {
    padding: 0 1.5rem;
  }
`

const ExampleHeader = styled.h3`
  font-family: 'Roboto', sans-serif;
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1rem 0;
  text-align: center;

  @media (max-width: 480px) {
    font-size: 1.25rem;
  }
`

const CodeBlock = styled.pre`
  background: #1f2937;
  color: #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  overflow-x: auto;
  margin: 0;

  @media (max-width: 480px) {
    font-size: 0.8rem;
    padding: 1rem;
  }
`

const FeaturesSection = styled.section`
  max-width: 1200px;
  margin: 4rem auto;
  padding: 0 2rem 4rem;

  @media (max-width: 768px) {
    padding: 0 1.5rem 3rem;
  }
`

const SectionHeader = styled.h3`
  font-family: 'Roboto', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 3rem 0;
  text-align: center;

  @media (max-width: 768px) {
    font-size: 1.75rem;
    margin: 0 0 2rem 0;
  }

  @media (max-width: 480px) {
    font-size: 1.5rem;
  }
`

const FeaturesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
`

const FeatureCard = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 20px rgba(74, 144, 226, 0.15);
    border-color: #4a90e2;
  }

  @media (max-width: 480px) {
    padding: 1.5rem;
  }
`

const IconWrapper = styled.div`
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #4a90e2 0%, #2a5298 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 1.25rem;
`

const FeatureTitle = styled.h4`
  font-family: 'Roboto', sans-serif;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.75rem 0;
`

const FeatureDescription = styled.p`
  font-family: 'Roboto', sans-serif;
  font-size: 0.95rem;
  font-weight: 400;
  color: #6b7280;
  margin: 0;
  line-height: 1.6;
`

const HomePage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <PageWrapper>
      <StickyHeader>
        <NavContainer>
          <NavLogo>KS</NavLogo>
          <NavCenter>
            <NavLink onClick={() => navigate('/login')}>Dashboard</NavLink>
            <NavLink onClick={() => navigate('/register')}>Services</NavLink>
            <NavLink href="#services">Features</NavLink>
          </NavCenter>
          <AuthButtons>
            <LoginButton onClick={() => navigate('/login')}>Login</LoginButton>
            <SignUpButton onClick={() => navigate('/register')}>Sign Up</SignUpButton>
          </AuthButtons>
        </NavContainer>
      </StickyHeader>

      <HeroSection>
        <HeroTitle>Social Media Automation Platform</HeroTitle>
        <HeroSubtitle>
          Streamline your Facebook and TikTok campaigns with powerful automation tools. Built for marketers and developers.
        </HeroSubtitle>
      </HeroSection>

      <QuickstartSection>
        <SectionTitle>Developer quickstart</SectionTitle>
        <Description>
          Connect your Facebook and TikTok accounts, automate campaigns, and track performance—all through our intuitive API and dashboard.
        </Description>
        <CTAButton onClick={() => navigate('/register')}>
          Get started for free →
        </CTAButton>
      </QuickstartSection>

      <ExampleSection>
        <ExampleHeader>Automation Example</ExampleHeader>
        <CodeBlock>{`// Schedule a Facebook post
await automation.schedulePost({
  platform: 'facebook',
  content: 'Check out our new product!',
  scheduledTime: '2024-01-15T10:00:00Z',
  autoPublish: true
});`}</CodeBlock>
      </ExampleSection>

      <FeaturesSection id="services">
        <SectionHeader>Choose Your Service</SectionHeader>
        <FeaturesGrid>
          <FeatureCard>
            <IconWrapper>
              <SocialIcon platform="facebook" size="large" />
            </IconWrapper>
            <FeatureTitle>Facebook Automation</FeatureTitle>
            <FeatureDescription>
              Automate post scheduling, manage campaigns, and access Facebook Marketing API features with powerful automation tools.
            </FeatureDescription>
            <CTAButton onClick={() => navigate('/register')}>
              Get Started →
            </CTAButton>
          </FeatureCard>

          <FeatureCard>
            <IconWrapper>
              <SocialIcon platform="tiktok" size="large" />
            </IconWrapper>
            <FeatureTitle>TikTok Automation</FeatureTitle>
            <FeatureDescription>
              Schedule videos, analyze performance, and leverage TikTok Creator API capabilities to grow your TikTok presence.
            </FeatureDescription>
            <CTAButton onClick={() => navigate('/register')}>
              Get Started →
            </CTAButton>
          </FeatureCard>

          <FeatureCard>
            <IconWrapper>INV</IconWrapper>
            <FeatureTitle>Invoice Generator</FeatureTitle>
            <FeatureDescription>
              Generate professional invoices automatically for your campaigns and services. Integration coming soon.
            </FeatureDescription>
            <CTAButton onClick={() => alert('Coming soon!')} style={{ opacity: 0.6 }}>
              Coming Soon
            </CTAButton>
          </FeatureCard>

          <FeatureCard>
            <IconWrapper>API</IconWrapper>
            <FeatureTitle>Analytics API</FeatureTitle>
            <FeatureDescription>
              Advanced analytics and reporting API for comprehensive insights into your social media performance. Integration coming soon.
            </FeatureDescription>
            <CTAButton onClick={() => alert('Coming soon!')} style={{ opacity: 0.6 }}>
              Coming Soon
            </CTAButton>
          </FeatureCard>
        </FeaturesGrid>
      </FeaturesSection>
    </PageWrapper>
  )
}

export default HomePage
