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
    
    def send_alert_email(self, recipients: List[str], new_alerts: List[Dict], all_alerts: List[Dict], inactivity_days: int = 10) -> bool:
        """
        Envoie un email d'alerte pour les nouvelles facilities sans consommation
        
        Args:
            recipients: Liste des emails destinataires
            new_alerts: Nouvelles alertes (facilities nouvellement detectees)
            all_alerts: Toutes les alertes actuelles
            inactivity_days: Nombre de jours d'inactivite
            
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
            # Construire le sujet avec le premier client
            first_alert = new_alerts[0]
            if len(new_alerts) == 1:
                subject = f"Absence de donnees_{first_alert.get('facility_id')}_{first_alert.get('facility_name', 'Client')}"
            else:
                subject = f"Absence de donnees - {len(new_alerts)} facilities sans consommation"
            
            html_content = self._build_alert_html(new_alerts, all_alerts, inactivity_days)
            
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
    
    def send_test_email(self, recipients: List[str]) -> bool:
        """
        Envoie un email de test aux destinataires
        
        Args:
            recipients: Liste des emails destinataires
            
        Returns:
            True si l'envoi a reussi, False sinon
        """
        if not recipients:
            logger.warning("Aucun destinataire pour l'email de test")
            return False
        
        if not self.is_configured():
            logger.warning("Service email non configure (SMTP_USER/SMTP_PASSWORD manquants)")
            return False
        
        try:
            subject = "[E-Wash] Email de test - Systeme d'alertes"
            html_content = self._build_test_email_html()
            
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
            
            logger.success(f"Email de test envoye a {len(recipients)} destinataire(s)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de test: {e}")
            return False
    
    def _build_alert_html(self, new_alerts: List[Dict], all_alerts: List[Dict], inactivity_days: int = 10) -> str:
        """Construit le contenu HTML de l'email d'alerte"""
        from datetime import timedelta
        
        now = datetime.now()
        now_str = now.strftime("%d/%m/%Y à %H:%M")
        
        # Liste des nouvelles alertes avec date de première inactivité
        new_alerts_html = ""
        for alert in new_alerts:
            days_inactive = alert.get('days_inactive', inactivity_days)
            first_inactive_date = (now - timedelta(days=days_inactive)).strftime("%d/%m/%Y")
            
            new_alerts_html += f"""
            <tr style="background-color: #fff3cd;">
                <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">
                    {alert.get('facility_id')}
                </td>
                <td style="padding: 12px; border: 1px solid #e0e0e0; color: #34495e;">
                    {alert.get('facility_name')}
                </td>
                <td style="padding: 12px; border: 1px solid #e0e0e0; color: #7f8c8d;">
                    {alert.get('owner', '-')}
                </td>
                <td style="padding: 12px; border: 1px solid #e0e0e0; color: #e74c3c; font-weight: bold; text-align: center;">
                    {first_inactive_date}
                </td>
                <td style="padding: 12px; border: 1px solid #e0e0e0; color: #e67e22; font-weight: bold; text-align: center;">
                    {days_inactive} jours
                </td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f6f9;">
            <div style="max-width: 700px; margin: 30px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                
                <!-- Header avec gradient -->
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 50%, #c44569 100%); padding: 30px 25px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 10px;">⚠️</div>
                    <h1 style="margin: 0; color: white; font-size: 26px; font-weight: 600;">Alerte Consommation E-Wash</h1>
                    <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">Vérification du {now_str}</p>
                </div>
                
                <!-- Corps du message -->
                <div style="padding: 30px 25px;">
                    
                    <!-- Bandeau d'alerte -->
                    <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%); border-left: 4px solid #ff9800; padding: 15px 20px; border-radius: 6px; margin-bottom: 25px;">
                        <h2 style="margin: 0 0 8px 0; color: #d84315; font-size: 20px; display: flex; align-items: center;">
                            <span style="font-size: 24px; margin-right: 10px;">🚨</span>
                            {len(new_alerts)} Nouvelle(s) Facility(s) Sans Données
                        </h2>
                        <p style="margin: 0; color: #5d4037; font-size: 14px;">
                            Les installations suivantes n'ont enregistré aucune consommation de produits
                        </p>
                    </div>
                    
                    <!-- Tableau des alertes -->
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0; border-radius: 8px; overflow: hidden;">
                        <thead>
                            <tr style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);">
                                <th style="padding: 14px 12px; text-align: left; color: white; font-weight: 600; font-size: 13px;">N° Client</th>
                                <th style="padding: 14px 12px; text-align: left; color: white; font-weight: 600; font-size: 13px;">Facility</th>
                                <th style="padding: 14px 12px; text-align: left; color: white; font-weight: 600; font-size: 13px;">Groupe</th>
                                <th style="padding: 14px 12px; text-align: center; color: white; font-weight: 600; font-size: 13px;">1ère Inactivité</th>
                                <th style="padding: 14px 12px; text-align: center; color: white; font-weight: 600; font-size: 13px;">Durée</th>
                            </tr>
                        </thead>
                        <tbody>
                            {new_alerts_html}
                        </tbody>
                    </table>
                    
                    <!-- Statistiques -->
                    <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-left: 4px solid #4caf50; padding: 18px 20px; border-radius: 6px; margin-top: 25px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <p style="margin: 0; color: #2e7d32; font-size: 14px; font-weight: 600;">📊 Statistiques</p>
                                <p style="margin: 5px 0 0 0; color: #1b5e20; font-size: 13px;">
                                    Total des alertes actives : <strong style="font-size: 18px;">{len(all_alerts)}</strong> facilities
                                </p>
                            </div>
                        </div>
                    </div>
                    
                </div>
                
                <!-- Footer -->
                <div style="background: #f8f9fa; padding: 20px 25px; border-top: 1px solid #e0e0e0;">
                    <p style="margin: 0; color: #6c757d; font-size: 12px; line-height: 1.6;">
                        <strong>ℹ️ Information :</strong> Cet email a été envoyé automatiquement par le système de monitoring E-Wash.<br>
                        Pour modifier les paramètres de notification, connectez-vous à l'interface TMH Reports.
                    </p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _build_test_email_html(self) -> str:
        """Construit le contenu HTML de l'email de test"""
        now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f6f9;">
            <div style="max-width: 700px; margin: 30px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                
                <!-- Header avec gradient bleu -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px 25px; text-align: center;">
                    <h1 style="margin: 0; color: white; font-size: 26px; font-weight: 600;">Email de Test</h1>
                    <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">Système d'Alertes E-Wash</p>
                </div>
                
                <!-- Corps du message -->
                <div style="padding: 30px 25px;">
                    
                    <!-- Message de test simple -->
                    <p style="margin: 0 0 25px 0; color: #2c3e50; font-size: 15px; line-height: 1.6;">
                        <strong>Ceci est un Email de Test</strong><br>
                        Si vous recevez ce message, cela signifie que le système d'alertes est correctement configuré et fonctionnel.
                    </p>
                    
                    <!-- Exemple d'alerte réelle -->
                    <h3 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 16px;">Exemple d'alerte réelle :</h3>
                    
                    <!-- Bandeau d'alerte exemple -->
                    <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%); border-left: 4px solid #ff9800; padding: 15px 20px; border-radius: 6px; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 8px 0; color: #d84315; font-size: 18px;">
                            1 Nouvelle Facility Sans Données
                        </h2>
                        <p style="margin: 0; color: #5d4037; font-size: 14px;">
                            L'installation suivante n'a enregistré aucune consommation de produits
                        </p>
                    </div>
                    
                    <!-- Tableau exemple -->
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);">
                                <th style="padding: 14px 12px; text-align: left; color: white; font-weight: 600; font-size: 13px;">N° Client</th>
                                <th style="padding: 14px 12px; text-align: left; color: white; font-weight: 600; font-size: 13px;">Facility</th>
                                <th style="padding: 14px 12px; text-align: left; color: white; font-weight: 600; font-size: 13px;">Groupe</th>
                                <th style="padding: 14px 12px; text-align: center; color: white; font-weight: 600; font-size: 13px;">1ère Inactivité</th>
                                <th style="padding: 14px 12px; text-align: center; color: white; font-weight: 600; font-size: 13px;">Durée</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="background-color: #fff3cd;">
                                <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">12345</td>
                                <td style="padding: 12px; border: 1px solid #e0e0e0; color: #34495e;">Client ABC - Site Principal</td>
                                <td style="padding: 12px; border: 1px solid #e0e0e0; color: #7f8c8d;">Groupe Nord</td>
                                <td style="padding: 12px; border: 1px solid #e0e0e0; color: #e74c3c; font-weight: bold; text-align: center;">03/07/2026</td>
                                <td style="padding: 12px; border: 1px solid #e0e0e0; color: #e67e22; font-weight: bold; text-align: center;">3 jours</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <!-- Statistiques exemple -->
                    <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-left: 4px solid #4caf50; padding: 18px 20px; border-radius: 6px; margin-top: 25px;">
                        <p style="margin: 0; color: #2e7d32; font-size: 14px; font-weight: 600;">📊 Statistiques</p>
                        <p style="margin: 5px 0 0 0; color: #1b5e20; font-size: 13px;">
                            Total des alertes actives : <strong style="font-size: 16px;">5</strong> facilities
                        </p>
                    </div>
                    
                </div>
                
                <!-- Footer -->
                <div style="background: #f8f9fa; padding: 20px 25px; border-top: 1px solid #e0e0e0;">
                    <p style="margin: 0; color: #6c757d; font-size: 12px; line-height: 1.6;">
                        <strong>ℹ️ Information :</strong> Cet email a été envoyé automatiquement par le système de monitoring E-Wash.<br>
                        Pour modifier les paramètres de notification, connectez-vous à l'interface TMH Reports.
                    </p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        return html
