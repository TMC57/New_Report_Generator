"""
Script de test reproduisant EXACTEMENT la logique de l'ancien projet (reportGenerator-tmh)
Basé sur DataTransform.py lignes 9-63
"""
import requests
from datetime import datetime, timedelta
import json

# Configuration (copié de model.py)
API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1NjI4NDQ4MzkxNSwibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.MHOogWqC84PZOBDvl-KlASj07Ly-CuyqBbcIj8KFmsc"
BASE_URL = "https://app.cm2w.net/cm2w-api/v2/api-key-auth"

def date_tsd(date_str, format_str):
    """Convertit une date en timestamp milliseconds (copié de MyTime.py)"""
    dt = datetime.strptime(date_str, format_str)
    return int(dt.timestamp() * 1000)

def body_total_qty_report(from_date, to_date, facility_id=None):
    """Copié de model.py lignes 4-29"""
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    params = {
        "pageNumber": 1,
        "pageSize": 1000000000,
        "fromDate": date_tsd(from_date, "%Y-%m-%d"),
        "thruDate": date_tsd(to_date, "%Y-%m-%d"),
        "reportType": "total-qty-facility",
        "facilityId": None,
    }
    if facility_id is not None:
        params["facilityId"] = facility_id
    
    endpoint = "/total-qty-report"
    
    return endpoint, headers, params

def model(endpoint, headers, params):
    """Copié de model.py lignes 74-77"""
    url = BASE_URL + endpoint
    return requests.get(url, headers=headers, params=params)

def get_total_qty_every_days(Json_to_fill, from_date, to_date, facilityId=None):
    """
    COPIE EXACTE de DataTransform.py lignes 9-63
    Récupère les quantités jour par jour
    """
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

    return Json_to_fill

if __name__ == "__main__":
    FACILITY_ID = 28194
    FROM_DATE = "2026-03-01"
    TO_DATE = "2026-03-14"
    
    print("\n" + "="*80)
    print("🚀 Test avec la logique EXACTE de l'ancien projet")
    print("="*80)
    print(f"Facility: {FACILITY_ID}")
    print(f"Période: {FROM_DATE} → {TO_DATE}")
    print("="*80 + "\n")
    
    # Étape 1: Récupérer les données de base (total sur toute la période)
    print("📊 Étape 1: Récupération des données de base (total période)")
    endpoint, headers, params = body_total_qty_report(FROM_DATE, TO_DATE, FACILITY_ID)
    response = model(endpoint, headers, params)
    
    if response.status_code == 200:
        Json_to_fill = response.json()
        print(f"✅ Données de base récupérées")
        
        # Afficher les totaux de base
        for facility in Json_to_fill.get("data", {}).get("results", []):
            if facility["facilityId"] == FACILITY_ID:
                print(f"\n📦 Produits dans la facility {FACILITY_ID}:")
                for product in facility.get("products", []):
                    print(f"  - {product['name']} (_id={product['_id']}): qty total = {product['qty']}")
        
        # Étape 2: Enrichir avec les données quotidiennes
        print(f"\n📊 Étape 2: Enrichissement avec données quotidiennes")
        print("-" * 80)
        Json_to_fill = get_total_qty_every_days(Json_to_fill, FROM_DATE, TO_DATE, FACILITY_ID)
        
        # Afficher les résultats
        print("\n" + "="*80)
        print("📊 RÉSULTATS FINAUX (logique ancien projet)")
        print("="*80)
        
        for facility in Json_to_fill.get("data", {}).get("results", []):
            if facility["facilityId"] == FACILITY_ID:
                for product in facility.get("products", []):
                    print(f"\n📦 {product['name']} (_id={product['_id']})")
                    print(f"   Total période: {product['qty']}")
                    
                    daily_quantities = product.get("dailyQuantities", [])
                    if daily_quantities:
                        print(f"   Données quotidiennes ({len(daily_quantities)} jours):")
                        for day in daily_quantities:
                            qty = day['qty']
                            print(f"     {day['date']}: qty={qty} | ÷10={qty/10:.1f} mL | ÷10000={qty/10000:.3f} L")
                    else:
                        print("   ⚠️ Aucune donnée quotidienne")
        
        # Sauvegarder le résultat
        output_file = f"old_logic_result_facility_{FACILITY_ID}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(Json_to_fill, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultat complet sauvegardé dans: {output_file}")
    else:
        print(f"❌ Erreur API: {response.status_code}")
    
    print("\n" + "="*80)
    print("✅ Test terminé")
    print("="*80 + "\n")
