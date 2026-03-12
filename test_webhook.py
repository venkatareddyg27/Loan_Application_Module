import requests

url = "http://localhost:8000/webhooks/razorpay"

payload = {
    "event": "payout.processed",
    "payload": {
        "payout": {
            "entity": {
                "id": "mock_payout_12345",
                "status": "processed"
            }
        }
    }
}

headers = {
    "Content-Type": "application/json",
    "x-razorpay-signature": "test"
}

response = requests.post(url, json=payload, headers=headers)

print("Status:", response.status_code)
print("Response:", response.text)