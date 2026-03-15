import os
from fastapi import APIRouter, HTTPException
from typing import Optional
from refactored.services.facility_service import FacilityService
from refactored.pdf_generator.generator import PDFGenerator
from refactored.utils.logger import get_logger
from refactored.config.settings import DATA_CACHE_DIR

router = APIRouter(prefix="/api/v2", tags=["Reports V2"])
logger = get_logger("API_Routes")

@router.get("/test-data-retrieval")
def test_data_retrieval(
    facility_id: Optional[int] = None,
    from_date: str = "2025-01-01",
    to_date: str = "2025-01-31"
):
    """
    Endpoint de test pour vérifier la récupération des données
    Retourne les données complètes d'une ou toutes les facilities
    """
    logger.info(f"Test data retrieval: facility_id={facility_id}, {from_date} → {to_date}")
    
    try:
        service = FacilityService()
        
        if facility_id:
            facility = service.get_complete_facility_data(facility_id, from_date, to_date)
            if not facility:
                raise HTTPException(status_code=404, detail=f"Facility {facility_id} not found")
            
            output_path = DATA_CACHE_DIR / f"facility_{facility_id}_data.json"
            service.save_facility_data_to_json(facility, str(output_path))
            
            return {
                "success": True,
                "facility": {
                    "facility_id": facility.facility_id,
                    "facility_name": facility.facility_name,
                    "owner": facility.owner,
                    "display_name": facility.get_display_name(),
                    "display_title": facility.get_display_title(),
                    "filename_base": facility.get_filename_base(),
                    "client_number": facility.client_number,
                    "client_name": facility.client_name,
                    "address": facility.address,
                    "group": facility.group,
                    "excel_matched": facility.excel_matched,
                    "excel_match_method": facility.excel_match_method,
                    "devices_count": len(facility.devices),
                    "products_count": len(facility.products),
                    "stock_products_count": len(facility.stock_products),
                    "zones": facility.zones,
                    "has_all_required_data": facility.has_all_required_data(),
                    "missing_data": facility.get_missing_data(),
                    "devices": [
                        {
                            "device_id": d.device_id,
                            "serial_number": d.serial_number,
                            "zone": d.zone
                        }
                        for d in facility.devices
                    ],
                    "products": [
                        {
                            "product_id": p.product_id,
                            "name": p.name,
                            "total_qty": p.total_qty,
                            "zone": p.zone,
                            "daily_quantities_count": len(p.daily_quantities),
                            "monthly_quantities_count": len(p.monthly_quantities),
                            "daily_quantities": p.daily_quantities[:5] if len(p.daily_quantities) > 5 else p.daily_quantities,
                            "monthly_quantities": p.monthly_quantities
                        }
                        for p in facility.products
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
                        for p in facility.stock_products
                    ]
                }
            }
        else:
            facilities = service.get_all_facilities_data(from_date, to_date)
            
            return {
                "success": True,
                "total_count": len(facilities),
                "excel_matched_count": sum(1 for f in facilities if f.excel_matched),
                "complete_data_count": sum(1 for f in facilities if f.has_all_required_data()),
                "facilities": [
                    {
                        "facility_id": f.facility_id,
                        "facility_name": f.facility_name,
                        "display_name": f.get_display_name(),
                        "display_title": f.get_display_title(),
                        "excel_matched": f.excel_matched,
                        "has_all_required_data": f.has_all_required_data(),
                        "missing_data": f.get_missing_data(),
                        "devices_count": len(f.devices),
                        "products_count": len(f.products),
                        "zones": f.zones
                    }
                    for f in facilities
                ]
            }
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports-generation-v2")
def reports_generation_v2(
    from_date: str,
    to_date: str,
    facility_id: Optional[int] = None
):
    """
    Nouveau endpoint de génération de rapports utilisant le système refactorisé avec Playwright
    """
    logger.info(f"Génération rapports V2: facility_id={facility_id}, {from_date} → {to_date}")
    
    try:
        from refactored.pdf_generator import PDFGenerator
        
        service = FacilityService()
        pdf_gen = PDFGenerator()
        
        if facility_id:
            facility = service.get_complete_facility_data(facility_id, from_date, to_date)
            if not facility:
                raise HTTPException(status_code=404, detail=f"Facility {facility_id} not found")
            
            if not facility.has_all_required_data():
                missing = facility.get_missing_data()
                logger.warning(f"Données manquantes pour facility {facility_id}: {missing}")
                return {
                    "success": False,
                    "error": f"Données manquantes: {', '.join(missing)}",
                    "facility_id": facility_id
                }
            
            json_output_path = DATA_CACHE_DIR / f"facility_{facility_id}_complete.json"
            service.save_facility_data_to_json(facility, str(json_output_path))
            
            facility_dict = facility.to_dict()
            pdf_path = pdf_gen.generate_facility_report(facility_dict, from_date, to_date)
            
            logger.success(f"✅ PDF généré: {pdf_path}")
            
            return {
                "success": True,
                "message": f"PDF généré avec succès",
                "pdf_path": pdf_path,
                "json_path": json_output_path,
                "facility": {
                    "facility_id": facility.facility_id,
                    "display_title": facility.get_display_title(),
                    "filename_base": facility.get_filename_base(),
                    "has_all_data": facility.has_all_required_data()
                }
            }
        else:
            # Récupérer la liste des facility IDs
            devices_response = service.cm2w.get_devices_list()
            if not devices_response or not devices_response.get("data"):
                raise HTTPException(status_code=500, detail="Impossible de récupérer la liste des devices")
            
            facility_ids = set()
            for device_data in devices_response["data"]:
                fid = device_data.get("facilityId")
                if fid:
                    facility_ids.add(fid)
            
            total_facilities = len(facility_ids)
            logger.info(f"📋 {total_facilities} facilities à traiter")
            logger.info(f"🚀 Génération des PDFs en temps réel...")
            
            generated_pdfs = []
            generated_jsons = []
            incomplete_facilities = []
            
            # Traiter chaque facility une par une et générer immédiatement
            for i, fid in enumerate(sorted(facility_ids), 1):
                logger.info(f"📄 Traitement {i}/{total_facilities}: Facility {fid}")
                
                try:
                    facility = service.get_complete_facility_data(fid, from_date, to_date)
                    
                    if not facility:
                        logger.warning(f"⚠️ Facility {fid} ignorée (données non récupérables)")
                        continue
                    
                    if not facility.has_all_required_data():
                        missing = facility.get_missing_data()
                        logger.warning(f"⚠️ Facility {fid} incomplète: {', '.join(missing)}")
                        incomplete_facilities.append({
                            "facility_id": fid,
                            "facility_name": facility.facility_name,
                            "missing_data": missing
                        })
                        continue
                    
                    # Générer JSON immédiatement
                    json_output_path = DATA_CACHE_DIR / f"facility_{fid}_complete.json"
                    service.save_facility_data_to_json(facility, str(json_output_path))
                    generated_jsons.append(json_output_path)
                    
                    # Générer PDF immédiatement
                    facility_dict = facility.to_dict()
                    pdf_path = pdf_gen.generate_facility_report(facility_dict, from_date, to_date)
                    generated_pdfs.append(pdf_path)
                    
                    logger.success(f"✅ PDF généré pour facility {fid}: {pdf_path}")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur lors du traitement de facility {fid}: {e}")
                    import traceback
                    traceback.print_exc()
            
            logger.success(f"🎉 Génération terminée: {len(generated_pdfs)} PDFs créés sur {total_facilities} facilities")
            
            return {
                "success": True,
                "message": f"{len(generated_pdfs)} PDFs générés avec succès",
                "total_count": total_facilities,
                "complete_count": len(generated_pdfs),
                "incomplete_count": len(incomplete_facilities),
                "generated_pdfs": generated_pdfs,
                "generated_jsons": generated_jsons,
                "incomplete_facilities": incomplete_facilities
            }
    
    except Exception as e:
        logger.error(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
