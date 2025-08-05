#!/usr/bin/env python3
"""
Test script to verify the web application works locally before deploying to Vercel
"""
import requests
import time

def test_app():
    base_url = "http://localhost:5000"
    
    print("Testing Web Directory Bruteforcer...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
        else:
            print("✗ Health check failed")
            return False
    except Exception as e:
        print(f"✗ Could not connect to app: {e}")
        return False
    
    # Test main page
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✓ Main page loads successfully")
        else:
            print("✗ Main page failed to load")
            return False
    except Exception as e:
        print(f"✗ Main page error: {e}")
        return False
    
    # Test start_scan endpoint
    try:
        test_data = {
            'target_url': 'https://httpbin.org',
            'wordlist': 'get\npost\nput\ndelete',
            'extensions': ''
        }
        
        response = requests.post(f"{base_url}/start_scan", data=test_data)
        if response.status_code == 200:
            data = response.json()
            print("✓ Start scan endpoint works")
            print(f"  Session ID: {data.get('session_id', 'N/A')}")
            
            # Wait a bit and check status
            time.sleep(2)
            session_id = data.get('session_id')
            if session_id:
                status_response = requests.get(f"{base_url}/scan_status/{session_id}")
                if status_response.status_code == 200:
                    print("✓ Status endpoint works")
                    print(f"  Status: {status_response.json()}")
                else:
                    print("✗ Status endpoint failed")
            
        else:
            print(f"✗ Start scan failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Start scan error: {e}")
        return False
    
    print("\n✓ All tests passed! App is ready for deployment.")
    return True

if __name__ == "__main__":
    test_app()
