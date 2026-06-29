"""
Service pour detecter les facilities sans consommation
Integre dans Report_generator
"""
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from refactored.services.cm2w_service import CM2WService
from refactored.services.excel_service import ExcelService
from refactored.utils.logger import get_logger

logger = get_logger("Consumption_Monitor")

# Configuration par defaut
DEFAULT_INACTIVITY_DAYS = 10


class ConsumptionMonitorService:
    """Service pour verifier les consommations et detecter les facilities inactives"""
    
    def __init__(self):
        self.cm2w = CM2WService()
        self.excel_service = ExcelService()
    
    def get_excel_facility_ids(self) -> Set[int]:
        """
        Recupere les IDs des facilities presentes dans le fichier Excel uploade
        (listing_data.json) - ce sont les "N° client" du fichier Excel
        """
        excel_data = self.excel_service.load_excel_data()
        return set(excel_data.keys())
    
    def is_facility_in_excel(self, facility_id: int, facility_name: str, excel_ids: Set[int]) -> bool:
        """
        Verifie si une facility est presente dans le fichier Excel
        Utilise la meme logique de matching que ExcelService:
        1. Extrait le N° client du debut du nom (ex: "1070462396 GGE | Les Ulis")
        2. Sinon utilise le facility_id directement
        """
        # Extraire le N° client du nom de la facility
        parts = facility_name.split()
        if parts and parts[0].isdigit():
            client_number = int(parts[0])
            if client_number in excel_ids:
                return True
        
        # Fallback: verifier si facility_id est dans Excel
        return facility_id in excel_ids
    
    def check_all_facilities(
        self, 
        inactivity_days: int = DEFAULT_INACTIVITY_DAYS,
        only_configured: bool = False
    ) -> Dict:
        """
        Verifie toutes les facilities et retourne celles sans consommation
        
        Args:
            inactivity_days: Nombre de jours sans consommation pour considerer une facility inactive
            only_configured: Si True, ne verifie que les facilities presentes dans le fichier Excel
            
        Returns:
            Dict avec les resultats de la verification
        """
        # Recuperer les facility IDs du fichier Excel si necessaire
        excel_facility_ids: Set[int] = set()
        if only_configured:
            excel_facility_ids = self.get_excel_facility_ids()
            logger.info(f"Mode filtre: {len(excel_facility_ids)} facilities dans le fichier Excel")
        
        logger.info(f"Demarrage de la verification des consommations (seuil: {inactivity_days} jours)")
        
        # Calculer la periode a verifier
        to_date = datetime.now()
        from_date = to_date - timedelta(days=inactivity_days)
        
        from_date_str = from_date.strftime("%Y-%m-%d")
        to_date_str = to_date.strftime("%Y-%m-%d")
        
        logger.info(f"Periode verifiee: {from_date_str} -> {to_date_str}")
        
        # Recuperer toutes les facilities
        devices_response = self.cm2w.get_devices_list()
        
        if not devices_response or "data" not in devices_response:
            logger.error("Impossible de recuperer les facilities")
            return self._create_result([], 0, inactivity_days, from_date_str, to_date_str)
        
        # Extraire les facilities (filtrer si only_configured)
        facilities = []
        for facility_data in devices_response["data"]:
            facility_id = facility_data.get("facilityId")
            
            # Si mode filtre, ignorer les facilities non presentes dans le fichier Excel
            facility_name = facility_data.get("facilityName", "")
            if only_configured and not self.is_facility_in_excel(facility_id, facility_name, excel_facility_ids):
                continue
            
            facilities.append({
                "facility_id": facility_id,
                "facility_name": facility_name,
                "owner": facility_data.get("owner", "")
            })
        
        logger.info(f"{len(facilities)} facilities a verifier" + (" (filtrees)" if only_configured else ""))
        
        # Recuperer les consommations pour toutes les facilities
        consumption_data = self.cm2w.get_total_qty_report(from_date_str, to_date_str)
        
        if not consumption_data or "data" not in consumption_data:
            logger.error("Impossible de recuperer les donnees de consommation")
            return self._create_result([], len(facilities), inactivity_days, from_date_str, to_date_str)
        
        # Creer un mapping facility_id -> consommation totale
        consumption_map = {}
        for result in consumption_data.get("data", {}).get("results", []):
            facility_id = result.get("facilityId")
            total_qty = sum(p.get("qty", 0) for p in result.get("products", []))
            consumption_map[facility_id] = total_qty
        
        # Identifier les facilities sans consommation
        inactive_facilities = []
        
        for facility in facilities:
            facility_id = facility["facility_id"]
            total_consumption = consumption_map.get(facility_id, 0)
            
            if total_consumption == 0:
                inactive_facilities.append({
                    "facility_id": facility_id,
                    "facility_name": facility["facility_name"],
                    "owner": facility["owner"],
                    "total_consumption_ml": 0,
                    "days_inactive": inactivity_days
                })
        
        logger.success(f"Verification terminee: {len(inactive_facilities)} facilities sans consommation sur {len(facilities)}")
        
        return self._create_result(
            inactive_facilities, 
            len(facilities), 
            inactivity_days, 
            from_date_str, 
            to_date_str,
            only_configured
        )
    
    def _create_result(
        self, 
        alerts: List[Dict], 
        total_checked: int, 
        inactivity_days: int,
        from_date: str,
        to_date: str,
        only_configured: bool = False
    ) -> Dict:
        """Cree le dictionnaire de resultat"""
        return {
            "check_date": datetime.now().isoformat(),
            "from_date": from_date,
            "to_date": to_date,
            "inactivity_threshold_days": inactivity_days,
            "total_facilities_checked": total_checked,
            "alerts_count": len(alerts),
            "only_configured": only_configured,
            "alerts": alerts
        }
