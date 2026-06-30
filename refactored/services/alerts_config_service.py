"""
Service pour gerer la configuration des alertes de consommation
Persistance des parametres (seuil, emails, etc.)
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from refactored.utils.logger import get_logger

logger = get_logger("Alerts_Config")

CONFIG_FILE = Path("refactored/config/alerts_config.json")

DEFAULT_CONFIG = {
    "inactivity_days": 10,
    "only_configured": True,
    "schedule_time": "09:00",
    "notification_emails": [],
    "last_check_date": None,
    "last_alerts": []
}


class AlertsConfigService:
    """Service pour gerer la configuration des alertes"""
    
    def __init__(self):
        self.config_file = CONFIG_FILE
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """Cree le fichier de config s'il n'existe pas"""
        if not self.config_file.exists():
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_config(DEFAULT_CONFIG)
            logger.info("Fichier de configuration des alertes cree")
    
    def _load_config(self) -> Dict:
        """Charge la configuration depuis le fichier JSON"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Fusionner avec les valeurs par defaut pour les nouvelles cles
                return {**DEFAULT_CONFIG, **config}
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la config: {e}")
            return DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict):
        """Sauvegarde la configuration dans le fichier JSON"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info("Configuration des alertes sauvegardee")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la config: {e}")
            raise
    
    def get_config(self) -> Dict:
        """Recupere toute la configuration"""
        return self._load_config()
    
    def get_inactivity_days(self) -> int:
        """Recupere le seuil d'inactivite en jours"""
        return self._load_config().get("inactivity_days", 10)
    
    def set_inactivity_days(self, days: int) -> Dict:
        """Definit le seuil d'inactivite en jours"""
        if days < 1 or days > 365:
            raise ValueError("Le seuil doit etre entre 1 et 365 jours")
        
        config = self._load_config()
        config["inactivity_days"] = days
        self._save_config(config)
        logger.info(f"Seuil d'inactivite mis a jour: {days} jours")
        return config
    
    def get_only_configured(self) -> bool:
        """Recupere le parametre only_configured"""
        return self._load_config().get("only_configured", True)
    
    def set_only_configured(self, value: bool) -> Dict:
        """Definit le parametre only_configured"""
        config = self._load_config()
        config["only_configured"] = value
        self._save_config(config)
        logger.info(f"Filtre facilities configurees: {value}")
        return config
    
    def get_notification_emails(self) -> List[str]:
        """Recupere la liste des emails de notification"""
        return self._load_config().get("notification_emails", [])
    
    def add_notification_email(self, email: str) -> Dict:
        """Ajoute un email de notification"""
        email = email.strip().lower()
        if not email or "@" not in email:
            raise ValueError("Email invalide")
        
        config = self._load_config()
        emails = config.get("notification_emails", [])
        
        if email in emails:
            raise ValueError("Cet email est deja dans la liste")
        
        emails.append(email)
        config["notification_emails"] = emails
        self._save_config(config)
        logger.info(f"Email ajoute: {email}")
        return config
    
    def remove_notification_email(self, email: str) -> Dict:
        """Supprime un email de notification"""
        email = email.strip().lower()
        config = self._load_config()
        emails = config.get("notification_emails", [])
        
        if email not in emails:
            raise ValueError("Cet email n'est pas dans la liste")
        
        emails.remove(email)
        config["notification_emails"] = emails
        self._save_config(config)
        logger.info(f"Email supprime: {email}")
        return config
    
    def update_last_check(self, alerts: List[Dict]) -> Dict:
        """Met a jour la date de derniere verification et les alertes"""
        config = self._load_config()
        config["last_check_date"] = datetime.now().isoformat()
        config["last_alerts"] = alerts
        self._save_config(config)
        return config
    
    def get_last_alerts(self) -> List[Dict]:
        """Recupere les dernieres alertes"""
        return self._load_config().get("last_alerts", [])
    
    def get_new_alerts(self, current_alerts: List[Dict]) -> List[Dict]:
        """
        Compare les alertes actuelles avec les precedentes
        Retourne uniquement les nouvelles alertes (facilities qui n'etaient pas en alerte avant)
        """
        last_alerts = self.get_last_alerts()
        last_facility_ids = {a.get("facility_id") for a in last_alerts}
        
        new_alerts = [
            alert for alert in current_alerts 
            if alert.get("facility_id") not in last_facility_ids
        ]
        
        return new_alerts
