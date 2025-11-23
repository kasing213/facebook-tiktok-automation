import { Link } from 'react-router-dom'

const TermsOfService = () => {
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

      <h1 style={{ fontSize: '32px', marginBottom: '10px' }}>Terms of Service</h1>
      <p style={{ color: '#666', marginBottom: '30px' }}>Last updated: {new Date().toLocaleDateString()}</p>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>1. Acceptance of Terms</h2>
        <p>
          By accessing and using Facebook/TikTok Automation ("the Service"), you agree to be bound by these Terms of Service.
          If you do not agree to these terms, please do not use the Service.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>2. Description of Service</h2>
        <p>
          Our Service provides tools to help you manage and analyze your social media presence on Facebook and TikTok,
          including:
        </p>
        <ul style={{ marginLeft: '20px' }}>
          <li>Connecting and managing social media accounts</li>
          <li>Viewing page and account analytics</li>
          <li>Scheduling and automating content</li>
          <li>Generating reports on social media performance</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>3. User Accounts</h2>
        <p>You are responsible for:</p>
        <ul style={{ marginLeft: '20px' }}>
          <li>Maintaining the confidentiality of your account credentials</li>
          <li>All activities that occur under your account</li>
          <li>Notifying us immediately of any unauthorized use</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>4. Acceptable Use</h2>
        <p>You agree not to:</p>
        <ul style={{ marginLeft: '20px' }}>
          <li>Violate any laws or regulations</li>
          <li>Infringe on intellectual property rights</li>
          <li>Transmit harmful code or malware</li>
          <li>Attempt to gain unauthorized access to our systems</li>
          <li>Use the Service for spam or harassment</li>
          <li>Violate Facebook or TikTok's terms of service</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>5. Third-Party Services</h2>
        <p>
          Our Service integrates with Facebook and TikTok. Your use of these platforms is subject to their respective
          terms of service. We are not responsible for any changes to these third-party services that may affect our Service.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>6. Limitation of Liability</h2>
        <p>
          The Service is provided "as is" without warranties of any kind. We are not liable for any damages arising from
          your use of the Service, including but not limited to data loss, service interruptions, or unauthorized access.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>7. Termination</h2>
        <p>
          We reserve the right to terminate or suspend your account at any time for violation of these terms. You may
          also terminate your account at any time by deleting it through the Service.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>8. Changes to Terms</h2>
        <p>
          We may modify these Terms of Service at any time. Continued use of the Service after changes constitutes
          acceptance of the modified terms.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>9. Contact Information</h2>
        <p>For questions about these Terms of Service, contact us at:</p>
        <ul style={{ marginLeft: '20px', listStyle: 'none' }}>
          <li>Email: support@facebooktiktokautomation.app</li>
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

export default TermsOfService
