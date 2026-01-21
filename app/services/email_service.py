# app/services/email_service.py
"""
Enhanced email service for sending verification emails.

Supports two methods:
1. Gmail API with OAuth 2.0 (RECOMMENDED for cloud environments like Railway)
2. SMTP (fallback, often blocked by cloud providers)

Priority: Gmail API > SMTP > Console logging (dev mode)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from app.core.config import get_settings
from app.core.models import User

logger = logging.getLogger(__name__)

# Gmail API service - disabled until credentials are configured
# To enable: Set up Google OAuth credentials and change GMAIL_API_DISABLED to False
GMAIL_API_DISABLED = True  # TODO: Set to False when you have Google credentials

if GMAIL_API_DISABLED:
    GMAIL_API_AVAILABLE = False
    logger.info("Gmail API disabled - set GMAIL_API_DISABLED=False to enable when credentials ready")
else:
    # Try to import Gmail API service (optional dependency)
    try:
        from app.services.gmail_api_service import GmailAPIService, get_gmail_service
        # Check if credentials are available
        settings = get_settings()
        if (settings.GOOGLE_CLIENT_ID and
            settings.GOOGLE_CLIENT_SECRET and
            settings.GOOGLE_REFRESH_TOKEN):
            GMAIL_API_AVAILABLE = True
            logger.info("Gmail API enabled with credentials")
        else:
            GMAIL_API_AVAILABLE = False
            logger.info("Gmail API disabled - missing Google OAuth credentials")
    except ImportError as e:
        GMAIL_API_AVAILABLE = False
        logger.info(f"Gmail API not available (missing dependencies): {e}")


class EmailService:
    """Enhanced email service with template support"""

    def __init__(self):
        self.settings = get_settings()
        # Initialize Jinja2 environment for email templates
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        self._template_env = Environment(loader=FileSystemLoader(template_dir))

    def send_verification_email(self, user: User, verification_token: str) -> bool:
        """
        Send email verification email using template.

        Args:
            user: User object
            verification_token: Secure verification token

        Returns:
            bool: True if email was sent successfully
        """
        if not user.email:
            logger.error(f"User {user.id} has no email address")
            return False

        try:
            verification_url = f"{self.settings.FRONTEND_URL}/auth/verify-email?token={verification_token}"

            # Use template if available, otherwise fall back to inline HTML
            try:
                template = self._template_env.get_template("verification.html")
                html_content = template.render(
                    user_name=user.username or user.email.split("@")[0],
                    user_email=user.email,
                    verification_link=verification_url,
                    verification_token=verification_token,
                    expiry_hours=self.settings.EMAIL_VERIFICATION_EXPIRE_HOURS,
                    company_name=self.settings.SMTP_FROM_NAME
                )
            except Exception as template_error:
                logger.warning(f"Template error, using fallback HTML: {template_error}")
                html_content = self._get_fallback_verification_html(user, verification_url, verification_token)

            return self._send_email(
                to_email=user.email,
                subject="🚀 Verify Your Email - KS Automation",
                html_content=html_content,
                username=user.username or user.email.split("@")[0]
            )

        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            return False

    def send_verification_success_email(self, user: User) -> bool:
        """
        Send welcome email after successful verification.

        Args:
            user: Verified user object

        Returns:
            bool: True if email was sent successfully
        """
        if not user.email:
            return False

        try:
            # Use template if available
            try:
                template = self._template_env.get_template("verification_success.html")
                html_content = template.render(
                    user_name=user.username or user.email.split("@")[0],
                    dashboard_url=f"{self.settings.FRONTEND_URL}/dashboard",
                    company_name=self.settings.SMTP_FROM_NAME
                )
            except Exception as template_error:
                logger.warning(f"Template error, using fallback HTML: {template_error}")
                html_content = self._get_fallback_success_html(user)

            return self._send_email(
                to_email=user.email,
                subject="🎉 Welcome to KS Automation - Email Verified!",
                html_content=html_content,
                username=user.username or user.email.split("@")[0]
            )

        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {e}")
            return False

    def _send_email(self, to_email: str, subject: str, html_content: str, username: str) -> bool:
        """Internal method to send email via Gmail API, SMTP, or log to console"""

        # Priority 1: Try Gmail API (works on cloud providers like Railway)
        if GMAIL_API_AVAILABLE:
            gmail_service = get_gmail_service()
            if gmail_service.is_configured():
                logger.info(f"Attempting to send email via Gmail API to {to_email}")
                result = gmail_service.send_email(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    from_name=self.settings.SMTP_FROM_NAME
                )
                if result:
                    return True
                logger.warning(f"Gmail API failed for {to_email}, trying SMTP fallback...")

        # Priority 2: Try SMTP (may be blocked on cloud providers)
        if self.settings.SMTP_HOST and self.settings.SMTP_USER:
            logger.info(f"Attempting to send email via SMTP to {to_email}")
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"{self.settings.SMTP_FROM_NAME} <{self.settings.SMTP_FROM_EMAIL}>"
                msg['To'] = to_email

                # Add HTML content
                msg.attach(MIMEText(html_content, 'html'))

                # Send email
                with smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT, timeout=30) as server:
                    server.starttls()
                    server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD.get_secret_value())
                    server.send_message(msg)

                logger.info(f"Email sent via SMTP to {to_email}: {subject}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP Authentication failed for {to_email}: {e}. Check SMTP_USER and SMTP_PASSWORD")
            except smtplib.SMTPConnectError as e:
                logger.error(f"SMTP Connection failed for {to_email}: {e}. Gmail may be blocking connections from this IP")
            except smtplib.SMTPException as e:
                logger.error(f"SMTP Error for {to_email}: {type(e).__name__}: {e}")
            except Exception as e:
                logger.error(f"Failed to send email via SMTP to {to_email}: {type(e).__name__}: {e}")

        # Priority 3: Dev mode - log to console
        if not self.settings.SMTP_HOST and not (GMAIL_API_AVAILABLE and get_gmail_service().is_configured()):
            self._log_email_to_console(to_email, subject, html_content)
            return True  # Return True in dev mode so the flow continues

        # All methods failed
        logger.error(f"All email methods failed for {to_email}")
        return False

    def _log_email_to_console(self, to_email: str, subject: str, html_content: str) -> None:
        """Log email to console when SMTP is not configured (development)"""
        logger.info(f"""
        ================== EMAIL (Development Mode) ==================
        To: {to_email}
        Subject: {subject}

        {html_content[:500]}...

        Note: Configure SMTP settings to send real emails
        ===============================================================
        """)

    def _get_fallback_verification_html(self, user: User, verification_url: str, verification_token: str = None) -> str:
        """Fallback verification email HTML if template fails"""
        username = user.username or user.email.split("@")[0]
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
        return f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4A90E2;">Verify Your Email</h2>
                <p>Hello {username},</p>
                <p>Please verify your email address by clicking the button below:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" style="background: #4A90E2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Verify Email</a>
                </p>
                {token_section}
                <p>This link will expire in {self.settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.</p>
                <p style="font-size: 12px; color: #666;">If you didn't create an account, please ignore this email.</p>
            </div>
        </body>
        </html>
        """

    def _get_fallback_success_html(self, user: User) -> str:
        """Fallback welcome email HTML if template fails"""
        username = user.username or user.email.split("@")[0]
        return f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #10b981;">Welcome to KS Automation!</h2>
                <p>Hello {username},</p>
                <p>Your email has been successfully verified! You now have full access to all features.</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{self.settings.FRONTEND_URL}/dashboard" style="background: #4A90E2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a>
                </p>
                <p>Thank you for choosing KS Automation!</p>
            </div>
        </body>
        </html>
        """

    def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """
        Send password reset email.

        Args:
            user: User object
            reset_token: Secure password reset token

        Returns:
            bool: True if email was sent successfully
        """
        if not user.email:
            logger.error(f"User {user.id} has no email address")
            return False

        try:
            reset_url = f"{self.settings.FRONTEND_URL}/reset-password?token={reset_token}"

            # Use template if available, otherwise fall back to inline HTML
            try:
                template = self._template_env.get_template("password_reset.html")
                html_content = template.render(
                    user_name=user.username or user.email.split("@")[0],
                    user_email=user.email,
                    reset_link=reset_url,
                    reset_token=reset_token,
                    expiry_hours=1,  # Password reset expires in 1 hour
                    company_name=self.settings.SMTP_FROM_NAME
                )
            except Exception as template_error:
                logger.warning(f"Template error, using fallback HTML: {template_error}")
                html_content = self._get_fallback_password_reset_html(user, reset_url, reset_token)

            return self._send_email(
                to_email=user.email,
                subject="🔐 Reset Your Password - KS Automation",
                html_content=html_content,
                username=user.username or user.email.split("@")[0]
            )

        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")
            return False

    def _get_fallback_password_reset_html(self, user: User, reset_url: str, reset_token: str = None) -> str:
        """Fallback password reset email HTML if template fails"""
        username = user.username or user.email.split("@")[0]
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
        return f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #ef4444;">Reset Your Password</h2>
                <p>Hello {username},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background: #ef4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Reset Password</a>
                </p>
                {token_section}
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p style="font-size: 12px; color: #666;">If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                <p style="font-size: 12px; color: #666; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                    For security reasons, this link can only be used once.
                </p>
            </div>
        </body>
        </html>
        """

    def is_configured(self) -> bool:
        """Check if email service is properly configured (Gmail API or SMTP)"""
        # Check Gmail API first
        if GMAIL_API_AVAILABLE:
            gmail_service = get_gmail_service()
            if gmail_service.is_configured():
                return True
        # Fall back to SMTP check
        return bool(self.settings.SMTP_HOST and self.settings.SMTP_USER)


# Keep backward compatibility for existing code
def send_verification_email(to_email: str, verification_url: str, username: str, verification_token: str = None) -> bool:
    """
    Send email verification email.

    Priority: Gmail API > SMTP > Dev mode (console logging)

    Args:
        to_email: Recipient email address
        verification_url: Full URL for email verification
        username: User's username for personalization
        verification_token: Raw token for manual entry (optional, extracted from URL if not provided)

    Returns:
        True if email sent successfully, False otherwise
    """
    # Extract token from URL if not provided
    if not verification_token and "token=" in verification_url:
        verification_token = verification_url.split("token=")[-1].split("&")[0]

    settings = get_settings()

    # Priority 1: Try Gmail API (works on cloud providers like Railway)
    if GMAIL_API_AVAILABLE:
        gmail_service = get_gmail_service()
        if gmail_service.is_configured():
            logger.info(f"Sending verification email via Gmail API to {to_email}")
            result = gmail_service.send_verification_email(
                to_email=to_email,
                verification_url=verification_url,
                username=username,
                verification_token=verification_token
            )
            if result:
                return True
            logger.warning(f"Gmail API failed for {to_email}, trying SMTP fallback...")

    # Priority 2: Try SMTP (may be blocked on cloud providers)
    if settings.SMTP_HOST and settings.SMTP_USER:
        logger.info(f"Sending verification email via SMTP to {to_email}")
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Verify Your Email Address - KS Automation'
            msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = to_email

            # Plain text version
            token_text = ""
            if verification_token:
                token_text = f"""
Or copy and paste this verification code:

{verification_token}

"""
            text_content = f"""
Hello {username},

Please verify your email address by clicking the link below:

{verification_url}

{token_text}This link will expire in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.

If you did not create an account, please ignore this email.

Best regards,
The {settings.SMTP_FROM_NAME} Team
"""

            # HTML version
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
        .link-box {{ background: #f3f4f6; padding: 12px; border-radius: 6px; font-size: 13px; word-break: break-all; color: #6b7280; margin-top: 20px; }}
        .footer {{ text-align: center; margin-top: 30px; color: #9ca3af; font-size: 12px; }}
        .expire-notice {{ background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 12px; margin: 20px 0; font-size: 14px; color: #92400e; }}
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

            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <div class="link-box">
                {verification_url}
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

            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            # Send email via SMTP
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD.get_secret_value())
                server.send_message(msg)

            logger.info(f"Verification email sent via SMTP to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed for {to_email}: {e}. Check SMTP_USER and SMTP_PASSWORD")
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP Connection failed for {to_email}: {e}. Gmail may block cloud provider IPs")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error for {to_email}: {type(e).__name__}: {e}")
        except Exception as e:
            logger.error(f"SMTP failed for {to_email}: {type(e).__name__}: {e}")

    # Priority 3: Dev mode - log to console
    gmail_configured = GMAIL_API_AVAILABLE and get_gmail_service().is_configured()
    smtp_configured = settings.SMTP_HOST and settings.SMTP_USER

    if not gmail_configured and not smtp_configured:
        logger.warning("No email service configured - using dev mode")
        print(f"\n{'='*60}")
        print(f"EMAIL VERIFICATION (Dev Mode)")
        print(f"{'='*60}")
        print(f"To: {to_email}")
        print(f"Username: {username}")
        print(f"Verification URL: {verification_url}")
        if verification_token:
            print(f"Token: {verification_token}")
        print(f"{'='*60}\n")
        return True  # Return True in dev mode

    # All configured methods failed
    logger.error(f"All email methods failed for {to_email}")
    return False
