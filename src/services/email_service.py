"""
Email service using Resend for sending verification and password reset emails.
"""

import os
from typing import Optional

import resend
from loguru import logger


class EmailService:
    """Service for sending emails via Resend API."""

    def __init__(self):
        """Initialize Resend with API key from environment."""
        api_key = os.getenv('RESEND_API_KEY')
        if not api_key:
            logger.warning('RESEND_API_KEY not found in environment variables')
            self.api_key = None
        else:
            # Set the API key for the resend module
            resend.api_key = api_key
            self.api_key = api_key

        self.from_email = os.getenv(
            'RESEND_FROM_EMAIL', 'onboarding@resend.dev'
        )
        self.app_name = os.getenv('APP_NAME', 'Your App')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    async def send_verification_email(
        self, email: str, token: str, name: Optional[str] = None
    ) -> bool:
        """
        Send email verification email to user.

        Args:
            email: User's email address
            token: Verification token
            name: User's name (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.api_key:
            logger.error('Resend API key not found - check RESEND_API_KEY')
            return False

        verification_link = f'{self.frontend_url}/verify-email?token={token}'
        display_name = name if name else email.split('@', maxsplit=1)[0]

        try:
            params = {
                'from': self.from_email,
                'to': [email],
                'subject': f'Verify your {self.app_name} account',
                'html': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Welcome to {self.app_name}! 👋</h2>
                    <p>Hi {display_name},</p>
                    <p>Thanks for signing up! Please click the button below to verify your email address:</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}"
                           style="background-color: #007bff; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Verify Email Address
                        </a>
                    </div>

                    <p>Or copy and paste this link into your browser:</p>
                    <p style="background-color: #f8f9fa; padding: 10px; border-radius: 3px; word-break: break-all;">
                        {verification_link}
                    </p>

                    <p>This link will expire in 24 hours.</p>

                    <hr style="border: 1px solid #e9ecef; margin: 30px 0;">
                    <p style="color: #6c757d; font-size: 14px;">
                        If you didn't create an account, you can safely ignore this email.
                    </p>
                </div>
                """,
            }

            response = resend.emails.send(params)
            logger.info(
                f'Verification email sent to {email}, ID: {response.get("id")}'
            )
            return True

        except Exception as e:
            logger.error(
                f'Failed to send verification email to {email}: {str(e)}'
            )
            return False

    async def send_forgot_password_email(
        self, email: str, token: str, name: Optional[str] = None
    ) -> bool:
        """
        Send password reset email to user.

        Args:
            email: User's email address
            token: Password reset token
            name: User's name (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.api_key:
            logger.error('Resend API key not found - check RESEND_API_KEY')
            return False

        reset_link = f'{self.frontend_url}/reset-password?token={token}'
        display_name = name if name else email.split('@', maxsplit=1)[0]

        try:
            params = {
                'from': self.from_email,
                'to': [email],
                'subject': f'Reset your {self.app_name} password',
                'html': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Password Reset Request 🔒</h2>
                    <p>Hi {display_name},</p>
                    <p>We received a request to reset your password for your {self.app_name} account.</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}"
                           style="background-color: #dc3545; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>

                    <p>Or copy and paste this link into your browser:</p>
                    <p style="background-color: #f8f9fa; padding: 10px; border-radius: 3px; word-break: break-all;">
                        {reset_link}
                    </p>

                    <p>This link will expire in 1 hour for security reasons.</p>

                    <hr style="border: 1px solid #e9ecef; margin: 30px 0;">
                    <p style="color: #6c757d; font-size: 14px;">
                        If you didn't request this password reset, you can safely ignore this email.
                        Your password will not be changed.
                    </p>
                </div>
                """,
            }

            response = resend.emails.send(params)
            logger.info(
                f'Password reset email sent to {email}, ID: {response.get("id")}'
            )
            return True

        except Exception as e:
            logger.error(
                f'Failed to send password reset email to {email}: {str(e)}'
            )
            return False

    async def send_welcome_email(
        self, email: str, name: Optional[str] = None
    ) -> bool:
        """
        Send welcome email after successful verification.

        Args:
            email: User's email address
            name: User's name (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.api_key:
            logger.error('Resend API key not found - check RESEND_API_KEY')
            return False

        display_name = name if name else email.split('@', maxsplit=1)[0]
        dashboard_link = f'{self.frontend_url}/dashboard'

        try:
            params = {
                'from': self.from_email,
                'to': [email],
                'subject': f'Welcome to {self.app_name}! 🎉',
                'html': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Welcome to {self.app_name}! 🎉</h2>
                    <p>Hi {display_name},</p>
                    <p>Your account has been successfully verified! You're now ready to get started.</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{dashboard_link}"
                           style="background-color: #28a745; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Go to Dashboard
                        </a>
                    </div>

                    <p>Here's what you can do next:</p>
                    <ul>
                        <li>Complete your profile</li>
                        <li>Create your first organization</li>
                        <li>Invite team members</li>
                        <li>Explore all features</li>
                    </ul>

                    <hr style="border: 1px solid #e9ecef; margin: 30px 0;">
                    <p style="color: #6c757d; font-size: 14px;">
                        Need help? Reply to this email and we'll be happy to assist you!
                    </p>
                </div>
                """,
            }

            response = resend.emails.send(params)
            logger.info(
                f'Welcome email sent to {email}, ID: {response.get("id")}'
            )
            return True

        except Exception as e:
            logger.error(f'Failed to send welcome email to {email}: {str(e)}')
            return False


# Global instance
email_service = EmailService()
