import { Link } from 'react-router-dom'
import styled from 'styled-components'

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
  line-height: 1.6;
  color: ${props => props.theme.textPrimary};
  background: ${props => props.theme.background};

  @media (max-width: 768px) {
    padding: 20px 16px;
  }
`

const BackLink = styled(Link)`
  color: ${props => props.theme.accent};
  text-decoration: none;
  display: inline-block;
  margin-bottom: 30px;

  @media (max-width: 768px) {
    margin-bottom: 20px;
  }
`

const Title = styled.h1`
  font-size: 32px;
  margin-bottom: 10px;

  @media (max-width: 768px) {
    font-size: 24px;
  }
`

const LastUpdated = styled.p`
  color: ${props => props.theme.textMuted};
  margin-bottom: 30px;

  @media (max-width: 768px) {
    margin-bottom: 20px;
  }
`

const Section = styled.section`
  margin-bottom: 30px;

  @media (max-width: 768px) {
    margin-bottom: 20px;
  }
`

const SectionTitle = styled.h2`
  font-size: 24px;
  margin-bottom: 15px;

  @media (max-width: 768px) {
    font-size: 20px;
  }
`

const List = styled.ul`
  margin-left: 20px;

  @media (max-width: 768px) {
    margin-left: 16px;
  }
`

const Footer = styled.div`
  margin-top: 50px;
  padding-top: 20px;
  border-top: 1px solid ${props => props.theme.border};
  text-align: center;
  color: ${props => props.theme.textMuted};
  font-size: 14px;

  @media (max-width: 768px) {
    margin-top: 30px;
  }
`

const TermsOfService = () => {
  return (
    <Container>
      <BackLink to="/">&larr; Back to Home</BackLink>

      <Title>Terms of Service</Title>
      <LastUpdated>Last updated: {new Date().toLocaleDateString()}</LastUpdated>

      <Section>
        <SectionTitle>1. Acceptance of Terms</SectionTitle>
        <p>
          By accessing and using Facebook/TikTok Automation ("the Service"), you agree to be bound by these Terms of Service.
          If you do not agree to these terms, please do not use the Service.
        </p>
      </Section>

      <Section>
        <SectionTitle>2. Description of Service</SectionTitle>
        <p>
          Our Service provides tools to help you manage and analyze your social media presence on Facebook and TikTok,
          including:
        </p>
        <List>
          <li>Connecting and managing social media accounts</li>
          <li>Viewing page and account analytics</li>
          <li>Scheduling and automating content</li>
          <li>Generating reports on social media performance</li>
        </List>
      </Section>

      <Section>
        <SectionTitle>3. User Accounts</SectionTitle>
        <p>You are responsible for:</p>
        <List>
          <li>Maintaining the confidentiality of your account credentials</li>
          <li>All activities that occur under your account</li>
          <li>Notifying us immediately of any unauthorized use</li>
        </List>
      </Section>

      <Section>
        <SectionTitle>4. Acceptable Use</SectionTitle>
        <p>You agree not to:</p>
        <List>
          <li>Violate any laws or regulations</li>
          <li>Infringe on intellectual property rights</li>
          <li>Transmit harmful code or malware</li>
          <li>Attempt to gain unauthorized access to our systems</li>
          <li>Use the Service for spam or harassment</li>
          <li>Violate Facebook or TikTok's terms of service</li>
        </List>
      </Section>

      <Section>
        <SectionTitle>5. Third-Party Services</SectionTitle>
        <p>
          Our Service integrates with Facebook and TikTok. Your use of these platforms is subject to their respective
          terms of service. We are not responsible for any changes to these third-party services that may affect our Service.
        </p>
      </Section>

      <Section>
        <SectionTitle>6. Limitation of Liability</SectionTitle>
        <p>
          The Service is provided "as is" without warranties of any kind. We are not liable for any damages arising from
          your use of the Service, including but not limited to data loss, service interruptions, or unauthorized access.
        </p>
      </Section>

      <Section>
        <SectionTitle>7. Termination</SectionTitle>
        <p>
          We reserve the right to terminate or suspend your account at any time for violation of these terms. You may
          also terminate your account at any time by deleting it through the Service.
        </p>
      </Section>

      <Section>
        <SectionTitle>8. Changes to Terms</SectionTitle>
        <p>
          We may modify these Terms of Service at any time. Continued use of the Service after changes constitutes
          acceptance of the modified terms.
        </p>
      </Section>

      <Section>
        <SectionTitle>9. Contact Information</SectionTitle>
        <p>For questions about these Terms of Service, contact us at:</p>
        <ul style={{ marginLeft: '20px', listStyle: 'none' }}>
          <li>Email: support@facebooktiktokautomation.app</li>
          <li>Website: https://facebooktiktokautomation.vercel.app</li>
        </ul>
      </Section>

      <Footer>
        <p>&copy; {new Date().getFullYear()} Facebook/TikTok Automation. All rights reserved.</p>
      </Footer>
    </Container>
  )
}

export default TermsOfService
