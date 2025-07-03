import requests

API_TOKEN = "505b31e4f5fab8918657fb941a354c92981d81be9da8e180693959e5b739b641"
SITE_ID = "5c1bac5e34270258cfeecacf"

url = f"https://api.webflow.com/v2/sites/{SITE_ID}/collections"


headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "accept-version": "1.0.0"
}

response = requests.get(url, headers=headers)

print(f"Status code: {response.status_code}")
print("Response:")
print(response.text)