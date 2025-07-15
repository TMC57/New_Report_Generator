from model import model
from datetime import datetime, timedelta
from bodys import body_total_qty_report


def get_total_qty_every_days(Json_to_fill, from_date, to_date):
    current_date = datetime.strptime(from_date, "%Y-%m-%d")
    end_date = datetime.strptime(to_date, "%Y-%m-%d")
    date_str_to = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        date_str_to = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")

        # Appel API pour ce jour
        endpoint, headers, params = body_total_qty_report(
            from_date=date_str,
            to_date=date_str_to
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
