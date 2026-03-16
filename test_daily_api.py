"""
Script de test pour interroger l'API CM2W jour par jour
"""
import requests
from datetime import datetime, timedelta
import json

# Configuration
API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1NjI4NDQ4MzkxNSwibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.MHOogWqC84PZOBDvl-KlASj07Ly-CuyqBbcIj8KFmsc"
BASE_URL = "https://app.cm2w.net/cm2w-api/v2/api-key-auth"

def date_to_timestamp(date_str):
    """Convertit une date YYYY-MM-DD en timestamp milliseconds"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.timestamp() * 1000)

def get_daily_qty(date_str, facility_id):
    """
    Récupère les quantités pour UN SEUL JOUR
    
    Args:
        date_str: Date (format: YYYY-MM-DD)
        facility_id: ID de la facility
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Pour un jour spécifique : du jour J au jour J+1
    current_date = datetime.strptime(date_str, "%Y-%m-%d")
    next_date = current_date + timedelta(days=1)
    date_str_to = next_date.strftime("%Y-%m-%d")
    
    params = {
        "pageNumber": 1,
        "pageSize": 1000000000,
        "fromDate": date_to_timestamp(date_str),
        "thruDate": date_to_timestamp(date_str_to),
        "reportType": "total-qty-facility",
        "facilityId": facility_id
    }
    
    endpoint = "/total-qty-report"
    url = BASE_URL + endpoint
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("statusCode") == "SUCCESS":
            results = data.get("data", {}).get("results", [])
            
            for result in results:
                if result.get("facilityId") == facility_id:
                    return result.get("products", [])
        
        return []
            
    except Exception as e:
        print(f"❌ Erreur pour {date_str}: {e}")
        return []

if __name__ == "__main__":
    FACILITY_ID = 28194
    FROM_DATE = "2026-03-01"
    TO_DATE = "2026-03-14"
    
    print("\n" + "="*80)
    print("🚀 Test API CM2W - Quantités quotidiennes")
    print("="*80)
    print(f"Facility: {FACILITY_ID}")
    print(f"Période: {FROM_DATE} → {TO_DATE}")
    print("="*80 + "\n")
    
    current_date = datetime.strptime(FROM_DATE, "%Y-%m-%d")
    end_date = datetime.strptime(TO_DATE, "%Y-%m-%d")
    
    total_by_product = {}
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        
        print(f"\n📅 {date_str}")
        print("-" * 80)
        
        products = get_daily_qty(date_str, FACILITY_ID)
        
        if products:
            for product in products:
                product_id = product.get("_id")
                product_name = product.get("name", "Unknown")
                qty = product.get("qty", 0)
                
                # Conversions
                qty_div_10 = qty / 10
                qty_div_10000 = qty / 10000
                
                print(f"  📦 {product_name} (_id={product_id})")
                print(f"     qty brut: {qty}")
                print(f"     qty ÷ 10: {qty_div_10:.1f} mL")
                print(f"     qty ÷ 10000: {qty_div_10000:.3f} L")
                
                # Accumuler pour le total
                if product_name not in total_by_product:
                    total_by_product[product_name] = 0
                total_by_product[product_name] += qty
        else:
            print("  ⚠️ Aucune donnée pour ce jour")
        
        current_date += timedelta(days=1)
    
    print("\n" + "="*80)
    print("📊 TOTAUX SUR LA PÉRIODE")
    print("="*80)
    
    for product_name, total_qty in total_by_product.items():
        print(f"\n  📦 {product_name}")
        print(f"     Total qty brut: {total_qty}")
        print(f"     Total ÷ 10: {total_qty / 10:.1f} mL")
        print(f"     Total ÷ 10000: {total_qty / 10000:.3f} L")
    
    print("\n" + "="*80)
    print("✅ Test terminé")
    print("="*80 + "\n")
