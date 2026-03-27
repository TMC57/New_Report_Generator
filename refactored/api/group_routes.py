"""
Routes API pour la génération de rapports de groupe
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from refactored.services.cm2w_service import CM2WService
from refactored.services.group_service import GroupService
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
        
        # 1. Récupérer devices_list
        logger.info("1️⃣ Récupération de devices_list...")
        devices_response = cm2w.get_devices_list()
        if not devices_response or not devices_response.get("data"):
            raise HTTPException(status_code=500, detail="Impossible de récupérer devices_list")
        
        # 2. Mettre à jour GroupConfigJson.json
        logger.info("2️⃣ Mise à jour de GroupConfigJson.json...")
        group_config_result = group_service.update_group_config_from_devices(devices_response)
        groups_count = len(group_config_result.get("groups", []))
        logger.info(f"   → {groups_count} groupes dans la configuration")
        
        # 3. Récupérer total_qty (ajouter +1 jour à to_date pour l'API)
        logger.info("3️⃣ Récupération des quantités consommées...")
        to_date_obj = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
        to_date_plus_one = to_date_obj.strftime("%Y-%m-%d")
        
        total_qty_response = cm2w.get_total_qty_report(from_date, to_date_plus_one)
        if not total_qty_response:
            raise HTTPException(status_code=500, detail="Impossible de récupérer total_qty")
        
        # 4. Récupérer stock_levels
        logger.info("4️⃣ Récupération des niveaux de stock...")
        stock_levels_response = cm2w.get_stock_levels()
        if not stock_levels_response:
            raise HTTPException(status_code=500, detail="Impossible de récupérer stock_levels")
        
        # 5. Grouper les données par owner
        logger.info("5️⃣ Groupement des données par owner...")
        grouped_qty = group_service.group_quantities_by_owner(total_qty_response, devices_response)
        grouped_stock = group_service.group_stock_levels_by_owner(stock_levels_response, devices_response)
        
        owners_count = len(grouped_qty.get("owners", []))
        logger.info(f"   → {owners_count} owners trouvés avec des données")
        
        # 6. Générer les PDFs de groupe
        logger.info("6️⃣ Génération des PDFs de groupe...")
        
        # TODO: Implémenter la génération des PDFs
        # from refactored.pdf_generator.group_generator import GroupPDFGenerator
        # generator = GroupPDFGenerator()
        # pdfs_generated = generator.generate_all_group_pdfs(
        #     grouped_qty,
        #     grouped_stock,
        #     group_config_result["groups"],
        #     from_date,
        #     to_date
        # )
        
        # Pour l'instant, on retourne juste les données groupées
        logger.success(f"✅ Rapports de groupe préparés pour {owners_count} owners")
        
        return {
            "success": True,
            "groups_found": owners_count,
            "groups_in_config": groups_count,
            "message": f"{owners_count} rapports de groupe prêts à être générés",
            "data": {
                "grouped_quantities": grouped_qty,
                "grouped_stock": grouped_stock,
                "group_config": group_config_result["groups"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération des rapports de groupe: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
