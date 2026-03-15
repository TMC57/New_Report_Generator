import json
import os
import shutil
from pathlib import Path
from typing import Dict, Optional
from refactored.config.settings import CONFIG_DIR
from refactored.models.facility import FacilityConfig
from refactored.utils.logger import get_logger

logger = get_logger("Config_Service")

class ConfigService:
    """Service pour gérer la configuration locale des facilities"""
    
    def __init__(self):
        self.config_file = Path("refactored/config/configJson.json")
        
        old_config = Path("Config/configJson.json")
        if old_config.exists() and not self.config_file.exists():
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_config, self.config_file)
            logger.info(f"Config copiée de {old_config} vers {self.config_file}")
    
    def load_all_configs(self) -> Dict[int, FacilityConfig]:
        """
        Charge toutes les configurations depuis configJson.json
        Retourne un dict avec facility_id comme clé
        """
        logger.info("Chargement des configurations locales")
        
        if not self.config_file.exists():
            logger.warning("Fichier configJson.json introuvable")
            return {}
        
        try:
            with open(str(self.config_file), "r", encoding="utf-8") as f:
                config_list = json.load(f)
            
            configs = {}
            for item in config_list:
                facility_id = item.get("facilityId") or item.get("ID")
                if facility_id:
                    configs[facility_id] = FacilityConfig(
                        facility_id=facility_id,
                        cover_picture=item.get("cover_picture", ""),
                        material_picture=item.get("material_picture", ""),
                        inventory_monitoring_manager=item.get("inventory_monitoring_manager", {}),
                        customer_technical_relay_manager=item.get("customer_technical_relay_manager", {}),
                        file_referent=item.get("file_referent", {}),
                        primary_company_brand=item.get("primary_company_brand", ""),
                        derniere_intervention=item.get("dernière intervention", ""),
                        releves_buses=item.get("relevés buses", "")
                    )
            
            logger.success(f"✅ {len(configs)} configurations chargées")
            return configs
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des configs: {e}")
            return {}
    
    def get_config(self, facility_id: int) -> Optional[FacilityConfig]:
        """Récupère la configuration d'une facility spécifique"""
        configs = self.load_all_configs()
        return configs.get(facility_id)
