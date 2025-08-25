# colors_map.py
import re, hashlib

# === Mapping table (match par sous-chaîne, insensible à la casse/espaces) ===
# Exigences:
# - Jantes -> Violet
# - WNC40 -> Vert clair
# - Autoséchant -> Bleu clair
# - WNC31 -> Rouge
# - WNC50 -> Vert
# - WNC70 -> Vert clair (même que WNC40)
PRODUCT_COLOR_MAP = [
    (r"JANTES",   "#8064A2"),  # Violet (BlueViolet)
    (r"WNC40",    "#92D050"),  # Vert clair
    (r"AUTOSECHANT", "#00B0F0"),  # Bleu clair (sans accent pour matching robuste)
    (r"WNC31",    "#C0504D"),  # Rouge
    (r"WNC50",    "#00B050"),  # Vert
    (r"WNC70",    "#92D050"),  # Vert clair (même que WNC40)
    (r"EAU",    "#0070C0"),  # l'eau
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
