"""
Script de test pour récupérer toutes les données de la facility 39547
Période: 25/08/2025 - 31/08/2025
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
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        print("✅ Réponse reçue avec succès")
        data = response.json()
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la requête: {e}")
        return None

def display_facility_data(data):
    """Affiche les données brutes de l'API"""
    if not data:
        print("❌ Pas de données")
        return
    
    print("\n" + "="*80)
    print("� RÉPONSE BRUTE DE L'API (JSON)")
    print("="*80 + "\n")
    
    # Afficher le JSON brut avec indentation
    print(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    """Fonction principale"""
    print(f"\n{'='*80}")
    print(f"🚀 Test API CM2W - Facility 39547 (jour par jour)")
    print(f"{'='*80}\n")
    
    # Paramètres
    facility_id = 39547
    start_date = datetime.strptime("2025-08-25", "%Y-%m-%d")
    end_date = datetime.strptime("2025-08-31", "%Y-%m-%d")
    
    # Stocker toutes les réponses
    all_responses = {}
    
    # Boucle sur chaque jour
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        next_day = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        print(f"\n📅 Jour: {date_str}")
        print("-" * 80)
        
        # Récupérer les données pour ce jour
        data = get_total_qty_report(date_str, next_day, facility_id)
        
        if data:
            # Afficher les données brutes
            display_facility_data(data)
            
            # Stocker la réponse
            all_responses[date_str] = data
        
        # Passer au jour suivant
        current_date += timedelta(days=1)
    
    # Sauvegarder toutes les réponses dans un fichier JSON
    output_file = f"facility_{facility_id}_daily_2025-08-25_to_2025-08-31.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_responses, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n💾 Toutes les réponses quotidiennes sauvegardées dans: {output_file}")
    print(f"\n{'='*80}")
    print(f"✅ Test terminé - {len(all_responses)} jours interrogés")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
