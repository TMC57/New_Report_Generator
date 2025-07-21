import xmlrpc.client

# Informations de connexion
url = "https://tmh-corporation.odoo.com"  # Remplacez par l'URL de votre instance Odoo
db = "tmh-corporation"
username = "thomas.moreau@epitech.eu"
password = "X85jNPaw"

# Connexion au serveur XML-RPC
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")

# Authentification
uid = common.authenticate(db, username, password, {})

if uid:
    print(f"Authentification réussie, UID = {uid}")

    # Accès aux méthodes objet
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    
    # context = {'lang': 'en_GB'} # pour prendre un champ dans la langue que l'on veut, a rajouter dans les parametres 'fields'

    # Exemple: récupérer les 10 premiers enregistrements product.pricelist.item
    records = models.execute_kw(
        db, uid, password,
        'product.pricelist.item', 'search_read',
        [[]],  # Critères de recherche (vide = tous)
        {'fields': ["x_studio_nom_du_produit", "id","pricelist_id", "company_id", "currency_id", "product_tmpl_id", "base_pricelist_id", "display_name", "create_date", "price", "x_studio_id_webflow", "x_studio_reference_interne"], 'limit': 10}
    )

    print("Données récupérées:")
    for r in records:
        print(r)

else:
    print("Erreur d'authentification")
