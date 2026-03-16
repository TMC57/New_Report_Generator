import json
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
from refactored.config.settings import EXCEL_LISTINGS_DIR
from refactored.utils.logger import get_logger

logger = get_logger("Excel_Service")

class ExcelService:
    """Service pour gérer les données Excel"""
    
    def __init__(self):
        self.excel_dir = EXCEL_LISTINGS_DIR
        self.data_file = self.excel_dir / "listing_data.json"
        self.metadata_file = self.excel_dir / "metadata.json"
    
    def load_excel_data(self) -> Dict[int, dict]:
        """
        Charge les données Excel depuis listing_data.json
        Retourne un dict avec client_number comme clé
        """
        logger.info("Chargement des données Excel")
        
        if not self.data_file.exists():
            logger.warning("Aucun fichier Excel trouvé")
            return {}
        
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data_raw = json.load(f)
                data = {int(k): v for k, v in data_raw.items()}
                logger.success(f"✅ {len(data)} clients chargés depuis Excel")
                return data
        except Exception as e:
            logger.error(f"Erreur lors du chargement Excel: {e}")
            return {}
    
    def match_facility_to_excel(
        self,
        facility_id: int,
        facility_name: str,
        excel_data: Dict[int, dict]
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Trouve les données Excel correspondant à une facility
        
        Retourne: (excel_info, match_method) ou (None, None)
        
        Stratégie de matching (par ordre de priorité):
        1. Extraire le N° client du début du facilityName (ex: "1070462396 GGE | Les Ulis")
        2. Utiliser facility_id directement
        3. Fuzzy match sur le nom normalisé
        """
        if not excel_data:
            return None, None
        
        logger.info(f"Matching Excel pour facility {facility_id} '{facility_name}'")
        
        client_number = None
        parts = facility_name.split()
        if parts and parts[0].isdigit():
            client_number = int(parts[0])
            logger.info(f"  → N° client extrait du nom: {client_number}")
        else:
            logger.info(f"  → Aucun N° client trouvé au début du nom (première partie: '{parts[0] if parts else 'vide'}')")
        
        if client_number and client_number in excel_data:
            logger.info(f"  → ✅ Match par N° client extrait: {client_number}")
            return excel_data[client_number], f"N° client extrait du nom ({client_number})"
        
        if facility_id in excel_data:
            logger.debug(f"  → Match par facility_id: {facility_id}")
            return excel_data[facility_id], f"facility_id direct ({facility_id})"
        
        facility_name_normalized = facility_name.upper().strip()
        for excel_id, excel_entry in excel_data.items():
            excel_client_name = excel_entry.get("client_name", "").upper().strip()
            if excel_client_name and excel_client_name == facility_name_normalized:
                logger.debug(f"  → Match par nom: '{facility_name}' → N° {excel_id}")
                return excel_entry, f"correspondance par nom '{facility_name}' → N° {excel_id}"
        
        logger.debug(f"  → Aucun match trouvé")
        return None, None
    
    def get_metadata(self) -> Optional[dict]:
        """Récupère les métadonnées du fichier Excel uploadé"""
        if not self.metadata_file.exists():
            return None
        
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des métadonnées: {e}")
            return None
