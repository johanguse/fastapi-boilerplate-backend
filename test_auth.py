#!/usr/bin/env python3
"""
Test script for Better Auth integration endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_sign_in():
    """Test the Better Auth sign-in endpoint"""
    url = f"{BASE_URL}/auth/sign-in/email"
    data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    print(f"Testing sign-in at {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.text:
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response (text): {response.text}")
        
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_session():
    """Test the Better Auth session endpoint"""
    url = f"{BASE_URL}/auth/session"
    
    print(f"\nTesting session at {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.text:
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response (text): {response.text}")
        
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_sign_up():
    """Test the Better Auth sign-up endpoint"""
    url = f"{BASE_URL}/auth/sign-up/email"
    data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    
    print(f"\nTesting sign-up at {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.text:
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response (text): {response.text}")
        
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Testing Better Auth Integration")
    print("=" * 50)
    
    # Test sign-in
    sign_in_response = test_sign_in()
    
    # Test session (without authentication)
    session_response = test_session()
    
    # Test sign-up
    sign_up_response = test_sign_up()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")