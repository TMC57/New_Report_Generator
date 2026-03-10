# colors_map.py
import re, hashlib

# === Mapping table (match par sous-chaîne, insensible à la casse/espaces) ===
# Couleurs selon cahier des charges 2026
# Source: TR_ E-Wash - modifications des statistiques
PRODUCT_COLOR_MAP = [
    # WNC 40 - Emerald
    (r"WNC40",    "#65C482"),
    (r"WNC 40",   "#65C482"),
    
    # WNC 50 - Medium jungle
    (r"WNC50",    "#34A65F"),
    (r"WNC 50",   "#34A65F"),
    
    # WNC 60 - Sea green
    (r"WNC60",    "#1F8A4B"),
    (r"WNC 60",   "#1F8A4B"),
    
    # WNC 70 - Dark emerald
    (r"WNC70",    "#0F6A33"),
    (r"WNC 70",   "#0F6A33"),
    
    # WNC 31 - Tuscan sun
    (r"WNC31",    "#F7C844"),
    (r"WNC 31",   "#F7C844"),
    
    # Auto-séchant - Wisteria blue
    (r"AUTOSECHANT", "#8698CB"),
    (r"AUTOSECH",    "#8698CB"),
    (r"AUTO-SECHANT", "#8698CB"),
    
    # Purple (Jantes) - Indigo bloom
    (r"PURPLE",   "#7B3FA7"),
    (r"JANTES",   "#7B3FA7"),
    
    # Eau - Soft cyan
    (r"EAU",      "#90F1EF"),
]

# Palette fallback pour les produits non mappés (cohérente et déterministe)
FALLBACK_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

def _normalize(s: str) -> str:
    # Uppercase, retire espaces & accents de base (on simplifie 'AUTOSÉCHANT' -> 'AUTOSECHANT')
    s = (s or "").upper()
    s = re.sub(r"\s+", "", s)
    s = (s
         .replace("É", "E").replace("È", "E").replace("Ê", "E")
         .replace("À", "A").replace("Â", "A")
         .replace("Ù", "U").replace("Û", "U")
         .replace("Î", "I").replace("Ï", "I")
         .replace("Ô", "O").replace("Ö", "O")
    )
    return s

def get_color_for_product(name: str) -> str:
    n = _normalize(name)
    for pattern, color in PRODUCT_COLOR_MAP:
        if re.search(pattern, n):
            return color
    # Fallback déterministe (hash du nom)
    h = int(hashlib.md5(n.encode("utf-8")).hexdigest(), 16)
    return FALLBACK_COLORS[h % len(FALLBACK_COLORS)]

def get_colors_for_products(names) -> list[str]:
    return [get_color_for_product(n) for n in names]
