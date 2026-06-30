"""
Service pour envoyer des emails de notification
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime
from refactored.utils.logger import get_logger

logger = get_logger("Email_Service")

# Configuration SMTP depuis variables d'environnement
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "alerts@e-wash.fr")


class EmailService:
    """Service pour envoyer des emails de notification"""
    
    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
        self.from_email = SMTP_FROM
    
    def is_configured(self) -> bool:
        """Verifie si le service email est configure"""
        return bool(self.user and self.password)
    
    def send_alert_email(self, recipients: List[str], new_alerts: List[Dict], all_alerts: List[Dict]) -> bool:
        """
        Envoie un email d'alerte pour les nouvelles facilities sans consommation
        
        Args:
            recipients: Liste des emails destinataires
            new_alerts: Nouvelles alertes (facilities nouvellement detectees)
            all_alerts: Toutes les alertes actuelles
            
        Returns:
            True si l'envoi a reussi, False sinon
        """
        if not recipients:
            logger.warning("Aucun destinataire pour l'email d'alerte")
            return False
        
        if not self.is_configured():
            logger.warning("Service email non configure (SMTP_USER/SMTP_PASSWORD manquants)")
            return False
        
        if not new_alerts:
            logger.info("Aucune nouvelle alerte, pas d'email envoye")
            return True
        
        try:
            # Construire le contenu de l'email
            subject = f"[E-Wash] {len(new_alerts)} nouvelle(s) alerte(s) de consommation"
            html_content = self._build_alert_html(new_alerts, all_alerts)
            
            # Creer le message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(recipients)
            
            # Ajouter le contenu HTML
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # Envoyer l'email
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, recipients, msg.as_string())
            
            logger.success(f"Email d'alerte envoye a {len(recipients)} destinataire(s)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            return False
    
    def _build_alert_html(self, new_alerts: List[Dict], all_alerts: List[Dict]) -> str:
        """Construit le contenu HTML de l'email d'alerte"""
        now = datetime.now().strftime("%d/%m/%Y a %H:%M")
        
        # Liste des nouvelles alertes
        new_alerts_html = ""
        for alert in new_alerts:
            new_alerts_html += f"""
            <tr style="background-color: #fff3cd;">
                <td style="padding: 10px; border: 1px solid #ddd;">{alert.get('facility_id')}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{alert.get('facility_name')}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{alert.get('owner', '-')}</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #dc3545; font-weight: bold;">
                    {alert.get('days_inactive', 0)} jours
                </td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0;">⚠️ Alertes de Consommation E-Wash</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Verification du {now}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border: 1px solid #ddd; border-top: none;">
                <h2 style="color: #dc3545; margin-top: 0;">
                    🚨 {len(new_alerts)} Nouvelle(s) Alerte(s)
                </h2>
                <p>Les facilities suivantes n'ont enregistre aucune consommation de produits:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background-color: #343a40; color: white;">
                            <th style="padding: 10px; text-align: left;">ID</th>
                            <th style="padding: 10px; text-align: left;">Facility</th>
                            <th style="padding: 10px; text-align: left;">Groupe</th>
                            <th style="padding: 10px; text-align: left;">Inactivite</th>
                        </tr>
                    </thead>
                    <tbody>
                        {new_alerts_html}
                    </tbody>
                </table>
                
                <div style="background: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    <p style="margin: 0;">
                        <strong>Total des alertes actives:</strong> {len(all_alerts)} facilities
                    </p>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                
                <p style="color: #6c757d; font-size: 12px; margin: 0;">
                    Cet email a ete envoye automatiquement par le systeme de monitoring E-Wash.<br>
                    Pour modifier les parametres de notification, connectez-vous a l'interface TMH Reports.
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
