import requests
import json

# Test chat API with verbose output
try:
    print("Testing backend health endpoint...")
    health = requests.get('http://localhost:8000/health')
    print(f"Health: {health.status_code} - {health.text}")
    
    print("\n" + "="*50)
    print("Testing chat API...")
    response = requests.post(
        'http://localhost:8000/api/v1/chat',
        json={'message': 'hello'},
        headers={
            'Origin': 'http://localhost:3000',
            'Content-Type': 'application/json'
        }
    )
    
    print(f"\nStatus: {response.status_code}")
    print(f"Response Headers:")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")
    print(f"\nResponse Body: {response.text}")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
