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
from typing import List, Dict

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
