"""
Application FastAPI principale du projet refactorisé
Serveur autonome avec tous les endpoints nécessaires
"""
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from refactored.api.routes import router as reports_router
from refactored.api.upload_routes import router as upload_router
from refactored.api.config_routes import router as config_router
from refactored.api.group_routes import router as group_router
from refactored.auth import verify_odoo_token, get_current_user, require_auth

# Créer l'application FastAPI
app = FastAPI(
    title="Générateur de Rapports E-Wash",
    description="Système de génération de rapports de consommation - Version Refactorisée",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Monter tous les routers
app.include_router(reports_router)
app.include_router(upload_router)
app.include_router(config_router)
app.include_router(group_router)

# Chemins des dossiers
BASE_DIR = Path(__file__).parent.parent
REFACTORED_DIR = Path(__file__).parent
UPLOADS_DIR = REFACTORED_DIR / "uploads"
IMAGES_DIR = REFACTORED_DIR / "images"

# Frontend React - chercher d'abord dans refactored/frontend (Docker) puis dans pixel-perfect-replica-50/dist (local)
REACT_BUILD_DIR = REFACTORED_DIR / "frontend"
if not REACT_BUILD_DIR.exists():
    REACT_BUILD_DIR = BASE_DIR / "pixel-perfect-replica-50" / "dist"

# Créer les dossiers nécessaires
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Monter les dossiers statiques
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

# Servir le frontend React si disponible
if REACT_BUILD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(REACT_BUILD_DIR / "assets")), name="assets")

@app.get("/")
async def get_home(request: Request):
    """
    Page d'accueil - sert le frontend React
    Requiert une authentification via Odoo
    """
    # TEMPORAIRE: Authentification désactivée pour les tests
    # user_token = await get_current_user(request)
    # if not user_token:
    #     return RedirectResponse(url="/login-required", status_code=302)
    
    react_index = REACT_BUILD_DIR / "index.html"
    if react_index.exists():
        return FileResponse(react_index)
    else:
        return HTMLResponse("""
        <html>
            <head><title>Générateur de Rapports E-Wash</title></head>
            <body>
                <h1>Générateur de Rapports E-Wash</h1>
                <p>Frontend non trouvé. Veuillez builder le frontend React avec 'npm run build'</p>
                <p>API disponible sur <a href="/api/docs">/api/docs</a></p>
            </body>
        </html>
        """, status_code=200)

@app.get("/health")
async def health_check():
    """
    Endpoint de santé pour vérifier que le serveur fonctionne
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "project": "refactored"
    }

# ==================== ENDPOINTS D'AUTHENTIFICATION ODOO ====================

@app.get("/auth")
async def authenticate_with_token(request: Request, token: str):
    """
    Endpoint d'authentification avec token Odoo
    URL: /auth?token=xxx
    """
    if await verify_odoo_token(token):
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="auth_token",
            value=token,
            max_age=3600,  # 1 heure
            httponly=True,
            secure=False,  # Mettre True en HTTPS
            path="/",
            samesite='lax'
        )
        return response
    else:
        raise HTTPException(status_code=401, detail="Token invalide")

@app.get("/logout")
async def logout(request: Request):
    """
    Déconnexion - supprime la session
    """
    response = RedirectResponse(url="/login-required", status_code=302)
    response.delete_cookie("auth_token")
    return response

@app.get("/login-required")
async def login_required():
    """
    Page affichée quand l'authentification est requise
    """
    return HTMLResponse("""
    <html>
        <head>
            <title>Authentification requise</title>
            <style>
                body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
                .container { text-align: center; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔒 Authentification requise</h1>
                <p>Vous devez vous connecter depuis Odoo pour accéder à cette application.</p>
                <p>Veuillez retourner dans Odoo et utiliser le lien d'accès approprié.</p>
            </div>
        </body>
    </html>
    """)

@app.post("/api/verify-token")
async def verify_token_endpoint(request: Request):
    """
    Endpoint pour qu'Odoo vérifie un token
    """
    data = await request.json()
    token = data.get("token")

    if not token:
        raise HTTPException(status_code=400, detail="Token manquant")

    is_valid = await verify_odoo_token(token)
    return {"valid": is_valid}

# ==================== FIN AUTHENTIFICATION ====================

# Endpoints de compatibilité pour le frontend
@app.post("/upload-excel-listing")
async def upload_excel_listing_compat(file: UploadFile = File(...)):
    """
    Endpoint de compatibilité pour l'upload Excel
    Redirige vers le nouveau système
    """
    from fastapi import UploadFile, File
    import json
    import shutil
    from datetime import datetime
    
    # Importer le parser Excel local
    from refactored.excel_parser import parse_listing_clients_excel
    
    try:
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Le fichier doit être au format Excel (.xlsx ou .xls)")
        
        excel_listings_dir = REFACTORED_DIR / "uploads" / "excel_listings"
        excel_listings_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le fichier Excel
        excel_file_path = excel_listings_dir / "current_listing.xlsx"
        with open(excel_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parser le fichier Excel
        excel_data = parse_listing_clients_excel(str(excel_file_path))
        
        # Sauvegarder les données parsées
        excel_data_path = excel_listings_dir / "listing_data.json"
        with open(excel_data_path, "w", encoding="utf-8") as f:
            json_data = {str(k): v for k, v in excel_data.items()}
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # Sauvegarder les métadonnées
        metadata_path = excel_listings_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            metadata = {
                "filename": file.filename,
                "facilities_count": len(excel_data),
                "upload_date": datetime.now().isoformat()
            }
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "filename": file.filename,
            "facilities_count": len(excel_data),
            "message": f"Fichier Excel parsé avec succès. {len(excel_data)} facilities trouvées."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du parsing: {str(e)}")

@app.get("/excel-listing-status")
async def get_excel_listing_status_compat():
    """
    Endpoint de compatibilité pour vérifier le statut Excel
    """
    import json
    
    excel_listings_dir = REFACTORED_DIR / "uploads" / "excel_listings"
    metadata_path = excel_listings_dir / "metadata.json"
    
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            return {
                "uploaded": True,
                "filename": metadata.get("filename"),
                "facilities_count": metadata.get("facilities_count"),
                "upload_date": metadata.get("upload_date")
            }
        except Exception:
            return {"uploaded": False}
    
    return {"uploaded": False}

@app.post("/upload")
async def upload_file_compat(file: UploadFile = File(...)):
    """
    Endpoint de compatibilité pour l'upload d'images
    """
    import shutil
    
    try:
        dst_path = UPLOADS_DIR / file.filename
        with open(dst_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"path": f"/uploads/{file.filename}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload: {str(e)}")

@app.get("/api/reports/list")
async def list_reports_compat():
    """
    Liste les dossiers de rapports (au lieu des fichiers PDF individuels)
    """
    import os
    from datetime import datetime
    import re
    
    reports_dir = REFACTORED_DIR / "reports"
    folders = []
    
    if not reports_dir.exists():
        return folders
    
    # Lister uniquement les dossiers de premier niveau
    for folder_name in os.listdir(reports_dir):
        folder_path = reports_dir / folder_name
        if not folder_path.is_dir():
            continue
        
        # Compter les fichiers PDF dans le dossier
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
        pdf_count = len(pdf_files)
        
        if pdf_count == 0:
            continue  # Ignorer les dossiers vides
        
        # Calculer la taille totale du dossier
        total_size = sum(
            os.path.getsize(folder_path / f) 
            for f in pdf_files
        )
        
        # Obtenir la date de modification du dossier
        folder_stat = os.stat(folder_path)
        
        # Extraire les dates du nom du dossier
        pattern = r'(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})'
        match = re.search(pattern, folder_name)
        
        date_range = None
        if match:
            from_date, to_date = match.groups()
            date_range = {
                "from_date": from_date,
                "to_date": to_date,
                "formatted": f"Du {from_date} au {to_date}"
            }
        
        # Déterminer le type de rapport
        report_type = "group" if folder_name.startswith("group") else "individual"
        
        folders.append({
            "folder_name": folder_name,
            "type": report_type,
            "pdf_count": pdf_count,
            "total_size": total_size,
            "date": datetime.fromtimestamp(folder_stat.st_mtime).isoformat(),
            "date_range": date_range,
            "files": pdf_files
        })
    
    # Trier par date décroissante
    folders.sort(key=lambda x: x['date'], reverse=True)
    return folders

@app.delete("/api/reports/folder/{folder_name:path}")
async def delete_report_folder(folder_name: str):
    """
    Supprime un dossier de rapports complet
    """
    import os
    import shutil
    
    reports_dir = REFACTORED_DIR / "reports"
    folder_path = reports_dir / folder_name
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail="Ce n'est pas un dossier")
    
    # Vérifier que le dossier est bien dans reports_dir (sécurité)
    try:
        folder_path.resolve().relative_to(reports_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Supprimer le dossier et son contenu
    shutil.rmtree(folder_path)
    return {"success": True, "message": f"Dossier {folder_name} supprimé"}

@app.delete("/api/reports/{filename}")
async def delete_report_compat(filename: str):
    """
    Supprime un rapport PDF (ancien endpoint pour compatibilité)
    """
    import os
    
    reports_dir = REFACTORED_DIR / "reports"
    
    # Chercher le fichier dans tous les sous-dossiers
    for root, dirs, files in os.walk(reports_dir):
        if filename in files:
            file_path = os.path.join(root, filename)
            os.remove(file_path)
            return {"success": True, "message": f"Rapport {filename} supprimé"}
    
    raise HTTPException(status_code=404, detail="Rapport non trouvé")

@app.get("/api/reports/download-folder/{folder_name:path}")
async def download_report_folder(folder_name: str):
    """
    Télécharge un dossier de rapports complet en ZIP
    """
    import os
    import zipfile
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    reports_dir = REFACTORED_DIR / "reports"
    folder_path = reports_dir / folder_name
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail="Ce n'est pas un dossier")
    
    # Vérifier que le dossier est bien dans reports_dir (sécurité)
    try:
        folder_path.resolve().relative_to(reports_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Créer un fichier ZIP en mémoire
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in os.listdir(folder_path):
            if file.endswith('.pdf'):
                file_path = folder_path / file
                zip_file.write(file_path, file)
    
    zip_buffer.seek(0)
    
    # Nom du fichier ZIP basé sur le nom du dossier
    zip_filename = f"{folder_name}.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )

@app.get("/api/reports/download/{filename}")
async def download_report_compat(filename: str):
    """
    Télécharge un rapport PDF (ancien endpoint pour compatibilité)
    """
    import os
    from fastapi.responses import FileResponse
    
    reports_dir = REFACTORED_DIR / "reports"
    
    # Chercher le fichier dans tous les sous-dossiers
    for root, dirs, files in os.walk(reports_dir):
        if filename in files:
            file_path = os.path.join(root, filename)
            return FileResponse(
                file_path,
                media_type="application/pdf",
                filename=filename,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    
    raise HTTPException(status_code=404, detail="Rapport non trouvé")

@app.get("/api/reports/preview/{filename}")
async def preview_report_compat(filename: str):
    """
    Prévisualise un rapport PDF dans le navigateur
    """
    import os
    from fastapi.responses import FileResponse
    
    reports_dir = REFACTORED_DIR / "reports"
    
    # Chercher le fichier dans tous les sous-dossiers
    for root, dirs, files in os.walk(reports_dir):
        if filename in files:
            file_path = os.path.join(root, filename)
            return FileResponse(
                file_path,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "inline",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    
    raise HTTPException(status_code=404, detail="Rapport non trouvé")

@app.post("/api/reports/download-multiple")
async def download_multiple_reports_compat(body: dict):
    """
    Télécharge plusieurs rapports dans un fichier ZIP
    """
    import os
    import zipfile
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    filenames = body.get("filenames", [])
    if not filenames:
        raise HTTPException(status_code=400, detail="Aucun fichier spécifié")
    
    reports_dir = REFACTORED_DIR / "reports"
    
    # Créer un fichier ZIP en mémoire
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in filenames:
            # Chercher le fichier dans tous les sous-dossiers
            found = False
            for root, dirs, files in os.walk(reports_dir):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    zip_file.write(file_path, filename)
                    found = True
                    break
            
            if not found:
                raise HTTPException(status_code=404, detail=f"Rapport {filename} non trouvé")
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=rapports.zip"}
    )

# Événements de démarrage/arrêt
@app.on_event("startup")
async def startup_event():
    """Actions au démarrage du serveur"""
    print("=" * 60)
    print("🚀 Serveur Générateur de Rapports E-Wash démarré")
    print("=" * 60)
    print(f"📁 Dossier uploads: {UPLOADS_DIR}")
    print(f"📁 Dossier images: {IMAGES_DIR}")
    print(f"📁 Frontend React: {REACT_BUILD_DIR}")
    print("=" * 60)
    print("📚 Documentation API: http://localhost:8000/api/docs")
    print("🌐 Application: http://localhost:8000")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Actions à l'arrêt du serveur"""
    print("\n👋 Serveur arrêté")
