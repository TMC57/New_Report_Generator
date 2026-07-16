"""
Service pour envoyer des emails de notification
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
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

# Logo E-Wash : embarque en inline (CID) si le fichier local existe (meilleure
# delivrabilite), sinon repli sur le lien externe GitHub.
LOGO_PATH = Path(__file__).parent.parent / "images" / "Logo - Solution de lavage connecté.png"
LOGO_REMOTE_URL = "https://raw.githubusercontent.com/TMC57/New_Report_Generator/main/refactored/images/Logo%20-%20Solution%20de%20lavage%20connect%C3%A9.png"


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

    def _logo_src(self) -> str:
        """Source du logo a utiliser dans le HTML : CID si embarque, sinon URL externe."""
        return "cid:logo" if LOGO_PATH.exists() else LOGO_REMOTE_URL

    def _create_message(self, subject: str, recipients: List[str], html_content: str) -> MIMEMultipart:
        """Construit le message. Si le logo local existe, il est embarque en inline (CID)
        via un conteneur multipart/related pour ameliorer la delivrabilite."""
        outer = MIMEMultipart("related")
        outer["Subject"] = subject
        outer["From"] = f"E-Wash Alertes <{self.from_email}>"
        outer["To"] = ", ".join(recipients)
        outer["Reply-To"] = self.from_email
        outer["X-Mailer"] = "TMH E-Wash Monitoring System"

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(html_content, "html", "utf-8"))
        outer.attach(alt)

        if LOGO_PATH.exists():
            try:
                with open(LOGO_PATH, "rb") as f:
                    img = MIMEImage(f.read())
                img.add_header("Content-ID", "<logo>")
                img.add_header("Content-Disposition", "inline", filename="logo.png")
                outer.attach(img)
            except Exception as e:
                logger.warning(f"Logo non embarque (repli sur lien externe): {e}")

        return outer

    def _send_message(self, msg: MIMEMultipart, recipients: List[str]) -> None:
        """Envoie le message via SMTP (SSL sur 465, sinon STARTTLS)."""
        if self.port == 465:
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(self.user, self.password)
                server.sendmail(self.from_email, recipients, msg.as_string())
        else:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, recipients, msg.as_string())
    
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

            # Creer le message (logo embarque en inline si disponible) et l'envoyer
            msg = self._create_message(subject, recipients, html_content)
            self._send_message(msg, recipients)

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

            # Creer le message (logo embarque en inline si disponible) et l'envoyer
            msg = self._create_message(subject, recipients, html_content)
            self._send_message(msg, recipients)

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
            <tr>
                <td style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#2c3e50;font-weight:bold;">{alert.get('facility_id')}</td>
                <td style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#34495e;">{alert.get('facility_name')}</td>
                <td style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#7f8c8d;">{alert.get('owner', '-')}</td>
                <td align="center" style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#c0392b;font-weight:bold;white-space:nowrap;">{first_inactive_date}</td>
                <td align="center" style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#d35400;font-weight:bold;white-space:nowrap;">{days_inactive} j</td>
            </tr>
            """
        
        html = f"""<!DOCTYPE html>
<html lang="fr" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Alerte Consommation E-Wash</title>
    <!--[if mso]>
    <noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
    <![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#f4f6f9;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f6f9;">
        <tr>
            <td align="center" style="padding:24px 12px;">
                <!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
                <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;background-color:#ffffff;border:1px solid #e6e8ec;border-radius:8px;">
                    <!-- Header -->
                    <tr>
                        <td bgcolor="#2c3e50" style="background-color:#2c3e50;padding:22px 24px;text-align:center;border-radius:8px 8px 0 0;">
                            <div style="font-family:Arial,Helvetica,sans-serif;font-size:20px;font-weight:bold;color:#ffffff;">Alerte Consommation E-Wash</div>
                            <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#c8d0da;padding-top:6px;">Vérification du {now_str}</div>
                        </td>
                    </tr>
                    <!-- Logo -->
                    <tr>
                        <td style="padding:28px 24px 6px 24px;text-align:center;">
                            <img src="{self._logo_src()}" alt="Solution de lavage connecté 2.0" width="240" style="width:240px;max-width:80%;height:auto;display:inline-block;border:0;">
                        </td>
                    </tr>
                    <!-- Bandeau d'alerte -->
                    <tr>
                        <td style="padding:10px 24px 0 24px;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#fff8ec;border-left:4px solid #e67e22;">
                                <tr>
                                    <td style="padding:14px 16px;font-family:Arial,Helvetica,sans-serif;">
                                        <div style="font-size:16px;font-weight:bold;color:#c0392b;">Absence de données depuis {inactivity_days} jours</div>
                                        <div style="font-size:13px;color:#7f5a3a;padding-top:4px;">{len(new_alerts)} installation(s) sans consommation de produits enregistrée</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Tableau des alertes -->
                    <tr>
                        <td style="padding:20px 24px 4px 24px;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;border:1px solid #e6e8ec;">
                                <tr>
                                    <td bgcolor="#2c3e50" width="14%" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">N° Client</td>
                                    <td bgcolor="#2c3e50" width="36%" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">Facility</td>
                                    <td bgcolor="#2c3e50" width="22%" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">Groupe</td>
                                    <td bgcolor="#2c3e50" width="16%" align="center" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">1ère inactivité</td>
                                    <td bgcolor="#2c3e50" width="12%" align="center" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">Durée</td>
                                </tr>
                                {new_alerts_html}
                            </table>
                        </td>
                    </tr>
                    <!-- Statistiques -->
                    <tr>
                        <td style="padding:16px 24px 0 24px;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#eef7f0;border:1px solid #d6ebd9;">
                                <tr>
                                    <td style="padding:14px 16px;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#2e7d32;">
                                        Total des alertes actives : <span style="font-size:18px;font-weight:bold;color:#1b5e20;">{len(all_alerts)}</span> facilities
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding:20px 24px 24px 24px;">
                            <div style="border-top:1px solid #e6e8ec;padding-top:16px;font-family:Arial,Helvetica,sans-serif;font-size:11px;line-height:1.6;color:#9aa2ac;">
                                Cet email a été envoyé automatiquement par le système de monitoring E-Wash.<br>
                                Pour modifier les paramètres de notification, connectez-vous à l'interface TMH Reports.
                            </div>
                        </td>
                    </tr>
                </table>
                <!--[if mso]></td></tr></table><![endif]-->
            </td>
        </tr>
    </table>
</body>
</html>"""

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
        
        html = f"""<!DOCTYPE html>
<html lang="fr" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Email de test E-Wash</title>
    <!--[if mso]>
    <noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
    <![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#f4f6f9;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f6f9;">
        <tr>
            <td align="center" style="padding:24px 12px;">
                <!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
                <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;background-color:#ffffff;border:1px solid #e6e8ec;border-radius:8px;">
                    <!-- Header -->
                    <tr>
                        <td bgcolor="#2c3e50" style="background-color:#2c3e50;padding:22px 24px;text-align:center;border-radius:8px 8px 0 0;">
                            <div style="font-family:Arial,Helvetica,sans-serif;font-size:20px;font-weight:bold;color:#ffffff;">Email de test</div>
                            <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#c8d0da;padding-top:6px;">Système d'alertes E-Wash</div>
                        </td>
                    </tr>
                    <!-- Logo -->
                    <tr>
                        <td style="padding:28px 24px 6px 24px;text-align:center;">
                            <img src="{self._logo_src()}" alt="Solution de lavage connecté 2.0" width="240" style="width:240px;max-width:80%;height:auto;display:inline-block;border:0;">
                        </td>
                    </tr>
                    <!-- Message de test -->
                    <tr>
                        <td style="padding:8px 24px 0 24px;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#eef7f0;border-left:4px solid #4caf50;">
                                <tr>
                                    <td style="padding:14px 16px;font-family:Arial,Helvetica,sans-serif;">
                                        <div style="font-size:15px;font-weight:bold;color:#2e7d32;">Configuration validée</div>
                                        <div style="font-size:13px;color:#3c6b40;padding-top:4px;">Si vous recevez ce message, le système d'alertes est correctement configuré et fonctionnel. Voici un aperçu d'une alerte réelle :</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Tableau exemple -->
                    <tr>
                        <td style="padding:20px 24px 4px 24px;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;border:1px solid #e6e8ec;">
                                <tr>
                                    <td bgcolor="#2c3e50" width="14%" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">N° Client</td>
                                    <td bgcolor="#2c3e50" width="36%" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">Facility</td>
                                    <td bgcolor="#2c3e50" width="22%" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">Groupe</td>
                                    <td bgcolor="#2c3e50" width="16%" align="center" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">1ère inactivité</td>
                                    <td bgcolor="#2c3e50" width="12%" align="center" style="background-color:#2c3e50;padding:10px;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;">Durée</td>
                                </tr>
                                <tr>
                                    <td style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#2c3e50;font-weight:bold;">{facility_id}</td>
                                    <td style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#34495e;">{facility_name}</td>
                                    <td style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#7f8c8d;">{owner}</td>
                                    <td align="center" style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#c0392b;font-weight:bold;white-space:nowrap;">{first_inactive_date}</td>
                                    <td align="center" style="padding:12px 10px;border-bottom:1px solid #eceef1;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#d35400;font-weight:bold;white-space:nowrap;">{days_inactive} j</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding:20px 24px 24px 24px;">
                            <div style="border-top:1px solid #e6e8ec;padding-top:16px;font-family:Arial,Helvetica,sans-serif;font-size:11px;line-height:1.6;color:#9aa2ac;">
                                Cet email a été envoyé automatiquement par le système de monitoring E-Wash.<br>
                                Pour modifier les paramètres de notification, connectez-vous à l'interface TMH Reports.
                            </div>
                        </td>
                    </tr>
                </table>
                <!--[if mso]></td></tr></table><![endif]-->
            </td>
        </tr>
    </table>
</body>
</html>"""

        return html
