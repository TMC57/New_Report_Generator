
# group_parameter.py
import json, os

GROUP_FILE = "GroupConfigJson.json"

def build_group_config_from_devices_list(devices_list_json: dict):
    """
    Add-only: lit l'existant GroupConfigJson.json, backfill les champs qui manquent,
    et AJOUTE un bloc par owner absent. Ne modifie pas les owners déjà présents.
    """
    # 1) Charger l'existant (ou liste vide)
    output = []
    if os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            try:
                output = json.load(f)
            except json.JSONDecodeError:
                output = []

    # 2) Backfill des champs attendus (comme Json_parameter.py)
    def ensure_group_fields(item: dict) -> dict:
        item.setdefault("owner", "OWNER_INCONNU")
        item.setdefault("facilities", [])  # RO dans l'UI; on ne la modifie pas ici
        item.setdefault("cover_picture", "")
        item.setdefault("inventory_monitoring_manager", {
            "full_name": "", "mail_adresse": "", "phone_number": ""
        })
        item.setdefault("customer_technical_relay_manager", {
            "full_name": "", "mail_adresse": "", "phone_number": ""
        })
        item.setdefault("file_referent", {
            "full_name": "", "mail_adresse": "", "phone_number": ""
        })
        item.setdefault("primary_company_brand", "")
        return item

    output = [ensure_group_fields(dict(item)) for item in output]

    # 3) Owners déjà présents
    existing_owners = { (item.get("owner") or "OWNER_INCONNU") for item in output }

    # 4) Collecte des owners depuis devices_list_json
    owners_found = set()
    for fac in (devices_list_json or {}).get("data", []) or []:
        owner = fac.get("owner") or "OWNER_INCONNU"
        owners_found.add(owner)

    # 5) Ajouter un bloc pour chaque owner absent (ADD-ONLY)
    for owner in sorted(owners_found):
        if owner not in existing_owners:
            # Option: initialiser la liste de sites visibles en RO à la création
            facilities = []
            for fac in (devices_list_json or {}).get("data", []) or []:
                if (fac.get("owner") or "OWNER_INCONNU") == owner:
                    facilities.append({
                        "facilityId": fac.get("facilityId"),
                        "facilityName": fac.get("facilityName")
                    })
            output.append(ensure_group_fields({
                "owner": owner,
                "facilities": facilities,
                "cover_picture": "",
                "inventory_monitoring_manager": {
                    "full_name": "", "mail_adresse": "", "phone_number": ""
                },
                "customer_technical_relay_manager": {
                    "full_name": "", "mail_adresse": "", "phone_number": ""
                },
                "file_referent": {
                    "full_name": "", "mail_adresse": "", "phone_number": ""
                },
                "primary_company_brand": ""
            }))

    # 6) Écrire le fichier (sans retirer l'existant)
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return {"groups": output}
