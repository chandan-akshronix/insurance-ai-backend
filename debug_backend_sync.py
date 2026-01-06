
import requests
from datetime import date
import json

url = "http://localhost:8000/agent/sync"

# Payload EXACTLY as agent sends it (no applicationtype, no lastUpdated)
payload = {
    "applicationId": "695ca98c5b1273e34b44d1dd",
    "status": "processing",
    "currentStep": "ingest",
    "agentData": {"foo": "bar"},
    "stepHistory": [],
    "startTime": date.today().isoformat()
}

print(f"Sending payload to {url}...")
try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
