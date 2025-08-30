import requests
import json
from MyTime import date_tsd


def body_detailed(from_date, to_date, facility_id=None):
    api_key = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1MTg5NzQ3MTI2MywibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.XDDPirczrQmymN3nXIwPb03JlipsNUXo_jbR053fqaQ"
    headers = {"Authorization": f"Bearer {api_key}"}

    params = {
        "pageNumber": 1,
        "pageSize": 10,  # valeur max supportée par l'API (souvent 500 ou 1000)
        "fromDate": date_tsd(from_date, "%Y-%m-%d"),
        "thruDate": date_tsd(to_date, "%Y-%m-%d"),
        "reportType": "total-qty-facility",
    }
    if facility_id is not None:
        params["facilityId"] = facility_id

    endpoint = "/detailed-report"
    return endpoint, headers, params    


def fetch_all(from_date, to_date, facility_id=None):
    base_url = "https://app.cm2w.net/cm2w-api/v2/api-key-auth"
    endpoint, headers, params = body_detailed(from_date, to_date, facility_id)

    all_results = []
    page = 1

    while True:
        params["pageNumber"] = page
        response = requests.get(base_url + endpoint, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            break

        data = response.json()
        results = data.get("data", {}).get("results", [])

        if not results:
            break

        for item in results:
            serial = item.get("serialNumber")
            event_date = item.get("eventDate")
            event_id = item.get("eventId")

            # Certains events peuvent avoir plusieurs products
            products = item.get("products", [])
            if products:
                for product in products:
                    product_id = product.get("productId")
                    all_results.append({
                        "serialNumber": serial,
                        "eventDate": event_date,
                        "eventId": event_id,
                        "productId": product_id
                    })
            else:
                all_results.append({
                    "serialNumber": serial,
                    "eventDate": event_date,
                    "eventId": event_id,
                    "productId": None
                })

        print(f"📄 Page {page} récupérée ({len(results)} éléments bruts)")

        # stop si plus de pages
        if "totalPages" in data.get("data", {}) and page >= data["data"]["totalPages"]:
            break

        page += 1

    return all_results


if __name__ == "__main__":
    results = fetch_all("2025-01-01", "2025-01-31", facility_id=27789)

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"✅ {len(results)} événements enregistrés dans result.json")
