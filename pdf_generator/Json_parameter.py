import json
import os

def transform_facility_json(input_json):
    facilities = input_json.get("data", {}).get("results", [])
    output = []

    # Lire le fichier existant si présent
    if os.path.exists("configJson.json"):
        with open("configJson.json", "r", encoding="utf-8") as f:
            try:
                output = json.load(f)
            except json.JSONDecodeError:
                output = []  # Si le fichier est vide ou corrompu

    # Créer une liste des IDs existants
    existing_ids = {item.get("ID") for item in output}

    for facility in facilities:
        facility_id = facility.get("facilityId")

        # Ajouter seulement si l'ID n'existe pas déjà
        if facility_id not in existing_ids:
            entry = {
                "ID": facility_id,  # Nouveau champ ID
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
                "primary_company_brand": ""
            }
            output.append(entry)

    # Réécriture du fichier avec l'ensemble des données
    with open("configJson.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    return {"facilities": output}
