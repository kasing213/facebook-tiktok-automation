# app/services/gmail_api_service.py
"""
Gmail API Email Service - Uses Google OAuth 2.0 instead of SMTP.

This is the recommended approach for cloud environments (Railway, Vercel, etc.)
because direct SMTP connections to Gmail are often blocked.

Setup Instructions:
1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Gmail API: APIs & Services > Library > Search "Gmail API" > Enable
4. Create OAuth 2.0 credentials:
   - APIs & Services > Credentials > Create Credentials > OAuth client ID
   - Application type: Web application
   - Add authorized redirect URI: http://localhost:8000/auth/google/callback
   - Download the credentials JSON
5. Run the setup script to get refresh token (one-time):
   python scripts/setup_gmail_oauth.py
6. Add the credentials to your .env file
"""

import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class GmailAPIService:
    """Send emails using Gmail API with OAuth 2.0"""

    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def __init__(self):
        self.settings = get_settings()
        self._service = None

    def _get_credentials(self) -> Optional[Credentials]:
        """Get valid Gmail API credentials"""
        try:
            # Check if Gmail OAuth is configured
            if not self.settings.GOOGLE_CLIENT_ID or not self.settings.GOOGLE_CLIENT_SECRET:
                logger.warning("Google OAuth credentials not configured")
                return None

            if not self.settings.GOOGLE_REFRESH_TOKEN:
                logger.warning("Google refresh token not configured. Run setup_gmail_oauth.py first.")
                return None

            # Create credentials from refresh token
            creds = Credentials(
                token=None,
                refresh_token=self.settings.GOOGLE_REFRESH_TOKEN.get_secret_value(),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.settings.GOOGLE_CLIENT_ID,
                client_secret=self.settings.GOOGLE_CLIENT_SECRET.get_secret_value(),
                scopes=self.SCOPES
            )

            # Refresh the access token
            if not creds.valid:
                creds.refresh(Request())

            return creds

        except Exception as e:
            logger.error(f"Failed to get Gmail credentials: {type(e).__name__}: {e}")
            return None

    def _get_service(self):
        """Get Gmail API service instance"""
        if self._service is None:
            creds = self._get_credentials()
            if creds:
                self._service = build('gmail', 'v1', credentials=creds)
        return self._service

    def is_configured(self) -> bool:
        """Check if Gmail API is properly configured"""
        return bool(
            self.settings.GOOGLE_CLIENT_ID and
            self.settings.GOOGLE_CLIENT_SECRET and
            self.settings.GOOGLE_REFRESH_TOKEN
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email using Gmail API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            text_content: Plain text body (optional)
            from_name: Sender display name (optional)

        Returns:
            bool: True if email was sent successfully
        """
        if not self.is_configured():
            logger.warning("Gmail API not configured, cannot send email")
            return False

        try:
            service = self._get_service()
            if not service:
                logger.error("Failed to get Gmail API service")
                return False

            # Create message
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['Subject'] = subject

            # Set From header with display name
            sender_name = from_name or self.settings.SMTP_FROM_NAME
            sender_email = self.settings.SMTP_FROM_EMAIL
            message['From'] = f"{sender_name} <{sender_email}>"

            # Add plain text version if provided
            if text_content:
                message.attach(MIMEText(text_content, 'plain'))

            # Add HTML version
            message.attach(MIMEText(html_content, 'html'))

            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send the message
            send_result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent via Gmail API to {to_email}, message ID: {send_result.get('id')}")
            return True

        except HttpError as e:
            logger.error(f"Gmail API HTTP error sending to {to_email}: {e.status_code} - {e.reason}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email via Gmail API to {to_email}: {type(e).__name__}: {e}")
            return False

    def send_verification_email(
        self,
        to_email: str,
        verification_url: str,
        username: str,
        verification_token: Optional[str] = None
    ) -> bool:
        """
        Send email verification email using Gmail API.

        Args:
            to_email: Recipient email address
            verification_url: Full URL for email verification
            username: User's username for personalization
            verification_token: Raw token for manual entry

        Returns:
            bool: True if email was sent successfully
        """
        settings = self.settings

        # Build token section for manual entry
        token_section = ""
        if verification_token:
            token_section = f"""
            <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
                <p style="margin: 0 0 10px 0; color: #166534; font-weight: 600; font-size: 14px;">Your Verification Code:</p>
                <div style="background: #ffffff; border: 1px dashed #10b981; border-radius: 6px; padding: 15px; font-family: 'Courier New', monospace; font-size: 14px; letter-spacing: 1px; word-break: break-all; color: #1f2937;">
                    {verification_token}
                </div>
                <p style="margin: 10px 0 0 0; color: #6b7280; font-size: 12px;">Copy this code and paste it in the verification field</p>
            </div>
            """

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
        .content {{ background: #ffffff; padding: 40px 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px; }}
        .button {{ display: inline-block; background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; }}
        .expire-notice {{ background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 12px; margin: 20px 0; font-size: 14px; color: #92400e; }}
        .footer {{ text-align: center; margin-top: 30px; color: #9ca3af; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Verify Your Email</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>

            <p style="text-align: center; margin: 35px 0;">
                <a href="{verification_url}" class="button">Verify Email Address</a>
            </p>

            {token_section}

            <div class="expire-notice">
                This verification link will expire in <strong>{settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours</strong>.
            </div>

            <p style="margin-top: 30px; color: #6b7280; font-size: 14px;">
                If you did not create an account with us, please ignore this email.
            </p>
        </div>
        <div class="footer">
            <p>&copy; 2026 {settings.SMTP_FROM_NAME}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
Hello {username},

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.

If you did not create an account, please ignore this email.

Best regards,
The {settings.SMTP_FROM_NAME} Team
"""

        return self.send_email(
            to_email=to_email,
            subject="Verify Your Email Address - KS Automation",
            html_content=html_content,
            text_content=text_content
        )

    def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
        username: str,
        reset_token: Optional[str] = None
    ) -> bool:
        """
        Send password reset email using Gmail API.

        Args:
            to_email: Recipient email address
            reset_url: Full URL for password reset
            username: User's username for personalization
            reset_token: Raw token for manual entry

        Returns:
            bool: True if email was sent successfully
        """
        settings = self.settings

        token_section = ""
        if reset_token:
            token_section = f"""
            <div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
                <p style="margin: 0 0 10px 0; color: #991b1b; font-weight: 600; font-size: 14px;">Your Reset Code:</p>
                <div style="background: #ffffff; border: 1px dashed #ef4444; border-radius: 6px; padding: 15px; font-family: 'Courier New', monospace; font-size: 14px; letter-spacing: 1px; word-break: break-all; color: #1f2937;">
                    {reset_token}
                </div>
                <p style="margin: 10px 0 0 0; color: #6b7280; font-size: 12px;">Copy this code and paste it in the reset field</p>
            </div>
            """

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
        .content {{ background: #ffffff; padding: 40px 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px; }}
        .button {{ display: inline-block; background: #ef4444; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reset Your Password</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>

            <p style="text-align: center; margin: 35px 0;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>

            {token_section}

            <p><strong>This link will expire in 1 hour.</strong></p>
            <p style="font-size: 14px; color: #6b7280;">If you didn't request a password reset, please ignore this email.</p>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(
            to_email=to_email,
            subject="Reset Your Password - KS Automation",
            html_content=html_content
        )


# Global instance for easy access
_gmail_service: Optional[GmailAPIService] = None


def get_gmail_service() -> GmailAPIService:
    """Get the global Gmail API service instance"""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = GmailAPIService()
    return _gmail_service
