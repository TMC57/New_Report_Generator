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
            facility_name = first_alert.get('facility_name', 'Client')
            # Extraire uniquement le nom sans le numéro au début
            name_parts = facility_name.split(maxsplit=1)
            clean_name = name_parts[1] if len(name_parts) > 1 else facility_name
            
            if len(new_alerts) == 1:
                subject = f"Absence de donnees_{first_alert.get('facility_id')}_{clean_name}"
            else:
                subject = f"Absence de donnees - {len(new_alerts)} facilities sans consommation"
            
            html_content = self._build_alert_html(new_alerts, all_alerts, inactivity_days)
            
            # Creer le message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"E-Wash Alertes <{self.from_email}>"
            msg["To"] = ", ".join(recipients)
            msg["Reply-To"] = self.from_email
            msg["X-Mailer"] = "TMH E-Wash Monitoring System"
            
            # Ajouter le contenu HTML
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # Envoyer l'email
            if self.port == 465:
                # SSL
                with smtplib.SMTP_SSL(self.host, self.port) as server:
                    server.login(self.user, self.password)
                    server.sendmail(self.from_email, recipients, msg.as_string())
            else:
                # STARTTLS (port 587)
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls()
                    server.login(self.user, self.password)
                    server.sendmail(self.from_email, recipients, msg.as_string())
            
            logger.success(f"Email d'alerte envoye a {len(recipients)} destinataire(s)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            return False
    
    def send_test_email(self, recipients: List[str], real_alert: List[Dict] = None) -> bool:
        """
        Envoie un email de test aux destinataires
        
        Args:
            recipients: Liste des emails destinataires
            real_alert: Liste contenant une vraie facility en alerte (optionnel)
            
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
            html_content = self._build_test_email_html(real_alert)
            
            # Creer le message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"E-Wash Alertes <{self.from_email}>"
            msg["To"] = ", ".join(recipients)
            msg["Reply-To"] = self.from_email
            msg["X-Mailer"] = "TMH E-Wash Monitoring System"
            
            # Ajouter le contenu HTML
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # Envoyer l'email
            if self.port == 465:
                # SSL
                with smtplib.SMTP_SSL(self.host, self.port) as server:
                    server.login(self.user, self.password)
                    server.sendmail(self.from_email, recipients, msg.as_string())
            else:
                # STARTTLS (port 587)
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
                <td style="padding: 10px 8px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; font-size: 13px; word-wrap: break-word;">
                    {alert.get('facility_id')}
                </td>
                <td style="padding: 10px 8px; border: 1px solid #e0e0e0; color: #34495e; font-size: 13px; word-wrap: break-word;">
                    {alert.get('facility_name')}
                </td>
                <td style="padding: 10px 8px; border: 1px solid #e0e0e0; color: #7f8c8d; font-size: 13px; word-wrap: break-word;">
                    {alert.get('owner', '-')}
                </td>
                <td style="padding: 10px 8px; border: 1px solid #e0e0e0; color: #e74c3c; font-weight: bold; text-align: center; font-size: 13px;">
                    {first_inactive_date}
                </td>
                <td style="padding: 10px 8px; border: 1px solid #e0e0e0; color: #e67e22; font-weight: bold; text-align: center; font-size: 13px;">
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
            <div style="max-width: 700px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                
                <!-- Header avec gradient -->
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 50%, #c44569 100%); padding: 25px 20px; text-align: center;">
                    <h1 style="margin: 0; color: white; font-size: 24px; font-weight: 600;">Alerte Consommation E-Wash</h1>
                    <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 13px;">Vérification du {now_str}</p>
                </div>
                
                <!-- Corps du message -->
                <div style="padding: 25px 20px;">
                    
                    <!-- Logo E-Wash -->
                    <div style="text-align: center; margin-bottom: 25px;">
                        <img src="https://raw.githubusercontent.com/TMC57/New_Report_Generator/main/refactored/images/Logo%20-%20Solution%20de%20lavage%20connect%C3%A9.png" alt="E-Wash Solution de lavage connecté" style="max-width: 350px; height: auto;">
                    </div>
                    
                    <!-- Titre d'alerte -->
                    <h2 style="margin: 0 0 10px 0; color: #d84315; font-size: 20px; text-align: center;">
                        ⚠️ Absence de données depuis {inactivity_days} jours
                    </h2>
                    <p style="margin: 0 0 25px 0; color: #5d4037; font-size: 14px; text-align: center;">
                        {len(new_alerts)} installation(s) n'ont enregistré aucune consommation de produits
                    </p>
                    
                    <!-- Tableau des alertes -->
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; max-width: 100%; border-collapse: collapse; margin: 20px 0; table-layout: fixed;">
                            <thead>
                                <tr style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);">
                                    <th style="padding: 12px 8px; text-align: left; color: white; font-weight: 600; font-size: 12px; width: 12%;">N° Client</th>
                                    <th style="padding: 12px 8px; text-align: left; color: white; font-weight: 600; font-size: 12px; width: 35%;">Facility</th>
                                    <th style="padding: 12px 8px; text-align: left; color: white; font-weight: 600; font-size: 12px; width: 23%;">Groupe</th>
                                    <th style="padding: 12px 8px; text-align: center; color: white; font-weight: 600; font-size: 12px; width: 15%;">1ère Inactivité</th>
                                    <th style="padding: 12px 8px; text-align: center; color: white; font-weight: 600; font-size: 12px; width: 15%;">Durée</th>
                                </tr>
                            </thead>
                            <tbody>
                                {new_alerts_html}
                            </tbody>
                        </table>
                    </div>
                    
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
    
    def _build_test_email_html(self, real_alert: List[Dict] = None) -> str:
        """Construit le contenu HTML de l'email de test"""
        from datetime import timedelta
        
        now = datetime.now()
        now_str = now.strftime("%d/%m/%Y à %H:%M")
        
        # Utiliser une vraie facility si disponible, sinon exemple fictif
        if real_alert and len(real_alert) > 0:
            alert = real_alert[0]
            facility_id = alert.get('facility_id', 12345)
            facility_name = alert.get('facility_name', 'Client ABC - Site Principal')
            owner = alert.get('owner', 'Groupe Nord')
            days_inactive = alert.get('days_inactive', 3)
            first_inactive_date = (now - timedelta(days=days_inactive)).strftime("%d/%m/%Y")
        else:
            facility_id = 12345
            facility_name = "Client ABC - Site Principal"
            owner = "Groupe Nord"
            days_inactive = 3
            first_inactive_date = "03/07/2026"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f6f9;">
            <div style="max-width: 700px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                
                <!-- Header avec gradient bleu -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px 20px; text-align: center;">
                    <h1 style="margin: 0; color: white; font-size: 24px; font-weight: 600;">Email de Test</h1>
                    <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 13px;">Système d'Alertes E-Wash</p>
                </div>
                
                <!-- Corps du message -->
                <div style="padding: 25px 20px;">
                    
                    <!-- Message de test simple -->
                    <p style="margin: 0 0 20px 0; color: #2c3e50; font-size: 15px; line-height: 1.6;">
                        <strong>Ceci est un Email de Test</strong><br>
                        Si vous recevez ce message, cela signifie que le système d'alertes est correctement configuré et fonctionnel.
                    </p>
                    
                    <!-- Exemple d'alerte réelle -->
                    <h3 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 16px;">Exemple d'alerte réelle :</h3>
                    
                    <!-- Logo E-Wash -->
                    <div style="text-align: center; margin-bottom: 25px;">
                        <img src="https://raw.githubusercontent.com/TMC57/New_Report_Generator/main/refactored/images/Logo%20-%20Solution%20de%20lavage%20connect%C3%A9.png" alt="E-Wash Solution de lavage connecté" style="max-width: 350px; height: auto;">
                    </div>
                    
                    <!-- Titre d'alerte exemple -->
                    <h2 style="margin: 0 0 10px 0; color: #d84315; font-size: 18px; text-align: center;">
                        ⚠️ Absence de données depuis {days_inactive} jours
                    </h2>
                    <p style="margin: 0 0 20px 0; color: #5d4037; font-size: 14px; text-align: center;">
                        1 installation n'a enregistré aucune consommation de produits
                    </p>
                    
                    <!-- Tableau exemple -->
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);">
                                <th style="padding: 10px 6px; text-align: left; color: white; font-weight: 600; font-size: 11px;">N° Client</th>
                                <th style="padding: 10px 6px; text-align: left; color: white; font-weight: 600; font-size: 11px;">Facility</th>
                                <th style="padding: 10px 6px; text-align: left; color: white; font-weight: 600; font-size: 11px;">Groupe</th>
                                <th style="padding: 10px 6px; text-align: center; color: white; font-weight: 600; font-size: 11px;">1ère Inactivité</th>
                                <th style="padding: 10px 6px; text-align: center; color: white; font-weight: 600; font-size: 11px;">Durée</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="background-color: #fff3cd;">
                                <td style="padding: 8px 6px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; font-size: 12px;">{facility_id}</td>
                                <td style="padding: 8px 6px; border: 1px solid #e0e0e0; color: #34495e; font-size: 12px;">{facility_name}</td>
                                <td style="padding: 8px 6px; border: 1px solid #e0e0e0; color: #7f8c8d; font-size: 12px;">{owner}</td>
                                <td style="padding: 8px 6px; border: 1px solid #e0e0e0; color: #e74c3c; font-weight: bold; text-align: center; font-size: 12px;">{first_inactive_date}</td>
                                <td style="padding: 8px 6px; border: 1px solid #e0e0e0; color: #e67e22; font-weight: bold; text-align: center; font-size: 12px;">{days_inactive} jours</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <!-- Statistiques exemple -->
                    <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-left: 4px solid #4caf50; padding: 18px 20px; border-radius: 6px; margin-top: 20px;">
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
