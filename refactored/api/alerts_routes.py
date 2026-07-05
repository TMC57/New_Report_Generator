"""
Routes API pour les alertes de consommation
"""
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from refactored.services.consumption_monitor_service import ConsumptionMonitorService
from refactored.services.alerts_config_service import AlertsConfigService
from refactored.services.email_service import EmailService
from refactored.utils.logger import get_logger

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])
logger = get_logger("Alerts_Routes")


class EmailRequest(BaseModel):
    email: str


class ConfigUpdateRequest(BaseModel):
    inactivity_days: Optional[int] = None
    only_configured: Optional[bool] = None


@router.get("/inactive-facilities")
def get_inactive_facilities(
    days: int = Query(default=None, ge=1, le=365, description="Nombre de jours sans consommation"),
    only_configured: bool = Query(default=None, description="Filtrer uniquement les facilities configurees")
):
    """
    Recupere la liste des facilities sans consommation depuis X jours
    Utilise les parametres sauvegardes si non specifies
    """
    config_service = AlertsConfigService()
    
    # Utiliser les valeurs sauvegardees si non specifiees
    if days is None:
        days = config_service.get_inactivity_days()
    if only_configured is None:
        only_configured = config_service.get_only_configured()
    
    logger.info(f"Verification des facilities inactives (seuil: {days} jours, only_configured: {only_configured})")
    
    try:
        service = ConsumptionMonitorService()
        result = service.check_all_facilities(
            inactivity_days=days,
            only_configured=only_configured
        )
        
        logger.success(f"Verification terminee: {result['alerts_count']} alertes")
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
def get_alerts_config():
    """Recupere la configuration des alertes"""
    try:
        config_service = AlertsConfigService()
        config = config_service.get_config()
        
        # Ajouter l'info sur la configuration email
        email_service = EmailService()
        config["email_configured"] = email_service.is_configured()
        
        return config
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation de la config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
def update_alerts_config(request: ConfigUpdateRequest):
    """Met a jour la configuration des alertes (seuil, filtre)"""
    try:
        config_service = AlertsConfigService()
        
        if request.inactivity_days is not None:
            if request.inactivity_days < 1 or request.inactivity_days > 365:
                raise HTTPException(status_code=400, detail="Le seuil doit etre entre 1 et 365 jours")
            config_service.set_inactivity_days(request.inactivity_days)
        
        if request.only_configured is not None:
            config_service.set_only_configured(request.only_configured)
        
        return config_service.get_config()
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de la mise a jour de la config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails")
def get_notification_emails():
    """Recupere la liste des emails de notification"""
    try:
        config_service = AlertsConfigService()
        return {"emails": config_service.get_notification_emails()}
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails")
def add_notification_email(request: EmailRequest):
    """Ajoute un email de notification"""
    try:
        config_service = AlertsConfigService()
        config = config_service.add_notification_email(request.email)
        return {"emails": config.get("notification_emails", [])}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de l'email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/emails/{email}")
def remove_notification_email(email: str):
    """Supprime un email de notification"""
    try:
        config_service = AlertsConfigService()
        config = config_service.remove_notification_email(email)
        return {"emails": config.get("notification_emails", [])}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-email")
def test_email_notification():
    """Envoie un email de test"""
    try:
        config_service = AlertsConfigService()
        email_service = EmailService()
        
        if not email_service.is_configured():
            raise HTTPException(
                status_code=400, 
                detail="Service email non configure. Definissez SMTP_USER et SMTP_PASSWORD."
            )
        
        emails = config_service.get_notification_emails()
        if not emails:
            raise HTTPException(status_code=400, detail="Aucun email de notification configure")
        
        # Envoyer un email de test
        success = email_service.send_test_email(emails)
        
        if success:
            return {"message": f"Email de test envoye a {len(emails)} destinataire(s)"}
        else:
            raise HTTPException(status_code=500, detail="Echec de l'envoi de l'email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de test: {e}")
        raise HTTPException(status_code=500, detail=str(e))
