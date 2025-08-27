# group_parameter.py  (ou dans Json_parameter.py si tu préfères)
import json, os

GROUP_FILE = "GroupConfigJson.json"

def build_group_config_from_devices_list(devices_list_json: dict) -> dict:
    """
    Construit/maintient GroupConfigJson.json : un item par 'owner' unique.
    Chaque item reprend la même logique que configJson.json (champs éditables).
    """
    # Charger l'existant si présent (pour ne pas perdre les valeurs déjà saisies)
    existing = []
    if os.path.exists(GROUP_FILE):
        try:
            with open(GROUP_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    # index existant par owner
    by_owner = {item.get("owner"): item for item in existing}

    # Collecter les owners + la liste des sites rattachés
    owners = {}
    for fac in (devices_list_json or {}).get("data", []):
        owner = fac.get("owner") or "OWNER_INCONNU"
        owners.setdefault(owner, {"owner": owner, "facilities": []})
        owners[owner]["facilities"].append({
            "facilityId": fac.get("facilityId"),
            "facilityName": fac.get("facilityName"),
        })

    # Gabarit d’un enregistrement “groupe” (similaire à configJson.json)
    def empty_group(owner: str, facilities: list):
        return {
            "owner": owner,
            "facilities": facilities,  # affichage en lecture seule dans l’UI
            "cover_picture": "",
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


    # Fusion : on conserve les champs déjà saisis si l’owner existe
    output = []
    for owner, payload in owners.items():
        facilities = payload["facilities"]
        if owner in by_owner:
            item = by_owner[owner]
            item["facilities"] = facilities  # rafraîchir la liste des sites
        else:
            item = empty_group(owner, facilities)
        output.append(item)

    # Écrire le fichier
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return {"groups": output}
