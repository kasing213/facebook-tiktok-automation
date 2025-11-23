import React, { useState } from 'react'
import { Link } from 'react-router-dom'

const DataDeletion = () => {
  const [confirmationUrl, setConfirmationUrl] = useState('')

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

      <h1 style={{ fontSize: '32px', marginBottom: '10px' }}>Data Deletion Instructions</h1>
      <p style={{ color: '#666', marginBottom: '30px' }}>How to request deletion of your data from Facebook/TikTok Automation</p>

      <section style={{ marginBottom: '30px', background: '#f0f2f5', padding: '20px', borderRadius: '8px' }}>
        <h2 style={{ fontSize: '20px', marginBottom: '15px' }}>Quick Summary</h2>
        <p>
          When you delete our app from your Facebook account, we automatically delete all your data associated
          with Facebook, including access tokens and profile information. This happens immediately.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Option 1: Remove App from Facebook</h2>
        <p style={{ marginBottom: '15px' }}>
          The easiest way to delete your data is to remove our app from your Facebook account:
        </p>
        <ol style={{ marginLeft: '20px', marginBottom: '15px' }}>
          <li style={{ marginBottom: '10px' }}>
            Go to your Facebook Settings: <a href="https://www.facebook.com/settings?tab=applications" target="_blank" rel="noopener noreferrer">Apps and Websites</a>
          </li>
          <li style={{ marginBottom: '10px' }}>
            Find "Facebook/TikTok Automation" in the list
          </li>
          <li style={{ marginBottom: '10px' }}>
            Click "Remove" or "Remove App"
          </li>
          <li style={{ marginBottom: '10px' }}>
            Confirm the removal
          </li>
        </ol>
        <p style={{
          background: '#e7f3ff',
          padding: '15px',
          borderLeft: '4px solid #4267B2',
          marginTop: '15px'
        }}>
          <strong>Result:</strong> All your Facebook data (access tokens, profile info, page data) will be automatically
          deleted from our servers within 48 hours.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Option 2: Delete Your Account</h2>
        <p style={{ marginBottom: '15px' }}>
          You can also delete all your data by deleting your account on our platform:
        </p>
        <ol style={{ marginLeft: '20px', marginBottom: '15px' }}>
          <li style={{ marginBottom: '10px' }}>
            Log in to: <a href="https://facebooktiktokautomation.vercel.app/login">https://facebooktiktokautomation.vercel.app</a>
          </li>
          <li style={{ marginBottom: '10px' }}>
            Go to your Dashboard
          </li>
          <li style={{ marginBottom: '10px' }}>
            Click on "Account Settings" or "Profile Settings"
          </li>
          <li style={{ marginBottom: '10px' }}>
            Click "Delete Account"
          </li>
          <li style={{ marginBottom: '10px' }}>
            Confirm the deletion
          </li>
        </ol>
        <p style={{
          background: '#e7f3ff',
          padding: '15px',
          borderLeft: '4px solid #4267B2',
          marginTop: '15px'
        }}>
          <strong>Result:</strong> Your entire account and all associated data (Facebook, TikTok, user profile) will be
          permanently deleted within 30 days.
        </p>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Option 3: Contact Us</h2>
        <p style={{ marginBottom: '15px' }}>
          If you need assistance with data deletion or have questions, contact us at:
        </p>
        <div style={{
          background: '#f0f2f5',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '15px'
        }}>
          <p style={{ margin: '0 0 10px 0' }}>
            <strong>Email:</strong> <a href="mailto:privacy@facebooktiktokautomation.app">privacy@facebooktiktokautomation.app</a>
          </p>
          <p style={{ margin: '0' }}>
            <strong>Response Time:</strong> Within 48 hours
          </p>
        </div>
        <p>
          In your email, please include:
        </p>
        <ul style={{ marginLeft: '20px' }}>
          <li>Your email address or username</li>
          <li>Which data you want deleted (Facebook, TikTok, or all)</li>
          <li>Any additional details or concerns</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>What Data Gets Deleted</h2>
        <p style={{ marginBottom: '15px' }}>When you request data deletion, we remove:</p>

        <h3 style={{ fontSize: '18px', marginBottom: '10px', marginTop: '20px' }}>Facebook Data:</h3>
        <ul style={{ marginLeft: '20px', marginBottom: '15px' }}>
          <li>Facebook OAuth access tokens (encrypted)</li>
          <li>Your Facebook profile information (ID, name, email)</li>
          <li>Facebook Page data and access tokens</li>
          <li>Page engagement metrics and analytics</li>
          <li>Any cached Facebook data</li>
        </ul>

        <h3 style={{ fontSize: '18px', marginBottom: '10px', marginTop: '20px' }}>TikTok Data:</h3>
        <ul style={{ marginLeft: '20px', marginBottom: '15px' }}>
          <li>TikTok OAuth access tokens (encrypted)</li>
          <li>Your TikTok profile information</li>
          <li>TikTok account statistics</li>
          <li>Any cached TikTok data</li>
        </ul>

        <h3 style={{ fontSize: '18px', marginBottom: '10px', marginTop: '20px' }}>Account Data:</h3>
        <ul style={{ marginLeft: '20px' }}>
          <li>Your account credentials (username, email, password hash)</li>
          <li>Profile settings and preferences</li>
          <li>Automation rules and scheduled tasks</li>
          <li>Activity logs and usage history</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Data Retention</h2>
        <p>
          We retain data only as long as necessary to provide our services. When you delete:
        </p>
        <ul style={{ marginLeft: '20px' }}>
          <li><strong>Facebook/TikTok connection:</strong> Related data deleted within 48 hours</li>
          <li><strong>Full account:</strong> All data deleted within 30 days</li>
          <li><strong>Legal requirements:</strong> Some logs may be retained for up to 90 days for security and compliance</li>
        </ul>
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Automated Data Deletion Process</h2>
        <p style={{ marginBottom: '15px' }}>
          When Facebook sends us a deletion request (when you remove our app), we automatically:
        </p>
        <ol style={{ marginLeft: '20px' }}>
          <li style={{ marginBottom: '10px' }}>
            Receive the deletion request from Facebook's API
          </li>
          <li style={{ marginBottom: '10px' }}>
            Identify all data associated with your Facebook user ID
          </li>
          <li style={{ marginBottom: '10px' }}>
            Delete all tokens, profile data, and cached information
          </li>
          <li style={{ marginBottom: '10px' }}>
            Send a confirmation URL back to Facebook
          </li>
          <li style={{ marginBottom: '10px' }}>
            Generate a confirmation code (shown below if available)
          </li>
        </ol>

        {confirmationUrl && (
          <div style={{
            background: '#d4edda',
            border: '1px solid #c3e6cb',
            padding: '15px',
            borderRadius: '8px',
            marginTop: '20px'
          }}>
            <p style={{ margin: '0 0 10px 0', fontWeight: 'bold', color: '#155724' }}>
              ✓ Deletion Confirmed
            </p>
            <p style={{ margin: '0', color: '#155724' }}>
              Confirmation URL: <code style={{ background: '#fff', padding: '2px 6px', borderRadius: '4px' }}>{confirmationUrl}</code>
            </p>
          </div>
        )}
      </section>

      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Questions?</h2>
        <p>
          If you have any questions about data deletion or our privacy practices:
        </p>
        <ul style={{ marginLeft: '20px' }}>
          <li>Read our <Link to="/privacy-policy">Privacy Policy</Link></li>
          <li>Contact us at <a href="mailto:privacy@facebooktiktokautomation.app">privacy@facebooktiktokautomation.app</a></li>
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
        <p style={{ marginTop: '10px' }}>
          <Link to="/privacy-policy" style={{ color: '#4267B2', marginRight: '20px' }}>Privacy Policy</Link>
          <Link to="/terms-of-service" style={{ color: '#4267B2' }}>Terms of Service</Link>
        </p>
      </div>
    </div>
  )
}

export default DataDeletion
