"""
Service de gestion des couleurs des produits selon le cahier des charges
"""
import json
from pathlib import Path
from typing import Optional

class ProductColorService:
    """Gère les couleurs des produits pour les graphiques"""
    
    def __init__(self):
        config_path = Path(__file__).parent.parent / "config" / "product_colors.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.product_colors = self.config.get("product_colors", {})
        self.color_names = self.config.get("color_names", {})
        self.product_references = self.config.get("product_references", {})
    
    def get_color_for_product(self, product_name: str) -> Optional[str]:
        """
        Retourne la couleur HEX pour un produit donné
        
        Args:
            product_name: Nom du produit (ex: "WNC 40 20 L Zone 1" ou "WNC 40")
            
        Returns:
            Code couleur HEX (ex: "#65C482") ou None si non trouvé
        """
        # Normaliser le nom du produit (majuscules, sans espaces multiples)
        normalized_name = ' '.join(product_name.upper().split())
        
        # Essayer de matcher avec les clés de configuration
        # Ordre de priorité : match le plus spécifique d'abord
        best_match = None
        best_match_length = 0
        
        for key in self.product_colors.keys():
            key_upper = key.upper()
            # Si la clé est dans le nom du produit
            if key_upper in normalized_name:
                # Garder le match le plus long (plus spécifique)
                if len(key_upper) > best_match_length:
                    best_match = key
                    best_match_length = len(key_upper)
        
        if best_match:
            return self.product_colors[best_match]
        
        # Fallback : essayer de détecter les patterns courants
        # WNC XX (où XX est un nombre)
        import re
        wnc_match = re.search(r'WNC\s*(\d+)', normalized_name)
        if wnc_match:
            wnc_num = wnc_match.group(1)
            wnc_key = f"WNC {wnc_num}"
            if wnc_key in self.product_colors:
                return self.product_colors[wnc_key]
        
        # Auto-séchant
        if 'AUTO' in normalized_name and 'SECHANT' in normalized_name.replace('É', 'E'):
            return self.product_colors.get("Auto-séchant")
        
        # Purple
        if 'PURPLE' in normalized_name or 'JANTES' in normalized_name:
            return self.product_colors.get("Purple")
        
        # Eau
        if normalized_name == 'EAU' or normalized_name.startswith('EAU '):
            return self.product_colors.get("Eau")
        
        return None
    
    def get_color_for_reference(self, reference: str) -> Optional[str]:
        """
        Retourne la couleur HEX pour une référence produit
        
        Args:
            reference: Référence produit (ex: "089047020")
            
        Returns:
            Code couleur HEX ou None si non trouvé
        """
        product_key = self.product_references.get(reference)
        if product_key:
            return self.product_colors.get(product_key)
        return None
    
    def get_default_colors(self) -> list:
        """
        Retourne la liste des couleurs par défaut pour les graphiques
        Utilisé quand on ne peut pas identifier le produit
        """
        return [
            '#0066cc', '#ff6600', '#00cc66', '#cc00cc', 
            '#cccc00', '#00cccc', '#cc0066', '#6600cc'
        ]

# Instance singleton
_color_service = None

def get_color_service() -> ProductColorService:
    """Factory pour obtenir le service de couleurs"""
    global _color_service
    if _color_service is None:
        _color_service = ProductColorService()
    return _color_service
