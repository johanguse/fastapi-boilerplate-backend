#!/usr/bin/env python3
"""
Comprehensive test script for Resend email functionality.
Tests all email services and configurations to verify email sending works properly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services.email_service import email_service
from src.utils.email import send_email
from src.services.token_service import token_service
from src.common.session import get_async_session
from src.common.config import settings


async def test_environment_configuration():
    """Test environment configuration for email services."""
    print("🔧 Testing Environment Configuration")
    print("=" * 50)
    
    # Check required environment variables
    env_vars = {
        'RESEND_API_KEY': os.getenv('RESEND_API_KEY'),
        'RESEND_FROM_EMAIL': os.getenv('RESEND_FROM_EMAIL'),
        'FRONTEND_URL': os.getenv('FRONTEND_URL'),
        'APP_NAME': os.getenv('APP_NAME'),
    }
    
    print("Environment Variables:")
    for key, value in env_vars.items():
        status = "✅ SET" if value else "❌ NOT SET"
        display_value = value if value else "None"
        print(f"  {key}: {status} ({display_value})")
    
    # Check email service configuration
    print(f"\nEmail Service Configuration:")
    print(f"  API Key configured: {'✅ YES' if email_service.api_key else '❌ NO'}")
    print(f"  FROM_EMAIL: {email_service.from_email}")
    print(f"  APP_NAME: {email_service.app_name}")
    print(f"  FRONTEND_URL: {email_service.frontend_url}")
    
    if not email_service.api_key:
        print("\n❌ CRITICAL: RESEND_API_KEY not configured!")
        print("   Set RESEND_API_KEY in your .env file to enable email functionality.")
        return False
    
    return True


async def test_basic_email_sending():
    """Test basic email sending functionality."""
    print("\n📧 Testing Basic Email Sending")
    print("=" * 50)
    
    test_email = "johanguse@gmail.com"
    test_subject = "Test Email from Resend"
    test_html = """
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>🧪 Test Email</h2>
        <p>This is a test email to verify Resend integration is working properly.</p>
        <p><strong>Test Details:</strong></p>
        <ul>
            <li>Service: Resend API</li>
            <li>From: {from_email}</li>
            <li>App: {app_name}</li>
            <li>Frontend URL: {frontend_url}</li>
        </ul>
        <p>If you receive this email, the email service is working correctly! ✅</p>
    </div>
    """.format(
        from_email=email_service.from_email,
        app_name=email_service.app_name,
        frontend_url=email_service.frontend_url
    )
    
    try:
        result = await send_email(
            to_email=test_email,
            subject=test_subject,
            html_content=test_html
        )
        
        if result:
            print(f"✅ Basic email sent successfully to {test_email}")
            return True
        else:
            print(f"❌ Failed to send basic email to {test_email}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending basic email: {str(e)}")
        return False


async def test_verification_email():
    """Test email verification functionality."""
    print("\n🔐 Testing Email Verification")
    print("=" * 50)
    
    test_email = "johanguse@gmail.com"
    test_token = "test-verification-token-12345"
    test_name = "Test User"
    
    try:
        result = await email_service.send_verification_email(
            email=test_email,
            token=test_token,
            name=test_name
        )
        
        if result:
            print(f"✅ Verification email sent successfully to {test_email}")
            print(f"   Token: {test_token}")
            print(f"   Verification link: {email_service.frontend_url}/verify-email?token={test_token}")
            return True
        else:
            print(f"❌ Failed to send verification email to {test_email}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending verification email: {str(e)}")
        return False


async def test_password_reset_email():
    """Test password reset email functionality."""
    print("\n🔒 Testing Password Reset Email")
    print("=" * 50)
    
    test_email = "johanguse@gmail.com"
    test_token = "test-reset-token-67890"
    test_name = "Test User"
    
    try:
        result = await email_service.send_forgot_password_email(
            email=test_email,
            token=test_token,
            name=test_name
        )
        
        if result:
            print(f"✅ Password reset email sent successfully to {test_email}")
            print(f"   Token: {test_token}")
            print(f"   Reset link: {email_service.frontend_url}/reset-password?token={test_token}")
            return True
        else:
            print(f"❌ Failed to send password reset email to {test_email}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending password reset email: {str(e)}")
        return False


async def test_welcome_email():
    """Test welcome email functionality."""
    print("\n🎉 Testing Welcome Email")
    print("=" * 50)
    
    test_email = "johanguse@gmail.com"
    test_name = "Test User"
    
    try:
        result = await email_service.send_welcome_email(
            email=test_email,
            name=test_name
        )
        
        if result:
            print(f"✅ Welcome email sent successfully to {test_email}")
            print(f"   Dashboard link: {email_service.frontend_url}/dashboard")
            return True
        else:
            print(f"❌ Failed to send welcome email to {test_email}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending welcome email: {str(e)}")
        return False


async def test_token_service():
    """Test token service functionality."""
    print("\n🎫 Testing Token Service")
    print("=" * 50)
    
    try:
        # Get database session
        async for session in get_async_session():
            test_email = "johanguse@gmail.com"
            
            # Test verification token creation
            verification_token = await token_service.create_verification_token(
                session, test_email
            )
            print(f"✅ Verification token created: {verification_token[:20]}...")
            
            # Test password reset token creation
            reset_token = await token_service.create_password_reset_token(
                session, test_email
            )
            print(f"✅ Password reset token created: {reset_token[:20]}...")
            
            # Test token verification
            verified_email = await token_service.verify_token(
                session, verification_token, 'verification'
            )
            if verified_email == test_email:
                print(f"✅ Token verification successful: {verified_email}")
            else:
                print(f"❌ Token verification failed: expected {test_email}, got {verified_email}")
            
            break
            
    except Exception as e:
        print(f"❌ Error testing token service: {str(e)}")
        return False
    
    return True


async def test_real_email_address():
    """Test with a real email address (if provided)."""
    print("\n📮 Testing with Real Email Address")
    print("=" * 50)
    
    # You can set this environment variable to test with a real email
    real_email = os.getenv('TEST_EMAIL_ADDRESS')
    
    if not real_email:
        print("ℹ️  No TEST_EMAIL_ADDRESS environment variable set.")
        print("   Set TEST_EMAIL_ADDRESS=your-email@example.com to test with real email.")
        return True
    
    print(f"Testing with real email: {real_email}")
    
    try:
        result = await email_service.send_verification_email(
            email=real_email,
            token="real-test-token-12345",
            name="Test User"
        )
        
        if result:
            print(f"✅ Real email sent successfully to {real_email}")
            print("   Check your inbox for the verification email!")
            return True
        else:
            print(f"❌ Failed to send real email to {real_email}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending real email: {str(e)}")
        return False


async def main():
    """Run all email tests."""
    print("🧪 Resend Email Service Test Suite")
    print("=" * 60)
    
    # Test environment configuration first
    config_ok = await test_environment_configuration()
    if not config_ok:
        print("\n❌ Configuration test failed. Please fix environment variables and try again.")
        return
    
    # Run all tests
    tests = [
        ("Basic Email Sending", test_basic_email_sending),
        ("Email Verification", test_verification_email),
        ("Password Reset Email", test_password_reset_email),
        ("Welcome Email", test_welcome_email),
        ("Token Service", test_token_service),
        ("Real Email Address", test_real_email_address),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Email service is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if not os.getenv('RESEND_API_KEY'):
        print("  - Set RESEND_API_KEY in your .env file")
    if not os.getenv('RESEND_FROM_EMAIL'):
        print("  - Set RESEND_FROM_EMAIL to your verified domain")
    if not os.getenv('TEST_EMAIL_ADDRESS'):
        print("  - Set TEST_EMAIL_ADDRESS to test with real email delivery")
    print("  - Check Resend dashboard for delivery status")
    print("  - Verify your domain in Resend if using custom FROM_EMAIL")


if __name__ == "__main__":
    asyncio.run(main())

