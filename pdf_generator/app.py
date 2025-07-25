from model import model, body_total_qty_report
from datetime import datetime, timedelta
from calendar import monthrange

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
        date_to   = end_of_month.strftime("%Y-%m-%d")

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
