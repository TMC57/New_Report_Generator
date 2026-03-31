"""
Service pour récupérer les données depuis Odoo via JSON-RPC
Utilisé pour récupérer les devis (sale.order) pour le tableau Produits Livrés
"""
import requests
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from refactored.utils.logger import get_logger

logger = get_logger("Odoo_Service")

# Configuration Odoo
ODOO_URL = "https://tmh-corporation-odoo.odoo.com"
ODOO_DB = "tmh-corporation-odoo-main-22400696"
ODOO_USERNAME = "communication@tmh-corporation.com"
ODOO_PASSWORD = "Fr23021998"


class OdooService:
    """Service pour interagir avec l'API Odoo"""
    
    def __init__(self):
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.password = ODOO_PASSWORD
        self.uid = None
    
    def authenticate(self) -> Optional[int]:
        """
        Authentifie avec Odoo et retourne l'UID
        """
        if self.uid:
            return self.uid
            
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [self.db, self.username, self.password, {}]
                },
                "id": 1
            }
            response = requests.post(
                f"{self.url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            result = response.json()
            self.uid = result.get("result")
            
            if self.uid:
                logger.success(f"✅ Authentification Odoo réussie (uid={self.uid})")
            else:
                logger.error("❌ Échec authentification Odoo")
                
            return self.uid
            
        except Exception as e:
            logger.error(f"❌ Erreur authentification Odoo: {e}")
            return None
    
    def _call(self, model: str, method: str, args: List, kwargs: Dict = None) -> Any:
        """
        Effectue un appel RPC vers Odoo
        """
        if not self.uid:
            self.authenticate()
            
        if not self.uid:
            logger.error("❌ Impossible d'appeler Odoo sans authentification")
            return None
            
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [self.db, self.uid, self.password, model, method, args, kwargs or {}]
                },
                "id": 2
            }
            response = requests.post(
                f"{self.url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            result = response.json()
            
            if "error" in result:
                logger.error(f"❌ Erreur Odoo: {result['error']}")
                return None
                
            return result.get("result")
            
        except Exception as e:
            logger.error(f"❌ Erreur appel Odoo ({model}.{method}): {e}")
            return None
    
    def extract_client_code(self, facility_name: str) -> Optional[str]:
        """
        Extrait le code client du nom de la facility
        Ex: "1070280831 GARAGE PARIS BREST PROCUREUR" -> "1070280831"
        """
        if not facility_name:
            return None
            
        # Chercher un code numérique au début du nom (10 chiffres commençant par 107)
        match = re.match(r'^(\d{10})', facility_name.strip())
        if match:
            return match.group(1)
        
        # Sinon chercher n'importe quel code numérique de 10 chiffres
        match = re.search(r'(107\d{7})', facility_name)
        if match:
            return match.group(1)
            
        return None
    
    def get_sales_orders_by_client_code(
        self,
        client_code: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère les devis (sale.order) pour un code client donné
        
        Args:
            client_code: Code client (ex: "1070280831")
            from_date: Date de début (format YYYY-MM-DD)
            to_date: Date de fin (format YYYY-MM-DD)
            
        Returns:
            Liste des devis avec leurs lignes de produits
        """
        logger.info(f"🔍 Recherche des devis pour code client: {client_code}")
        
        # Construire le domaine de recherche directement sur sale.order
        # Le champ correct est partner_shipping_id.x_studio_code_client (champ Studio personnalisé)
        domain = [
            ['partner_shipping_id.x_studio_code_client', '=', client_code]
        ]
        
        # NOTE: On ne filtre PAS par date pour l'instant - on récupère tous les devis
        # et on filtrera par année dans le tableau des produits livrés
        
        # Récupérer les devis
        orders = self._call(
            'sale.order',
            'search_read',
            [domain],
            {
                'fields': [
                    'id',
                    'name',  # Référence du devis (ex: S00123)
                    'date_order',
                    'partner_id',
                    'partner_shipping_id',
                    'state',
                    'amount_total',
                    'order_line'
                ],
                'order': 'date_order desc'
            }
        )
        
        if not orders:
            logger.info(f"   Aucun devis trouvé pour {client_code}")
            return []
        
        logger.info(f"   {len(orders)} devis trouvés")
        
        # Récupérer les détails des lignes de commande
        for order in orders:
            line_ids = order.get('order_line', [])
            if line_ids:
                lines = self._call(
                    'sale.order.line',
                    'read',
                    [line_ids],
                    {
                        'fields': [
                            'id',
                            'product_id',
                            'name',  # Description du produit
                            'product_uom_qty',  # Quantité
                            'price_unit',
                            'price_subtotal'
                        ]
                    }
                )
                order['order_lines_details'] = lines or []
            else:
                order['order_lines_details'] = []
        
        return orders
    
    def get_delivered_products_for_facility(
        self,
        facility_name: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère les produits livrés pour une facility
        
        Args:
            facility_name: Nom de la facility (contient le code client)
            from_date: Date de début (format YYYY-MM-DD)
            to_date: Date de fin (format YYYY-MM-DD)
            
        Returns:
            Dictionnaire avec les devis et produits livrés
        """
        # Extraire le code client du nom de la facility
        client_code = self.extract_client_code(facility_name)
        
        if not client_code:
            logger.warning(f"⚠️ Impossible d'extraire le code client de: {facility_name}")
            return {
                "facility_name": facility_name,
                "client_code": None,
                "orders": [],
                "products_summary": {}
            }
        
        logger.info(f"📦 Récupération des produits livrés pour {facility_name}")
        logger.info(f"   Code client extrait: {client_code}")
        
        # Récupérer les devis
        orders = self.get_sales_orders_by_client_code(client_code, from_date, to_date)
        
        # Agréger les produits par nom
        products_summary = {}
        for order in orders:
            order_date = order.get('date_order', '')
            if order_date:
                # Extraire le mois de la commande
                try:
                    dt = datetime.strptime(order_date[:10], "%Y-%m-%d")
                    month_key = dt.strftime("%Y-%m")
                except:
                    month_key = "unknown"
            else:
                month_key = "unknown"
            
            for line in order.get('order_lines_details', []):
                product_name = line.get('name', 'Produit inconnu')
                qty = line.get('product_uom_qty', 0)
                
                if product_name not in products_summary:
                    products_summary[product_name] = {
                        "total_qty": 0,
                        "by_month": {}
                    }
                
                products_summary[product_name]["total_qty"] += qty
                
                if month_key not in products_summary[product_name]["by_month"]:
                    products_summary[product_name]["by_month"][month_key] = 0
                products_summary[product_name]["by_month"][month_key] += qty
        
        result = {
            "facility_name": facility_name,
            "client_code": client_code,
            "from_date": from_date,
            "to_date": to_date,
            "orders_count": len(orders),
            "orders": orders,
            "products_summary": products_summary
        }
        
        logger.success(f"✅ {len(orders)} devis, {len(products_summary)} produits uniques")
        
        return result
