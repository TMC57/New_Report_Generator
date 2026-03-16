"""
Script de test pour interroger l'API CM2W et afficher les valeurs brutes
"""
import requests
from datetime import datetime
import json

# Configuration
API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1NjI4NDQ4MzkxNSwibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.MHOogWqC84PZOBDvl-KlASj07Ly-CuyqBbcIj8KFmsc"
BASE_URL = "https://app.cm2w.net/cm2w-api/v2/api-key-auth"

def date_to_timestamp(date_str):
    """Convertit une date YYYY-MM-DD en timestamp milliseconds"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.timestamp() * 1000)

def get_total_qty_report(from_date, to_date, facility_id):
    """
    Récupère le rapport de quantités totales pour une facility et une période
    
    Args:
        from_date: Date de début (format: YYYY-MM-DD)
        to_date: Date de fin (format: YYYY-MM-DD)
        facility_id: ID de la facility
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    params = {
        "pageNumber": 1,
        "pageSize": 1000000000,
        "fromDate": date_to_timestamp(from_date),
        "thruDate": date_to_timestamp(to_date),
        "reportType": "total-qty-facility",
        "facilityId": facility_id
    }
    
    endpoint = "/total-qty-report"
    url = BASE_URL + endpoint
    
    print(f"\n{'='*80}")
    print(f"🔍 Requête API")
    print(f"{'='*80}")
    print(f"URL: {url}")
    print(f"Facility ID: {facility_id}")
    print(f"Période: {from_date} → {to_date}")
    print(f"{'='*80}\n")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("statusCode") == "SUCCESS":
            results = data.get("data", {}).get("results", [])
            
            print(f"✅ Réponse reçue avec succès")
            print(f"Nombre de résultats: {len(results)}\n")
            
            for result in results:
                if result.get("facilityId") == facility_id:
                    print(f"\n{'='*80}")
                    print(f"📊 Facility {result.get('facilityId')} - {result.get('facilityName')}")
                    print(f"{'='*80}")
                    
                    products = result.get("products", [])
                    print(f"\nNombre de produits: {len(products)}\n")
                    
                    for product in products:
                        product_id = product.get("_id")
                        product_name = product.get("name", "Unknown")
                        qty = product.get("qty", 0)
                        
                        # Conversions selon la doc API (qty en 0.1ml)
                        qty_ml = qty * 0.1
                        qty_l = qty_ml / 1000
                        
                        print(f"  📦 Produit: {product_name}")
                        print(f"     _id: {product_id}")
                        print(f"     qty (brut): {qty}")
                        print(f"     qty en mL (×0.1): {qty_ml:.1f} mL")
                        print(f"     qty en L (÷1000): {qty_l:.3f} L")
                        print(f"     qty ÷ 10: {qty / 10:.1f}")
                        print(f"     qty ÷ 10000: {qty / 10000:.3f}")
                        print()
            
            # Sauvegarder la réponse complète dans un fichier
            output_file = f"api_response_facility_{facility_id}_{from_date}_to_{to_date}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Réponse complète sauvegardée dans: {output_file}")
            
            return data
        else:
            print(f"❌ Erreur API: {data.get('statusCode')}")
            print(f"Message: {data.get('message')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

if __name__ == "__main__":
    # Paramètres à modifier selon vos besoins
    FACILITY_ID = 28194
    FROM_DATE = "2026-03-01"
    TO_DATE = "2026-03-14"
    
    print("\n" + "="*80)
    print("🚀 Test API CM2W - Total Quantity Report")
    print("="*80)
    
    get_total_qty_report(FROM_DATE, TO_DATE, FACILITY_ID)
    
    print("\n" + "="*80)
    print("✅ Test terminé")
    print("="*80 + "\n")
