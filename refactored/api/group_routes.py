"""
Routes API pour la génération de rapports de groupe
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
from refactored.services.cm2w_service import CM2WService
from refactored.services.group_service import GroupService
from refactored.services.config_service import ConfigService
from refactored.services.odoo_service import OdooService
from refactored.utils.logger import get_logger

logger = get_logger("Group_Routes")

router = APIRouter(prefix="/api/v2", tags=["group-reports"])

@router.get("/reports-generation-group")
async def generate_group_reports(
    from_date: str,
    to_date: str
):
    """
    Génère les rapports de groupe (1 PDF par owner)
    
    Workflow:
    1. Récupère devices_list depuis CM2W
    2. Met à jour GroupConfigJson.json (ajoute nouveaux owners)
    3. Récupère total_qty et stock_levels
    4. Groupe les données par owner
    5. Génère les PDFs de groupe
    
    Args:
        from_date: Date de début (YYYY-MM-DD)
        to_date: Date de fin (YYYY-MM-DD)
    
    Returns:
        {"success": True, "groups_generated": X, "message": "..."}
    """
    try:
        logger.info(f"🔄 Génération des rapports de groupe du {from_date} au {to_date}")
        
        # Services
        cm2w = CM2WService()
        group_service = GroupService()
        config_service = ConfigService()
        
        # 1. Récupérer devices_list
        logger.info("1️⃣ Récupération de devices_list...")
        devices_response = cm2w.get_devices_list()
        if not devices_response or not devices_response.get("data"):
            raise HTTPException(status_code=500, detail="Impossible de récupérer devices_list")
        
        # 2. Mettre à jour configJson.json (facilities individuelles)
        logger.info("2️⃣ Mise à jour de configJson.json...")
        config_service.update_config_from_devices(devices_response)
        
        # 3. Mettre à jour GroupConfigJson.json (groupes)
        logger.info("3️⃣ Mise à jour de GroupConfigJson.json...")
        group_config_result = group_service.update_group_config_from_devices(devices_response)
        groups_count = len(group_config_result.get("groups", []))
        logger.info(f"   → {groups_count} groupes dans la configuration")
        
        # 4. Récupérer total_qty (ajouter +1 jour à to_date pour l'API)
        logger.info("4️⃣ Récupération des quantités consommées...")
        to_date_obj = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
        to_date_plus_one = to_date_obj.strftime("%Y-%m-%d")
        
        total_qty_response = cm2w.get_total_qty_report(from_date, to_date_plus_one)
        if not total_qty_response:
            raise HTTPException(status_code=500, detail="Impossible de récupérer total_qty")
        
        # 5. Récupérer stock_levels
        logger.info("5️⃣ Récupération des niveaux de stock...")
        stock_levels_response = cm2w.get_stock_levels()
        if not stock_levels_response:
            raise HTTPException(status_code=500, detail="Impossible de récupérer stock_levels")
        
        # 6. Grouper les données par owner
        logger.info("6️⃣ Groupement des données par owner...")
        grouped_qty = group_service.group_quantities_by_owner(total_qty_response, devices_response)
        grouped_stock = group_service.group_stock_levels_by_owner(stock_levels_response, devices_response)
        
        owners_count = len(grouped_qty.get("owners", []))
        logger.info(f"   → {owners_count} owners trouvés avec des données")
        
        # 7. Récupérer les données Odoo pour chaque facility
        logger.info("7️⃣ Récupération des données Odoo (produits livrés)...")
        odoo_service = OdooService()
        facilities_odoo_data: Dict[int, Dict] = {}
        
        # Récupérer la liste de toutes les facilities
        all_facilities = devices_response.get("data", [])
        logger.info(f"   → {len(all_facilities)} facilities à traiter")
        
        for idx, facility in enumerate(all_facilities, 1):
            facility_id = facility.get("facilityId")
            facility_name = facility.get("facilityName", "")
            
            if not facility_id or not facility_name:
                continue
            
            try:
                logger.info(f"   [{idx}/{len(all_facilities)}] Récupération Odoo pour {facility_name}...")
                odoo_data = odoo_service.get_delivered_products_for_facility(
                    facility_name,
                    from_date,
                    to_date
                )
                
                if odoo_data and odoo_data.get("orders_count", 0) > 0:
                    facilities_odoo_data[facility_id] = odoo_data
                    logger.success(f"   ✅ {odoo_data.get('orders_count', 0)} commandes trouvées")
                else:
                    logger.info(f"   ⏭️  Aucune commande Odoo")
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Erreur Odoo pour {facility_name}: {e}")
        
        logger.info(f"   → {len(facilities_odoo_data)} facilities avec données Odoo")
        
        # 8. Grouper les données Odoo par owner
        logger.info("8️⃣ Groupement des données Odoo par owner...")
        grouped_odoo = group_service.group_odoo_deliveries_by_owner(
            facilities_odoo_data,
            devices_response
        )
        
        # Fusionner les données Odoo dans grouped_qty
        odoo_by_owner = {o["owner"]: o for o in grouped_odoo.get("owners", [])}
        for owner_data in grouped_qty.get("owners", []):
            owner_name = owner_data.get("owner")
            if owner_name in odoo_by_owner:
                owner_data["odoo_products_by_month"] = odoo_by_owner[owner_name].get("products_by_month", {})
                logger.info(f"   → {owner_name}: {len(owner_data['odoo_products_by_month'])} produits Odoo")
            else:
                owner_data["odoo_products_by_month"] = {}
        
        # 9. Générer les PDFs de groupe
        logger.info("9️⃣ Génération des PDFs de groupe...")
        
        from refactored.pdf_generator.group_generator import GroupPDFGenerator
        generator = GroupPDFGenerator()
        pdfs_generated = generator.generate_all_group_pdfs(
            grouped_qty,
            grouped_stock,
            group_config_result["groups"],
            from_date,
            to_date
        )
        
        logger.success(f"✅ {len(pdfs_generated)} rapports de groupe générés")
        
        return {
            "success": True,
            "groups_found": owners_count,
            "groups_in_config": groups_count,
            "pdfs_generated": len(pdfs_generated),
            "message": f"{len(pdfs_generated)} rapports de groupe générés avec succès",
            "pdf_files": [str(Path(p).name) for p in pdfs_generated]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération des rapports de groupe: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
