import json
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Any, List
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
                        facility_name=item.get("facilityName", ""),
                        cover_picture=item.get("cover_picture", "")
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
    
    def update_config_from_devices(self, devices_list: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour configJson.json depuis devices_list (ADD-ONLY)
        - Ajoute les nouvelles facilities
        - Ne modifie pas les facilities existantes (préserve cover_picture)
        - Format simplifié: facilityId, facilityName, cover_picture
        
        Returns:
            {"facilities": [...], "added": X, "total": Y}
        """
        logger.info("🔄 Mise à jour de configJson.json depuis devices_list...")
        
        # Charger la config existante
        existing_config: List[Dict] = []
        if self.config_file.exists():
            try:
                with open(str(self.config_file), "r", encoding="utf-8") as f:
                    existing_config = json.load(f)
            except Exception as e:
                logger.warning(f"Erreur lecture config existante: {e}")
                existing_config = []
        
        # Créer un dict des facilities existantes par ID
        existing_by_id = {}
        for item in existing_config:
            fac_id = item.get("facilityId") or item.get("ID")
            if fac_id:
                existing_by_id[fac_id] = item
        
        # Parcourir devices_list et ajouter les nouvelles facilities
        added_count = 0
        for facility_data in devices_list.get("data", []):
            fac_id = facility_data.get("facilityId")
            fac_name = facility_data.get("facilityName", "")
            
            if fac_id and fac_id not in existing_by_id:
                # Nouvelle facility - ajouter avec format simplifié
                new_entry = {
                    "facilityId": fac_id,
                    "facilityName": fac_name,
                    "cover_picture": "/uploads/Croix rouge.jpg"  # Image par défaut
                }
                existing_by_id[fac_id] = new_entry
                added_count += 1
                logger.info(f"   + Nouvelle facility ajoutée: {fac_name} ({fac_id})")
            elif fac_id and fac_id in existing_by_id:
                # Facility existante - mettre à jour le nom si nécessaire
                existing_by_id[fac_id]["facilityName"] = fac_name
                # Migrer l'ancien format si nécessaire
                if "ID" in existing_by_id[fac_id] and "facilityId" not in existing_by_id[fac_id]:
                    existing_by_id[fac_id]["facilityId"] = existing_by_id[fac_id].pop("ID")
        
        # Convertir en liste et simplifier le format (garder uniquement les champs essentiels)
        output = []
        for fac_id, item in existing_by_id.items():
            simplified = {
                "facilityId": fac_id,
                "facilityName": item.get("facilityName", ""),
                "cover_picture": item.get("cover_picture", "/uploads/Croix rouge.jpg")
            }
            output.append(simplified)
        
        # Trier par facilityName
        output.sort(key=lambda x: x.get("facilityName", ""))
        
        # Sauvegarder
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(str(self.config_file), "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.success(f"✅ configJson.json mis à jour: {added_count} ajoutées, {len(output)} total")
        
        return {
            "facilities": output,
            "added": added_count,
            "total": len(output)
        }
