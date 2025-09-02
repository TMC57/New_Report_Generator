import json
import os

def transform_facility_json(input_json):
    facilities = input_json.get("data", [])
    output = []

    # Lire l'existant s'il existe
    if os.path.exists("Config/configJson.json"):
        with open("Config/configJson.json", "r", encoding="utf-8") as f:
            try:
                output = json.load(f)
            except json.JSONDecodeError:
                output = []  # fichier vide/corrompu

    # --- Backfill: garantir que chaque item possède les 2 nouveaux champs ---
    def ensure_custom_fields(item: dict):
        # On utilise exactement les libellés demandés comme clés JSON
        # (accents et espaces autorisés). table.html les gère en notation bracket.
        item.setdefault("dernière intervention", "")
        item.setdefault("relevés buses", "")
        return item

    # marquer les IDs existants
    existing_ids = {item.get("ID") for item in output}

    # 1) compléter les existants
    output = [ensure_custom_fields(dict(item)) for item in output]

    # 2) créer les nouveaux
    for facility in facilities:
        facility_id = facility.get("facilityId")
        if facility_id not in existing_ids:
            entry = {
                "ID": facility_id,
                "facilityId": facility_id,
                "facilityName": facility.get("facilityName"),
                "cover_picture": "",
                "material_picture": "",
                "inventory_monitoring_manager": {
                    "full_name": "",
                    "mail_adresse": "",
                    "phone_number": ""
                },
                "customer_technical_relay_manager": {
                    "full_name": "",
                    "mail_adresse": "",
                    "phone_number": ""
                },
                "file_referent": {
                    "full_name": "",
                    "mail_adresse": "",
                    "phone_number": ""
                },
                "primary_company_brand": "",
    
                "dernière intervention": "",
                "relevés buses": "",
            }
            output.append(entry)

    # Écriture
    with open("Config/configJson.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    return {"facilities": output}
