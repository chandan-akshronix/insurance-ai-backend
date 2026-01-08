import requests
import json
import datetime

url = "http://localhost:8000/agent/sync"

# COMPLEX PAYLOAD MIMICKING AGENT
state = {
    "claim_id": "695e03fa5b1273e34b44d1e7",
    "policy_id": None,
    "fnol_data": {
      "_id": "695e03fa5b1273e34b44d1e7",
      "user_id": "1",
      "userId": "1",
      "claim_type": "life",
      "policy_id": "85",
      "policyNumber": "LIF20260107065103",
      "status": "submitted",
      "intimation_date": "2026-01-07",
      "intimation_time": "12:24",
      "documents": [
        {
          "filename": "Gemini_Generated_Image_1r2xl41r2xl41r2x.png",
          "url": "https://insurancedocuments.blob.core.windows.net/insurance-docs/claims/pending/1/death-certificate/c561918d-c525-4e56-87c7-3fbaa5225a1a.png",
          "documentId": 363,
          "docType": "claim_document",
          "category": "death-certificate"
        }
      ]
    },
    "policy_sql_data": {
      "id": 85,
      "userId": 1,
      "type": "life",
      "planName": "Basic Plan",
      "policyNumber": "LIF20260107065103",
      "coverage": 8500000.0,
      "premium": 9300.0,
      "status": "Active",
      "applicationId": "695e02575b1273e34b44d1e6"
    }
}

payload = {
    "applicationId": "695e03fa5b1273e34b44d1e7",
    "applicationtype": "claim",
    "status": "manual_review",
    "currentStep": "proof_verification",
    "agentData": state,
    "stepHistory": [
        {
            "id": 1,
            "name": "FNOL Validation",
            "status": "completed",
            "timestamp": "2026-01-07 15:42:24",
            "summary": "Initial claim ingestion and schema validation.",
            "decision": {"outcome": "Claim Validated & Accepted"}
        }
    ],
    "startTime": "2026-01-07"
}

print(f"Sending COMPLEX payload to {url}...")
try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
