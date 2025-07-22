def transform_facility_json(input_json):
    facilities = input_json.get("data", {}).get("results", [])
    output = []

    for facility in facilities:
        entry = {
            "facilityId": facility.get("facilityId"),
            "facilityName": facility.get("facilityName"),
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
        output.append(entry)

    return {"facilities": output}
