"""
Scheduler pour la verification quotidienne des alertes de consommation
Execute automatiquement a 9h00 chaque jour
"""
import threading
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from refactored.services.consumption_monitor_service import ConsumptionMonitorService
from refactored.services.alerts_config_service import AlertsConfigService
from refactored.services.email_service import EmailService
from refactored.utils.logger import get_logger

logger = get_logger("Alerts_Scheduler")

# Scheduler global
_scheduler = None
_scheduler_lock = threading.Lock()


def run_daily_check():
    """
    Execute la verification quotidienne des alertes
    - Verifie les facilities sans consommation
    - Compare avec les alertes precedentes
    - Envoie un email si nouvelles alertes
    """
    logger.info("=" * 60)
    logger.info("[SCHEDULER] Demarrage de la verification quotidienne")
    logger.info(f"[SCHEDULER] Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        config_service = AlertsConfigService()
        monitor_service = ConsumptionMonitorService()
        email_service = EmailService()
        
        # Recuperer les parametres sauvegardes
        inactivity_days = config_service.get_inactivity_days()
        only_configured = config_service.get_only_configured()
        
        logger.info(f"[SCHEDULER] Parametres: seuil={inactivity_days}j, only_configured={only_configured}")
        
        # Executer la verification
        result = monitor_service.check_all_facilities(
            inactivity_days=inactivity_days,
            only_configured=only_configured
        )
        
        current_alerts = result.get("alerts", [])
        logger.info(f"[SCHEDULER] {len(current_alerts)} alertes detectees")
        
        # Detecter les nouvelles alertes
        new_alerts = config_service.get_new_alerts(current_alerts)
        logger.info(f"[SCHEDULER] {len(new_alerts)} nouvelle(s) alerte(s)")
        
        # Envoyer un email si nouvelles alertes
        if new_alerts:
            emails = config_service.get_notification_emails()
            if emails:
                logger.info(f"[SCHEDULER] Envoi d'email a {len(emails)} destinataire(s)")
                sent = email_service.send_alert_email(emails, new_alerts, current_alerts, inactivity_days)
                if sent:
                    config_service.mark_email_sent(len(emails))
            else:
                logger.warning("[SCHEDULER] Nouvelles alertes mais aucun email configure")
        
        # Sauvegarder les alertes actuelles pour la prochaine comparaison
        config_service.update_last_check(current_alerts)
        
        logger.success(f"[SCHEDULER] Verification terminee avec succes")
        
    except Exception as e:
        logger.error(f"[SCHEDULER] Erreur lors de la verification: {e}")
        import traceback
        traceback.print_exc()


def start_scheduler():
    """Demarre le scheduler pour les verifications quotidiennes"""
    global _scheduler
    
    with _scheduler_lock:
        if _scheduler is not None:
            logger.info("[SCHEDULER] Scheduler deja demarre")
            return
        
        logger.info("[SCHEDULER] Demarrage du scheduler...")
        
        _scheduler = BackgroundScheduler(timezone="Europe/Paris")
        
        # Ajouter le job quotidien a 9h00
        _scheduler.add_job(
            run_daily_check,
            trigger=CronTrigger(hour=9, minute=0),
            id="daily_consumption_check",
            name="Verification quotidienne des consommations",
            replace_existing=True
        )
        
        _scheduler.start()
        
        logger.success("[SCHEDULER] Scheduler demarre - Prochaine execution a 09:00")


def stop_scheduler():
    """Arrete le scheduler"""
    global _scheduler
    
    with _scheduler_lock:
        if _scheduler is not None:
            _scheduler.shutdown()
            _scheduler = None
            logger.info("[SCHEDULER] Scheduler arrete")


def get_scheduler_status():
    """Retourne le statut du scheduler"""
    global _scheduler
    
    if _scheduler is None:
        return {"running": False, "next_run": None}
    
    jobs = _scheduler.get_jobs()
    next_run = None
    
    for job in jobs:
        if job.id == "daily_consumption_check":
            next_run = job.next_run_time.isoformat() if job.next_run_time else None
            break
    
    return {
        "running": _scheduler.running,
        "next_run": next_run
    }
