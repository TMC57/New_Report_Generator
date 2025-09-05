from model import model, body_total_qty_report
from datetime import datetime, timedelta
from calendar import monthrange
import re
from collections import OrderedDict
from collections import defaultdict
from typing import Dict, Any, List, Tuple

def get_total_qty_every_days(Json_to_fill, from_date, to_date, facilityId=None):
    current_date = datetime.strptime(from_date, "%Y-%m-%d")
    end_date = datetime.strptime(to_date, "%Y-%m-%d")
    date_str_to = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        date_str_to = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")

        # Appel API pour ce jour
        endpoint, headers, params = body_total_qty_report(
            date_str,
            date_str_to,
            facilityId
        )
        response = model(endpoint, headers, params)

        if response.status_code != 200:
            print(f"Erreur API pour {date_str} : {response.status_code}")
            current_date += timedelta(days=1)
            continue

        daily_data = response.json().get("data", {}).get("results", [])

        for daily_facility in daily_data:
            facility_id = daily_facility["facilityId"]
            
            # On cherche la facility correspondante dans Json_to_fill
            target_facility = next((f for f in Json_to_fill["data"]["results"] if f["facilityId"] == facility_id), None)

            if not target_facility:
                continue  # Facility pas présente dans le JSON de base

            for daily_product in daily_facility.get("products", []):
                product_id = daily_product["_id"]
                qty = daily_product["qty"]

                # On cherche le produit correspondant dans cette facility
                target_product = next((p for p in target_facility["products"] if p["_id"] == product_id), None)
                if not target_product:
                    continue  # Produit pas dans le JSON de base

                # Ajout du champ dailyQuantities s'il n'existe pas
                if "dailyQuantities" not in target_product:
                    target_product["dailyQuantities"] = []

                # On ajoute l'entrée pour ce jour
                target_product["dailyQuantities"].append({
                    "date": date_str,
                    "qty": qty
                })

        current_date += timedelta(days=1)

    return(Json_to_fill)



def get_total_qty_every_month(Json_to_fill, to_date, facilityId=None):
    """
    Récupère les quantités pour les 12 derniers mois (inclus le mois de `to_date`).
    Exemple : to_date = 2025-03-30 -> on prend d'office :
      2024-04, 2024-05, ..., 2025-02, 2025-03
    Les résultats sont stockés dans `MonthlyQuantities`.
    """
    end_date = datetime.strptime(to_date, "%Y-%m-%d")

    # --- Helpers ----------------------------------------------------------------
    def first_day_of_month(dt: datetime) -> datetime:
        return datetime(dt.year, dt.month, 1)

    def add_months(dt: datetime, n: int) -> datetime:
        """Retourne le 1er jour du mois `n` mois après (ou avant si n<0) `dt`."""
        y = dt.year + (dt.month - 1 + n) // 12
        m = (dt.month - 1 + n) % 12 + 1
        return datetime(y, m, 1)
    # ----------------------------------------------------------------------------

    # Point de départ : 11 mois avant le mois de to_date
    start_month = add_months(first_day_of_month(end_date), -11)

    # Boucle sur 12 mois exactement
    current = start_month
    for _ in range(12):
        # Début du mois courant
        start_of_month = datetime(current.year, current.month, 1)

        # Dernier jour du mois courant
        last_day = monthrange(current.year, current.month)[1]
        end_of_month = datetime(current.year, current.month, last_day)

        # Pour le tout dernier mois (celui de to_date), on tronque éventuellement à to_date
        # si tu préfères couvrir le mois entier malgré tout, supprime cette ligne.
        if (current.year == end_date.year and current.month == end_date.month) and end_of_month > end_date:
            end_of_month = end_date

        # Formats YYYY-MM-DD
        date_from = start_of_month.strftime("%Y-%m-%d")
        # On ajoute un jour pour couvrir le dernier jour du mois
        date_to = (end_of_month + timedelta(days=1)).strftime("%Y-%m-%d")

        # Appel API
        endpoint, headers, params = body_total_qty_report(
            date_from,
            date_to,
            facilityId
        )
        response = model(endpoint, headers, params)

        if response.status_code != 200:
            print(f"Erreur API pour {date_from} -> {date_to} : {response.status_code}")
            # Passer au mois suivant
            current = add_months(current, 1)
            continue

        monthly_data = response.json().get("data", {}).get("results", [])

        for monthly_facility in monthly_data:
            facility_id = monthly_facility["facilityId"]

            # Chercher la facility correspondante dans Json_to_fill
            target_facility = next(
                (f for f in Json_to_fill["data"]["results"] if f["facilityId"] == facility_id),
                None
            )
            if not target_facility:
                continue  # Facility absente dans le JSON de base

            for monthly_product in monthly_facility.get("products", []):
                product_id = monthly_product["_id"]
                qty = monthly_product["qty"]

                # Chercher le produit correspondant
                target_product = next(
                    (p for p in target_facility["products"] if p["_id"] == product_id),
                    None
                )
                if not target_product:
                    continue  # Produit absent dans le JSON de base

                # Créer le champ MonthlyQuantities si nécessaire
                if "MonthlyQuantities" not in target_product:
                    target_product["MonthlyQuantities"] = []

                target_product["MonthlyQuantities"].append({
                    "month": start_of_month.strftime("%Y-%m"),
                    "from": date_from,
                    "to": date_to,
                    "qty": qty
                })

        # Passer au mois suivant
        current = add_months(current, 1)

    return Json_to_fill



def enrich_json_with_zone(json_data):
    zone_patterns = [
        r"zone\s*(\d+)",  # "zone 1", "Zone 2"
        r"z(\d+)",        # "z1", "Z2"
    ]

    for facility in json_data["data"]["results"]:
        for product in facility.get("products", []):
            name = product.get("name", "").lower()
            product["zone"] = None  # valeur par défaut
            for pattern in zone_patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    product["zone"] = f"ZONE {match.group(1)}"
                    break  # on garde la première correspondance
            if product["zone"] is None:
                product["zone"] = "GLOBAL"  # si aucune zone trouvée

    return json_data


def group_qty_by_owner_and_facility(total_qty_json: Dict[str, Any],
                                    devices_list_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agrège les quantités consommées par produit, regroupées par owner puis par facility.

    Entrées:
      - total_qty_json: JSON de "total quantity" (clé data.results avec [{ facilityId, facilityName, products:[{productId, name, qty}, ...] }, ...])
      - devices_list_json: JSON de "device list" (clé data: [{ owner, facilityId, facilityName, ... }, ...])

    Sortie:
      {
        "owners": [
          {
            "owner": "...",
            "totalQty": <somme de toutes les qty du groupe>,
            "facilities": [
              {
                "facilityId": ...,
                "facilityName": "...",
                "totalQty": <somme de toutes les qty de la facility>,
                "products": [
                  {"productId": 214059, "name": "WNC40 Vannes", "qty": <somme>},
                  ...
                ]
              },
              ...
            ]
          },
          ...
        ]
      }
    """
    # 1) Dictionnaire: facilityId -> (owner, facilityName)
    fac_to_owner: Dict[int, Dict[str, str]] = {}
    for fac in (devices_list_json or {}).get("data", []):
        fac_to_owner[fac.get("facilityId")] = {
            "owner": fac.get("owner") or "OWNER_INCONNU",
            "facilityName": fac.get("facilityName") or ""
        }

    # 2) Agrégation par owner -> facility -> product
    owners = defaultdict(lambda: {
        "owner": None,
        "totalQty": 0.0,
        "facilities": defaultdict(lambda: {
            "facilityId": None,
            "facilityName": "",
            "totalQty": 0.0,
            # On stocke productId et nom séparés
            "products": defaultdict(lambda: {"productId": None, "name": "", "qty": 0.0})
        })
    })

    results: List[Dict[str, Any]] = (total_qty_json or {}).get("data", {}).get("results", []) or []
    for row in results:
        fac_id = row.get("facilityId")
        fac_name = row.get("facilityName") or ""
        meta = fac_to_owner.get(fac_id, {"owner": "OWNER_INCONNU", "facilityName": fac_name})
        owner_name = meta["owner"]

        # Initialise structures
        owner_bucket = owners[owner_name]
        owner_bucket["owner"] = owner_name
        fac_bucket = owner_bucket["facilities"][fac_id]
        fac_bucket["facilityId"] = fac_id
        fac_bucket["facilityName"] = fac_name or meta.get("facilityName", "")

        # Produits pour cette ligne
        for p in (row.get("products") or []):
            pname_raw = (p.get("name") or "UNKNOWN PRODUCT").strip()
            # nettoie le nom -> supprime l'ID déjà présent au début
            pname_clean = re.sub(r'^\s*\d+\s+', '', pname_raw)

            pid = p.get("productId")

            # qty -> float robuste
            qty = p.get("qty") or 0
            try:
                qty = float(qty)
            except Exception:
                qty = 0.0

            # clé d'agrégation = productId si dispo, sinon nom
            product_key = pid if pid is not None else pname_clean

            # Récupère/initialise le bucket produit
            prod_bucket = fac_bucket["products"][product_key]
            if not prod_bucket["name"]:
                prod_bucket["name"] = pname_clean
            if prod_bucket["productId"] is None and pid is not None:
                prod_bucket["productId"] = pid

            prod_bucket["qty"] += qty
            fac_bucket["totalQty"] += qty
            owner_bucket["totalQty"] += qty

    # 3) Mise en forme finale
    owners_list = []
    for owner_name, ob in owners.items():
        facilities_list = []
        for fac_id, fb in ob["facilities"].items():
            products_list = sorted(
                fb["products"].values(),
                key=lambda pr: (pr["name"] or "")
            )
            facilities_list.append({
                "facilityId": fb["facilityId"],
                "facilityName": fb["facilityName"],
                "totalQty": fb["totalQty"],
                "products": products_list
            })
        facilities_list.sort(key=lambda x: (x["facilityName"] or "", x["facilityId"] or 0))
        owners_list.append({
            "owner": ob["owner"] or owner_name,
            "totalQty": ob["totalQty"],
            "facilities": facilities_list
        })

    owners_list.sort(key=lambda x: x["owner"] or "")
    return {"owners": owners_list}




def enrich_qty_with_stock_products(qty_json: Dict[str, Any],
                                   stock_json: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Vérifie, facility par facility, que tous les produits du stock (stock_json)
    existent dans qty_json. Si un produit manque, on l'ajoute avec un "squelette"
    de produit conforme à qty (sans dailyQuantities / MonthlyQuantities).

    Retourne: (qty_json_modifié, nb_produits_ajoutés)
    """
    def _norm(s):
        return (s or "").strip().lower()

    # 1) Accès aux sections utiles (tolérant aux absences)
    qty_root = (qty_json or {}).setdefault("data", {}).setdefault("results", [])
    stock_root = (stock_json or {}).get("data", []) or []

    # 2) Indexe qty par facilityId
    fac_index = {item.get("facilityId"): item for item in qty_root}

    added = 0

    for fac in stock_root:
        fac_id = fac.get("facilityId")
        fac_name = fac.get("facilityName") or ""

        if fac_id is None:
            continue

        # a) Récupère (ou crée) l'entrée facility côté qty
        if fac_id not in fac_index:
            # Structure calquée sur ton gty.txt (valeurs génériques) :contentReference[oaicite:1]{index=1}
            new_fac = {
                "_id": fac_id,
                "facilityId": fac_id,
                "facilityName": fac_name,
                "lq": 0,
                "lQty": 0,
                "products": [],
                "clientPrice": 0,
                "clientCur": None,
                # weekly bins (si présents dans tes autres résultats)
                "w0": 0, "w1": 0, "w2": 0, "w3": 0, "w4": 0, "w5": 0, "w6": 0, "w7": 0, "w8": 0, "w9": 0,
                # borne temporelle si besoin ; on laisse vide si on ne l’a pas
                # "tsd": None,
            }
            qty_root.append(new_fac)
            fac_index[fac_id] = new_fac

        qty_fac_entry = fac_index[fac_id]
        qty_products = qty_fac_entry.setdefault("products", [])

        # b) Ensemble des produits déjà présents (par id et par nom normalisé)
        existing_ids = set()
        existing_names = set()
        for p in qty_products:
            if p.get("productId") is not None:
                existing_ids.add(p["productId"])
            existing_names.add(_norm(p.get("name")))

        # c) Parcourt les produits du stock, et ajoute les manquants
        for sp in (fac.get("products") or []):
            pid = sp.get("productId")
            pname = sp.get("productName") or ""

            # Critères d'existence: productId OU nom normalisé
            already = (pid in existing_ids) or (_norm(pname) in existing_names)
            if already:
                continue

            # Squelette produit calqué sur gty.txt (sans daily/monthly) :contentReference[oaicite:2]{index=2}
            new_product = {
                "_id": pid,
                "productId": pid,
                "name": pname,
                "qty": 0,          # quantité totale (brute, en unités "source")
                "price": 0.0,
                "cur": "eu",       # cohérent avec tes exemples
                "gr": 0,
                "isSolid": False,
                "ratio": 1.0,
                "dailyQuantities": [],      # ← vide (pas de données)
                "MonthlyQuantities": [],    # ← vide (pas de données)
                "zone": sp.get("zone", ""), # stockLvl ne l’a pas toujours ; on met "" si absent
            }
            qty_products.append(new_product)
            # mets à jour les sets pour éviter doublons au sein de la même facility
            if pid is not None:
                existing_ids.add(pid)
            existing_names.add(_norm(pname))
            added += 1

    return qty_json#, added


def enrich_qty_with_stock_products2(qty_json: dict, stocks_json: dict) -> dict:
    """
    Aligne les noms de produits dans qty_json à partir de stocks_json en matchant par productId.
    - qty_json : dict avec data.results -> facilities -> products[] (champ 'name')
    - stocks_json : dict avec data -> facilities -> products[] (champ 'productName')
    Modifie qty_json en place et le retourne.
    """
    # 1) Construire un index productId -> productName depuis stocks_json
    pid_to_stock_name = {}
    try:
        for fac in (stocks_json.get("data") or []):
            for sp in (fac.get("products") or []):
                pid = sp.get("productId")
                pname = sp.get("productName") or sp.get("name")  # fallback si jamais
                if pid is not None and pname:
                    pid_to_stock_name[pid] = pname
    except AttributeError:
        # Si jamais stocks_json["data"] n'est pas une liste
        pass

    # 2) Parcourir qty_json et remplacer les noms si différents
    try:
        for fac in (qty_json.get("data", {}).get("results") or []):
            for qp in (fac.get("products") or []):
                pid = qp.get("productId")
                stock_name = pid_to_stock_name.get(pid)
                if not stock_name:
                    continue
                cur = qp.get("name") or qp.get("productName") or qp.get("ProductName")
                if cur != stock_name:
                    qp["name"] = stock_name
                    if "productName" in qp:
                        qp["productName"] = stock_name
                    if "ProductName" in qp:
                        qp["ProductName"] = stock_name
    except AttributeError:
        # Si jamais qty_json n'a pas la structure attendue, on ne plante pas
        pass

    return qty_json


def reconcile_qty_ids_with_stocklevels(
    qty_json: Dict[str, Any],
    stock_levels_json: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Compare les noms des produits entre qty_json et stock_levels_json.
    Si le nom diffère pour un même productId, on essaie de retrouver le productId
    correct dans stockLevels (priorité même facility, sinon global) et on met à jour.

    Retourne: (qty_modifié, corrections)
    """

    # --- 1) Index stockLevels ---
    data = (stock_levels_json or {}).get("data", []) or []

    by_fac_id_to_name = {}     # (facilityId, productId) -> productName
    by_fac_name_to_id = {}     # (facilityId, productName) -> productId
    global_id_to_name = {}     # productId -> productName
    global_name_to_id = {}     # productName -> productId

    for fac in data:
        f_id = fac.get("facilityId")
        for pr in fac.get("products", []) or []:
            pid = pr.get("productId")
            pname = pr.get("productName") or ""
            if f_id is not None and pid is not None:
                by_fac_id_to_name[(f_id, pid)] = pname
                by_fac_name_to_id[(f_id, pname)] = pid
            if pid is not None:
                global_id_to_name[pid] = pname
            if pname:
                global_name_to_id[pname] = pid

    # --- 2) Parcours qty & corrections ---
    qty_mod = qty_json
    corrections: List[Dict[str, Any]] = []

    for owner in (qty_mod or {}).get("owners", []) or []:
        for fac in owner.get("facilities", []) or []:
            f_id = fac.get("facilityId")
            products = fac.get("products", []) or []
            for p in products:
                pid_old = p.get("productId")
                qty_name = p.get("name") or ""

                # Nom en stockLevels pour l'ID courant
                stock_name_for_old = None
                if f_id is not None and pid_old is not None:
                    stock_name_for_old = by_fac_id_to_name.get((f_id, pid_old))
                if stock_name_for_old is None and pid_old is not None:
                    stock_name_for_old = global_id_to_name.get(pid_old)

                if not stock_name_for_old:
                    continue

                # Si noms identiques -> OK
                if stock_name_for_old == qty_name:
                    continue

                # Sinon, chercher l'ID du nom qty dans stockLevels
                pid_new = None
                if f_id is not None:
                    pid_new = by_fac_name_to_id.get((f_id, qty_name))
                if pid_new is None:
                    pid_new = global_name_to_id.get(qty_name)

                if pid_new is not None and pid_new != pid_old:
                    p["productId"] = pid_new
                    corrections.append({
                        "facilityId": f_id,
                        "oldProductId": pid_old,
                        "newProductId": pid_new,
                        "qtyName": qty_name,
                        "oldIdStockName": stock_name_for_old,
                        "matchedStockName": global_id_to_name.get(pid_new)
                    })

    return qty_mod, corrections


def group_stocklevels_by_owner_and_facility(
    stock_levels_json: Dict[str, Any],
    devices_list_json: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Regroupe les données de stockLevels par owner -> facility -> products
    en gardant remainingQuantity, averageDailyConsumption, remainingDays,
    et conserve le champ currentTime dans le JSON.
    """

    # 1) facilityId -> owner, facilityName
    fac_to_owner: Dict[int, Dict[str, str]] = {}
    for fac in (devices_list_json or {}).get("data", []):
        fac_to_owner[fac.get("facilityId")] = {
            "owner": fac.get("owner") or "OWNER_INCONNU",
            "facilityName": fac.get("facilityName") or ""
        }

    # 2) Agrégation par owner -> facility
    owners = defaultdict(lambda: {
        "owner": None,
        "facilities": defaultdict(lambda: {
            "facilityId": None,
            "facilityName": "",
            "products": []
        })
    })

    results: List[Dict[str, Any]] = (stock_levels_json or {}).get("data", []) or []
    for row in results:
        fac_id = row.get("facilityId")
        meta = fac_to_owner.get(
            fac_id,
            {"owner": "OWNER_INCONNU", "facilityName": row.get("facilityName", "")}
        )
        owner_name = meta["owner"]

        owner_bucket = owners[owner_name]
        owner_bucket["owner"] = owner_name

        fac_bucket = owner_bucket["facilities"][fac_id]
        fac_bucket["facilityId"] = fac_id
        fac_bucket["facilityName"] = meta.get("facilityName", "")

        # Produits
        for p in (row.get("products") or []):
            fac_bucket["products"].append({
                "productId": p.get("productId"),
                "name": p.get("productName") or "",
                "remainingQuantity": p.get("remainingQuantity") or 0,
                "averageDailyConsumption": p.get("averageDailyConsumption") or 0,
                "remainingDays": p.get("remainingDays") or 0
            })

    # 3) Mise en forme finale
    owners_list = []
    for owner_name, ob in owners.items():
        facilities_list = []
        for fac_id, fb in ob["facilities"].items():
            products_list = sorted(fb["products"], key=lambda pr: pr["name"])
            facilities_list.append({
                "facilityId": fb["facilityId"],
                "facilityName": fb["facilityName"],
                "products": products_list
            })
        facilities_list.sort(key=lambda x: (x["facilityName"] or "", x["facilityId"] or 0))
        owners_list.append({
            "owner": ob["owner"] or owner_name,
            "facilities": facilities_list
        })

    owners_list.sort(key=lambda x: x["owner"] or "")

    # 4) On garde currentTime dans la structure du JSON final
    return {
        "owners": owners_list,
        "currentTime": stock_levels_json.get("currentTime")
    }
