"""
Routes API pour la gestion des configurations (facilities et groupes)
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import List
from refactored.utils.logger import get_logger

logger = get_logger("Config_Routes")

router = APIRouter(prefix="/api/v2/config", tags=["config"])

# Chemins des fichiers de configuration (absolus)
CONFIG_DIR = Path(__file__).parent.parent / "config"
FACILITIES_CONFIG_FILE = CONFIG_DIR / "configJson.json"
GROUPS_CONFIG_FILE = CONFIG_DIR / "GroupConfigJson.json"

# Créer le dossier si nécessaire
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/facilities")
async def get_facilities_config():
    """
    Récupère la configuration de toutes les facilities
    """
    try:
        if not FACILITIES_CONFIG_FILE.exists():
            logger.warning("Fichier de configuration des facilities introuvable")
            return []
        
        with open(FACILITIES_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        logger.info(f"Configuration chargée: {len(config)} facilities")
        return config
    
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement de la configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/facilities")
async def save_facilities_config(items: List[dict]):
    """
    Sauvegarde la configuration des facilities
    """
    try:
        with open(FACILITIES_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        logger.success(f"✅ Configuration sauvegardée: {len(items)} facilities")
        
        return {
            "success": True,
            "saved": len(items),
            "message": f"{len(items)} facilities sauvegardées"
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups")
async def get_groups_config():
    """
    Récupère la configuration de tous les groupes
    """
    try:
        if not GROUPS_CONFIG_FILE.exists():
            logger.warning("Fichier de configuration des groupes introuvable")
            return []
        
        with open(GROUPS_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        logger.info(f"Configuration chargée: {len(config)} groupes")
        return config
    
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement de la configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/groups")
async def save_groups_config(items: List[dict]):
    """
    Sauvegarde la configuration des groupes
    """
    try:
        with open(GROUPS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        logger.success(f"✅ Configuration sauvegardée: {len(items)} groupes")
        
        return {
            "success": True,
            "saved": len(items),
            "message": f"{len(items)} groupes sauvegardés"
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/facility/{facility_id}")
async def get_facility_config(facility_id: int):
    """
    Récupère la configuration d'une facility spécifique
    """
    try:
        if not FACILITIES_CONFIG_FILE.exists():
            raise HTTPException(status_code=404, detail="Configuration introuvable")
        
        with open(FACILITIES_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Chercher la facility
        for facility in config:
            if facility.get("facilityId") == facility_id or facility.get("ID") == facility_id:
                return facility
        
        raise HTTPException(status_code=404, detail=f"Facility {facility_id} non trouvée")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/facility/{facility_id}")
async def update_facility_config(facility_id: int, facility_data: dict):
    """
    Met à jour la configuration d'une facility spécifique
    """
    try:
        if not FACILITIES_CONFIG_FILE.exists():
            config = []
        else:
            with open(FACILITIES_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        
        # Chercher et mettre à jour la facility
        found = False
        for i, facility in enumerate(config):
            if facility.get("facilityId") == facility_id or facility.get("ID") == facility_id:
                config[i] = facility_data
                found = True
                break
        
        # Si pas trouvée, l'ajouter
        if not found:
            config.append(facility_data)
        
        # Sauvegarder
        with open(FACILITIES_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.success(f"✅ Facility {facility_id} mise à jour")
        
        return {
            "success": True,
            "message": f"Facility {facility_id} mise à jour",
            "facility": facility_data
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/facility/{facility_id}")
async def delete_facility_config(facility_id: int):
    """
    Supprime la configuration d'une facility
    """
    try:
        if not FACILITIES_CONFIG_FILE.exists():
            raise HTTPException(status_code=404, detail="Configuration introuvable")
        
        with open(FACILITIES_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Filtrer pour supprimer la facility
        original_count = len(config)
        config = [f for f in config if f.get("facilityId") != facility_id and f.get("ID") != facility_id]
        
        if len(config) == original_count:
            raise HTTPException(status_code=404, detail=f"Facility {facility_id} non trouvée")
        
        # Sauvegarder
        with open(FACILITIES_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.success(f"✅ Facility {facility_id} supprimée")
        
        return {
            "success": True,
            "message": f"Facility {facility_id} supprimée"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))
