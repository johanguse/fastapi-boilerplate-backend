"""
Additional tests for exception handling scenarios to ensure robust error handling.
"""
import pytest
from unittest.mock import Mock

from src.common.exceptions import (
    APIError,
    NotFoundError, 
    PermissionError,
    ValidationError,
    AuthenticationError,
    OrganizationError,
    ProjectError,
    PaymentError,
)


class TestExceptionMessages:
    """Test exception message behavior in various scenarios"""
    
    def test_permission_error_preserves_custom_message(self):
        """Test that PermissionError preserves custom detail messages"""
        custom_message = "User is not a member of this organization"
        err = PermissionError(detail=custom_message)
        assert err.detail == custom_message
        assert "member" in err.detail.lower()
        assert "organization" in err.detail.lower()
    
    def test_validation_error_preserves_custom_message(self):
        """Test that ValidationError preserves custom detail messages"""
        custom_message = "Email validation failed"
        err = ValidationError(detail=custom_message)
        assert err.detail == custom_message
        assert "validation" in err.detail.lower()
        assert "email" in err.detail.lower()
    
    def test_exception_with_translation_params(self):
        """Test exceptions with translation parameters"""
        err = ValidationError(
            detail="Field must be at least {min_length} characters",
            min_length=8
        )
        # Should preserve the detail message format
        assert "min_length" in err.detail or "8" in err.detail
    
    def test_exception_inheritance_chain(self):
        """Test that exceptions maintain proper inheritance"""
        from fastapi import HTTPException
        
        exceptions_to_test = [
            NotFoundError(),
            PermissionError(),
            ValidationError(),
            AuthenticationError(),
            OrganizationError(),
            ProjectError(),
            PaymentError(),
        ]
        
        for exc in exceptions_to_test:
            assert isinstance(exc, APIError)
            assert isinstance(exc, HTTPException)
            assert hasattr(exc, 'status_code')
            assert hasattr(exc, 'detail')


class TestExceptionContexts:
    """Test exceptions in different application contexts"""
    
    def test_permission_error_in_project_context(self):
        """Test permission error in project membership context"""
        err = PermissionError(detail="User is not a member of this organization")
        
        # Should contain key words that tests expect
        error_str = str(err).lower()
        assert any(word in error_str for word in ["member", "organization", "permission"])
    
    def test_validation_error_in_form_context(self):
        """Test validation error in form validation context"""
        err = ValidationError(detail="Invalid email format provided")
        
        # Should contain validation-related words
        error_str = str(err).lower()
        assert any(word in error_str for word in ["validation", "invalid", "format"])
    
    def test_not_found_error_in_resource_context(self):
        """Test not found error for various resources"""
        contexts = [
            "Project not found",
            "Organization not found", 
            "User resource not found",
            "The requested item was not found"
        ]
        
        for context in contexts:
            err = NotFoundError(detail=context)
            assert "not found" in err.detail.lower()
            assert err.status_code == 404


class TestExceptionStringRepresentation:
    """Test how exceptions are converted to strings for testing"""
    
    def test_exception_str_contains_detail(self):
        """Test that str(exception) contains the detail message"""
        message = "Custom error message for testing"
        err = PermissionError(detail=message)
        
        # The string representation should contain the detail
        error_str = str(err)
        assert message.lower() in error_str.lower()
    
    def test_exception_str_format_consistency(self):
        """Test consistent string format across different exception types"""
        message = "Test message"
        exceptions = [
            NotFoundError(detail=message),
            PermissionError(detail=message),
            ValidationError(detail=message),
        ]
        
        for exc in exceptions:
            error_str = str(exc)
            # Should contain the message in some form
            assert message.lower() in error_str.lower()


class TestTranslationBehavior:
    """Test translation key behavior"""
    
    def test_no_translation_key_preserves_detail(self):
        """Test that no translation_key preserves original detail"""
        original_detail = "Original error message"
        err = PermissionError(detail=original_detail)
        
        # Should preserve the original detail when no translation_key is provided
        assert err.detail == original_detail
    
    def test_explicit_translation_key_none(self):
        """Test explicitly setting translation_key to None"""
        original_detail = "Explicit none translation key"
        err = ValidationError(detail=original_detail, translation_key=None)
        
        # Should preserve original detail
        assert err.detail == original_detail
    
    def test_custom_translation_key(self):
        """Test behavior with custom translation keys"""
        err = NotFoundError(
            detail="Default message",
            translation_key="error.not_found"
        )
        
        # Should either use translation or fallback to detail
        assert err.detail in ["Default message", "Resource not found"]