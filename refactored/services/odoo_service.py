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
        # Format Odoo: liste de tuples (field, operator, value)
        # Filtrer uniquement les devis de la société "TMH Corporation SA"
        domain = [
            ('partner_shipping_id.x_studio_code_client', '=', client_code),
            ('company_id.name', '=', 'TMH Corporation SA')
        ]
        
        # Filtrer par date si fourni (pour limiter aux commandes de l'année en cours)
        if from_date:
            domain.append(('date_order', '>=', f"{from_date} 00:00:00"))
        if to_date:
            domain.append(('date_order', '<=', f"{to_date} 23:59:59"))
        
        logger.info(f"   Domaine de recherche: {domain}")
        
        # Utiliser search puis read au lieu de search_read pour s'assurer que le filtre fonctionne
        order_ids = self._call(
            'sale.order',
            'search',
            [domain],
            {'order': 'date_order desc'}
        )
        
        if not order_ids:
            logger.info(f"   Aucun devis trouvé pour {client_code}")
            return []
        
        logger.info(f"   {len(order_ids)} IDs de devis trouvés: {order_ids}")
        
        # Récupérer les détails des commandes
        orders = self._call(
            'sale.order',
            'read',
            [order_ids],
            {
                'fields': [
                    'id',
                    'name',
                    'date_order',
                    'partner_id',
                    'partner_shipping_id',
                    'state',
                    'amount_total',
                    'order_line'
                ]
            }
        )
        
        if not orders:
            logger.info(f"   Aucun devis trouvé pour {client_code}")
            return []
        
        logger.info(f"   {len(orders)} devis récupérés:")
        for order in orders:
            partner_shipping = order.get('partner_shipping_id', [])
            partner_name = partner_shipping[1] if isinstance(partner_shipping, list) and len(partner_shipping) > 1 else str(partner_shipping)
            logger.info(f"      - {order.get('name')} (ID:{order.get('id')}): {order.get('date_order')} - Partner: {partner_name}")
        
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
        Récupère les produits livrés pour une facility donnée
        
        Args:
            facility_name: Nom de la facility (ex: "1070280831 GARAGE PARIS BREST PROCUREUR")
            from_date: Date de début (format YYYY-MM-DD) - utilisé pour déterminer l'année
            to_date: Date de fin (format YYYY-MM-DD) - utilisé pour déterminer l'année
            
        Returns:
            Dictionnaire avec les devis et produits agrégés
        """
        # Extraire le code client du nom de la facility
        client_code = self.extract_client_code(facility_name)
        
        if not client_code:
            logger.warning(f"⚠️ Impossible d'extraire le code client de '{facility_name}'")
            return {
                "facility_name": facility_name,
                "client_code": None,
                "from_date": from_date,
                "to_date": to_date,
                "orders_count": 0,
                "orders": [],
                "products_summary": {}
            }
        
        # Calculer les dates de début et fin de l'année en cours
        # On utilise to_date pour déterminer l'année
        if to_date:
            try:
                end_date = datetime.strptime(to_date, "%Y-%m-%d")
                current_year = end_date.year
            except:
                current_year = datetime.now().year
        else:
            current_year = datetime.now().year
        
        # Récupérer toutes les commandes de l'année en cours (janvier à décembre)
        year_start = f"{current_year}-01-01"
        year_end = f"{current_year}-12-31"
        
        logger.info(f"   Récupération des commandes pour l'année {current_year} ({year_start} à {year_end})")
        
        # Récupérer les devis
        orders = self.get_sales_orders_by_client_code(client_code, year_start, year_end)
        
        # Structurer les commandes de manière claire
        # Chaque commande contient ses articles avec leurs quantités
        orders_structured = []
        products_by_month = {}  # Pour l'agrégation par mois
        
        for order in orders:
            order_name = order.get('name', '')
            order_date = order.get('date_order', '')
            
            # Extraire le mois
            month_key = "unknown"
            if order_date:
                try:
                    dt = datetime.strptime(order_date[:10], "%Y-%m-%d")
                    month_key = dt.strftime("%Y-%m")
                except:
                    pass
            
            # Structurer les articles de cette commande
            articles = []
            for line in order.get('order_lines_details', []):
                product_name = line.get('name', 'Produit inconnu')
                qty = line.get('product_uom_qty', 0)
                
                # Ignorer les lignes sans produit (qty = 0 et pas de product_id)
                if qty == 0 and not line.get('product_id'):
                    continue
                
                articles.append({
                    "product_name": product_name,
                    "quantity": qty
                })
                
                # Agrégation par mois
                if product_name not in products_by_month:
                    products_by_month[product_name] = {}
                if month_key not in products_by_month[product_name]:
                    products_by_month[product_name][month_key] = 0
                products_by_month[product_name][month_key] += qty
            
            # Ajouter la commande structurée
            if articles:  # Seulement si la commande a des articles
                orders_structured.append({
                    "order_ref": order_name,
                    "date": order_date[:10] if order_date else "",
                    "month": month_key,
                    "articles": articles
                })
        
        # Log des commandes pour debug
        logger.info(f"   Commandes structurées:")
        for o in orders_structured:
            logger.info(f"      {o['order_ref']} ({o['date']}): {len(o['articles'])} articles")
            for a in o['articles']:
                logger.info(f"         - {a['product_name']}: {a['quantity']}")
        
        result = {
            "facility_name": facility_name,
            "client_code": client_code,
            "year": current_year,
            "orders_count": len(orders_structured),
            "orders": orders_structured,
            "products_by_month": products_by_month
        }
        
        logger.success(f"✅ {len(orders_structured)} commandes, {len(products_by_month)} produits uniques")
        
        return result
