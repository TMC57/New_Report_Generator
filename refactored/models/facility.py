from dataclasses import dataclass, field
from typing import Optional, List, Dict
from .device import Device
from .product import Product, ProductConsumption

@dataclass
class FacilityConfig:
    """Configuration locale d'une facility (depuis configJson.json)"""
    facility_id: int
    facility_name: str = ""
    cover_picture: str = ""

@dataclass
class FacilityData:
    """Modèle complet d'une facility avec toutes ses données"""
    
    facility_id: int
    facility_name: str
    owner: str = ""
    
    client_number: Optional[int] = None
    client_name: Optional[str] = None
    address: Optional[str] = None
    group: Optional[str] = None
    local_config: Optional[dict] = None
    cover_picture_path: Optional[str] = None
    material_picture_path: Optional[str] = None
    last_intervention_date: Optional[str] = None
    buses_info: Optional[str] = None
    
    devices: List[Device] = field(default_factory=list)
    products: List[ProductConsumption] = field(default_factory=list)
    stock_products: List[Product] = field(default_factory=list)
    
    config: Optional[FacilityConfig] = None
    
    zones: List[str] = field(default_factory=list)
    
    # Données de débit (flowrate) par device
    flowrate_data: Dict[int, Dict] = field(default_factory=dict)  # {device_id: events_data}
    
    # Données Odoo (produits livrés)
    odoo_delivered_products: Dict = field(default_factory=dict)  # {orders, products_summary, ...}
    
    excel_matched: bool = False
    excel_match_method: Optional[str] = None
    
    # Données Excel - Informations générales
    installation_date: Optional[str] = None
    zone_number: Optional[str] = None
    router_number: Optional[str] = None
    last_intervention: Optional[str] = None
    
    # Données Excel - Zone 1 (principale)
    produit_lavant: Optional[str] = None
    dilution_lavant: Optional[str] = None
    couleur_buse_lavant: Optional[str] = None
    produit_sechant: Optional[str] = None
    dilution_sechant: Optional[str] = None
    couleur_buse_sechant: Optional[str] = None
    autre_produit_lavant: Optional[str] = None
    autre_dilution_lavant: Optional[str] = None
    autre_couleur_buse_lavant: Optional[str] = None
    produit_jantes: Optional[str] = None
    dilution_jantes: Optional[str] = None
    
    # Données Excel - Zone 2
    produit_lavant_zone2: Optional[str] = None
    dilution_lavant_zone2: Optional[str] = None
    couleur_buse_lavant_zone2: Optional[str] = None
    produit_sechant_zone2: Optional[str] = None
    dilution_sechant_zone2: Optional[str] = None
    couleur_buse_sechant_zone2: Optional[str] = None
    autre_produit_lavant_zone2: Optional[str] = None
    autre_dilution_lavant_zone2: Optional[str] = None
    autre_couleur_buse_lavant_zone2: Optional[str] = None
    
    # Données Excel - Zone 3
    produit_lavant_zone3: Optional[str] = None
    dilution_lavant_zone3: Optional[str] = None
    couleur_buse_lavant_zone3: Optional[str] = None
    produit_sechant_zone3: Optional[str] = None
    dilution_sechant_zone3: Optional[str] = None
    couleur_buse_sechant_zone3: Optional[str] = None
    
    # Données Excel - Zone 4
    produit_lavant_zone4: Optional[str] = None
    dilution_lavant_zone4: Optional[str] = None
    couleur_buse_lavant_zone4: Optional[str] = None
    produit_sechant_zone4: Optional[str] = None
    dilution_sechant_zone4: Optional[str] = None
    couleur_buse_sechant_zone4: Optional[str] = None
    
    # Données Excel - Zone 5
    produit_lavant_zone5: Optional[str] = None
    dilution_lavant_zone5: Optional[str] = None
    couleur_buse_lavant_zone5: Optional[str] = None
    produit_sechant_zone5: Optional[str] = None
    dilution_sechant_zone5: Optional[str] = None
    couleur_buse_sechant_zone5: Optional[str] = None
    
    def get_display_name(self) -> str:
        """Retourne le nom à afficher (priorité au nom Excel)"""
        return self.client_name or self.facility_name
    
    def get_display_title(self) -> str:
        """Retourne le titre complet pour le PDF"""
        parts = []
        if self.client_number:
            parts.append(str(self.client_number))
        parts.append(self.get_display_name().upper())
        if self.address and self.address.strip():
            parts.append(self.address.upper())
        return " - ".join(parts)
    
    def get_filename_base(self) -> str:
        """Retourne la base du nom de fichier (sanitized)"""
        name = self.get_display_name()
        sanitized = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
        sanitized = sanitized.replace(' ', '_')
        return sanitized
    
    def has_all_required_data(self) -> bool:
        """Vérifie que toutes les données nécessaires sont présentes"""
        return (
            self.facility_id is not None and
            self.facility_name and
            len(self.devices) > 0 and
            len(self.products) > 0
        )
    
    def get_missing_data(self) -> List[str]:
        """Retourne la liste des données manquantes"""
        missing = []
        if not self.client_number:
            missing.append("client_number")
        if not self.client_name:
            missing.append("client_name")
        if not self.address:
            missing.append("address")
        if not self.devices:
            missing.append("devices")
        if not self.products:
            missing.append("products")
        return missing
    
    def to_dict(self) -> dict:
        """Convertit FacilityData en dictionnaire pour le générateur PDF"""
        return {
            "facility_id": self.facility_id,
            "facility_name": self.facility_name,
            "owner": self.owner,
            "client_number": self.client_number,
            "client_name": self.client_name,
            "address": self.address,
            "group": self.group,
            "cover_picture_path": self.cover_picture_path,
            "material_picture_path": self.material_picture_path,
            "last_intervention_date": self.last_intervention_date,
            "buses_info": self.buses_info,
            
            # Données Excel
            "installation_date": self.installation_date,
            "zone_number": self.zone_number,
            "router_number": self.router_number,
            "last_intervention": self.last_intervention,
            "produit_lavant": self.produit_lavant,
            "dilution_lavant": self.dilution_lavant,
            "couleur_buse_lavant": self.couleur_buse_lavant,
            "produit_sechant": self.produit_sechant,
            "dilution_sechant": self.dilution_sechant,
            "couleur_buse_sechant": self.couleur_buse_sechant,
            "autre_produit_lavant": self.autre_produit_lavant,
            "autre_dilution_lavant": self.autre_dilution_lavant,
            "autre_couleur_buse_lavant": self.autre_couleur_buse_lavant,
            "produit_jantes": self.produit_jantes,
            "dilution_jantes": self.dilution_jantes,
            "produit_lavant_zone2": self.produit_lavant_zone2,
            "dilution_lavant_zone2": self.dilution_lavant_zone2,
            "couleur_buse_lavant_zone2": self.couleur_buse_lavant_zone2,
            "produit_sechant_zone2": self.produit_sechant_zone2,
            "dilution_sechant_zone2": self.dilution_sechant_zone2,
            "couleur_buse_sechant_zone2": self.couleur_buse_sechant_zone2,
            "autre_produit_lavant_zone2": self.autre_produit_lavant_zone2,
            "autre_dilution_lavant_zone2": self.autre_dilution_lavant_zone2,
            "autre_couleur_buse_lavant_zone2": self.autre_couleur_buse_lavant_zone2,
            "produit_lavant_zone3": self.produit_lavant_zone3,
            "dilution_lavant_zone3": self.dilution_lavant_zone3,
            "couleur_buse_lavant_zone3": self.couleur_buse_lavant_zone3,
            "produit_sechant_zone3": self.produit_sechant_zone3,
            "dilution_sechant_zone3": self.dilution_sechant_zone3,
            "couleur_buse_sechant_zone3": self.couleur_buse_sechant_zone3,
            "produit_lavant_zone4": self.produit_lavant_zone4,
            "dilution_lavant_zone4": self.dilution_lavant_zone4,
            "couleur_buse_lavant_zone4": self.couleur_buse_lavant_zone4,
            "produit_sechant_zone4": self.produit_sechant_zone4,
            "dilution_sechant_zone4": self.dilution_sechant_zone4,
            "couleur_buse_sechant_zone4": self.couleur_buse_sechant_zone4,
            "produit_lavant_zone5": self.produit_lavant_zone5,
            "dilution_lavant_zone5": self.dilution_lavant_zone5,
            "couleur_buse_lavant_zone5": self.couleur_buse_lavant_zone5,
            "produit_sechant_zone5": self.produit_sechant_zone5,
            "dilution_sechant_zone5": self.dilution_sechant_zone5,
            "couleur_buse_sechant_zone5": self.couleur_buse_sechant_zone5,
            "devices": [
                {
                    "device_id": d.device_id,
                    "serial_number": d.serial_number,
                    "zone": d.zone
                }
                for d in self.devices
            ],
            "products": [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "total_qty": p.total_qty,
                    "zone": p.zone,
                    "daily_quantities": p.daily_quantities,
                    "monthly_quantities": p.monthly_quantities
                }
                for p in self.products
            ],
            "stock_products": [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "remaining_quantity": p.remaining_quantity,
                    "remaining_quantity_unit": p.remaining_quantity_unit,
                    "average_daily_consumption": p.average_daily_consumption,
                    "remaining_days": p.remaining_days,
                    "zone": p.zone
                }
                for p in self.stock_products
            ],
            "zones": self.zones,
            "flowrate_data": self.flowrate_data,
            "odoo_delivered_products": self.odoo_delivered_products
        }
