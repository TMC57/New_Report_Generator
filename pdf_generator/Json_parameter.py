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
                "materialPicture": "",
                "primary_company_brand": "",
                "inventory_monitoring_manager_full_name": "",
                "inventory_monitoring_manager_mail_adresse": "",
                "inventory_monitoring_manager_phone_number": "",
                "customer_technical_relay_manager_full_name": "",
                "customer_technical_relay_manager_mail_adresse": "",
                "customer_technical_relay_manager_phone_number": "",
                "file_referent_full_name": "",
                "file_referent_mail_adresse": "",
                "file_referent_phone_number": "",
            }
            output.append(entry)

    # Réécriture du fichier avec l'ensemble des données
    with open("configJson.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    return {"facilities": output}
