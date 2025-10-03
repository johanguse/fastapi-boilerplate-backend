"""Email templates for invitations and verification."""

from typing import Dict


def get_email_verification_template(
    name: str, verification_link: str, language: str = 'en-US'
) -> Dict[str, str]:
    """Get email verification template."""
    templates = {
        'en-US': {
            'subject': 'Verify your email address',
            'html': f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Our Platform!</h1>
        </div>
        <div class="content">
            <h2>Hi {name},</h2>
            <p>Thank you for signing up! Please verify your email address to get started.</p>
            <p>Click the button below to verify your email:</p>
            <a href="{verification_link}" class="button">Verify Email Address</a>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #6b7280;">{verification_link}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, you can safely ignore this email.</p>
        </div>
        <div class="footer">
            <p>© 2025 Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """,
        },
        'es-ES': {
            'subject': 'Verifica tu dirección de email',
            'html': f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>¡Bienvenido a Nuestra Plataforma!</h1>
        </div>
        <div class="content">
            <h2>Hola {name},</h2>
            <p>¡Gracias por registrarte! Por favor verifica tu dirección de email para comenzar.</p>
            <p>Haz clic en el botón a continuación para verificar tu email:</p>
            <a href="{verification_link}" class="button">Verificar Email</a>
            <p>O copia y pega este enlace en tu navegador:</p>
            <p style="word-break: break-all; color: #6b7280;">{verification_link}</p>
            <p>Este enlace expirará en 24 horas.</p>
            <p>Si no creaste una cuenta, puedes ignorar este email.</p>
        </div>
        <div class="footer">
            <p>© 2025 Tu Empresa. Todos los derechos reservados.</p>
        </div>
    </div>
</body>
</html>
            """,
        },
    }
    
    return templates.get(language, templates['en-US'])


def get_team_invitation_template(
    invited_by_name: str,
    organization_name: str,
    invitation_link: str,
    role: str,
    message: str = None,
    language: str = 'en-US',
) -> Dict[str, str]:
    """Get team invitation email template."""
    templates = {
        'en-US': {
            'subject': f'You\'re invited to join {organization_name}',
            'html': f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .info-box {{ background: white; padding: 15px; border-left: 4px solid #4F46E5; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Team Invitation</h1>
        </div>
        <div class="content">
            <h2>You've been invited!</h2>
            <p><strong>{invited_by_name}</strong> has invited you to join <strong>{organization_name}</strong> as a <strong>{role}</strong>.</p>
            {f'<div class="info-box"><p><em>{message}</em></p></div>' if message else ''}
            <p>Click the button below to accept the invitation:</p>
            <a href="{invitation_link}" class="button">Accept Invitation</a>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #6b7280;">{invitation_link}</p>
            <p>This invitation will expire in 7 days.</p>
            <p>If you don't want to join this team, you can safely ignore this email.</p>
        </div>
        <div class="footer">
            <p>© 2025 Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """,
        },
        'es-ES': {
            'subject': f'Estás invitado a unirte a {organization_name}',
            'html': f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .info-box {{ background: white; padding: 15px; border-left: 4px solid #4F46E5; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Invitación al Equipo</h1>
        </div>
        <div class="content">
            <h2>¡Has sido invitado!</h2>
            <p><strong>{invited_by_name}</strong> te ha invitado a unirte a <strong>{organization_name}</strong> como <strong>{role}</strong>.</p>
            {f'<div class="info-box"><p><em>{message}</em></p></div>' if message else ''}
            <p>Haz clic en el botón a continuación para aceptar la invitación:</p>
            <a href="{invitation_link}" class="button">Aceptar Invitación</a>
            <p>O copia y pega este enlace en tu navegador:</p>
            <p style="word-break: break-all; color: #6b7280;">{invitation_link}</p>
            <p>Esta invitación expirará en 7 días.</p>
            <p>Si no quieres unirte a este equipo, puedes ignorar este email.</p>
        </div>
        <div class="footer">
            <p>© 2025 Tu Empresa. Todos los derechos reservados.</p>
        </div>
    </div>
</body>
</html>
            """,
        },
    }
    
    return templates.get(language, templates['en-US'])


def get_password_reset_template(
    name: str, reset_link: str, language: str = 'en-US'
) -> Dict[str, str]:
    """Get password reset email template."""
    templates = {
        'en-US': {
            'subject': 'Reset your password',
            'html': f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .warning {{ background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset</h1>
        </div>
        <div class="content">
            <h2>Hi {name},</h2>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <a href="{reset_link}" class="button">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #6b7280;">{reset_link}</p>
            <div class="warning">
                <p><strong>Security Notice:</strong> This link will expire in 1 hour. If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
            </div>
        </div>
        <div class="footer">
            <p>© 2025 Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """,
        },
    }
    
    return templates.get(language, templates['en-US'])

