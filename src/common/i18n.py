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
    
    SUPPORTED_LANGUAGES = [
        'en-US', 'en-GB', 
        'es-ES', 'es-MX', 
        'fr-FR', 'fr-CA', 
        'de-DE', 
        'pt-BR', 'pt-PT'
    ]
    DEFAULT_LANGUAGE = 'en-US'
    
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
    
    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """Get list of supported language codes."""
        return cls.SUPPORTED_LANGUAGES.copy()
    
    @classmethod
    def is_supported_language(cls, lang_code: str) -> bool:
        """Check if language code is supported."""
        return lang_code in cls.SUPPORTED_LANGUAGES
    
    @classmethod
    def get_fallback_language(cls, lang_code: str) -> str:
        """
        Get fallback language for regional variants.
        
        Args:
            lang_code: Language code (e.g., 'en-US', 'pt-BR')
            
        Returns:
            Fallback language code
        """
        # If exact match exists, return it
        if lang_code in cls.SUPPORTED_LANGUAGES:
            return lang_code
        
        # Try to find regional variant or base language
        if '-' in lang_code:
            base_lang = lang_code.split('-')[0]
            # Look for any supported regional variant of the base language
            for supported in cls.SUPPORTED_LANGUAGES:
                if supported.startswith(base_lang + '-'):
                    return supported
        else:
            # If given base language, try to find a regional variant
            for supported in cls.SUPPORTED_LANGUAGES:
                if supported.startswith(lang_code + '-'):
                    return supported
        
        return cls.DEFAULT_LANGUAGE
    
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
            # Extract language code (before any ';' for q-value)
            lang_code = lang_entry.strip().split(';')[0].strip()
            # Try exact match first, then fallback
            fallback_lang = cls.get_fallback_language(lang_code)
            if fallback_lang != cls.DEFAULT_LANGUAGE or lang_code == cls.DEFAULT_LANGUAGE:
                languages.append(fallback_lang)
        
        return languages[0] if languages else cls.DEFAULT_LANGUAGE
    
    def translate(
        self,
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
            language = self.DEFAULT_LANGUAGE
        
        # Use fallback language logic for regional variants
        language = self.get_fallback_language(language)
        
        # Get translation from the specified language dictionary
        translations = self._translations.get(language, self._translations.get(self.DEFAULT_LANGUAGE, {}))
        
        # Navigate through nested keys (e.g., 'auth.invalid_credentials')
        message = translations
        for key_part in key.split('.'):
            if isinstance(message, dict) and key_part in message:
                message = message[key_part]
            else:
                # Return the original key if translation not found
                return key
        
        # Ensure we have a string message
        if not isinstance(message, str):
            return key
        
        # Format the message with provided variables
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError):
            # Return the unformatted message if formatting fails
            return message
    
    def get_plural_form(self, language: str, count: int) -> str:
        """
        Determines the correct pluralization form using Babel's Locale class.
        
        Args:
            language: The language code
            count: The number to determine pluralization for
            
        Returns:
            The plural form category (one, few, many, other, etc.)
        """
        try:
            locale = Locale.parse(language)
            plural_form = locale.plural_form(count)
            return plural_form
        except Exception:
            return "other"  # Fallback to 'other' if something goes wrong
    
    def translate_plural(
        self,
        key: str,
        count: int,
        language: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Translate a pluralized message key.
        
        Args:
            key: The base translation key (e.g., 'messages.count')
            count: The number to determine pluralization for
            language: The target language code
            **kwargs: Variables for string formatting (including count)
            
        Returns:
            The translated and formatted message
        """
        if language is None:
            language = self.DEFAULT_LANGUAGE
        
        if not self.is_supported_language(language):
            language = self.DEFAULT_LANGUAGE
        
        # Get the plural form for this count and language
        plural_form = self.get_plural_form(language, count)
        
        # Build the plural key (e.g., 'messages.one' or 'messages.other')
        plural_key = f"{key}.{plural_form}"
        
        # Try to get the specific plural form first
        message = self.translate(plural_key, language, count=count, **kwargs)
        
        # If not found, try the 'other' form as fallback
        if message == plural_key:
            other_key = f"{key}.other"
            message = self.translate(other_key, language, count=count, **kwargs)
            
            # If still not found, return the original key
            if message == other_key:
                return key
        
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