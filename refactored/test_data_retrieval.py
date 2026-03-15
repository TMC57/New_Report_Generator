"""
Script de test pour valider la récupération des données
Usage: python -m refactored.test_data_retrieval --facility-id 28194 --from-date 2025-01-01 --to-date 2025-01-31 --debug
"""
import sys
import os
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DEBUG_MODE"] = "true"

from refactored.services.facility_service import FacilityService
from refactored.utils.logger import get_logger

logger = get_logger("Test_Data_Retrieval")

def test_single_facility(facility_id: int, from_date: str, to_date: str):
    """Teste la récupération des données pour une seule facility"""
    logger.info(f"=" * 80)
    logger.info(f"TEST: Récupération des données pour facility {facility_id}")
    logger.info(f"Période: {from_date} → {to_date}")
    logger.info(f"=" * 80)
    
    service = FacilityService()
    facility = service.get_complete_facility_data(facility_id, from_date, to_date)
    
    if not facility:
        logger.error(f"❌ ÉCHEC: Impossible de récupérer les données")
        return False
    
    logger.info(f"\n" + "=" * 80)
    logger.info(f"RÉSULTAT FINAL")
    logger.info(f"=" * 80)
    logger.info(f"Facility ID: {facility.facility_id}")
    logger.info(f"Facility Name: {facility.facility_name}")
    logger.info(f"Owner: {facility.owner}")
    logger.info(f"")
    logger.info(f"📊 DONNÉES EXCEL:")
    logger.info(f"  - Matched: {facility.excel_matched}")
    logger.info(f"  - Method: {facility.excel_match_method}")
    logger.info(f"  - Client Number: {facility.client_number}")
    logger.info(f"  - Client Name: {facility.client_name}")
    logger.info(f"  - Address: {facility.address}")
    logger.info(f"  - Group: {facility.group}")
    logger.info(f"")
    logger.info(f"🔧 DEVICES: {len(facility.devices)}")
    for device in facility.devices:
        logger.info(f"  - Device {device.device_id}: {device.serial_number} (Zone: {device.zone})")
    logger.info(f"")
    logger.info(f"📦 PRODUITS EN STOCK: {len(facility.stock_products)}")
    for product in facility.stock_products[:5]:
        logger.info(f"  - {product.name}: {product.remaining_quantity} {product.remaining_quantity_unit}")
    if len(facility.stock_products) > 5:
        logger.info(f"  ... et {len(facility.stock_products) - 5} autres")
    logger.info(f"")
    logger.info(f"📈 PRODUITS CONSOMMÉS: {len(facility.products)}")
    for product in facility.products[:5]:
        logger.info(f"  - {product.name}: {product.total_qty} L")
    if len(facility.products) > 5:
        logger.info(f"  ... et {len(facility.products) - 5} autres")
    logger.info(f"")
    logger.info(f"🏷️ ZONES: {', '.join(facility.zones) if facility.zones else 'Aucune'}")
    logger.info(f"")
    logger.info(f"✅ VALIDATION:")
    if facility.has_all_required_data():
        logger.success(f"  ✅ Toutes les données nécessaires sont présentes")
    else:
        missing = facility.get_missing_data()
        logger.warning(f"  ⚠️ Données manquantes: {', '.join(missing)}")
    logger.info(f"")
    logger.info(f"📄 TITRE PDF: {facility.get_display_title()}")
    logger.info(f"📁 NOM FICHIER: {facility.get_filename_base()}")
    logger.info(f"=" * 80)
    
    output_file = f"refactored/cache/facility_{facility_id}_data.json"
    service.save_facility_data_to_json(facility, output_file)
    logger.info(f"💾 Données sauvegardées dans: {output_file}")
    
    return True

def test_all_facilities(from_date: str, to_date: str):
    """Teste la récupération des données pour toutes les facilities"""
    logger.info(f"=" * 80)
    logger.info(f"TEST: Récupération de TOUTES les facilities")
    logger.info(f"Période: {from_date} → {to_date}")
    logger.info(f"=" * 80)
    
    service = FacilityService()
    facilities = service.get_all_facilities_data(from_date, to_date)
    
    logger.info(f"\n" + "=" * 80)
    logger.info(f"RÉSUMÉ GLOBAL")
    logger.info(f"=" * 80)
    logger.info(f"Total facilities: {len(facilities)}")
    
    matched_count = sum(1 for f in facilities if f.excel_matched)
    complete_count = sum(1 for f in facilities if f.has_all_required_data())
    
    logger.info(f"Excel matched: {matched_count}/{len(facilities)}")
    logger.info(f"Données complètes: {complete_count}/{len(facilities)}")
    logger.info(f"")
    
    logger.info(f"📋 LISTE DES FACILITIES:")
    for facility in facilities:
        status = "✅" if facility.has_all_required_data() else "⚠️"
        excel_status = "📊" if facility.excel_matched else "❌"
        logger.info(f"  {status} {excel_status} {facility.facility_id}: {facility.get_display_name()}")
    
    logger.info(f"=" * 80)
    
    summary_file = "refactored/cache/all_facilities_summary.json"
    summary = {
        "total_count": len(facilities),
        "excel_matched_count": matched_count,
        "complete_data_count": complete_count,
        "facilities": [
            {
                "facility_id": f.facility_id,
                "facility_name": f.facility_name,
                "display_name": f.get_display_name(),
                "display_title": f.get_display_title(),
                "excel_matched": f.excel_matched,
                "has_complete_data": f.has_all_required_data(),
                "missing_data": f.get_missing_data(),
                "devices_count": len(f.devices),
                "products_count": len(f.products),
                "zones": f.zones
            }
            for f in facilities
        ]
    }
    
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 Résumé sauvegardé dans: {summary_file}")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test de récupération des données facilities")
    parser.add_argument("--facility-id", type=int, help="ID de la facility à tester (optionnel)")
    parser.add_argument("--from-date", required=True, help="Date de début (YYYY-MM-DD)")
    parser.add_argument("--to-date", required=True, help="Date de fin (YYYY-MM-DD)")
    parser.add_argument("--debug", action="store_true", help="Activer le mode debug")
    
    args = parser.parse_args()
    
    if args.debug:
        os.environ["DEBUG_MODE"] = "true"
    
    if args.facility_id:
        success = test_single_facility(args.facility_id, args.from_date, args.to_date)
    else:
        success = test_all_facilities(args.from_date, args.to_date)
    
    sys.exit(0 if success else 1)
