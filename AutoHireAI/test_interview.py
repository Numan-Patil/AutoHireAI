import requests
import json

# API endpoint
url = 'http://localhost:5000/api/test-interview'

# Test data
data = {
    "candidate": {
        "name": "John Doe",
        "email": "john@example.com"
    }
}

# Make the request
response = requests.post(url, json=data)

# Print the response
print("Status Code:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))
