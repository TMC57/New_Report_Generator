"""
Service pour récupérer les données de débit (flowrate) depuis l'API CM2W
Basé sur l'ancien getDebit.py
"""
import requests
from typing import Optional, Dict, List
from datetime import datetime
from refactored.utils.logger import get_logger

logger = get_logger("Flowrate_Service")

class FlowrateService:
    """Service pour récupérer les données de débit depuis CM2W"""
    
    def __init__(self):
        self.base_url = "https://sh1.cm2w.net/cm2w-api/v2"
        self.email = "e-service@tmh-corporation.com"
        self.password = "Jer160276@"
        self.session = None
        self.token = None
    
    def _date_to_timestamp(self, date_str: str) -> int:
        """Convertit une date YYYY-MM-DD en timestamp milliseconds"""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp() * 1000)
    
    def login(self) -> bool:
        """
        Authentification sur l'API CM2W pour obtenir une session
        Retourne True si succès, False sinon
        """
        logger.info("🔐 Authentification sur CM2W pour flowrate...")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        
        login_url = f"{self.base_url}/users/login"
        payload = {
            "email": self.email,
            "password": self.password
        }
        
        try:
            response = self.session.post(login_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get("token") or data.get("accessToken") or data.get("jwt")
            
            if self.token:
                self.session.headers["Authorization"] = f"Bearer {self.token}"
                logger.success("✅ Authentification réussie")
                return True
            
            if "JSESSIONID" in self.session.cookies:
                logger.success("✅ Authentification réussie (cookie)")
                return True
            
            logger.error("❌ Pas de token ni de cookie après login")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur lors de l'authentification: {e}")
            return False
    
    def get_flowrate_events(
        self,
        device_id: int,
        from_date: str,
        to_date: str,
        page: int = 1,
        page_size: int = 5000
    ) -> Optional[Dict]:
        """
        Récupère les événements de débit (flowrate) pour un device
        
        Args:
            device_id: ID du device
            from_date: Date de début (format YYYY-MM-DD)
            to_date: Date de fin (format YYYY-MM-DD)
            page: Numéro de page
            page_size: Taille de page
            
        Returns:
            Dict contenant les événements ou None si erreur
        """
        if not self.session:
            logger.warning("⚠️ Pas de session active, tentative de login...")
            if not self.login():
                return None
        
        logger.info(f"📊 Récupération flowrate pour device {device_id} ({from_date} → {to_date})")
        
        from_ms = self._date_to_timestamp(from_date)
        to_ms = self._date_to_timestamp(to_date)
        
        events_url = f"{self.base_url}/events"
        params = {
            "deviceId": str(device_id),
            "reportType": "flowrate",
            "fromDate": str(from_ms),
            "thruDate": str(to_ms),
            "pageNumber": str(page),
            "pageSize": str(page_size),
            "endPoint": "events",
        }
        
        try:
            response = self.session.get(events_url, params=params, timeout=60)
            
            if response.status_code == 401:
                logger.warning("⚠️ Token expiré, nouvelle tentative de login...")
                if self.login():
                    response = self.session.get(events_url, params=params, timeout=60)
                else:
                    logger.error("❌ Impossible de se reconnecter")
                    return None
            
            response.raise_for_status()
            data = response.json()
            
            # Compter les événements
            events_count = 0
            if isinstance(data, dict) and "data" in data:
                if isinstance(data["data"], dict) and "results" in data["data"]:
                    events_count = len(data["data"]["results"])
                elif isinstance(data["data"], list):
                    events_count = len(data["data"])
            elif isinstance(data, list):
                events_count = len(data)
            
            logger.success(f"✅ {events_count} événements de débit récupérés")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur lors de la récupération des événements: {e}")
            return None
    
    def get_flowrate_for_facility(
        self,
        device_ids: List[int],
        from_date: str,
        to_date: str
    ) -> Dict[int, Dict]:
        """
        Récupère les données de débit pour tous les devices d'une facility
        
        Args:
            device_ids: Liste des IDs de devices
            from_date: Date de début (format YYYY-MM-DD)
            to_date: Date de fin (format YYYY-MM-DD)
            
        Returns:
            Dict {device_id: events_data}
        """
        logger.info(f"📊 Récupération flowrate pour {len(device_ids)} devices")
        
        results = {}
        for device_id in device_ids:
            events = self.get_flowrate_events(device_id, from_date, to_date)
            if events:
                results[device_id] = events
        
        logger.success(f"✅ Flowrate récupéré pour {len(results)}/{len(device_ids)} devices")
        return results
