import xmlrpc.client
import requests
import re

# ========== CONFIG ODOO ==========
url = "https://tmh-corporation.odoo.com"
db = "tmh-corporation"
username = "thomas.moreau@epitech.eu"
password = "X85jNPaw"

# ========== CONFIG WEBFLOW ==========
API_TOKEN = "505b31e4f5fab8918657fb941a354c92981d81be9da8e180693959e5b739b641"
COLLECTION_ID = "5f1e86981034731b32c4665e"
CHAMP_PRIX = "prix-vente-tvac-ciel"

headers_webflow = {
    "Authorization": f"Bearer {API_TOKEN}",
    "accept-version": "1.0.0",
    "Content-Type": "application/json"
}

# ========== CONNEXION ODOO ==========
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

if not uid:
    print("❌ Erreur d'authentification Odoo")
    exit()

models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
odoo_products = models.execute_kw(
    db, uid, password,
    'product.pricelist.item', 'search_read',
    [[]],
    {'fields': ["id", "price", "x_studio_id_webflow", "name"], 'limit': 1000}
)

print(f"✅ Produits Odoo récupérés : {len(odoo_products)}")

# ========== RÉCUPÉRATION DES PRODUITS WEBFLOW ==========
webflow_products = []
limit = 100
offset = 0

while True:
    params = {"limit": limit, "offset": offset}
    url_items = f"https://api.webflow.com/v2/collections/{COLLECTION_ID}/items"
    response = requests.get(url_items, headers=headers_webflow, params=params)
    response.raise_for_status()

    items = response.json().get("items", [])
    if not items:
        break

    webflow_products.extend(items)
    offset += len(items)

print(f"✅ Produits Webflow récupérés : {len(webflow_products)}")

# Dictionnaire pour accès rapide aux produits Webflow par ID
webflow_dict = {item["id"]: item for item in webflow_products}

# ========== UTILITAIRE DE NETTOYAGE ==========
def nettoyer_prix(valeur):
    if valeur is None:
        return None
    if isinstance(valeur, str):
        valeur = re.sub(r"[^\d,\.]", "", valeur.replace(" ", "").replace("\u00a0", ""))
    valeur = str(valeur).replace(",", ".")
    try:
        return round(float(valeur), 2)
    except ValueError:
        return None

# ========== COMPARAISON & MISE À JOUR ==========
for produit in odoo_products:
    webflow_id = produit.get("x_studio_id_webflow")
    odoo_price = nettoyer_prix(produit.get("price"))
    odoo_name = produit.get("name", "Nom inconnu")

    if not webflow_id or webflow_id not in webflow_dict:
        continue  # Pas de correspondance

    webflow_item = webflow_dict[webflow_id]
    webflow_price = nettoyer_prix(webflow_item["fieldData"].get(CHAMP_PRIX))
    webflow_name = webflow_item["fieldData"].get("name", "Nom inconnu")

    # Print pour chaque produit avec le nom
    print(f"\n🟦 Odoo → ID: {produit['id']} | Nom: {odoo_name} | Prix: {odoo_price}")
    print(f"🟨 Webflow → ID: {webflow_id} | Nom: {webflow_name} | Prix: {webflow_price}")

    if odoo_price is None or webflow_price is None:
        print("⚠️ Prix non valide, on saute")
        continue

    if odoo_price != webflow_price:
        # Mise à jour Webflow
        patch_url = f"https://api.webflow.com/v2/collections/{COLLECTION_ID}/items/{webflow_id}/live"
        body = {
            "fieldData": {
                CHAMP_PRIX: odoo_price
            }
        }

        response = requests.patch(patch_url, headers=headers_webflow, json=body)

        if response.status_code == 200:
            print(f"✅ Prix mis à jour → {webflow_name} | Ancien : {webflow_price} | Nouveau : {odoo_price}")
        else:
            print(f"❌ Erreur mise à jour {webflow_name} ({webflow_id}) : {response.status_code} - {response.text}")
    else:
        print(f"✔️ Aucun changement requis pour {webflow_name}")
