"""Email service for sending invitations and verification emails."""

import logging
from typing import Optional

from fastapi import BackgroundTasks

from src.common.config import settings
from src.invitations.email_templates import (
    get_email_verification_template,
    get_password_reset_template,
    get_team_invitation_template,
)

logger = logging.getLogger(__name__)


async def send_email_verification(
    email: str,
    name: str,
    verification_link: str,
    language: str = 'en-US',
    background_tasks: Optional[BackgroundTasks] = None,
):
    """Send email verification email."""
    template = get_email_verification_template(name, verification_link, language)
    
    def send():
        try:
            # Import here to avoid issues if resend not configured
            import resend
            resend.api_key = settings.RESEND_API_KEY
            
            resend.Emails.send({
                'from': settings.FROM_EMAIL,
                'to': email,
                'subject': template['subject'],
                'html': template['html'],
            })
            logger.info(f'Email verification sent to {email}')
        except Exception as e:
            logger.error(f'Failed to send verification email to {email}: {str(e)}')
    
    if background_tasks:
        background_tasks.add_task(send)
    else:
        send()


async def send_team_invitation(
    email: str,
    invited_by_name: str,
    organization_name: str,
    invitation_link: str,
    role: str,
    message: Optional[str] = None,
    language: str = 'en-US',
    background_tasks: Optional[BackgroundTasks] = None,
):
    """Send team invitation email."""
    template = get_team_invitation_template(
        invited_by_name, organization_name, invitation_link, role, message, language
    )
    
    def send():
        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY
            
            resend.Emails.send({
                'from': settings.FROM_EMAIL,
                'to': email,
                'subject': template['subject'],
                'html': template['html'],
            })
            logger.info(f'Team invitation sent to {email}')
        except Exception as e:
            logger.error(f'Failed to send invitation to {email}: {str(e)}')
    
    if background_tasks:
        background_tasks.add_task(send)
    else:
        send()


async def send_password_reset(
    email: str,
    name: str,
    reset_link: str,
    language: str = 'en-US',
    background_tasks: Optional[BackgroundTasks] = None,
):
    """Send password reset email."""
    template = get_password_reset_template(name, reset_link, language)
    
    def send():
        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY
            
            resend.Emails.send({
                'from': settings.FROM_EMAIL,
                'to': email,
                'subject': template['subject'],
                'html': template['html'],
            })
            logger.info(f'Password reset email sent to {email}')
        except Exception as e:
            logger.error(f'Failed to send password reset to {email}: {str(e)}')
    
    if background_tasks:
        background_tasks.add_task(send)
    else:
        send()

