#!/usr/bin/env python3
"""
Test script for the Custom ChatGPT API
"""
import requests
import json
import time

def test_api(base_url="http://localhost:8000"):
    """Test the ChatGPT API endpoints"""
    
    print("Testing Custom ChatGPT API...")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
    
    print()
    
    # Test 2: Detailed health check
    print("2. Testing detailed health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Detailed health check passed")
            print(f"   Status: {health_data.get('status')}")
            print(f"   ChatGPT accessible: {health_data.get('chatgpt_accessible')}")
        else:
            print(f"❌ Detailed health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Detailed health check error: {str(e)}")
    
    print()
    
    # Test 3: Chat endpoint
    print("3. Testing chat endpoint...")
    test_prompt = "Hello! Please respond with just 'API test successful' to confirm this is working."
    
    try:
        payload = {
            "prompt": test_prompt,
            "max_retries": 2
        }
        
        print(f"   Sending prompt: {test_prompt}")
        print("   Waiting for response... (this may take 30-60 seconds)")
        
        response = requests.post(
            f"{base_url}/chat", 
            json=payload, 
            timeout=120
        )
        
        if response.status_code == 200:
            chat_data = response.json()
            if chat_data.get("success"):
                print("✅ Chat endpoint working!")
                print(f"   Response: {chat_data.get('response')}")
            else:
                print("❌ Chat endpoint returned error")
                print(f"   Error: {chat_data.get('error_message')}")
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Chat request timed out (this is normal for first request)")
    except Exception as e:
        print(f"❌ Chat endpoint error: {str(e)}")
    
    print()
    print("-" * 50)
    print("Test completed!")

if __name__ == "__main__":
    import sys
    
    # Allow custom URL via command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    test_api(base_url)
