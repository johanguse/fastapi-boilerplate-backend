import os

import resend

from app.core.config import settings

resend.api_key = os.environ['RESEND_API_KEY']


def send_invitation_email(to_email: str, team_name: str, frontend_url: str):
    subject = f'Invitation to join {team_name} on Our Platform'
    body = f"""
    Hello,

    You have been invited to join the team {team_name} on Our Platform.
    To accept this invitation, please click on the following link:

    {frontend_url}/accept-invitation?email={to_email}&team={team_name}

    If you did not expect this invitation, please ignore this email.

    Best regards,
    Our Platform Team
    """

    try:
        params = {
            'from': settings.RESEND_FROM_EMAIL,
            'to': to_email,
            'subject': subject,
            'html': body,
        }

        email = resend.emails.send(params)
        print(
            f'Invitation email sent successfully to {to_email}. Email ID: {email.id}'
        )
    except Exception as e:
        print(f'Failed to send invitation email: {str(e)}')
