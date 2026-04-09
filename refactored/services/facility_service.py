from typing import List, Optional, Dict
from refactored.models.facility import FacilityData
from refactored.models.device import Device
from refactored.models.product import Product, ProductConsumption
from refactored.services.cm2w_service import CM2WService
from refactored.services.excel_service import ExcelService
from refactored.services.config_service import ConfigService
from refactored.services.flowrate_service import FlowrateService
from refactored.services.odoo_service import OdooService
from refactored.utils.logger import get_logger

logger = get_logger("Facility_Service")

class FacilityService:
    """Service principal pour consolider toutes les données d'une facility"""
    
    def __init__(self):
        self.cm2w = CM2WService()
        self.excel = ExcelService()
        self.config = ConfigService()
        self.flowrate = FlowrateService()
        self.odoo = OdooService()
    
    def get_complete_facility_data(
        self,
        facility_id: int,
        from_date: str,
        to_date: str
    ) -> Optional[FacilityData]:
        """
        Récupère et consolide toutes les données pour une facility
        
        Étapes:
        1. Récupérer données CM2W (devices, quantités, stocks)
        2. Enrichir avec données Excel (client_number, address, group)
        3. Enrichir avec config locale (photos, contacts)
        4. Calculer zones et produits
        5. Valider que toutes les données nécessaires sont présentes
        """
        logger.info(f"🔄 Récupération complète des données pour facility {facility_id}")
        
        devices_response = self.cm2w.get_devices_list(facility_id)
        if not devices_response or not devices_response.get("data"):
            logger.warning(f"⚠️ Aucun device trouvé pour facility {facility_id}, création d'une facility vide")
            facility = FacilityData(
                facility_id=facility_id,
                facility_name=f"Facility {facility_id}",
                owner="Unknown"
            )
            facility_info = None
        else:
            facility_info = None
            for facility_data in devices_response["data"]:
                if facility_data.get("facilityId") == facility_id:
                    facility_info = facility_data
                    break
            
            if not facility_info:
                logger.warning(f"⚠️ Facility {facility_id} introuvable dans la réponse devices, création d'une facility vide")
                facility = FacilityData(
                    facility_id=facility_id,
                    facility_name=f"Facility {facility_id}",
                    owner="Unknown"
                )
            else:
                facility = FacilityData(
                    facility_id=facility_id,
                    facility_name=facility_info.get("facilityName", ""),
                    owner=facility_info.get("owner", "")
                )
        
        logger.debug(f"Facility de base créée: {facility.facility_name}", facility_id)
        
        if facility_info:
            devices = [Device.from_cm2w_data(d) for d in facility_info.get("devices", [])]
            facility.devices = devices
            logger.debug(f"  → {len(devices)} devices trouvés", facility_id)
        else:
            facility.devices = []
            logger.debug(f"  → 0 devices (facility sans devices)", facility_id)
        
        excel_data = self.excel.load_excel_data()
        if excel_data:
            excel_info, match_method = self.excel.match_facility_to_excel(
                facility_id,
                facility.facility_name,
                excel_data
            )
            
            if excel_info:
                facility.excel_matched = True
                facility.excel_match_method = match_method
                facility.client_number = int(list(excel_data.keys())[list(excel_data.values()).index(excel_info)])
                facility.client_name = excel_info.get("client_name")
                facility.address = excel_info.get("address")
                facility.group = excel_info.get("group")
                
                # Informations générales
                facility.installation_date = excel_info.get("installation_date")
                facility.zone_number = excel_info.get("zone_number")
                facility.router_number = excel_info.get("router_number")
                facility.last_intervention = excel_info.get("last_intervention")
                
                # Zone 1 (principale)
                facility.produit_lavant = excel_info.get("produit_lavant")
                facility.dilution_lavant = excel_info.get("dilution_lavant")
                facility.couleur_buse_lavant = excel_info.get("couleur_buse_lavant")
                facility.produit_sechant = excel_info.get("produit_sechant")
                facility.dilution_sechant = excel_info.get("dilution_sechant")
                facility.couleur_buse_sechant = excel_info.get("couleur_buse_sechant")
                facility.autre_produit_lavant = excel_info.get("autre_produit_lavant")
                facility.autre_dilution_lavant = excel_info.get("autre_dilution_lavant")
                facility.autre_couleur_buse_lavant = excel_info.get("autre_couleur_buse_lavant")
                facility.produit_jantes = excel_info.get("produit_jantes")
                facility.dilution_jantes = excel_info.get("dilution_jantes")
                
                # Zone 2
                facility.produit_lavant_zone2 = excel_info.get("produit_lavant_zone2")
                facility.dilution_lavant_zone2 = excel_info.get("dilution_lavant_zone2")
                facility.couleur_buse_lavant_zone2 = excel_info.get("couleur_buse_lavant_zone2")
                facility.produit_sechant_zone2 = excel_info.get("produit_sechant_zone2")
                facility.dilution_sechant_zone2 = excel_info.get("dilution_sechant_zone2")
                facility.couleur_buse_sechant_zone2 = excel_info.get("couleur_buse_sechant_zone2")
                facility.autre_produit_lavant_zone2 = excel_info.get("autre_produit_lavant_zone2")
                facility.autre_dilution_lavant_zone2 = excel_info.get("autre_dilution_lavant_zone2")
                facility.autre_couleur_buse_lavant_zone2 = excel_info.get("autre_couleur_buse_lavant_zone2")
                
                # Zone 3
                facility.produit_lavant_zone3 = excel_info.get("produit_lavant_zone3")
                facility.dilution_lavant_zone3 = excel_info.get("dilution_lavant_zone3")
                facility.couleur_buse_lavant_zone3 = excel_info.get("couleur_buse_lavant_zone3")
                facility.produit_sechant_zone3 = excel_info.get("produit_sechant_zone3")
                facility.dilution_sechant_zone3 = excel_info.get("dilution_sechant_zone3")
                facility.couleur_buse_sechant_zone3 = excel_info.get("couleur_buse_sechant_zone3")
                
                # Zone 4
                facility.produit_lavant_zone4 = excel_info.get("produit_lavant_zone4")
                facility.dilution_lavant_zone4 = excel_info.get("dilution_lavant_zone4")
                facility.couleur_buse_lavant_zone4 = excel_info.get("couleur_buse_lavant_zone4")
                facility.produit_sechant_zone4 = excel_info.get("produit_sechant_zone4")
                facility.dilution_sechant_zone4 = excel_info.get("dilution_sechant_zone4")
                facility.couleur_buse_sechant_zone4 = excel_info.get("couleur_buse_sechant_zone4")
                
                # Zone 5
                facility.produit_lavant_zone5 = excel_info.get("produit_lavant_zone5")
                facility.dilution_lavant_zone5 = excel_info.get("dilution_lavant_zone5")
                facility.couleur_buse_lavant_zone5 = excel_info.get("couleur_buse_lavant_zone5")
                facility.produit_sechant_zone5 = excel_info.get("produit_sechant_zone5")
                facility.dilution_sechant_zone5 = excel_info.get("dilution_sechant_zone5")
                facility.couleur_buse_sechant_zone5 = excel_info.get("couleur_buse_sechant_zone5")
                
                logger.success(f"✅ Excel matched via {match_method}", facility_id)
                logger.info(f"  → Client: {facility.client_name}", facility_id)
                logger.info(f"  → N°: {facility.client_number}", facility_id)
                logger.info(f"  → Adresse: {facility.address}", facility_id)
                logger.info(f"  → Date installation: {facility.installation_date}", facility_id)
                logger.info(f"  → Produit lavant: {facility.produit_lavant}", facility_id)
                logger.info(f"  → Dilution lavant: {facility.dilution_lavant}", facility_id)
            else:
                logger.warning(f"⚠️ Aucune donnée Excel trouvée", facility_id)
        
        config = self.config.get_config(facility_id)
        if config:
            facility.local_config = config
            facility.cover_picture_path = config.cover_picture or ""
            # Les champs suivants ne sont plus dans FacilityConfig simplifié
            facility.material_picture_path = ""
            facility.last_intervention_date = ""
            facility.buses_info = ""
            logger.debug(f"  → Config locale chargée", facility_id)
        
        stock_response = self.cm2w.get_stock_levels(facility_id)
        if stock_response and stock_response.get("data"):
            for stock_item in stock_response["data"]:
                if stock_item.get("facilityId") == facility_id:
                    for product_data in stock_item.get("products", []):
                        product = Product.from_stock_data(product_data)
                        facility.stock_products.append(product)
            logger.debug(f"  → {len(facility.stock_products)} produits en stock", facility_id)
        
        qty_response = self.cm2w.get_total_qty_report(from_date, to_date, facility_id)
        if qty_response and qty_response.get("data", {}).get("results"):
            for result in qty_response["data"]["results"]:
                if result.get("facilityId") == facility_id:
                    for product_data in result.get("products", []):
                        product_id = product_data.get("_id")
                        product_name = product_data.get("name", "")
                        qty = float(product_data.get("qty", 0))
                        
                        logger.info(f"  🆕 Création produit: {product_name} | _id={product_id} | qty={qty}", facility_id)
                        
                        consumption = ProductConsumption(
                            product_id=product_id,
                            name=product_name,
                            total_qty=qty
                        )
                        facility.products.append(consumption)
            logger.debug(f"  → {len(facility.products)} produits consommés", facility_id)
        
        logger.info(f"Récupération des données quotidiennes...", facility_id)
        daily_data = self.cm2w.get_daily_quantities(from_date, to_date, facility_id)
        for day_entry in daily_data:
            date_str = day_entry["date"]
            logger.debug(f"📅 Date: {date_str}", facility_id)
            for facility_data in day_entry["data"]:
                if facility_data.get("facilityId") == facility_id:
                    logger.debug(f"  Facility {facility_id} - {len(facility_data.get('products', []))} produits", facility_id)
                    for product_data in facility_data.get("products", []):
                        product_id = product_data.get("_id")
                        product_name = product_data.get("name", "Unknown")
                        qty = float(product_data.get("qty", 0))
                        
                        logger.info(f"    📦 Produit: {product_name} | _id={product_id} | qty={qty}", facility_id)
                        
                        product = next((p for p in facility.products if p.product_id == product_id), None)
                        if product:
                            product.daily_quantities.append({
                                "date": date_str,
                                "qty": qty
                            })
                            logger.info(f"      ✅ Ajouté à {product.name}", facility_id)
                        else:
                            logger.info(f"      ❌ Produit non trouvé dans la liste initiale", facility_id)
        
        logger.info(f"Récupération des données mensuelles...", facility_id)
        monthly_data = self.cm2w.get_monthly_quantities(to_date, facility_id, months_count=12)
        for month_entry in monthly_data:
            year = month_entry["year"]
            month = month_entry["month"]
            for facility_data in month_entry["data"]:
                if facility_data.get("facilityId") == facility_id:
                    for product_data in facility_data.get("products", []):
                        product_id = product_data.get("_id")
                        qty = float(product_data.get("qty", 0))
                        
                        product = next((p for p in facility.products if p.product_id == product_id), None)
                        if product:
                            product.monthly_quantities.append({
                                "year": year,
                                "month": month,
                                "qty": qty
                            })
        
        logger.debug(f"  → Données quotidiennes et mensuelles ajoutées", facility_id)
        
        # Récupération des données de débit (flowrate)
        logger.info(f"Récupération des données de débit (flowrate)...", facility_id)
        device_ids = [device.device_id for device in facility.devices if device.device_id]
        
        if device_ids:
            # Authentification pour flowrate
            if self.flowrate.login():
                flowrate_results = self.flowrate.get_flowrate_for_facility(
                    device_ids, 
                    from_date, 
                    to_date
                )
                facility.flowrate_data = flowrate_results
                logger.success(f"✅ Données flowrate récupérées pour {len(flowrate_results)} devices", facility_id)
            else:
                logger.warning(f"⚠️ Impossible de récupérer les données flowrate (échec authentification)", facility_id)
        else:
            logger.warning(f"⚠️ Aucun device ID trouvé, pas de données flowrate", facility_id)
        
        # Récupération des données Odoo (devis/produits livrés)
        logger.info(f"📦 Récupération des données Odoo (produits livrés)...", facility_id)
        try:
            odoo_data = self.odoo.get_delivered_products_for_facility(
                facility.facility_name,
                from_date,
                to_date
            )
            facility.odoo_delivered_products = odoo_data
            if odoo_data.get("orders_count", 0) > 0:
                logger.success(f"✅ Données Odoo récupérées: {odoo_data.get('orders_count', 0)} devis, {len(odoo_data.get('products_summary', {}))} produits", facility_id)
            else:
                logger.info(f"   Aucun devis Odoo trouvé pour cette facility", facility_id)
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération données Odoo: {e}", facility_id)
            facility.odoo_delivered_products = {}
        
        zones = set()
        for device in facility.devices:
            if device.zone:
                zones.add(device.zone)
        
        import re
        for product in facility.products:
            zone_match = re.search(r'Zone\s+(\d+)', product.name, re.IGNORECASE)
            if zone_match:
                zone_num = zone_match.group(1)
                zones.add(f"ZONE {zone_num}")
                product.zone = f"ZONE {zone_num}"
        
        for product in facility.stock_products:
            zone_match = re.search(r'Zone\s+(\d+)', product.name, re.IGNORECASE)
            if zone_match:
                zone_num = zone_match.group(1)
                zones.add(f"ZONE {zone_num}")
                product.zone = f"ZONE {zone_num}"
        
        if not zones:
            zones.add("GLOBAL")
        
        facility.zones = sorted(list(zones))
        logger.debug(f"  → Zones détectées: {facility.zones}", facility_id)
        
        # Mapper les noms de produits API vers les noms Excel (après récupération de toutes les données)
        self._map_product_names_to_excel(facility)
        
        if facility.has_all_required_data():
            logger.success(f"✅ Données complètes pour facility {facility_id}", facility_id)
        else:
            missing = facility.get_missing_data()
            logger.warning(f"⚠️ Données manquantes: {', '.join(missing)}", facility_id)
        
        return facility
    
    def get_all_facilities_data(
        self,
        from_date: str,
        to_date: str,
        facility_id: Optional[int] = None
    ) -> List[FacilityData]:
        """
        Récupère les données complètes pour toutes les facilities (ou une seule si facility_id fourni)
        """
        logger.info("🔄 Récupération de toutes les facilities")
        
        devices_response = self.cm2w.get_devices_list(facility_id)
        if not devices_response or not devices_response.get("data"):
            logger.error("Impossible de récupérer la liste des devices")
            return []
        
        facility_ids = set()
        for device_data in devices_response["data"]:
            fid = device_data.get("facilityId")
            if fid:
                facility_ids.add(fid)
        
        logger.info(f"📋 {len(facility_ids)} facilities à traiter")
        
        facilities = []
        for fid in sorted(facility_ids):
            facility_data = self.get_complete_facility_data(fid, from_date, to_date)
            if facility_data:
                facilities.append(facility_data)
        
        logger.success(f"✅ {len(facilities)} facilities complètes récupérées")
        return facilities
    
    def save_facility_data_to_json(self, facility: FacilityData, output_path: str):
        """Sauvegarde les données d'une facility dans un JSON pour inspection"""
        import json
        from pathlib import Path
        
        logger.info(f"💾 Sauvegarde JSON pour facility {facility.facility_id} vers {output_path}")
        
        # Créer le dossier si nécessaire
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Utiliser to_dict() au lieu de asdict() pour éviter les problèmes de sérialisation
        data = facility.to_dict()
        
        # Ajouter les données supplémentaires
        data["local_config"] = facility.local_config
        data["excel_matched"] = facility.excel_matched
        data["excel_match_method"] = facility.excel_match_method
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.success(f"✅ JSON sauvegardé: {output_path}")
    
    def _map_product_names_to_excel(self, facility: FacilityData):
        """
        Mappe les noms de produits API vers les noms Excel correspondants.
        Cela permet d'avoir des noms cohérents dans les graphiques et d'éviter
        les doublons avec des noms légèrement différents.
        
        Si un produit API ne trouve pas de match, on lui attribue un nom Excel
        non utilisé (fallback).
        """
        import re
        import unicodedata
        
        def normalize_name(name: str) -> str:
            """Normalise un nom pour le matching"""
            if not name:
                return ""
            # Retirer les accents
            name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
            # Majuscules, retirer espaces et tirets
            name = name.upper().replace(" ", "").replace("-", "")
            return name
        
        def find_match(api_name: str, excel_products: list, re_module) -> tuple:
            """Trouve le meilleur match Excel pour un nom API. Retourne (match_name, excel_prod_index) ou (None, None)"""
            normalized_api = normalize_name(api_name)
            
            # Ignorer les produits qui sont clairement de l'eau (pas un produit chimique)
            if normalized_api.startswith("EAU") or normalized_api == "EAU":
                return "SKIP", -1  # Marqueur spécial pour ignorer ce produit
            
            for idx, excel_prod in enumerate(excel_products):
                excel_normalized = excel_prod["normalized"]
                
                # Match direct (le nom API est contenu dans le nom Excel ou vice versa)
                if normalized_api in excel_normalized or excel_normalized in normalized_api:
                    return excel_prod["name"], idx
                
                # Match par type de produit (autoséchant)
                if excel_prod["type"] == "sechant":
                    if "AUTOSECHANT" in normalized_api or "SECHANT" in normalized_api:
                        return excel_prod["name"], idx
                
                # Match SHAMP/SHAMPO/SHAMPOING vers produit lavant
                if excel_prod["type"] == "lavant":
                    if "SHAMP" in normalized_api or "SHAMPO" in normalized_api or "SHAMPOING" in normalized_api:
                        return excel_prod["name"], idx
                
                # Match spécial pour jantes (ex: "Nettoyant jante bmw P" -> "Nettoyant jantes purple")
                if excel_prod["type"] == "jantes":
                    if "JANTE" in normalized_api or "JANTES" in normalized_api:
                        # Vérifier si les mots clés correspondent
                        api_words = set(normalized_api.split())
                        excel_words = set(excel_prod["normalized"].split())
                        
                        # Si "PURPLE" ou "P" dans API et "PURPLE" dans Excel
                        if ("PURPLE" in api_words or "P" in api_words) and "PURPLE" in excel_prod["normalized"]:
                            return excel_prod["name"], idx
                        # Si "BMW" dans les deux
                        if "BMW" in api_words and "BMW" in excel_words:
                            return excel_prod["name"], idx
                        # Match générique pour jantes si pas d'autres spécificités
                        if "NETTOYANT" in normalized_api and "NETTOYANT" in excel_prod["normalized"]:
                            return excel_prod["name"], idx
                
                # Match par numéro WNC
                api_wnc_match = re_module.search(r'WNC\s*(\d+)', normalized_api, re_module.IGNORECASE)
                excel_wnc_match = re_module.search(r'WNC\s*(\d+)', excel_normalized, re_module.IGNORECASE)
                if api_wnc_match and excel_wnc_match:
                    api_wnc_num = api_wnc_match.group(1)
                    excel_wnc_num = excel_wnc_match.group(1)
                    if api_wnc_num == excel_wnc_num:
                        # Vérifier aussi UC/ULTRACONCENTRÉ
                        if "UC" in normalized_api and "ULTRACONCENTRE" in excel_normalized:
                            return excel_prod["name"], idx
                        if "UC" not in normalized_api and "ULTRACONCENTRE" not in excel_normalized:
                            return excel_prod["name"], idx
            
            return None, None
        
        # Collecter tous les produits Excel de la facility
        excel_products = []
        
        # Produits par zone (zone 1 = sans suffixe, zones 2-5 avec suffixe)
        for zone_num in range(1, 6):
            zone_suffix = "" if zone_num == 1 else f"_zone{zone_num}"
            
            for prod_type in ["lavant", "sechant", "jantes"]:
                key = f"produit_{prod_type}{zone_suffix}"
                excel_name = getattr(facility, key, None)
                if excel_name:
                    excel_products.append({
                        "type": prod_type,
                        "zone": zone_num,
                        "name": excel_name,
                        "normalized": normalize_name(excel_name),
                        "used": False
                    })
            
            # Autre produit lavant
            autre_key = f"autre_produit_lavant{zone_suffix}"
            autre_name = getattr(facility, autre_key, None)
            if autre_name:
                excel_products.append({
                    "type": "autre_lavant",
                    "zone": zone_num,
                    "name": autre_name,
                    "normalized": normalize_name(autre_name),
                    "used": False
                })
        
        if not excel_products:
            logger.debug(f"  → Aucun produit Excel trouvé, pas de mapping", facility.facility_id)
            return
        
        logger.info(f"  📝 Mapping des noms de produits vers Excel ({len(excel_products)} produits Excel)", facility.facility_id)
        
        # Liste des produits sans match (pour le fallback)
        unmatched_products = []
        
        # Premier passage : mapper les produits avec les règles de matching
        for product in facility.products:
            api_name = product.name
            match_name, match_idx = find_match(api_name, excel_products, re)
            
            if match_name == "SKIP":
                # Produit à ignorer (ex: EAU) - on garde le nom original
                logger.debug(f"    ⏭️ Ignoré (eau/autre): '{api_name}'", facility.facility_id)
                continue
            elif match_name and match_name != api_name:
                logger.debug(f"    🔄 '{api_name}' → '{match_name}'", facility.facility_id)
                product.name = match_name
                excel_products[match_idx]["used"] = True
            elif not match_name:
                # Pas de match trouvé, on garde pour le fallback
                unmatched_products.append(product)
        
        # Deuxième passage : attribuer les noms Excel non utilisés aux produits sans match
        unused_excel = [ep for ep in excel_products if not ep["used"]]
        for product in unmatched_products:
            if unused_excel:
                # Attribuer le premier nom Excel non utilisé
                fallback = unused_excel.pop(0)
                logger.info(f"    🔄 Fallback: '{product.name}' → '{fallback['name']}'", facility.facility_id)
                product.name = fallback["name"]
                fallback["used"] = True
            else:
                logger.warning(f"    ⚠️ Pas de nom Excel disponible pour '{product.name}'", facility.facility_id)
        
        # Faire la même chose pour les produits en stock
        unmatched_stock = []
        for product in facility.stock_products:
            api_name = product.name
            match_name, match_idx = find_match(api_name, excel_products, re)
            
            if match_name == "SKIP":
                logger.debug(f"    ⏭️ Ignoré Stock (eau/autre): '{api_name}'", facility.facility_id)
                continue
            elif match_name and match_name != api_name:
                logger.debug(f"    🔄 Stock: '{api_name}' → '{match_name}'", facility.facility_id)
                product.name = match_name
                excel_products[match_idx]["used"] = True
            elif not match_name:
                unmatched_stock.append(product)
        
        # Fallback pour les produits en stock
        unused_excel = [ep for ep in excel_products if not ep["used"]]
        for product in unmatched_stock:
            if unused_excel:
                fallback = unused_excel.pop(0)
                logger.info(f"    🔄 Fallback Stock: '{product.name}' → '{fallback['name']}'", facility.facility_id)
                product.name = fallback["name"]
                fallback["used"] = True
        
        # Faire la même chose pour les données flowrate
        unmatched_flowrate = []
        if facility.flowrate_data:
            for device_id, device_data in facility.flowrate_data.items():
                if not isinstance(device_data, dict):
                    continue
                data = device_data.get("data", {})
                results = data.get("results", [])
                
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    api_name = result.get("productName", "")
                    if not api_name:
                        continue
                    
                    match_name, match_idx = find_match(api_name, excel_products, re)
                    
                    if match_name == "SKIP":
                        logger.debug(f"    ⏭️ Ignoré Flowrate (eau/autre): '{api_name}'", facility.facility_id)
                        continue
                    elif match_name and match_name != api_name:
                        logger.debug(f"    🔄 Flowrate: '{api_name}' → '{match_name}'", facility.facility_id)
                        result["productName"] = match_name
                        excel_products[match_idx]["used"] = True
                    elif not match_name:
                        unmatched_flowrate.append(result)
        
        # Fallback pour les données flowrate
        unused_excel = [ep for ep in excel_products if not ep["used"]]
        for result in unmatched_flowrate:
            if unused_excel:
                fallback = unused_excel.pop(0)
                logger.info(f"    🔄 Fallback Flowrate: '{result.get('productName', '')}' → '{fallback['name']}'", facility.facility_id)
                result["productName"] = fallback["name"]
                fallback["used"] = True
