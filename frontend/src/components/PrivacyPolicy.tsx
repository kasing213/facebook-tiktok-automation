import React from 'react'
import { Link } from 'react-router-dom'

const PrivacyPolicy = () => {
  return (
    <div style={{
      maxWidth: '800px',
      margin: '0 auto',
      padding: '40px 20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      lineHeight: '1.6',
      color: '#333'
    }}>
      <div style={{ marginBottom: '30px' }}>
        <Link to="/" style={{ color: '#4267B2', textDecoration: 'none' }}>← Back to Home</Link>
      </div>

      <h1 style={{ fontSize: '32px', marginBottom: '10px' }}>Privacy Policy</h1>
      <p style={{ color: '#666', marginBottom: '30px' }}>Last updated: {new Date().toLocaleDateString()}</p>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Introduction</h2>
        <p>
          Welcome to Facebook/TikTok Automation ("we," "our," or "us"). We are committed to protecting your privacy
          and handling your data in an open and transparent manner. This Privacy Policy explains how we collect, use,
          and share information when you use our social media automation platform.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Information We Collect</h2>

        <h3 style={{ fontSize: '18px', marginBottom: '10px' }}>1. Information You Provide</h3>
        <ul style={{ marginLeft: '20px', marginBottom: '15px' }}>
          <li>Account information (username, email, password)</li>
          <li>Profile information you choose to provide</li>
        </ul>

        <h3 style={{ fontSize: '18px', marginBottom: '10px' }}>2. Information from Social Media Platforms</h3>
        <p>When you connect your Facebook or TikTok accounts, we collect:</p>
        <ul style={{ marginLeft: '20px', marginBottom: '15px' }}>
          <li><strong>Facebook:</strong> Your public profile information, pages you manage, and page engagement metrics</li>
          <li><strong>TikTok:</strong> Your basic profile information, display name, and account statistics</li>
        </ul>

        <h3 style={{ fontSize: '18px', marginBottom: '10px' }}>3. Automatically Collected Information</h3>
        <ul style={{ marginLeft: '20px' }}>
          <li>Usage data and analytics</li>
          <li>Device information and IP address</li>
          <li>Browser type and version</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>How We Use Your Information</h2>
        <p>We use the information we collect to:</p>
        <ul style={{ marginLeft: '20px' }}>
          <li>Provide and maintain our service</li>
          <li>Display your connected social media accounts and analytics</li>
          <li>Send you notifications about your account activity</li>
          <li>Improve and optimize our platform</li>
          <li>Ensure security and prevent fraud</li>
          <li>Comply with legal obligations</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Facebook Permissions</h2>
        <p>Our app requests the following Facebook permissions:</p>
        <ul style={{ marginLeft: '20px' }}>
          <li><strong>public_profile:</strong> To identify you and display your name and profile picture</li>
          <li><strong>email:</strong> To create and manage your account</li>
          <li><strong>pages_show_list:</strong> To display the Facebook Pages you manage</li>
          <li><strong>pages_read_engagement:</strong> To show you engagement metrics for your pages</li>
        </ul>
        <p style={{ marginTop: '15px' }}>
          We only request the minimum permissions necessary to provide our service. You can revoke these permissions
          at any time through your Facebook settings.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Data Security</h2>
        <p>
          We implement appropriate technical and organizational measures to protect your personal information, including:
        </p>
        <ul style={{ marginLeft: '20px' }}>
          <li>Encryption of sensitive data in transit and at rest</li>
          <li>Secure password hashing using industry-standard algorithms</li>
          <li>Regular security audits and updates</li>
          <li>Limited access to personal information</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Data Sharing</h2>
        <p>We do not sell your personal information. We may share your information only in these circumstances:</p>
        <ul style={{ marginLeft: '20px' }}>
          <li>With your explicit consent</li>
          <li>To comply with legal obligations</li>
          <li>To protect our rights and prevent fraud</li>
          <li>With service providers who assist in operating our platform (under strict confidentiality agreements)</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Your Rights</h2>
        <p>You have the right to:</p>
        <ul style={{ marginLeft: '20px' }}>
          <li>Access your personal information</li>
          <li>Correct inaccurate data</li>
          <li>Delete your account and associated data</li>
          <li>Export your data</li>
          <li>Withdraw consent for data processing</li>
          <li>Disconnect social media accounts at any time</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Data Retention</h2>
        <p>
          We retain your information only as long as necessary to provide our services and comply with legal obligations.
          When you delete your account, we will delete or anonymize your personal information within 30 days, except where
          we are required to retain it by law.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Third-Party Services</h2>
        <p>
          Our service integrates with Facebook and TikTok. Your use of these platforms is governed by their respective
          privacy policies:
        </p>
        <ul style={{ marginLeft: '20px' }}>
          <li><a href="https://www.facebook.com/privacy/policy/" target="_blank" rel="noopener noreferrer">Facebook Privacy Policy</a></li>
          <li><a href="https://www.tiktok.com/legal/privacy-policy" target="_blank" rel="noopener noreferrer">TikTok Privacy Policy</a></li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Children's Privacy</h2>
        <p>
          Our service is not intended for users under the age of 13. We do not knowingly collect personal information
          from children under 13. If you believe we have collected information from a child under 13, please contact us
          immediately.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Changes to This Policy</h2>
        <p>
          We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new
          Privacy Policy on this page and updating the "Last updated" date.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Contact Us</h2>
        <p>If you have any questions about this Privacy Policy, please contact us at:</p>
        <ul style={{ marginLeft: '20px', listStyle: 'none' }}>
          <li>Email: privacy@facebooktiktokautomation.app</li>
          <li>Website: https://facebooktiktokautomation.vercel.app</li>
        </ul>
      </section>

      <div style={{
        marginTop: '50px',
        paddingTop: '20px',
        borderTop: '1px solid #ddd',
        textAlign: 'center',
        color: '#666',
        fontSize: '14px'
      }}>
        <p>© {new Date().getFullYear()} Facebook/TikTok Automation. All rights reserved.</p>
      </div>
    </div>
  )
}

export default PrivacyPolicy
