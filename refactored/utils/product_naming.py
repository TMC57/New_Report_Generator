"""
Normalisation de noms de produits pour les sites dont le nommage CM2W est non
standard (ex: produits nommes "Auto sech uc z2 car espace", doublons de produits
au nom identique sans marqueur de zone...).

IMPORTANT : ces regles s'appliquent UNIQUEMENT aux facility_id listes dans
SITE_PRODUCT_NAME_OVERRIDES. Pour tout autre site, les fonctions renvoient les
données inchangées -> aucun impact sur le reste des rapports.
"""
import re
import unicodedata
from typing import List, Dict, Optional
from difflib import SequenceMatcher

# ---------------------------------------------------------------------------
# Configuration par site.
# Format: { facility_id (int): [ (motif_regex_sur_nom_normalise, nom_canonique), ... ] }
# Le nom normalise = majuscules, sans accents, sans espaces ni tirets.
# Le premier motif qui matche donne le nom canonique du produit.
# ---------------------------------------------------------------------------
SITE_PRODUCT_NAME_OVERRIDES = {
    # 1071123521 SAS CAR ESPACE : nommage CM2W non standard ("... z1/z2 car espace").
    # "Auto sech uc z2 car espace" doit etre regroupe avec l'auto-sechant reference.
    46811: [
        (r"AUTOSECH", "Auto-séchant ultraconcentré 20L - 0893025020"),
    ],
}


def _normalize(name: str) -> str:
    """Majuscules, sans accents, sans espaces ni tirets."""
    if not name:
        return ""
    name = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    return name.upper().replace(" ", "").replace("-", "")


def site_has_overrides(facility_id) -> bool:
    """True si ce site a des regles de normalisation specifiques."""
    try:
        return int(facility_id) in SITE_PRODUCT_NAME_OVERRIDES
    except (TypeError, ValueError):
        return False


def canonical_product_name(facility_id, raw_name: str) -> str:
    """Renvoie le nom canonique d'un produit pour ce site.

    - Site sans regle -> nom inchange.
    - Site avec regles -> applique la premiere regle qui matche, sinon nom inchange.
    """
    rules = None
    try:
        rules = SITE_PRODUCT_NAME_OVERRIDES.get(int(facility_id))
    except (TypeError, ValueError):
        return raw_name
    if not rules:
        return raw_name

    norm = _normalize(raw_name)
    for pattern, canonical in rules:
        if re.search(pattern, norm):
            return canonical
    return raw_name


def merge_products_by_canonical(facility_id, products: List[Dict]) -> List[Dict]:
    """Fusionne les produits de meme nom canonique (quantites journalieres sommees).

    - Site sans regle -> liste renvoyee telle quelle (aucun regroupement).
    - Site avec regles -> les produits au nom canonique identique (doublons au nom
      strictement egal, ou alias comme "Auto sech...") sont fusionnes en une seule
      serie, en additionnant les quantites par date.

    `products` : liste de {"name": str, "daily_data": [{"date": str, "qty": float}]}.
    L'ordre de sortie suit la premiere apparition de chaque nom canonique.
    """
    if not site_has_overrides(facility_id):
        return products

    merged = {}   # canonical_name -> {date: qty}
    order = []
    for p in products:
        cname = canonical_product_name(facility_id, p.get("name", "PRODUITS INCONNUS"))
        if cname not in merged:
            merged[cname] = {}
            order.append(cname)
        for item in p.get("daily_data", []):
            date_str = item.get("date")
            qty = item.get("qty", 0) or 0
            if date_str is not None:
                merged[cname][date_str] = merged[cname].get(date_str, 0) + qty

    result = []
    for cname in order:
        daily = [{"date": d, "qty": q} for d, q in sorted(merged[cname].items())]
        result.append({"name": cname, "daily_data": daily})
    return result


# ---------------------------------------------------------------------------
# Liste canonique des produits pour les RAPPORTS DE GROUPE.
# Tout produit (meme mal nomme) est rapproche de cette liste et renomme en
# consequence, pour un regroupement propre dans les graphiques et tableaux.
# Chaque entree: nom affiche, references produit (prefixes), mots-cles.
# ---------------------------------------------------------------------------
GROUP_CANONICAL_PRODUCTS = [
    {
        "name": "WNC 40 NETTOYANT CARROSSERIE ULTRACONCENTRÉ 20 L – 089047020",
        "refs": ["089047020", "08904701"],
        "keywords": ["WNC40"],
    },
    {
        "name": "WNC 50 NETTOYANT CARROSSERIE 200L - 08904711",
        "refs": ["08904711"],
        "keywords": ["WNC50"],
    },
    {
        "name": "AUTO-SÉCHANT ULTRACONCENTRÉ 20L – 0893025020",
        "refs": ["0893025020", "0893025650"],
        "keywords": ["AUTOSECHANT", "AUTOSECH", "SECHANT"],
    },
    {
        "name": "NETTOYANT JANTES PURPLE 200 L - 0893477009073",
        "refs": ["0893477009"],
        "keywords": ["JANTE", "PURPLE"],
    },
    {
        "name": "EAU",
        "refs": [],
        "keywords": ["EAU"],
        "water": True,
    },
]

# Mots indiquant du MATERIEL / SERVICE (pas un produit chimique de la liste).
# Evite les faux positifs (ex: "Lance auto sechant", "Pistolet nettoyant jante").
_HARDWARE_WORDS = [
    "LANCE", "PISTOLET", "TUYAU", "POMPE", "BOITIER", "SUPPORT", "VENTURI",
    "COUPLEUR", "EMBOUT", "REDUCTEUR", "ENROULEUR", "FLOWMETER", "ROUTEUR",
    "SAV", "EXPEDITION", "INSTALLATION", "OEUVRE", "SYSTEME", "POIGNEE",
    "JUMBO", "DIVERS", "TELESCOPIC", "DECONTAMINANT",
]

_MATCH_THRESHOLD = 35.0


def match_group_canonical(raw_name: str) -> Optional[str]:
    """
    Rapproche un nom de produit de la liste canonique GROUP_CANONICAL_PRODUCTS
    (rapports de groupe uniquement).

    Algorithme de plus haute correspondance : reference produit (prefixe commun,
    poids fort) + mots-cles + similarite textuelle. Le materiel/service est exclu.

    Renvoie le nom canonique, ou None si aucune correspondance suffisante.
    """
    if not raw_name:
        return None
    norm = _normalize(raw_name)

    # Eau : regle stricte (nom normalise commencant par EAU)
    if norm.startswith("EAU"):
        return "EAU"

    # Materiel / service -> jamais un produit chimique de la liste
    if any(w in norm for w in _HARDWARE_WORDS):
        return None

    raw_refs = re.findall(r'\d{5,}', raw_name or "")
    best_name, best_score = None, 0.0

    for product in GROUP_CANONICAL_PRODUCTS:
        if product.get("water"):
            continue
        score = 0.0
        # Correspondance par reference (prefixe commun entre ref produit et nom)
        for cref in product["refs"]:
            if any(rr.startswith(cref) or cref.startswith(rr) for rr in raw_refs):
                score += 100.0
                break
        # Correspondance par mots-cles
        if any(kw in norm for kw in product["keywords"]):
            score += 40.0
        # Similarite textuelle (depart de tie-break, faible poids)
        score += SequenceMatcher(None, norm, _normalize(product["name"])).ratio() * 10.0

        if score > best_score:
            best_score, best_name = score, product["name"]

    # Exiger au moins une correspondance ref/mot-cle (la similarite seule < seuil)
    return best_name if best_score >= _MATCH_THRESHOLD else None
