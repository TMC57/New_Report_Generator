"""
Routes API pour la gestion des uploads (images et Excel)
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import json
from typing import List
from refactored.utils.logger import get_logger

logger = get_logger("Upload_Routes")

router = APIRouter(prefix="/api/v2/uploads", tags=["uploads"])

# Dossiers de destination
UPLOADS_DIR = Path("refactored/uploads")
EXCEL_LISTINGS_DIR = UPLOADS_DIR / "excel_listings"

# Créer les dossiers si nécessaire
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
EXCEL_LISTINGS_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/facility-image")
async def upload_facility_image(file: UploadFile = File(...)):
    """
    Upload une image de facility
    """
    try:
        # Vérifier le type de fichier
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non autorisé. Extensions autorisées: {', '.join(allowed_extensions)}"
            )
        
        # Sauvegarder le fichier
        file_path = UPLOADS_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.success(f"✅ Image uploadée: {file.filename}")
        
        return {
            "success": True,
            "filename": file.filename,
            "path": f"/uploads/{file.filename}",
            "message": "Image uploadée avec succès"
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/material-image")
async def upload_material_image(file: UploadFile = File(...)):
    """
    Upload une image de matériel (Orsy Connecté, etc.)
    """
    return await upload_facility_image(file)

@router.post("/excel-listing")
async def upload_excel_listing(file: UploadFile = File(...)):
    """
    Upload un fichier Excel de listing clients
    Note: Le parsing Excel doit être fait côté frontend ou via un autre endpoint
    """
    try:
        # Vérifier le type de fichier
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Type de fichier non autorisé. Extensions autorisées: .xlsx, .xls"
            )
        
        # Sauvegarder le fichier Excel
        file_path = EXCEL_LISTINGS_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.success(f"✅ Fichier Excel uploadé: {file.filename}")
        
        return {
            "success": True,
            "filename": file.filename,
            "path": str(file_path),
            "message": "Fichier Excel uploadé avec succès"
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/excel-data")
async def save_excel_data(data: dict):
    """
    Sauvegarde les données Excel parsées (listing_data.json)
    """
    try:
        output_file = EXCEL_LISTINGS_DIR / "listing_data.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Sauvegarder aussi les métadonnées
        metadata_file = EXCEL_LISTINGS_DIR / "metadata.json"
        metadata = {
            "last_updated": str(Path(output_file).stat().st_mtime),
            "total_clients": len(data) if isinstance(data, dict) else 0
        }
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.success(f"✅ Données Excel sauvegardées: {len(data)} clients")
        
        return {
            "success": True,
            "message": f"Données Excel sauvegardées ({len(data)} clients)",
            "path": str(output_file)
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images")
async def list_images():
    """
    Liste toutes les images disponibles
    """
    try:
        images = []
        for file_path in UPLOADS_DIR.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                images.append({
                    "filename": file_path.name,
                    "path": f"/uploads/{file_path.name}",
                    "size": file_path.stat().st_size
                })
        
        return {
            "success": True,
            "images": images,
            "total": len(images)
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors du listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/excel-status")
async def get_excel_status():
    """
    Retourne le statut des données Excel
    """
    try:
        data_file = EXCEL_LISTINGS_DIR / "listing_data.json"
        metadata_file = EXCEL_LISTINGS_DIR / "metadata.json"
        
        if not data_file.exists():
            return {
                "success": True,
                "has_data": False,
                "message": "Aucune donnée Excel disponible"
            }
        
        # Charger les métadonnées
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        
        # Compter les clients
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            total_clients = len(data) if isinstance(data, dict) else 0
        
        return {
            "success": True,
            "has_data": True,
            "total_clients": total_clients,
            "metadata": metadata
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/image/{filename}")
async def delete_image(filename: str):
    """
    Supprime une image
    """
    try:
        file_path = UPLOADS_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image non trouvée")
        
        file_path.unlink()
        logger.success(f"✅ Image supprimée: {filename}")
        
        return {
            "success": True,
            "message": f"Image {filename} supprimée"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression: {e}")
        raise HTTPException(status_code=500, detail=str(e))
