import xmlrpc.client
import requests
import re

def nettoyer_prix(prix):
    s = str(prix)
    # Garder uniquement chiffres et virgules
    s = re.sub(r"[^0-9,]", "", s)
    # Remplacer virgule par point décimal
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        print(f"Impossible de convertir '{s}' en float")
        return None

# --- Connexion Odoo ---
url = "https://tmh-corporation.odoo.com"
db = "tmh-corporation"
username = "thomas.moreau@epitech.eu"
password = "X85jNPaw"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

if not uid:
    print("Erreur d'authentification Odoo")
    exit()

models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

records = models.execute_kw(
    db, uid, password,
    'product.pricelist.item', 'search_read',
    [[]],
    {'fields': ["id", "price", "x_studio_id_webflow", "display_name"], 'limit': 10}
)

print(f"{len(records)} enregistrements récupérés depuis Odoo.")

# --- Mise à jour Webflow ---
token = "505b31e4f5fab8918657fb941a354c92981d81be9da8e180693959e5b739b641"
collection_id = "5f1e86981034731b32c4665e"
champ_prix = "prix-vente-tvac-ciel"
base_url = "https://api.webflow.com/v2"

headers = {
    "Authorization": f"Bearer {token}",
    "accept-version": "1.0.0",
    "Content-Type": "application/json"
}

for r in records:
    item_id = r.get("x_studio_id_webflow")
    nom_produit = r.get("display_name")
    nouveau_prix = r.get("price")

    if not item_id:
        print(f"Produit Odoo ID {r['id']} sans x_studio_id_webflow, skip.\n")
        continue
    if nouveau_prix is None:
        print(f"Produit Odoo ID {r['id']} sans prix, skip.\n")
        continue

    nouveau_prix = nettoyer_prix(nouveau_prix)
    if nouveau_prix is None:
        print(f"Prix invalide pour item {item_id}, skip.")
        continue

    print(f"   Mise à jour du produit Webflow ID {item_id} avec le prix : {nouveau_prix}")

    url = f"{base_url}/collections/{collection_id}/items/{item_id}/live"
    body = {"fieldData": {champ_prix: nouveau_prix}}

    response = requests.patch(url, json=body, headers=headers)

    if response.status_code == 200:
        print(f"✅ \033[1;32mMise à jour réussie pour item {item_id} ({nom_produit}) \n   nouveau prix {nouveau_prix}\033[0m\n")
    else:
        print(f"❌ Erreur mise à jour item {item_id} : {response.status_code} - {response.text}\n")
