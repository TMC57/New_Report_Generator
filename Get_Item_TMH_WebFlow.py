import requests
import json

API_TOKEN = "505b31e4f5fab8918657fb941a354c92981d81be9da8e180693959e5b739b641"
COLLECTION_ID = "5f1e86981034731b32c4665e"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "accept-version": "1.0.0"
}

params = {
    "limit": 50,
    "offset": 0  # Commencer au premier item
}

url = f"https://api.webflow.com/v2/collections/{COLLECTION_ID}/items"

response = requests.get(url, headers=headers, params=params)
response.raise_for_status()

items = response.json().get("items", [])
print(f"Nombre d'items récupérés : {len(items)}")

with open("items.txt", "w", encoding="utf-8") as f:
    f.write(json.dumps(items, indent=2, ensure_ascii=False))
