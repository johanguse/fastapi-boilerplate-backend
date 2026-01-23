#!/usr/bin/env python3
"""
Test script to verify email functionality is working properly.
Run this script to test all email functions with detailed logging.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.email_service import email_service
from src.utils.email import send_email
from src.invitations.email_service import send_email_verification, send_team_invitation, send_password_reset


async def test_email_service():
    """Test the main email service functions."""
    print("=== Testing Email Service ===")
    
    # Test configuration validation
    print(f"API Key configured: {email_service.api_key is not None}")
    print(f"FROM_EMAIL: {email_service.from_email}")
    print(f"APP_NAME: {email_service.app_name}")
    print(f"FRONTEND_URL: {email_service.frontend_url}")
    
    # Test verification email
    print("\n--- Testing Verification Email ---")
    result = await email_service.send_verification_email(
        email="test@example.com",
        token="test-token-123",
        name="Test User"
    )
    print(f"Verification email result: {result}")
    
    # Test password reset email
    print("\n--- Testing Password Reset Email ---")
    result = await email_service.send_forgot_password_email(
        email="test@example.com",
        token="test-reset-token-456",
        name="Test User"
    )
    print(f"Password reset email result: {result}")
    
    # Test welcome email
    print("\n--- Testing Welcome Email ---")
    result = await email_service.send_welcome_email(
        email="test@example.com",
        name="Test User"
    )
    print(f"Welcome email result: {result}")


async def test_utils_email():
    """Test the utils email function."""
    print("\n=== Testing Utils Email ===")
    
    result = await send_email(
        to_email="test@example.com",
        subject="Test Email",
        html_content="<h1>Test Email</h1><p>This is a test email.</p>"
    )
    print(f"Utils email result: {result}")


async def test_invitations_email():
    """Test the invitations email functions."""
    print("\n=== Testing Invitations Email Service ===")
    
    # Test email verification
    print("\n--- Testing Email Verification ---")
    await send_email_verification(
        email="test@example.com",
        name="Test User",
        verification_link="https://example.com/verify?token=test123"
    )
    
    # Test team invitation
    print("\n--- Testing Team Invitation ---")
    await send_team_invitation(
        email="test@example.com",
        invited_by_name="Admin User",
        organization_name="Test Org",
        invitation_link="https://example.com/invite?token=invite123",
        role="member"
    )
    
    # Test password reset
    print("\n--- Testing Password Reset ---")
    await send_password_reset(
        email="test@example.com",
        name="Test User",
        reset_link="https://example.com/reset?token=reset123"
    )


async def main():
    """Run all email tests."""
    print("Email Function Test Script")
    print("=" * 50)
    
    # Check environment variables
    print("Environment Check:")
    print(f"RESEND_API_KEY: {'Set' if os.getenv('RESEND_API_KEY') else 'NOT SET'}")
    print(f"RESEND_FROM_EMAIL: {os.getenv('RESEND_FROM_EMAIL', 'NOT SET')}")
    print(f"FRONTEND_URL: {os.getenv('FRONTEND_URL', 'NOT SET')}")
    print(f"APP_NAME: {os.getenv('APP_NAME', 'NOT SET')}")
    
    if not os.getenv('RESEND_API_KEY'):
        print("\n❌ RESEND_API_KEY not set! Set it in your .env file to test email functionality.")
        return
    
    try:
        await test_email_service()
        await test_utils_email()
        await test_invitations_email()
        
        print("\n✅ All email tests completed! Check the logs above for any errors.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
