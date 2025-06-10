#!/usr/bin/env python
"""
Simple test script for GitHub OAuth integration
Run this after setting up GitHub OAuth to verify it's working
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')

def test_github_oauth_setup():
    """Test if GitHub OAuth is properly configured"""
    print("🔍 Testing GitHub OAuth Setup...")
    print(f"Base URL: {BASE_URL}")
    
    # Check environment variables
    if not GITHUB_CLIENT_ID:
        print("❌ GITHUB_CLIENT_ID not found in environment")
        return False
    else:
        print(f"✅ GITHUB_CLIENT_ID: {GITHUB_CLIENT_ID[:8]}...")
    
    if not GITHUB_CLIENT_SECRET:
        print("❌ GITHUB_CLIENT_SECRET not found in environment")
        return False
    else:
        print(f"✅ GITHUB_CLIENT_SECRET: {GITHUB_CLIENT_SECRET[:8]}...")
    
    return True

def test_initiate_endpoint():
    """Test the GitHub OAuth initiate endpoint"""
    print("\n🚀 Testing GitHub OAuth Initiate Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/github/")
        
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get('authorization_url')
            
            if auth_url and 'github.com' in auth_url:
                print("✅ GitHub OAuth initiate endpoint working")
                print(f"✅ Authorization URL generated: {auth_url[:50]}...")
                print(f"📋 Full Authorization URL: {auth_url}")
                return auth_url
            else:
                print("❌ Invalid authorization URL received")
                print(f"Response: {data}")
                return None
        else:
            print(f"❌ Endpoint returned status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Django server")
        print("💡 Make sure Django server is running: python manage.py runserver")
        return None
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return None

def test_django_server():
    """Test if Django server is running"""
    print("\n🌐 Testing Django Server...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/hello/")
        if response.status_code == 200:
            print("✅ Django server is running")
            return True
        else:
            print(f"⚠️ Django server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Django server is not running")
        print("💡 Start it with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Django server: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 GitHub OAuth Integration Test\n")
    
    # Test 1: Environment setup
    if not test_github_oauth_setup():
        print("\n❌ GitHub OAuth not properly configured")
        print("💡 Please check GITHUB_OAUTH_SETUP.md for setup instructions")
        return
    
    # Test 2: Django server
    if not test_django_server():
        print("\n❌ Django server issues")
        return
    
    # Test 3: GitHub OAuth endpoint
    auth_url = test_initiate_endpoint()
    
    if auth_url:
        print("\n🎉 GitHub OAuth integration is working!")
        print("\n📋 Next steps to test complete flow:")
        print("1. Copy the authorization URL above")
        print("2. Open it in your browser")
        print("3. Authorize your GitHub application")
        print("4. Check if you're redirected to the callback URL")
        print("5. Verify user authentication in the response")
        
        print(f"\n🔗 Authorization URL:\n{auth_url}")
        
        print(f"\n📍 Expected callback URL:")
        print(f"{BASE_URL}/api/auth/github/callback/")
        
    else:
        print("\n❌ GitHub OAuth integration has issues")
        print("💡 Check the error messages above and GITHUB_OAUTH_SETUP.md")

if __name__ == "__main__":
    main() 