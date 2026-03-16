"""
Script pour uploader manuellement le fichier Excel et le parser
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from refactored.excel_parser import parse_listing_clients_excel
import json

def upload_excel(excel_file_path: str):
    """
    Upload et parse un fichier Excel/CSV
    """
    excel_path = Path(excel_file_path)
    
    if not excel_path.exists():
        print(f"❌ Fichier non trouvé: {excel_file_path}")
        return False
    
    print(f"📂 Parsing du fichier: {excel_path.name}")
    
    try:
        # Parser le fichier
        excel_data = parse_listing_clients_excel(str(excel_path))
        
        print(f"✅ {len(excel_data)} clients parsés")
        
        # Afficher quelques exemples
        print("\n📋 Exemples de clients chargés:")
        for i, (client_id, data) in enumerate(list(excel_data.items())[:5]):
            print(f"  {client_id}: {data.get('client_name')} - {data.get('address')}")
        
        # Sauvegarder dans le répertoire attendu
        excel_listings_dir = Path(__file__).parent / "uploads" / "excel_listings"
        excel_listings_dir.mkdir(parents=True, exist_ok=True)
        
        listing_data_path = excel_listings_dir / "listing_data.json"
        
        with open(listing_data_path, 'w', encoding='utf-8') as f:
            json.dump(excel_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Données sauvegardées dans: {listing_data_path}")
        
        # Créer aussi le fichier metadata
        metadata = {
            "original_filename": excel_path.name,
            "upload_date": "2026-03-16",
            "total_clients": len(excel_data)
        }
        
        metadata_path = excel_listings_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Metadata sauvegardées dans: {metadata_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Chemin vers le fichier Excel
    excel_file = r"C:\Users\Thomas\Documents\Report_generator\Base de données 12032026.xlsx"
    
    # Si le fichier .xlsx n'existe pas, essayer le CSV
    if not Path(excel_file).exists():
        excel_file = r"C:\Users\Thomas\Documents\Report_generator\Base de données 12032026(Feuil1).csv"
    
    print("🚀 Upload manuel du fichier Excel\n")
    
    if upload_excel(excel_file):
        print("\n✅ Upload terminé avec succès!")
        print("\n💡 Tu peux maintenant générer un rapport et le tableau de la page 2 sera rempli.")
    else:
        print("\n❌ Échec de l'upload")
