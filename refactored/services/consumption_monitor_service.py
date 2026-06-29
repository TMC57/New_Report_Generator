"""
Service pour detecter les facilities sans consommation
Integre dans Report_generator
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from refactored.services.cm2w_service import CM2WService
from refactored.utils.logger import get_logger

logger = get_logger("Consumption_Monitor")

# Configuration par defaut
DEFAULT_INACTIVITY_DAYS = 10


class ConsumptionMonitorService:
    """Service pour verifier les consommations et detecter les facilities inactives"""
    
    def __init__(self):
        self.cm2w = CM2WService()
    
    def check_all_facilities(self, inactivity_days: int = DEFAULT_INACTIVITY_DAYS) -> Dict:
        """
        Verifie toutes les facilities et retourne celles sans consommation
        
        Args:
            inactivity_days: Nombre de jours sans consommation pour considerer une facility inactive
            
        Returns:
            Dict avec les resultats de la verification
        """
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
        
        # Extraire les facilities
        facilities = []
        for facility_data in devices_response["data"]:
            facilities.append({
                "facility_id": facility_data.get("facilityId"),
                "facility_name": facility_data.get("facilityName", ""),
                "owner": facility_data.get("owner", "")
            })
        
        logger.info(f"{len(facilities)} facilities trouvees")
        
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
            to_date_str
        )
    
    def _create_result(
        self, 
        alerts: List[Dict], 
        total_checked: int, 
        inactivity_days: int,
        from_date: str,
        to_date: str
    ) -> Dict:
        """Cree le dictionnaire de resultat"""
        return {
            "check_date": datetime.now().isoformat(),
            "from_date": from_date,
            "to_date": to_date,
            "inactivity_threshold_days": inactivity_days,
            "total_facilities_checked": total_checked,
            "alerts_count": len(alerts),
            "alerts": alerts
        }
