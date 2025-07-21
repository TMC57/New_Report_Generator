import requests

# Variables
token = "505b31e4f5fab8918657fb941a354c92981d81be9da8e180693959e5b739b641"
collection_id = "5f1e86981034731b32c4665e"
item_id = "6606aadb917147e2af779bb6"
champ_prix = "prix-vente-tvac-ciel"
nouveau_prix = 666.9

# Construction de l'URL
base_url = "https://api.webflow.com/v2"
url = f"{base_url}/collections/{collection_id}/items/{item_id}/live"

# En-têtes
headers = { 
    "Authorization": f"Bearer {token}",
    "accept-version": "1.0.0",
    "Content-Type": "application/json"
}

# Corps de la requête
body = {
    "fieldData": {
        champ_prix: nouveau_prix
    }
}

# Requête PATCH
response = requests.patch(url, json=body, headers=headers)

# Affichage du résultat
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
