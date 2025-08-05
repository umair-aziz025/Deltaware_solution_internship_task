#!/usr/bin/env python3
"""
Test script to verify the Flask app works locally before deploying to Vercel
"""

import sys
import os
import requests
import time
import subprocess
import threading

def test_local_server():
    """Test the Flask app running locally"""
    print("🧪 Testing Flask app locally...")
    
    # Add the api directory to Python path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
    
    try:
        # Import the Flask app
        from index import app
        
        print("✅ Flask app imported successfully")
        
        # Test the health endpoint
        with app.test_client() as client:
            print("🔍 Testing /health endpoint...")
            response = client.get('/health')
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.get_json()}")
                print("✅ Health endpoint working")
            else:
                print("❌ Health endpoint failed")
                return False
            
            print("🔍 Testing / endpoint...")
            response = client.get('/')
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✅ Main endpoint working")
            else:
                print("❌ Main endpoint failed")
                print(f"   Error: {response.get_data(as_text=True)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Flask app: {e}")
        return False

def test_simple_version():
    """Test the simple version of the app"""
    print("\n🧪 Testing simple Flask app...")
    
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
    
    try:
        from simple import app
        print("✅ Simple Flask app imported successfully")
        
        with app.test_client() as client:
            response = client.get('/')
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.get_json()}")
                print("✅ Simple app working")
                return True
            else:
                print("❌ Simple app failed")
                return False
                
    except Exception as e:
        print(f"❌ Error testing simple app: {e}")
        return False

def main():
    print("🚀 Flask App Local Testing")
    print("=" * 40)
    
    # Test simple version first
    simple_works = test_simple_version()
    
    # Test main version
    main_works = test_local_server()
    
    print("\n📊 Test Results:")
    print("=" * 40)
    print(f"Simple app: {'✅ PASS' if simple_works else '❌ FAIL'}")
    print(f"Main app:   {'✅ PASS' if main_works else '❌ FAIL'}")
    
    if simple_works and main_works:
        print("\n🎉 All tests passed! The app should work on Vercel.")
        print("\n📝 Next steps:")
        print("1. Commit these changes to GitHub")
        print("2. Deploy to Vercel")
        print("3. Test the deployed endpoints")
    else:
        print("\n⚠️  Some tests failed. Fix the issues before deploying.")
    
    return simple_works and main_works

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
