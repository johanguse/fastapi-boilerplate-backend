"""
Email service using Resend for sending verification and password reset emails.
"""

from typing import Optional

import resend
from loguru import logger

from src.common.config import settings


class EmailService:
    """Service for sending emails via Resend API."""

    def __init__(self):
        """Initialize Resend with API key from environment."""
        api_key = settings.RESEND_API_KEY
        if not api_key:
            logger.error('RESEND_API_KEY not found in environment variables - email functionality will not work')
            self.api_key = None
        else:
            # Set the API key for the resend module
            resend.api_key = api_key
            self.api_key = api_key
            logger.info('Resend API key configured successfully')

        self.from_email = settings.RESEND_FROM_EMAIL or 'onboarding@resend.dev'
        self.app_name = settings.PROJECT_NAME or 'Your App'
        self.frontend_url = settings.FRONTEND_URL or 'http://localhost:5173'

        # Validate configuration
        self._validate_configuration()

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
            logger.error(f'Resend API key not found - check RESEND_API_KEY. Cannot send verification email to {email}')
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

            response = resend.Emails.send(params)
            logger.info(
                f'Verification email sent to {email}, ID: {response.get("id")}'
            )
            return True

        except Exception as e:
            logger.exception(
                f'Failed to send verification email to {email}: {str(e)}. Response: {response if "response" in locals() else "No response"}'
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
            logger.error(f'Resend API key not found - check RESEND_API_KEY. Cannot send password reset email to {email}')
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

            response = resend.Emails.send(params)
            logger.info(
                f'Password reset email sent to {email}, ID: {response.get("id")}'
            )
            return True

        except Exception as e:
            logger.exception(
                f'Failed to send password reset email to {email}: {str(e)}. Response: {response if "response" in locals() else "No response"}'
            )
            return False

    async def send_welcome_email(
        self, email: str, name: Optional[str] = None, is_onboarding: bool = False
    ) -> bool:
        """
        Send welcome email after successful verification or onboarding completion.

        Args:
            email: User's email address
            name: User's name (optional)
            is_onboarding: If True, send onboarding completion welcome email

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.api_key:
            logger.error(f'Resend API key not found - check RESEND_API_KEY. Cannot send welcome email to {email}')
            return False

        display_name = name if name else email.split('@', maxsplit=1)[0]
        dashboard_link = f'{self.frontend_url}'

        # Different subject and content for onboarding completion
        if is_onboarding:
            subject = 'Welcome to AI Project Management! 🎉'
            heading = 'Welcome to AI Project Management! 🎉'
            main_message = 'Congratulations! Your onboarding is complete and your workspace is ready. You can now start collaborating with your team and exploring all the features we have to offer.'
            next_steps = [
                'Explore your dashboard',
                'Invite team members',
                'Create your first project',
                'Explore AI-powered features',
            ]
        else:
            subject = f'Welcome to {self.app_name}! 🎉'
            heading = f'Welcome to {self.app_name}! 🎉'
            main_message = 'Your account has been successfully verified! You\'re now ready to get started.'
            next_steps = [
                'Complete your profile',
                'Create your first organization',
                'Invite team members',
                'Explore all features',
            ]

        try:
            params = {
                'from': self.from_email,
                'to': [email],
                'subject': subject,
                'html': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>{heading}</h2>
                    <p>Hi {display_name},</p>
                    <p>{main_message}</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{dashboard_link}"
                           style="background-color: #28a745; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Go to Dashboard
                        </a>
                    </div>

                    <p>Here's what you can do next:</p>
                    <ul>
                        {''.join([f'<li>{step}</li>' for step in next_steps])}
                    </ul>

                    <hr style="border: 1px solid #e9ecef; margin: 30px 0;">
                    <p style="color: #6c757d; font-size: 14px;">
                        Need help? Reply to this email and we'll be happy to assist you!
                    </p>
                </div>
                """,
            }

            response = resend.Emails.send(params)
            logger.info(
                f'Welcome email sent to {email}, ID: {response.get("id")}'
            )
            return True

        except Exception as e:
            logger.exception(
                f'Failed to send welcome email to {email}: {str(e)}. Response: {response if "response" in locals() else "No response"}'
            )
            return False

    async def send_otp_email(
        self, email: str, otp_code: str, name: Optional[str] = None
    ) -> bool:
        """
        Send OTP code email to user.

        Args:
            email: User's email address
            otp_code: 6-digit OTP code
            name: User's name (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.api_key:
            logger.warning('Cannot send OTP email: RESEND_API_KEY not configured')
            return False

        try:
            display_name = name or email.split('@', maxsplit=1)[0]

            # Use from_email as-is if it already contains a name format, otherwise add app_name
            if '<' in self.from_email and '>' in self.from_email:
                from_address = self.from_email
            else:
                from_address = f'{self.app_name} <{self.from_email}>'

            params = {
                'from': from_address,
                'to': [email],
                'subject': f'Your {self.app_name} verification code',
                'html': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #333; margin: 0;">{self.app_name}</h1>
                    </div>

                    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px; margin-bottom: 20px;">
                        <h2 style="color: #333; margin-top: 0;">Your verification code</h2>
                        <p>Hi {display_name},</p>
                        <p>Use this code to complete your registration or login:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <div style="background-color: #007bff; color: white; padding: 20px; 
                                        border-radius: 10px; font-size: 32px; font-weight: bold; 
                                        letter-spacing: 5px; display: inline-block;">
                                {otp_code}
                            </div>
                        </div>
                        
                        <p><strong>This code expires in 15 minutes.</strong></p>
                        <p>If you didn't request this code, you can safely ignore this email.</p>
                    </div>

                    <div style="background-color: #e9ecef; padding: 20px; border-radius: 5px;">
                        <h3 style="color: #495057; margin-top: 0;">Security Tips:</h3>
                        <ul style="color: #6c757d;">
                            <li>Never share this code with anyone</li>
                            <li>Our team will never ask for your verification code</li>
                            <li>If you suspect unauthorized access, contact us immediately</li>
                        </ul>
                    </div>

                    <hr style="border: 1px solid #e9ecef; margin: 30px 0;">
                    <p style="color: #6c757d; font-size: 14px; text-align: center;">
                        This is an automated message. Please do not reply to this email.
                    </p>
                </div>
                """,
            }

            response = resend.Emails.send(params)
            logger.info(
                f'OTP email sent to {email}, ID: {response.get("id")}'
            )
            return True

        except Exception as e:
            logger.exception(
                f'Failed to send OTP email to {email}: {str(e)}. Response: {response if "response" in locals() else "No response"}'
            )
            return False

    def _validate_configuration(self) -> None:
        """Validate Resend configuration and log warnings/errors."""
        if not self.api_key:
            logger.error('Email service disabled: RESEND_API_KEY not configured')
            return

        if not self.from_email or self.from_email == 'onboarding@resend.dev':
            logger.warning(
                f'Using default FROM_EMAIL: {self.from_email}. Consider setting RESEND_FROM_EMAIL to your domain.'
            )
        else:
            logger.info(f'FROM_EMAIL configured: {self.from_email}')

        logger.info(f'Email service initialized with APP_NAME: {self.app_name}, FRONTEND_URL: {self.frontend_url}')


# Global instance
email_service = EmailService()
