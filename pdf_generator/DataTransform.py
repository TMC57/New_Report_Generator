from model import model, body_total_qty_report
from datetime import datetime, timedelta
from calendar import monthrange
import re
from collections import OrderedDict
from collections import defaultdict
from typing import Dict, Any, List

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
      - total_qty_json: JSON de "total quantity" (clé data.results avec [{ facilityId, facilityName, products:[{name, qty}, ...] }, ...])
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
                  {"name": "...", "qty": <somme>},
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
        "totalQty": 0,
        "facilities": defaultdict(lambda: {
            "facilityId": None,
            "facilityName": "",
            "totalQty": 0,
            "products": defaultdict(int)  # name -> qty
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
        for p in row.get("products", []) or []:
            pname = (p.get("name") or "UNKNOWN PRODUCT").strip()
            qty = p.get("qty") or 0
            try:
                qty = float(qty)
            except Exception:
                qty = 0.0

            fac_bucket["products"][pname] += qty
            fac_bucket["totalQty"] += qty
            owner_bucket["totalQty"] += qty

    # 3) Mise en forme finale (transformer les defaultdict en listes propres)
    owners_list = []
    for owner_name, ob in owners.items():
        facilities_list = []
        for fac_id, fb in ob["facilities"].items():
            products_list = [{"name": n, "qty": v} for n, v in sorted(fb["products"].items())]
            facilities_list.append({
                "facilityId": fb["facilityId"],
                "facilityName": fb["facilityName"],
                "totalQty": fb["totalQty"],
                "products": products_list
            })
        # trier les facilities par nom (ou id)
        facilities_list.sort(key=lambda x: (x["facilityName"] or "", x["facilityId"] or 0))
        owners_list.append({
            "owner": ob["owner"] or owner_name,
            "totalQty": ob["totalQty"],
            "facilities": facilities_list
        })

    # trier les owners par nom
    owners_list.sort(key=lambda x: x["owner"] or "")
    return {"owners": owners_list}
