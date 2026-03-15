import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from refactored.config.settings import CM2W_API_BASE_URL, CM2W_API_KEY
from refactored.utils.logger import get_logger

logger = get_logger("CM2W_Service")

class CM2WService:
    """Service pour récupérer les données depuis l'API CM2W"""
    
    def __init__(self):
        self.base_url = CM2W_API_BASE_URL
        self.headers = {"Authorization": f"Bearer {CM2W_API_KEY}"}
    
    def _make_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Effectue une requête à l'API CM2W"""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"API Request: {endpoint} with params: {params}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            logger.debug(f"API Response: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            return None
    
    def get_devices_list(self, facility_id: Optional[int] = None) -> Optional[dict]:
        """
        Récupère la liste des devices/routeurs
        Endpoint: /installation-sites/devices
        """
        logger.info(f"Récupération de la liste des devices" + (f" pour facility {facility_id}" if facility_id else ""))
        
        params = {"facilityId": facility_id} if facility_id else {}
        result = self._make_request("/installation-sites/devices", params)
        
        if result:
            devices_count = len(result.get("data", []))
            logger.success(f"✅ {devices_count} devices récupérés")
        
        return result
    
    def get_total_qty_report(
        self, 
        from_date: str, 
        to_date: str, 
        facility_id: Optional[int] = None
    ) -> Optional[dict]:
        """
        Récupère le rapport de quantités totales
        Endpoint: /total-qty-report
        Dates au format: YYYY-MM-DD
        """
        logger.info(f"Récupération des quantités totales de {from_date} à {to_date}" + 
                   (f" pour facility {facility_id}" if facility_id else ""))
        
        from_ms = self._date_to_timestamp(from_date)
        to_ms = self._date_to_timestamp(to_date)
        
        params = {
            "pageNumber": 1,
            "pageSize": 1000000000,
            "fromDate": from_ms,
            "thruDate": to_ms,
            "reportType": "total-qty-facility",
        }
        
        if facility_id is not None:
            params["facilityId"] = facility_id
        
        result = self._make_request("/total-qty-report", params)
        
        if result:
            results_count = len(result.get("data", {}).get("results", []))
            logger.success(f"✅ Quantités récupérées pour {results_count} facilities")
        
        return result
    
    def get_stock_levels(self, facility_id: Optional[int] = None) -> Optional[dict]:
        """
        Récupère les niveaux de stock
        Endpoint: /installation-sites/stocks
        """
        logger.info(f"Récupération des niveaux de stock" + 
                   (f" pour facility {facility_id}" if facility_id else ""))
        
        params = {"facilityId": facility_id} if facility_id else {}
        result = self._make_request("/installation-sites/stocks", params)
        
        if result:
            logger.success(f"✅ Niveaux de stock récupérés")
        
        return result
    
    def get_daily_quantities(
        self,
        from_date: str,
        to_date: str,
        facility_id: Optional[int] = None
    ) -> List[dict]:
        """
        Récupère les quantités jour par jour
        Retourne une liste de résultats quotidiens
        """
        logger.info(f"Récupération des quantités quotidiennes de {from_date} à {to_date}")
        
        current_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        daily_results = []
        day_count = 0
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            date_str_to = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
            
            logger.debug(f"Récupération jour {date_str}")
            
            result = self.get_total_qty_report(date_str, date_str_to, facility_id)
            
            if result and result.get("data", {}).get("results"):
                daily_results.append({
                    "date": date_str,
                    "data": result["data"]["results"]
                })
                day_count += 1
            
            current_date += timedelta(days=1)
        
        logger.success(f"✅ {day_count} jours de données récupérés")
        return daily_results
    
    def get_monthly_quantities(
        self,
        to_date: str,
        facility_id: Optional[int] = None,
        months_count: int = 12
    ) -> List[dict]:
        """
        Récupère les quantités pour les N derniers mois
        """
        logger.info(f"Récupération des quantités mensuelles ({months_count} mois)")
        
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        monthly_results = []
        
        for i in range(months_count - 1, -1, -1):
            year = end_date.year
            month = end_date.month - i
            
            while month <= 0:
                month += 12
                year -= 1
            
            first_day = datetime(year, month, 1)
            
            if month == 12:
                last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1) - timedelta(days=1)
            
            if last_day > end_date:
                last_day = end_date
            
            from_str = first_day.strftime("%Y-%m-%d")
            to_str = (last_day + timedelta(days=1)).strftime("%Y-%m-%d")
            
            logger.debug(f"Récupération mois {year}-{month:02d}")
            
            result = self.get_total_qty_report(from_str, to_str, facility_id)
            
            if result and result.get("data", {}).get("results"):
                monthly_results.append({
                    "year": year,
                    "month": month,
                    "data": result["data"]["results"]
                })
        
        logger.success(f"✅ {len(monthly_results)} mois de données récupérés")
        return monthly_results
    
    @staticmethod
    def _date_to_timestamp(date_str: str) -> int:
        """Convertit une date YYYY-MM-DD en timestamp milliseconds"""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp() * 1000)
