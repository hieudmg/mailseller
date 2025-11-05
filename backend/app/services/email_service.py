import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS

    def _create_message(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> MIMEMultipart:
        """Create email message with text and optional HTML body"""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email

        # Add text version
        text_part = MIMEText(body_text, "plain", "utf-8")
        message.attach(text_part)

        # Add HTML version if provided
        if body_html:
            html_part = MIMEText(body_html, "html", "utf-8")
            message.attach(html_part)

        return message

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SMTP

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.smtp_user or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False

        try:
            message = self._create_message(to_email, subject, body_text, body_html)

            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                # Login
                server.login(self.smtp_user, self.smtp_password)

                # Send email
                server.send_message(message)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(f"SMTP authentication failed for user {self.smtp_user}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> dict[str, List[str]]:
        """
        Send email to multiple recipients

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body

        Returns:
            dict: {"success": [...], "failed": [...]}
        """
        results = {"success": [], "failed": []}

        for email in recipients:
            if self.send_email(email, subject, body_text, body_html):
                results["success"].append(email)
            else:
                results["failed"].append(email)

        return results

    # Pre-defined email templates
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email to new user"""
        subject = f"Welcome to {settings.PROJECT_NAME}!"

        body_text = f"""
Hello {username},

Welcome to {settings.PROJECT_NAME}! We're excited to have you on board.

Your account has been successfully created. You can now log in and start using our services.

If you have any questions or need assistance, please don't hesitate to contact us.

Best regards,
The {settings.PROJECT_NAME} Team
        """.strip()

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #4a5568;">Hello {username},</h2>

        <p>Welcome to <strong>{settings.PROJECT_NAME}</strong>! We're excited to have you on board.</p>

        <p>Your account has been successfully created. You can now log in and start using our services.</p>

        <p>If you have any questions or need assistance, please don't hesitate to contact us.</p>

        <p style="margin-top: 30px;">
            Best regards,<br>
            The {settings.PROJECT_NAME} Team
        </p>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(to_email, subject, body_text, body_html)

    def send_password_reset_email(
        self, to_email: str, reset_token: str, reset_url: Optional[str] = None
    ) -> bool:
        """Send password reset email"""
        if not reset_url:
            reset_url = f"{settings.APP_URL}/auth/reset-password?token={reset_token}"

        subject = "Password Reset Request"

        body_text = f"""
Hello,

We received a request to reset your password for your {settings.PROJECT_NAME} account.

To reset your password, please click the following link or copy it into your browser:
{reset_url}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email.

Best regards,
The {settings.PROJECT_NAME} Team
        """.strip()

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #4a5568;">Password Reset Request</h2>

        <p>We received a request to reset your password for your {settings.PROJECT_NAME} account.</p>

        <p>To reset your password, please click the button below:</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background-color: #4299e1; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Reset Password
            </a>
        </div>

        <p style="font-size: 14px; color: #718096;">
            Or copy and paste this link into your browser:<br>
            <a href="{reset_url}" style="color: #4299e1;">{reset_url}</a>
        </p>

        <p style="font-size: 14px; color: #718096;">
            This link will expire in 1 hour.
        </p>

        <p style="font-size: 14px; color: #718096;">
            If you did not request a password reset, please ignore this email.
        </p>

        <p style="margin-top: 30px;">
            Best regards,<br>
            The {settings.PROJECT_NAME} Team
        </p>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(to_email, subject, body_text, body_html)

    def send_purchase_confirmation_email(
        self, to_email: str, username: str, data_type: str, quantity: int, cost: float
    ) -> bool:
        """Send purchase confirmation email"""
        subject = "Purchase Confirmation"

        body_text = f"""
Hello {username},

Thank you for your purchase!

Purchase Details:
- Type: {data_type}
- Quantity: {quantity} items
- Total Cost: ${cost:.2f}

The items have been added to your account.

Best regards,
The {settings.PROJECT_NAME} Team
        """.strip()

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #4a5568;">Purchase Confirmation</h2>

        <p>Hello {username},</p>

        <p>Thank you for your purchase!</p>

        <div style="background-color: #f7fafc; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0;">Purchase Details</h3>
            <table style="width: 100%;">
                <tr>
                    <td style="padding: 5px 0;"><strong>Type:</strong></td>
                    <td style="padding: 5px 0;">{data_type}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>Quantity:</strong></td>
                    <td style="padding: 5px 0;">{quantity} items</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>Total Cost:</strong></td>
                    <td style="padding: 5px 0;">${cost:.2f}</td>
                </tr>
            </table>
        </div>

        <p>The items have been added to your account.</p>

        <p style="margin-top: 30px;">
            Best regards,<br>
            The {settings.PROJECT_NAME} Team
        </p>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(to_email, subject, body_text, body_html)

    def send_credit_added_email(
        self, to_email: str, username: str, amount: float, description: str
    ) -> bool:
        """Send email notification when credits are added"""
        subject = "Credits Added to Your Account"

        body_text = f"""
Hello {username},

Credits have been added to your account!

Amount: ${amount:.2f}
Reason: {description}

Your updated balance is now available in your dashboard.

Best regards,
The {settings.PROJECT_NAME} Team
        """.strip()

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #4a5568;">Credits Added to Your Account</h2>

        <p>Hello {username},</p>

        <p>Credits have been added to your account!</p>

        <div style="background-color: #f0fff4; padding: 20px; border-radius: 5px;
                    margin: 20px 0; border-left: 4px solid #48bb78;">
            <p style="margin: 0; font-size: 18px;">
                <strong>Amount:</strong> <span style="color: #48bb78;">${amount:.2f}</span>
            </p>
            <p style="margin: 10px 0 0 0;">
                <strong>Reason:</strong> {description}
            </p>
        </div>

        <p>Your updated balance is now available in your dashboard.</p>

        <p style="margin-top: 30px;">
            Best regards,<br>
            The {settings.PROJECT_NAME} Team
        </p>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(to_email, subject, body_text, body_html)

    def send_payment_confirmation_email(
        self, to_email: str, username: str, amount: float, payment_method: str
    ) -> bool:
        """Send payment confirmation email"""
        subject = "Payment Received"

        body_text = f"""
Hello {username},

We have received your payment!

Payment Details:
- Amount: ${amount:.2f}
- Method: {payment_method}

Your credits have been added to your account and are ready to use.

Thank you for your purchase!

Best regards,
The {settings.PROJECT_NAME} Team
        """.strip()

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #4a5568;">Payment Received</h2>

        <p>Hello {username},</p>

        <p>We have received your payment!</p>

        <div style="background-color: #f7fafc; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0;">Payment Details</h3>
            <table style="width: 100%;">
                <tr>
                    <td style="padding: 5px 0;"><strong>Amount:</strong></td>
                    <td style="padding: 5px 0;">${amount:.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>Method:</strong></td>
                    <td style="padding: 5px 0;">{payment_method}</td>
                </tr>
            </table>
        </div>

        <p>Your credits have been added to your account and are ready to use.</p>

        <p>Thank you for your purchase!</p>

        <p style="margin-top: 30px;">
            Best regards,<br>
            The {settings.PROJECT_NAME} Team
        </p>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(to_email, subject, body_text, body_html)


# Singleton instance
email_service = EmailService()
