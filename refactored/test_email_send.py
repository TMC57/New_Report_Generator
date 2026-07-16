"""
Script de test d'envoi d'email.

Usage :
    python refactored/test_email_send.py                 # envoie au SMTP_FROM
    python refactored/test_email_send.py destinataire@ex.com

Charge le .env, verifie la config SMTP, teste la connexion + l'authentification,
puis envoie le VRAI mail d'alerte du projet (template send_alert_email /
_build_alert_html) avec des donnees d'exemple, via le EmailService de production.
"""
import os
import sys
import ssl
import smtplib
import socket
from pathlib import Path
from dotenv import load_dotenv

# Charger le .env du dossier refactored (encoding utf-8-sig = tolerant au BOM)
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, encoding="utf-8-sig")

# Permettre l'import de "refactored.*"
sys.path.insert(0, str(Path(__file__).parent.parent))
from refactored.services.email_service import EmailService


def check_connection(host: str, port: int, user: str, password: str) -> bool:
    """Teste la connexion TCP + STARTTLS/SSL + l'authentification (sans envoyer)."""
    print(f"\n--- Test connexion {host}:{port} ---")
    try:
        with socket.create_connection((host, port), timeout=15) as s:
            print(f"  [OK] TCP connecte -> {s.getpeername()}")
    except Exception as e:
        print(f"  [ECHEC] TCP: {e!r}")
        return False

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=20)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
        with server:
            server.ehlo()
            if port != 465:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            server.login(user, password)
            print("  [OK] Authentification reussie")
        return True
    except Exception as e:
        print(f"  [ECHEC] SMTP/AUTH: {e!r}")
        return False


def main():
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("SMTP_FROM", "")

    print("=== Configuration SMTP ===")
    print(f"  SMTP_HOST : {host}")
    print(f"  SMTP_PORT : {port}")
    print(f"  SMTP_USER : {user}")
    print(f"  SMTP_FROM : {from_email}")
    print(f"  SMTP_PASSWORD : {'*** ('+str(len(password))+' car.)' if password else 'NON CONFIGURE'}")

    if not (user and password):
        print("\n[ERREUR] SMTP_USER / SMTP_PASSWORD manquants dans le .env. Abandon.")
        sys.exit(1)

    if not check_connection(host, port, user, password):
        print("\n[ERREUR] Connexion/auth impossible. On n'envoie pas.")
        sys.exit(1)

    # Destinataire : argument CLI, sinon on s'envoie a soi-meme (SMTP_FROM)
    recipient = sys.argv[1] if len(sys.argv) > 1 else from_email
    print(f"\n--- Envoi du mail d'alerte a : {recipient} ---")

    # Donnees d'exemple au format attendu par send_alert_email()
    # (memes cles que les vraies alertes : facility_id, facility_name, owner, days_inactive)
    inactivity_days = 10
    new_alerts = [
        {
            "facility_id": 39547,
            "facility_name": "12345 Station Lavage Exemple - Site Nord",
            "owner": "Groupe Nord",
            "days_inactive": 12,
        },
        {
            "facility_id": 40218,
            "facility_name": "67890 Station Lavage Exemple - Site Sud",
            "owner": "Groupe Sud",
            "days_inactive": 15,
        },
    ]
    # all_alerts = toutes les alertes actives (>= new_alerts). Ici on reprend les memes + une autre.
    all_alerts = new_alerts + [
        {
            "facility_id": 40999,
            "facility_name": "11111 Station Lavage Exemple - Site Est",
            "owner": "Groupe Est",
            "days_inactive": 30,
        },
    ]

    service = EmailService()
    ok = service.send_alert_email(
        recipients=[recipient],
        new_alerts=new_alerts,
        all_alerts=all_alerts,
        inactivity_days=inactivity_days,
    )

    print(f"\nResultat : {'[OK] Email envoye' if ok else '[ECHEC] Envoi echoue'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
