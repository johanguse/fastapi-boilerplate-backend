"""
Internationalization module for the backend API.
Provides translation support for error messages and API responses.
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from babel import Locale
from babel.core import UnknownLocaleError


class I18nManager:
    """Manages internationalization for the backend API."""
    
    SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'pt']
    DEFAULT_LANGUAGE = 'en'
    
    def __init__(self):
        """Initialize the I18n manager and load translation files."""
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files from the locales directory."""
        # Get the directory where this file is located
        current_dir = Path(__file__).parent
        locales_dir = current_dir / 'locales'
        
        for lang_code in self.SUPPORTED_LANGUAGES:
            locale_file = locales_dir / f'{lang_code}.json'
            if locale_file.exists():
                try:
                    with open(locale_file, 'r', encoding='utf-8') as f:
                        self._translations[lang_code] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Could not load translations for {lang_code}: {e}")
                    # Fallback to empty dict if file can't be loaded
                    self._translations[lang_code] = {}
            else:
                print(f"Warning: Translation file not found for {lang_code}")
                self._translations[lang_code] = {}
        'en': {
            # Authentication errors
            'auth.invalid_credentials': 'Invalid email or password',
            'auth.user_not_found': 'User not found',
            'auth.email_already_exists': 'Email already exists',
            'auth.account_disabled': 'Account is disabled',
            'auth.token_expired': 'Token has expired',
            'auth.invalid_token': 'Invalid token',
            'auth.insufficient_permissions': 'Insufficient permissions',
            'auth.password_too_weak': 'Password is too weak',
            'auth.email_not_verified': 'Email address is not verified',
            
            # Validation errors
            'validation.required_field': 'This field is required',
            'validation.invalid_email': 'Invalid email format',
            'validation.min_length': 'Must be at least {min_length} characters',
            'validation.max_length': 'Must be no more than {max_length} characters',
            'validation.invalid_format': 'Invalid format',
            
            # Organization errors
            'organization.not_found': 'Organization not found',
            'organization.access_denied': 'Access denied to organization',
            'organization.name_exists': 'Organization name already exists',
            'organization.member_not_found': 'Member not found',
            'organization.cannot_remove_owner': 'Cannot remove organization owner',
            
            # Project errors
            'project.not_found': 'Project not found',
            'project.access_denied': 'Access denied to project',
            'project.name_exists': 'Project name already exists',
            
            # Payment errors
            'payment.card_declined': 'Your card was declined',
            'payment.insufficient_funds': 'Insufficient funds',
            'payment.invalid_payment_method': 'Invalid payment method',
            'payment.subscription_not_found': 'Subscription not found',
            'payment.plan_not_found': 'Plan not found',
            
            # Generic errors
            'error.internal_server': 'Internal server error',
            'error.not_found': 'Resource not found',
            'error.bad_request': 'Bad request',
            'error.forbidden': 'Forbidden',
            'error.rate_limit': 'Rate limit exceeded',
            
            # Success messages
            'success.created': 'Successfully created',
            'success.updated': 'Successfully updated',
            'success.deleted': 'Successfully deleted',
            'success.email_sent': 'Email sent successfully',
        },
        'es': {
            # Authentication errors
            'auth.invalid_credentials': 'Email o contraseña inválidos',
            'auth.user_not_found': 'Usuario no encontrado',
            'auth.email_already_exists': 'El email ya existe',
            'auth.account_disabled': 'La cuenta está deshabilitada',
            'auth.token_expired': 'El token ha expirado',
            'auth.invalid_token': 'Token inválido',
            'auth.insufficient_permissions': 'Permisos insuficientes',
            'auth.password_too_weak': 'La contraseña es muy débil',
            'auth.email_not_verified': 'La dirección de email no está verificada',
            
            # Validation errors
            'validation.required_field': 'Este campo es obligatorio',
            'validation.invalid_email': 'Formato de email inválido',
            'validation.min_length': 'Debe tener al menos {min_length} caracteres',
            'validation.max_length': 'No debe tener más de {max_length} caracteres',
            'validation.invalid_format': 'Formato inválido',
            
            # Organization errors
            'organization.not_found': 'Organización no encontrada',
            'organization.access_denied': 'Acceso denegado a la organización',
            'organization.name_exists': 'El nombre de la organización ya existe',
            'organization.member_not_found': 'Miembro no encontrado',
            'organization.cannot_remove_owner': 'No se puede eliminar al propietario de la organización',
            
            # Project errors
            'project.not_found': 'Proyecto no encontrado',
            'project.access_denied': 'Acceso denegado al proyecto',
            'project.name_exists': 'El nombre del proyecto ya existe',
            
            # Payment errors
            'payment.card_declined': 'Su tarjeta fue rechazada',
            'payment.insufficient_funds': 'Fondos insuficientes',
            'payment.invalid_payment_method': 'Método de pago inválido',
            'payment.subscription_not_found': 'Suscripción no encontrada',
            'payment.plan_not_found': 'Plan no encontrado',
            
            # Generic errors
            'error.internal_server': 'Error interno del servidor',
            'error.not_found': 'Recurso no encontrado',
            'error.bad_request': 'Solicitud incorrecta',
            'error.forbidden': 'Prohibido',
            'error.rate_limit': 'Límite de velocidad excedido',
            
            # Success messages
            'success.created': 'Creado exitosamente',
            'success.updated': 'Actualizado exitosamente',
            'success.deleted': 'Eliminado exitosamente',
            'success.email_sent': 'Email enviado exitosamente',
        },
        'fr': {
            # Authentication errors
            'auth.invalid_credentials': 'Email ou mot de passe invalide',
            'auth.user_not_found': 'Utilisateur non trouvé',
            'auth.email_already_exists': 'L\'email existe déjà',
            'auth.account_disabled': 'Le compte est désactivé',
            'auth.token_expired': 'Le token a expiré',
            'auth.invalid_token': 'Token invalide',
            'auth.insufficient_permissions': 'Permissions insuffisantes',
            'auth.password_too_weak': 'Le mot de passe est trop faible',
            'auth.email_not_verified': 'L\'adresse email n\'est pas vérifiée',
            
            # Validation errors
            'validation.required_field': 'Ce champ est obligatoire',
            'validation.invalid_email': 'Format d\'email invalide',
            'validation.min_length': 'Doit contenir au moins {min_length} caractères',
            'validation.max_length': 'Ne doit pas dépasser {max_length} caractères',
            'validation.invalid_format': 'Format invalide',
            
            # Organization errors
            'organization.not_found': 'Organisation non trouvée',
            'organization.access_denied': 'Accès refusé à l\'organisation',
            'organization.name_exists': 'Le nom de l\'organisation existe déjà',
            'organization.member_not_found': 'Membre non trouvé',
            'organization.cannot_remove_owner': 'Impossible de supprimer le propriétaire de l\'organisation',
            
            # Project errors
            'project.not_found': 'Projet non trouvé',
            'project.access_denied': 'Accès refusé au projet',
            'project.name_exists': 'Le nom du projet existe déjà',
            
            # Payment errors
            'payment.card_declined': 'Votre carte a été refusée',
            'payment.insufficient_funds': 'Fonds insuffisants',
            'payment.invalid_payment_method': 'Méthode de paiement invalide',
            'payment.subscription_not_found': 'Abonnement non trouvé',
            'payment.plan_not_found': 'Plan non trouvé',
            
            # Generic errors
            'error.internal_server': 'Erreur interne du serveur',
            'error.not_found': 'Ressource non trouvée',
            'error.bad_request': 'Requête incorrecte',
            'error.forbidden': 'Interdit',
            'error.rate_limit': 'Limite de débit dépassée',
            
            # Success messages
            'success.created': 'Créé avec succès',
            'success.updated': 'Mis à jour avec succès',
            'success.deleted': 'Supprimé avec succès',
            'success.email_sent': 'Email envoyé avec succès',
        },
        'de': {
            # Authentication errors
            'auth.invalid_credentials': 'Ungültige E-Mail oder Passwort',
            'auth.user_not_found': 'Benutzer nicht gefunden',
            'auth.email_already_exists': 'E-Mail existiert bereits',
            'auth.account_disabled': 'Konto ist deaktiviert',
            'auth.token_expired': 'Token ist abgelaufen',
            'auth.invalid_token': 'Ungültiger Token',
            'auth.insufficient_permissions': 'Unzureichende Berechtigungen',
            'auth.password_too_weak': 'Passwort ist zu schwach',
            'auth.email_not_verified': 'E-Mail-Adresse ist nicht verifiziert',
            
            # Validation errors
            'validation.required_field': 'Dieses Feld ist erforderlich',
            'validation.invalid_email': 'Ungültiges E-Mail-Format',
            'validation.min_length': 'Muss mindestens {min_length} Zeichen haben',
            'validation.max_length': 'Darf höchstens {max_length} Zeichen haben',
            'validation.invalid_format': 'Ungültiges Format',
            
            # Organization errors
            'organization.not_found': 'Organisation nicht gefunden',
            'organization.access_denied': 'Zugriff auf Organisation verweigert',
            'organization.name_exists': 'Organisationsname existiert bereits',
            'organization.member_not_found': 'Mitglied nicht gefunden',
            'organization.cannot_remove_owner': 'Kann Organisationsbesitzer nicht entfernen',
            
            # Project errors
            'project.not_found': 'Projekt nicht gefunden',
            'project.access_denied': 'Zugriff auf Projekt verweigert',
            'project.name_exists': 'Projektname existiert bereits',
            
            # Payment errors
            'payment.card_declined': 'Ihre Karte wurde abgelehnt',
            'payment.insufficient_funds': 'Unzureichende Mittel',
            'payment.invalid_payment_method': 'Ungültige Zahlungsmethode',
            'payment.subscription_not_found': 'Abonnement nicht gefunden',
            'payment.plan_not_found': 'Plan nicht gefunden',
            
            # Generic errors
            'error.internal_server': 'Interner Serverfehler',
            'error.not_found': 'Ressource nicht gefunden',
            'error.bad_request': 'Fehlerhafte Anfrage',
            'error.forbidden': 'Verboten',
            'error.rate_limit': 'Rate-Limit überschritten',
            
            # Success messages
            'success.created': 'Erfolgreich erstellt',
            'success.updated': 'Erfolgreich aktualisiert',
            'success.deleted': 'Erfolgreich gelöscht',
            'success.email_sent': 'E-Mail erfolgreich gesendet',
        },
        'pt': {
            # Authentication errors
            'auth.invalid_credentials': 'Email ou senha inválidos',
            'auth.user_not_found': 'Usuário não encontrado',
            'auth.email_already_exists': 'Email já existe',
            'auth.account_disabled': 'Conta está desabilitada',
            'auth.token_expired': 'Token expirou',
            'auth.invalid_token': 'Token inválido',
            'auth.insufficient_permissions': 'Permissões insuficientes',
            'auth.password_too_weak': 'Senha muito fraca',
            'auth.email_not_verified': 'Endereço de email não verificado',
            
            # Validation errors
            'validation.required_field': 'Este campo é obrigatório',
            'validation.invalid_email': 'Formato de email inválido',
            'validation.min_length': 'Deve ter pelo menos {min_length} caracteres',
            'validation.max_length': 'Deve ter no máximo {max_length} caracteres',
            'validation.invalid_format': 'Formato inválido',
            
            # Organization errors
            'organization.not_found': 'Organização não encontrada',
            'organization.access_denied': 'Acesso negado à organização',
            'organization.name_exists': 'Nome da organização já existe',
            'organization.member_not_found': 'Membro não encontrado',
            'organization.cannot_remove_owner': 'Não é possível remover o proprietário da organização',
            
            # Project errors
            'project.not_found': 'Projeto não encontrado',
            'project.access_denied': 'Acesso negado ao projeto',
            'project.name_exists': 'Nome do projeto já existe',
            
            # Payment errors
            'payment.card_declined': 'Seu cartão foi recusado',
            'payment.insufficient_funds': 'Fundos insuficientes',
            'payment.invalid_payment_method': 'Método de pagamento inválido',
            'payment.subscription_not_found': 'Assinatura não encontrada',
            'payment.plan_not_found': 'Plano não encontrado',
            
            # Generic errors
            'error.internal_server': 'Erro interno do servidor',
            'error.not_found': 'Recurso não encontrado',
            'error.bad_request': 'Solicitação incorreta',
            'error.forbidden': 'Proibido',
            'error.rate_limit': 'Limite de taxa excedido',
            
            # Success messages
            'success.created': 'Criado com sucesso',
            'success.updated': 'Atualizado com sucesso',
            'success.deleted': 'Excluído com sucesso',
            'success.email_sent': 'Email enviado com sucesso',
        }
    }
    
    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """Get list of supported language codes."""
        return cls.SUPPORTED_LANGUAGES.copy()
    
    @classmethod
    def is_supported_language(cls, lang_code: str) -> bool:
        """Check if language code is supported."""
        return lang_code in cls.SUPPORTED_LANGUAGES
    
    @classmethod
    def get_language_from_accept_header(cls, accept_language: Optional[str]) -> str:
        """
        Extract the preferred language from Accept-Language header.
        
        Args:
            accept_language: The Accept-Language header value
            
        Returns:
            The preferred supported language code, or default language
        """
        if not accept_language:
            return cls.DEFAULT_LANGUAGE
        
        # Parse Accept-Language header (simplified)
        # Format: "en-US,en;q=0.9,es;q=0.8,fr;q=0.7"
        languages = []
        for lang_entry in accept_language.split(','):
            # Extract language code (before any '-' or ';')
            lang_code = lang_entry.strip().split(';')[0].split('-')[0].lower()
            if cls.is_supported_language(lang_code):
                languages.append(lang_code)
        
        return languages[0] if languages else cls.DEFAULT_LANGUAGE
    
    @classmethod
    def translate(
        cls,
        key: str,
        language: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Translate a message key to the specified language.
        
        Args:
            key: The translation key (e.g., 'auth.invalid_credentials')
            language: The target language code (defaults to DEFAULT_LANGUAGE)
            **kwargs: Variables for string formatting
            
        Returns:
            The translated message, or the key if translation not found
        """
        if language is None:
            language = cls.DEFAULT_LANGUAGE
        
        if not cls.is_supported_language(language):
            language = cls.DEFAULT_LANGUAGE
        
        # Get translation from the specified language dictionary
        translations = cls.TRANSLATIONS.get(language, cls.TRANSLATIONS[cls.DEFAULT_LANGUAGE])
        message = translations.get(key, key)
        
        # Format the message with provided variables
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError):
            # Return the unformatted message if formatting fails
            return message
    
    @classmethod
    def get_locale_info(cls, language: str) -> dict:
        """
        Get locale information for a language.
        
        Args:
            language: The language code
            
        Returns:
            Dictionary with locale information
        """
        try:
            locale = Locale.parse(language)
            return {
                'code': language,
                'name': locale.display_name,
                'english_name': locale.english_name,
                'direction': 'rtl' if locale.text_direction == 'rtl' else 'ltr'
            }
        except UnknownLocaleError:
            return {
                'code': language,
                'name': language.upper(),
                'english_name': language.upper(),
                'direction': 'ltr'
            }


# Global instance
i18n = I18nManager()


def t(key: str, language: Optional[str] = None, **kwargs) -> str:
    """
    Convenience function for translation.
    
    Args:
        key: Translation key
        language: Target language (optional)
        **kwargs: Formatting variables
        
    Returns:
        Translated message
    """
    return i18n.translate(key, language, **kwargs)