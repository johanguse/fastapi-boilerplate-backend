#!/usr/bin/env python3
"""
Test script for user registration with email verification.
Tests the complete registration flow including email sending.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests
from src.common.config import settings


def test_registration_with_email():
    """Test user registration and check if email verification is triggered."""
    print("🧪 Testing User Registration with Email Verification")
    print("=" * 60)
    
    base_url = 'http://localhost:8000'
    url = f'{base_url}/auth/sign-up/email'
    
    # Test data
    test_data = {
        'email': 'test-registration@example.com',
        'password': 'testpassword123',
        'name': 'Test Registration User',
    }
    
    print(f"Testing registration at: {url}")
    print(f"Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.text:
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                # Check if user was created successfully
                if response.status_code == 200 and 'user' in response_data:
                    user = response_data['user']
                    print(f"\n✅ User created successfully!")
                    print(f"   User ID: {user.get('id')}")
                    print(f"   Email: {user.get('email')}")
                    print(f"   Name: {user.get('name')}")
                    print(f"   Email Verified: {user.get('emailVerified')}")
                    
                    if not user.get('emailVerified'):
                        print(f"\n📧 Email verification should have been sent!")
                        print(f"   Check the server logs for email sending status.")
                        print(f"   Check {test_data['email']} inbox for verification email.")
                    else:
                        print(f"\n⚠️  User email is already verified (unexpected for new registration)")
                    
                    return True
                else:
                    print(f"\n❌ Registration failed")
                    return False
                    
            except Exception as e:
                print(f"Response (text): {response.text}")
                print(f"Error parsing JSON: {e}")
                return False
        else:
            print("No response body")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_email_configuration():
    """Test email service configuration."""
    print("\n🔧 Testing Email Configuration")
    print("=" * 40)
    
    print(f"RESEND_API_KEY: {'✅ SET' if settings.RESEND_API_KEY else '❌ NOT SET'}")
    print(f"RESEND_FROM_EMAIL: {settings.RESEND_FROM_EMAIL or '❌ NOT SET'}")
    print(f"FRONTEND_URL: {settings.FRONTEND_URL}")
    print(f"APP_NAME: {settings.PROJECT_NAME}")
    
    if not settings.RESEND_API_KEY:
        print("\n❌ RESEND_API_KEY not configured!")
        print("   Set RESEND_API_KEY in your .env file to enable email functionality.")
        return False
    
    return True


def test_resend_verification():
    """Test resending verification email."""
    print("\n📧 Testing Resend Verification Email")
    print("=" * 40)
    
    base_url = 'http://localhost:8000'
    url = f'{base_url}/auth/resend-verification'
    
    test_data = {
        'email': 'test-registration@example.com',
    }
    
    print(f"Testing resend verification at: {url}")
    print(f"Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.text:
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                if response.status_code == 200 and response_data.get('success'):
                    print(f"\n✅ Verification email resent successfully!")
                    return True
                else:
                    print(f"\n❌ Failed to resend verification email")
                    return False
                    
            except Exception as e:
                print(f"Response (text): {response.text}")
                print(f"Error parsing JSON: {e}")
                return False
        else:
            print("No response body")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all registration tests."""
    print("🧪 User Registration & Email Verification Test")
    print("=" * 60)
    
    # Test email configuration first
    config_ok = test_email_configuration()
    if not config_ok:
        print("\n❌ Email configuration test failed.")
        print("   Please configure RESEND_API_KEY and try again.")
        return
    
    # Test registration
    registration_ok = test_registration_with_email()
    
    # Test resend verification
    resend_ok = test_resend_verification()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 40)
    
    tests = [
        ("Email Configuration", config_ok),
        ("User Registration", registration_ok),
        ("Resend Verification", resend_ok),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Registration and email verification are working.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    # Instructions
    print("\n💡 Next Steps:")
    print("  1. Check your email inbox for verification emails")
    print("  2. Check server logs for email sending status")
    print("  3. Verify your Resend domain configuration")
    print("  4. Test with a real email address")


if __name__ == "__main__":
    main()

