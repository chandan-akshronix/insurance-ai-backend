
import requests
import json
import os

url = "http://localhost:8000/agent/sync"
payload_path = r"..\langgraph claim process\debug_payload.json"

if not os.path.exists(payload_path):
    print(f"Payload file not found: {payload_path}")
    exit(1)

with open(payload_path, "r") as f:
    payload = json.load(f)

print(f"Sending REAL payload to {url}...")
try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
