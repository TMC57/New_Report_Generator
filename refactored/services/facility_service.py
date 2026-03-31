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
