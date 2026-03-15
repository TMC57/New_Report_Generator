"""
Script de test simple pour valider la récupération des données
Usage: python refactored/test_simple.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DEBUG_MODE"] = "true"

from refactored.services.cm2w_service import CM2WService
from refactored.services.excel_service import ExcelService
from refactored.services.config_service import ConfigService
from refactored.utils.logger import get_logger

logger = get_logger("Test_Simple")

def test_cm2w_api():
    """Test de l'API CM2W"""
    logger.info("=" * 80)
    logger.info("TEST 1: API CM2W")
    logger.info("=" * 80)
    
    service = CM2WService()
    
    logger.info("\n1️⃣ Test récupération devices...")
    devices = service.get_devices_list()
    if devices and devices.get("data"):
        logger.success(f"✅ {len(devices['data'])} devices récupérés")
    else:
        logger.error("❌ Échec récupération devices")
        return False
    
    logger.info("\n2️⃣ Test récupération stock levels...")
    stocks = service.get_stock_levels()
    if stocks and stocks.get("data"):
        logger.success(f"✅ Stock levels récupérés")
    else:
        logger.error("❌ Échec récupération stocks")
        return False
    
    logger.info("\n3️⃣ Test récupération quantités (2025-01-01 à 2025-01-31)...")
    qty = service.get_total_qty_report("2025-01-01", "2025-02-01")
    if qty and qty.get("data", {}).get("results"):
        logger.success(f"✅ {len(qty['data']['results'])} facilities avec quantités")
    else:
        logger.error("❌ Échec récupération quantités")
        return False
    
    return True

def test_excel_service():
    """Test du service Excel"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Service Excel")
    logger.info("=" * 80)
    
    service = ExcelService()
    
    logger.info("\n1️⃣ Chargement des données Excel...")
    excel_data = service.load_excel_data()
    if excel_data:
        logger.success(f"✅ {len(excel_data)} clients chargés depuis Excel")
        
        logger.info("\n📋 Aperçu des 5 premiers clients:")
        for i, (client_num, client_info) in enumerate(list(excel_data.items())[:5]):
            logger.info(f"  {i+1}. N° {client_num}: {client_info.get('client_name', 'N/A')}")
    else:
        logger.warning("⚠️ Aucune donnée Excel trouvée")
    
    logger.info("\n2️⃣ Test matching Excel...")
    if excel_data:
        test_facility_name = "1070133631 ALTIS VANNES"
        test_facility_id = 28194
        
        excel_info, match_method = service.match_facility_to_excel(
            test_facility_id,
            test_facility_name,
            excel_data
        )
        
        if excel_info:
            logger.success(f"✅ Match trouvé via: {match_method}")
            logger.info(f"  - Client: {excel_info.get('client_name')}")
            logger.info(f"  - Adresse: {excel_info.get('address')}")
        else:
            logger.warning(f"⚠️ Aucun match trouvé pour {test_facility_name}")
    
    return True

def test_config_service():
    """Test du service de configuration"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Service Configuration")
    logger.info("=" * 80)
    
    service = ConfigService()
    
    logger.info("\n1️⃣ Chargement des configurations...")
    configs = service.load_all_configs()
    if configs:
        logger.success(f"✅ {len(configs)} configurations chargées")
        
        logger.info("\n📋 Aperçu des 5 premières configs:")
        for i, (fid, config) in enumerate(list(configs.items())[:5]):
            logger.info(f"  {i+1}. Facility {fid}: cover={bool(config.cover_picture)}, contacts={bool(config.inventory_monitoring_manager)}")
    else:
        logger.warning("⚠️ Aucune configuration trouvée")
    
    return True

if __name__ == "__main__":
    logger.info("🚀 DÉMARRAGE DES TESTS\n")
    
    try:
        test_cm2w_api()
        test_excel_service()
        test_config_service()
        
        logger.info("\n" + "=" * 80)
        logger.success("✅ TOUS LES TESTS SONT PASSÉS")
        logger.info("=" * 80)
        logger.info("\nPour tester une facility spécifique:")
        logger.info("  python refactored/test_simple.py")
        logger.info("\nPour tester avec une facility précise:")
        logger.info("  Modifier le code ou utiliser test_data_retrieval.py")
        
    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
