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

const SubTitle = styled.h3`
  font-size: 18px;
  margin-bottom: 10px;

  @media (max-width: 768px) {
    font-size: 16px;
  }
`

const List = styled.ul`
  margin-left: 20px;
  margin-bottom: 15px;

  @media (max-width: 768px) {
    margin-left: 16px;
  }
`

const ExternalLink = styled.a`
  color: ${props => props.theme.accent};
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

const PrivacyPolicy = () => {
  return (
    <Container>
      <BackLink to="/">&larr; Back to Home</BackLink>

      <Title>Privacy Policy</Title>
      <LastUpdated>Last updated: {new Date().toLocaleDateString()}</LastUpdated>

      <Section>
        <SectionTitle>Introduction</SectionTitle>
        <p>
          Welcome to Facebook/TikTok Automation ("we," "our," or "us"). We are committed to protecting your privacy
          and handling your data in an open and transparent manner. This Privacy Policy explains how we collect, use,
          and share information when you use our social media automation platform.
        </p>
      </Section>

      <Section>
        <SectionTitle>Information We Collect</SectionTitle>

        <SubTitle>1. Information You Provide</SubTitle>
        <List>
          <li>Account information (username, email, password)</li>
          <li>Profile information you choose to provide</li>
        </List>

        <SubTitle>2. Information from Social Media Platforms</SubTitle>
        <p>When you connect your Facebook or TikTok accounts, we collect:</p>
        <List>
          <li><strong>Facebook:</strong> Your public profile information, pages you manage, and page engagement metrics</li>
          <li><strong>TikTok:</strong> Your basic profile information, display name, and account statistics</li>
        </List>

        <SubTitle>3. Automatically Collected Information</SubTitle>
        <List>
          <li>Usage data and analytics</li>
          <li>Device information and IP address</li>
          <li>Browser type and version</li>
        </List>
      </Section>

      <Section>
        <SectionTitle>How We Use Your Information</SectionTitle>
        <p>We use the information we collect to:</p>
        <List>
          <li>Provide and maintain our service</li>
          <li>Display your connected social media accounts and analytics</li>
          <li>Send you notifications about your account activity</li>
          <li>Improve and optimize our platform</li>
          <li>Ensure security and prevent fraud</li>
          <li>Comply with legal obligations</li>
        </List>
      </Section>

      <Section>
        <SectionTitle>Facebook Permissions</SectionTitle>
        <p>Our app requests the following Facebook permissions:</p>
        <List>
          <li><strong>public_profile:</strong> To identify you and display your name and profile picture</li>
          <li><strong>email:</strong> To create and manage your account</li>
          <li><strong>pages_show_list:</strong> To display the Facebook Pages you manage</li>
          <li><strong>pages_read_engagement:</strong> To show you engagement metrics for your pages</li>
        </List>
        <p>
          We only request the minimum permissions necessary to provide our service. You can revoke these permissions
          at any time through your Facebook settings.
        </p>
      </Section>

      <Section>
        <SectionTitle>Data Security</SectionTitle>
        <p>
          We implement appropriate technical and organizational measures to protect your personal information, including:
        </p>
        <List>
          <li>Encryption of sensitive data in transit and at rest</li>
          <li>Secure password hashing using industry-standard algorithms</li>
          <li>Regular security audits and updates</li>
          <li>Limited access to personal information</li>
        </List>
      </Section>

      <Section>
        <SectionTitle>Data Sharing</SectionTitle>
        <p>We do not sell your personal information. We may share your information only in these circumstances:</p>
        <List>
          <li>With your explicit consent</li>
          <li>To comply with legal obligations</li>
          <li>To protect our rights and prevent fraud</li>
          <li>With service providers who assist in operating our platform (under strict confidentiality agreements)</li>
        </List>
      </Section>

      <Section>
        <SectionTitle>Your Rights</SectionTitle>
        <p>You have the right to:</p>
        <List>
          <li>Access your personal information</li>
          <li>Correct inaccurate data</li>
          <li>Delete your account and associated data</li>
          <li>Export your data</li>
          <li>Withdraw consent for data processing</li>
          <li>Disconnect social media accounts at any time</li>
        </List>
      </Section>

      <Section>
        <SectionTitle>Data Retention</SectionTitle>
        <p>
          We retain your information only as long as necessary to provide our services and comply with legal obligations.
          When you delete your account, we will delete or anonymize your personal information within 30 days, except where
          we are required to retain it by law.
        </p>
      </Section>

      <Section>
        <SectionTitle>Third-Party Services</SectionTitle>
        <p>
          Our service integrates with Facebook and TikTok. Your use of these platforms is governed by their respective
          privacy policies:
        </p>
        <List>
          <li><ExternalLink href="https://www.facebook.com/privacy/policy/" target="_blank" rel="noopener noreferrer">Facebook Privacy Policy</ExternalLink></li>
          <li><ExternalLink href="https://www.tiktok.com/legal/privacy-policy" target="_blank" rel="noopener noreferrer">TikTok Privacy Policy</ExternalLink></li>
        </List>
      </Section>

      <Section>
        <SectionTitle>Children's Privacy</SectionTitle>
        <p>
          Our service is not intended for users under the age of 13. We do not knowingly collect personal information
          from children under 13. If you believe we have collected information from a child under 13, please contact us
          immediately.
        </p>
      </Section>

      <Section>
        <SectionTitle>Changes to This Policy</SectionTitle>
        <p>
          We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new
          Privacy Policy on this page and updating the "Last updated" date.
        </p>
      </Section>

      <Section>
        <SectionTitle>Contact Us</SectionTitle>
        <p>If you have any questions about this Privacy Policy, please contact us at:</p>
        <ul style={{ marginLeft: '20px', listStyle: 'none' }}>
          <li>Email: privacy@facebooktiktokautomation.app</li>
          <li>Website: https://facebooktiktokautomation.vercel.app</li>
        </ul>
      </Section>

      <Footer>
        <p>&copy; {new Date().getFullYear()} Facebook/TikTok Automation. All rights reserved.</p>
      </Footer>
    </Container>
  )
}

export default PrivacyPolicy
