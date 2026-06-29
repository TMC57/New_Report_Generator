"""
Routes API pour les alertes de consommation
"""
from fastapi import APIRouter, HTTPException, Query
from refactored.services.consumption_monitor_service import ConsumptionMonitorService
from refactored.utils.logger import get_logger

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])
logger = get_logger("Alerts_Routes")


@router.get("/inactive-facilities")
def get_inactive_facilities(
    days: int = Query(default=10, ge=1, le=90, description="Nombre de jours sans consommation")
):
    """
    Recupere la liste des facilities sans consommation depuis X jours
    
    Args:
        days: Nombre de jours d'inactivite (defaut: 10, min: 1, max: 90)
        
    Returns:
        Dict avec les facilities inactives et les statistiques
    """
    logger.info(f"Verification des facilities inactives (seuil: {days} jours)")
    
    try:
        service = ConsumptionMonitorService()
        result = service.check_all_facilities(inactivity_days=days)
        
        logger.success(f"Verification terminee: {result['alerts_count']} alertes")
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))
