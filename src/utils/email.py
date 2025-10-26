import logging
from typing import Optional

import resend

from src.common.config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: Optional[str] = None,
) -> bool:
    """
    Send an email using Resend
    """
    if not settings.RESEND_API_KEY:
        logger.error(f'Cannot send email to {to_email} - RESEND_API_KEY not configured')
        return False

    try:
        params = {
            'from': from_email or settings.RESEND_FROM_EMAIL,
            'to': to_email,
            'subject': subject,
            'html': html_content,
        }

        response = resend.Emails.send(params)
        logger.info(
            f'Email sent successfully to {to_email}. ID: {response.get("id")}'
        )
        return True
    except Exception as e:
        logger.exception(f'Failed to send email to {to_email}: {str(e)}. Response: {response if "response" in locals() else "No response"}')
        return False


async def send_invitation_email(
    to_email: str,
    team_name: str,
    invited_by_email: str,
    frontend_url: Optional[str] = None,
) -> bool:
    """
    Send a team invitation email
    """
    subject = f'Invitation to join {team_name}'

    invite_url = (frontend_url or settings.FRONTEND_URL) + '/accept-invitation'

    html_content = f"""
    <h2>Team Invitation</h2>
    <p>Hello,</p>
    <p>You have been invited by {invited_by_email} to join the team "{team_name}".</p>
    <p>To accept this invitation, please click the link below:</p>
    <p><a href="{invite_url}?email={to_email}&team={team_name}">Accept Invitation</a></p>
    <p>If you did not expect this invitation, you can safely ignore this email.</p>
    <br>
    <p>Best regards,<br>{settings.PROJECT_NAME} Team</p>
    """

    return await send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )


async def send_welcome_email(
    to_email: str, user_name: Optional[str] = None
) -> bool:
    """
    Send a welcome email to new users
    """
    subject = f'Welcome to {settings.PROJECT_NAME}'

    html_content = f"""
    <h2>Welcome to {settings.PROJECT_NAME}!</h2>
    <p>Hello{f' {user_name}' if user_name else ''},</p>
    <p>Thank you for joining {settings.PROJECT_NAME}. We're excited to have you on board!</p>
    <p>To get started, you can:</p>
    <ul>
        <li>Create your first project</li>
        <li>Invite team members</li>
        <li>Upload training data</li>
    </ul>
    <p>If you have any questions, feel free to reach out to our support team.</p>
    <br>
    <p>Best regards,<br>{settings.PROJECT_NAME} Team</p>
    """

    return await send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )
