"""
Service pour gérer les groupes de facilities et leurs configurations
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from collections import defaultdict
from refactored.utils.logger import get_logger
from refactored.services.excel_service import ExcelService

logger = get_logger("Group_Service")

class GroupService:
    """Service pour gérer les groupes de facilities par owner"""
    
    def __init__(self):
        self.config_file = Path("refactored/config/GroupConfigJson.json")
        self.excel_service = ExcelService()
        
        # Fallback vers l'ancien chemin si nécessaire
        old_config = Path("Config/GroupConfigJson.json")
        if old_config.exists() and not self.config_file.exists():
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(old_config, self.config_file)
            logger.info(f"Config copiée de {old_config} vers {self.config_file}")
    
    def load_group_config(self) -> List[Dict]:
        """Charge la configuration des groupes depuis GroupConfigJson.json"""
        if not self.config_file.exists():
            logger.warning("Fichier GroupConfigJson.json introuvable")
            return []
        
        try:
            with open(str(self.config_file), "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Configuration chargée: {len(config)} groupes")
            return config
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la config groupe: {e}")
            return []
    
    def save_group_config(self, config: List[Dict]) -> bool:
        """Sauvegarde la configuration des groupes"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(str(self.config_file), "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.success(f"✅ Configuration sauvegardée: {len(config)} groupes")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def update_group_config_from_devices(self, devices_list: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour GroupConfigJson.json depuis devices_list (ADD-ONLY)
        - Ajoute les nouveaux owners
        - Ne modifie pas les owners existants
        - Backfill les champs manquants
        """
        # 1) Charger l'existant
        output = self.load_group_config()
        
        # 2) Backfill des champs attendus
        def ensure_group_fields(item: dict) -> dict:
            item.setdefault("owner", "OWNER_INCONNU")
            item.setdefault("facilities", [])
            item.setdefault("cover_picture", "")
            return item
        
        output = [ensure_group_fields(dict(item)) for item in output]
        
        # 3) Owners déjà présents
        existing_owners = {(item.get("owner") or "OWNER_INCONNU") for item in output}
        
        # 4) Collecte des owners depuis devices_list
        owners_found = set()
        owner_facilities = defaultdict(list)
        
        for fac in (devices_list or {}).get("data", []) or []:
            owner = fac.get("owner") or "OWNER_INCONNU"
            owners_found.add(owner)
            owner_facilities[owner].append({
                "facilityId": fac.get("facilityId"),
                "facilityName": fac.get("facilityName")
            })
        
        # 5) Ajouter un bloc pour chaque owner absent (ADD-ONLY)
        for owner in sorted(owners_found):
            if owner not in existing_owners:
                output.append(ensure_group_fields({
                    "owner": owner,
                    "facilities": owner_facilities[owner],
                    "cover_picture": ""
                }))
                logger.info(f"Nouveau groupe ajouté: {owner}")
        
        # 6) Mettre à jour la liste des facilities pour les owners existants
        for item in output:
            owner = item.get("owner")
            if owner in owner_facilities:
                item["facilities"] = owner_facilities[owner]
        
        # 7) Sauvegarder
        self.save_group_config(output)
        
        return {"groups": output}
    
    def group_quantities_by_owner(
        self,
        total_qty_json: Dict[str, Any],
        devices_list_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agrège les quantités consommées par produit, regroupées par owner puis par facility.
        
        Structure de sortie:
        {
          "owners": [
            {
              "owner": "...",
              "totalQty": <somme>,
              "facilities": [
                {
                  "facilityId": ...,
                  "facilityName": "...",
                  "totalQty": <somme>,
                  "products": [{"productId": ..., "name": "...", "qty": ...}]
                }
              ]
            }
          ]
        }
        """
        # 1) Dictionnaire: facilityId -> (owner, facilityName, address)
        fac_to_owner: Dict[int, Dict[str, str]] = {}
        
        # Charger les données Excel pour récupérer les adresses
        excel_data = self.excel_service.load_excel_data()
        
        for fac in (devices_list_json or {}).get("data", []):
            fac_id = fac.get("facilityId")
            fac_name = fac.get("facilityName") or ""
            
            # Chercher l'adresse dans le fichier Excel
            address = ""
            if excel_data and fac_id:
                excel_info, _ = self.excel_service.match_facility_to_excel(fac_id, fac_name, excel_data)
                if excel_info:
                    address = excel_info.get("address", "") or ""
            
            fac_to_owner[fac_id] = {
                "owner": fac.get("owner") or "OWNER_INCONNU",
                "facilityName": fac_name,
                "address": address
            }
        
        # 2) Agrégation par owner -> facility -> product
        owners = defaultdict(lambda: {
            "owner": None,
            "totalQty": 0.0,
            "facilities": defaultdict(lambda: {
                "facilityId": None,
                "facilityName": "",
                "address": "",
                "totalQty": 0.0,
                "products": defaultdict(lambda: {"productId": None, "name": "", "qty": 0.0})
            })
        })
        
        results: List[Dict[str, Any]] = (total_qty_json or {}).get("data", {}).get("results", []) or []
        for row in results:
            fac_id = row.get("facilityId")
            fac_name = row.get("facilityName") or ""
            meta = fac_to_owner.get(fac_id, {"owner": "OWNER_INCONNU", "facilityName": fac_name, "address": ""})
            owner_name = meta["owner"]
            
            # Initialise structures
            owner_bucket = owners[owner_name]
            owner_bucket["owner"] = owner_name
            fac_bucket = owner_bucket["facilities"][fac_id]
            fac_bucket["facilityId"] = fac_id
            fac_bucket["facilityName"] = fac_name or meta.get("facilityName", "")
            fac_bucket["address"] = meta.get("address", "")
            
            # Produits pour cette ligne
            for p in (row.get("products") or []):
                pname_raw = (p.get("name") or "UNKNOWN PRODUCT").strip()
                pid = p.get("productId")
                
                # qty -> float robuste
                qty = p.get("qty") or 0
                try:
                    qty = float(qty)
                except Exception:
                    qty = 0.0
                
                # clé d'agrégation = productId si dispo, sinon nom
                product_key = pid if pid is not None else pname_raw
                
                # Récupère/initialise le bucket produit
                prod_bucket = fac_bucket["products"][product_key]
                if not prod_bucket["name"]:
                    prod_bucket["name"] = pname_raw
                if prod_bucket["productId"] is None and pid is not None:
                    prod_bucket["productId"] = pid
                
                prod_bucket["qty"] += qty
                fac_bucket["totalQty"] += qty
                owner_bucket["totalQty"] += qty
        
        # 3) Mise en forme finale
        owners_list = []
        for owner_name, ob in owners.items():
            facilities_list = []
            for fac_id, fb in ob["facilities"].items():
                products_list = sorted(
                    fb["products"].values(),
                    key=lambda pr: (pr["name"] or "")
                )
                facilities_list.append({
                    "facilityId": fb["facilityId"],
                    "facilityName": fb["facilityName"],
                    "address": fb.get("address", ""),
                    "totalQty": fb["totalQty"],
                    "products": products_list
                })
            facilities_list.sort(key=lambda x: (x["facilityName"] or "", x["facilityId"] or 0))
            owners_list.append({
                "owner": ob["owner"] or owner_name,
                "totalQty": ob["totalQty"],
                "facilities": facilities_list
            })
        
        owners_list.sort(key=lambda x: x["owner"] or "")
        return {"owners": owners_list}
    
    def group_stock_levels_by_owner(
        self,
        stock_levels_json: Dict[str, Any],
        devices_list_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Regroupe les données de stockLevels par owner -> facility -> products
        """
        # 1) facilityId -> owner, facilityName
        fac_to_owner: Dict[int, Dict[str, str]] = {}
        for fac in (devices_list_json or {}).get("data", []):
            fac_to_owner[fac.get("facilityId")] = {
                "owner": fac.get("owner") or "OWNER_INCONNU",
                "facilityName": fac.get("facilityName") or ""
            }
        
        # 2) Agrégation par owner -> facility
        owners = defaultdict(lambda: {
            "owner": None,
            "facilities": defaultdict(lambda: {
                "facilityId": None,
                "facilityName": "",
                "products": []
            })
        })
        
        results: List[Dict[str, Any]] = (stock_levels_json or {}).get("data", []) or []
        for row in results:
            fac_id = row.get("facilityId")
            meta = fac_to_owner.get(
                fac_id,
                {"owner": "OWNER_INCONNU", "facilityName": row.get("facilityName", "")}
            )
            owner_name = meta["owner"]
            
            owner_bucket = owners[owner_name]
            owner_bucket["owner"] = owner_name
            
            fac_bucket = owner_bucket["facilities"][fac_id]
            fac_bucket["facilityId"] = fac_id
            fac_bucket["facilityName"] = meta.get("facilityName", "")
            
            # Produits
            for p in (row.get("products") or []):
                fac_bucket["products"].append({
                    "productId": p.get("productId"),
                    "name": p.get("productName") or "",
                    "remainingQuantity": p.get("remainingQuantity") or 0,
                    "averageDailyConsumption": p.get("averageDailyConsumption") or 0,
                    "remainingDays": p.get("remainingDays") or 0
                })
        
        # 3) Mise en forme finale
        owners_list = []
        for owner_name, ob in owners.items():
            facilities_list = []
            for fac_id, fb in ob["facilities"].items():
                products_list = sorted(fb["products"], key=lambda pr: pr["name"])
                facilities_list.append({
                    "facilityId": fb["facilityId"],
                    "facilityName": fb["facilityName"],
                    "products": products_list
                })
            facilities_list.sort(key=lambda x: (x["facilityName"] or "", x["facilityId"] or 0))
            owners_list.append({
                "owner": ob["owner"] or owner_name,
                "facilities": facilities_list
            })
        
        owners_list.sort(key=lambda x: x["owner"] or "")
        
        # 4) On garde currentTime dans la structure du JSON final
        return {
            "owners": owners_list,
            "currentTime": stock_levels_json.get("currentTime")
        }
    
    def _normalize_product_name(self, name: str) -> str:
        """
        Normalise un nom de produit pour éviter les doublons
        - Supprime les espaces multiples
        - Supprime les retours à la ligne
        - Met en majuscules
        - Supprime les espaces en début/fin
        - Unifie les variantes de volume (LITRES -> L)
        """
        if not name:
            return ""
        # Remplacer les retours à la ligne par des espaces
        name = name.replace('\n', ' ').replace('\r', ' ')
        # Supprimer les espaces multiples
        import re
        name = re.sub(r'\s+', ' ', name)
        # Supprimer les espaces en début/fin et mettre en majuscules
        name = name.strip().upper()
        # Unifier les variantes de volume : "200 LITRES" -> "200 L", "1000 LITRES" -> "1000 L", etc.
        name = re.sub(r'(\d+)\s*LITRES?\b', r'\1 L', name)
        # Supprimer les espaces multiples créés par les remplacements
        name = re.sub(r'\s+', ' ', name)
        return name.strip()
    
    def group_odoo_deliveries_by_owner(
        self,
        facilities_odoo_data: Dict[int, Dict[str, Any]],
        devices_list_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Regroupe les données Odoo (produits livrés) par owner
        
        Args:
            facilities_odoo_data: {facility_id: odoo_data}
            devices_list_json: Données des devices pour le mapping facility -> owner
            
        Returns:
            {
              "owners": [
                {
                  "owner": "...",
                  "products_by_month": {product_name: {month: qty}},
                  "facilities": [
                    {
                      "facilityId": ...,
                      "facilityName": "...",
                      "products_by_month": {product_name: {month: qty}}
                    }
                  ]
                }
              ]
            }
        """
        # 1) facilityId -> owner, facilityName
        fac_to_owner: Dict[int, Dict[str, str]] = {}
        for fac in (devices_list_json or {}).get("data", []):
            fac_to_owner[fac.get("facilityId")] = {
                "owner": fac.get("owner") or "OWNER_INCONNU",
                "facilityName": fac.get("facilityName") or ""
            }
        
        # 2) Agrégation par owner
        owners = defaultdict(lambda: {
            "owner": None,
            "products_by_month": defaultdict(lambda: defaultdict(float)),
            "facilities": defaultdict(lambda: {
                "facilityId": None,
                "facilityName": "",
                "products_by_month": {}
            })
        })
        
        # 3) Parcourir les données Odoo de chaque facility
        for facility_id, odoo_data in facilities_odoo_data.items():
            if not odoo_data or not odoo_data.get("products_by_month"):
                continue
            
            meta = fac_to_owner.get(
                facility_id,
                {"owner": "OWNER_INCONNU", "facilityName": ""}
            )
            owner_name = meta["owner"]
            
            owner_bucket = owners[owner_name]
            owner_bucket["owner"] = owner_name
            
            fac_bucket = owner_bucket["facilities"][facility_id]
            fac_bucket["facilityId"] = facility_id
            fac_bucket["facilityName"] = meta.get("facilityName", "")
            fac_bucket["products_by_month"] = odoo_data.get("products_by_month", {})
            
            # Agréger au niveau owner - regrouper par nom de produit NORMALISÉ
            # Si plusieurs facilities commandent le même produit, les quantités sont sommées
            for product_name, months_data in odoo_data.get("products_by_month", {}).items():
                # Normaliser le nom du produit pour éviter les doublons
                normalized_name = self._normalize_product_name(product_name)
                if not normalized_name:
                    continue
                for month_key, qty in months_data.items():
                    # Les produits avec le même nom normalisé sont regroupés
                    owner_bucket["products_by_month"][normalized_name][month_key] += qty
        
        # 4) Mise en forme finale
        owners_list = []
        for owner_name, ob in owners.items():
            # Convertir defaultdict en dict normal
            products_by_month_dict = {}
            for product_name, months_data in ob["products_by_month"].items():
                products_by_month_dict[product_name] = dict(months_data)
            
            facilities_list = []
            for fac_id, fb in ob["facilities"].items():
                facilities_list.append({
                    "facilityId": fb["facilityId"],
                    "facilityName": fb["facilityName"],
                    "products_by_month": fb.get("products_by_month", {})
                })
            
            facilities_list.sort(key=lambda x: (x["facilityName"] or "", x["facilityId"] or 0))
            owners_list.append({
                "owner": ob["owner"] or owner_name,
                "products_by_month": products_by_month_dict,
                "facilities": facilities_list
            })
        
        owners_list.sort(key=lambda x: x["owner"] or "")
        return {"owners": owners_list}
