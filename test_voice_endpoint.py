import requests

url = "http://localhost:8000/api/voice/process"
data = {
    "user_input": "Hello Arjun, I want to add a record.",
    "current_data": {},
    "context": "medical"
}

try:
    print("Sending request to voice/process...")
    response = requests.post(url, json=data, timeout=30)
    print("Status:", response.status_code)
    print("Body:", response.json())
except Exception as e:
    print("Error:", e)
