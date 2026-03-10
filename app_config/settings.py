"""
Configuration centralisée pour l'application de génération de rapports.
Toutes les constantes et paramètres de configuration sont définis ici.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# ==================== Chemins ====================
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "Config"
IMAGES_DIR = BASE_DIR / "images"
UPLOADS_DIR = BASE_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "Reports"
STATIC_DIR = BASE_DIR / "static"

# Fichiers de configuration
CONFIG_FILE = CONFIG_DIR / "configJson.json"
GROUP_CONFIG_FILE = CONFIG_DIR / "GroupConfigJson.json"

# ==================== API CM2W ====================
CM2W_API_KEY = os.getenv("CM2W_API_KEY", "")
CM2W_BASE_URL = os.getenv("CM2W_BASE_URL", "https://app.cm2w.net/cm2w-api/v2/api-key-auth")

# Endpoints CM2W
CM2W_ENDPOINTS = {
    "total_qty_report": "/total-qty-report",
    "devices_list": "/installation-sites/devices",
    "stock_levels": "/installation-sites/stocks",
}

# ==================== Application ====================
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "development")
APP_TITLE = "Générateur de Rapports E-wash"
APP_VERSION = "1.0.0"

# ==================== PDF Configuration ====================
# Dimensions
from reportlab.lib.units import cm

TOTAL_TABLE_WIDTH = 25 * cm

# Logos
LOGO_TMH_PATH = IMAGES_DIR / "Logo - Solution de lavage connecté.png"
LOGO_WURTH_PATH = IMAGES_DIR / "Würth_logo.png"

# Dimensions des logos
LOGO_WURTH_WIDTH = 4.5 * cm
LOGO_TMH_WIDTH = 10 * cm

# Marges et espacements
PDF_MARGIN_RIGHT = 2 * cm
PDF_MARGIN_LEFT = 2 * cm
PDF_MARGIN_TOP = 0.5 * cm
PDF_MARGIN_BOTTOM = 0

# Footer
FOOTER_X = 1 * cm
FOOTER_Y = 0.3 * cm
FOOTER_WIDTH_OFFSET = 2 * cm
FOOTER_HEIGHT = 2 * cm

# Footer text
FOOTER_TEXT = """EN CAS DE PANNE SUR LE SYSTÈME VENTURI, CONTACTEZ LE SUPPORT TECHNIQUE AU 03 88 64 72 10.
UNE QUESTION SUR VOTRE CONTRAT ? CONTACTEZ NOTRE SUPPORT ADMINISTRATIF AU 03 88 64 85 79 OU PAR MAIL systemes.solutions@wurth.fr."""

# Styles de police
FONT_TITLE = "Helvetica-Bold"
FONT_NORMAL = "Helvetica"
FONT_SIZE_TITLE = 14
FONT_SIZE_SUBTITLE = 12
FONT_SIZE_NORMAL = 10

# ==================== Logging ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "app.log")

# ==================== Validation ====================
def validate_config():
    """Valide que la configuration est correcte."""
    errors = []
    
    if not CM2W_API_KEY:
        errors.append("CM2W_API_KEY n'est pas définie dans .env")
    
    if not CONFIG_FILE.exists():
        errors.append(f"Fichier de configuration introuvable: {CONFIG_FILE}")
    
    if not LOGO_TMH_PATH.exists():
        errors.append(f"Logo TMH introuvable: {LOGO_TMH_PATH}")
    
    if not LOGO_WURTH_PATH.exists():
        errors.append(f"Logo Würth introuvable: {LOGO_WURTH_PATH}")
    
    if errors:
        raise ValueError(f"Erreurs de configuration:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True

# Valider au chargement du module (optionnel, peut être commenté en dev)
# validate_config()
