import os
import json
import shutil
import logging
import zipfile
import tempfile
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from model import model, body_total_qty_report, body_devices_list, body_stock_levels
from DataTransform import get_total_qty_every_days, get_total_qty_every_month, enrich_json_with_zone, group_qty_by_owner_and_facility, enrich_qty_with_stock_products, enrich_qty_with_stock_products2, reconcile_qty_ids_with_stocklevels, group_stocklevels_by_owner_and_facility
from pdfGen import generate_pdfs_by_facility
from Json_parameter import transform_facility_json
from group_parameter import build_group_config_from_devices_list
from GrouPdfGen import generate_group_pdfs
from product_sync import sync_product_names, add_missing_facilities
from auth import verify_odoo_token, get_current_user, require_auth


GROUP_FILE = "Config/GroupConfigJson.json"

logger = logging.getLogger("uvicorn.error")

# app = FastAPI()

app = FastAPI(
    title="Mon générateur de raport",
    description="Créez l'intégralité des rapports pour vos client en un instant",
    version="1.0.0",
    docs_url="/app",     # URL personnalisée pour Swagger UI
    redoc_url="/ma-redoc",   # URL personnalisée pour ReDoc
    swagger_ui_parameters={"theme": "dark"}  # Ajoute le dark mode
)

# Endpoints d'authentification
@app.get("/auth")
async def authenticate_with_token(request: Request, token: str):
    """
    Endpoint d'authentification avec token Odoo
    URL: /auth?token=xxx
    """
    # Vérifier le token auprès d'Odoo
    if await verify_odoo_token(token):
        # Token valide, créer une session locale
        response = RedirectResponse(url="/reports", status_code=302)
        # Définir un cookie avec le token (expire dans 1h)
        response.set_cookie(
            key="auth_token",
            value=token,
            max_age=3600,  # 1 heure
            httponly=True,
            secure=False  # Mettre True en HTTPS
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
        <head><title>Authentification requise</title></head>
        <body>
            <h1>Authentification requise</h1>
            <p>Vous devez vous connecter depuis Odoo pour accéder à cette application.</p>
            <p>Veuillez retourner dans Odoo et utiliser le lien d'accès approprié.</p>
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

# @app.get("/", tags=["Raports"])
# def read_root():
#     return {"message": "API opérationnelle"}

@app.get("/")
async def get_home(request: Request):
    """
    Page d'accueil - nécessite une authentification
    """
    user_token = await get_current_user(request)
    if not user_token:
        return RedirectResponse(url="/login-required", status_code=302)
    return FileResponse("static/table.html")

@app.get("/Reports_generation", tags=["Rapports"])
def  Total_Quantity_Report_grouped_by_facilities(
    user: str = Depends(require_auth),
    # pageNumber: int,
    # pageSize: int,
    from_date: str,
    to_date: str,
    facility_id: Optional[int] = None,  
    # DeviceId: Optional[int] = None
):
    """
    Endpoint GET /report qui retourne des données de rapport.
    Les dates sont en format 'YYYY-MM-DD'. zzz
    """ 
    print("Génération du rapport en cours...")

    endpoint, headers, params = body_devices_list(facility_id)
    devices_list = model(endpoint, headers, params).json()

    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
    to_date_plus_one = to_date_obj.strftime("%Y-%m-%d")

    endpoint, headers, params =  body_total_qty_report(from_date, to_date_plus_one, facility_id) 
    total_qty = model(endpoint, headers, params).json()

    agg = group_qty_by_owner_and_facility(total_qty, devices_list)

    # Exemple: afficher le total par owner
    # for o in agg["owners"]:
    #     print(o["owner"], "→", o["totalQty"])

    build_group_config_from_devices_list(devices_list)

    endpoint, headers, params = body_stock_levels(facility_id)
    stock_levels = model(endpoint, headers, params).json()
    # # ================= Data Transformation ================
    total_qty_Json = get_total_qty_every_days(total_qty, from_date, to_date, facility_id)
    total_qty_Json = enrich_qty_with_stock_products(total_qty_Json, stock_levels)
    total_qty_Json = get_total_qty_every_month(total_qty_Json, to_date, facility_id)

    # ici
    total_qty_Json = enrich_qty_with_stock_products2(total_qty_Json, stock_levels)

    # total_qty_Json = enrich_qty_with_stock_products(total_qty_Json, stock_levels)

    total_qty_Json = enrich_json_with_zone(total_qty_Json)

    # # ======================================================
    transform_facility_json(devices_list)
    generate_pdfs_by_facility(total_qty_Json, devices_list, stock_levels, from_date, to_date)


    return {"ok"}


@app.get("/Group_Reports_generation", tags=["Rapports"])
def Group_Report_generation(
    user: str = Depends(require_auth),
    from_date: str,
    to_date: str,
):
    """
    Endpoint GET /report qui retourne des données de rapport de groupe.
    Les dates sont en format 'YYYY-MM-DD'.
    """ 
    print("Génération du rapport de groupe en cours...")

    endpoint, headers, params = body_devices_list()
    devices_list = model(endpoint, headers, params).json()

    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
    to_date_plus_one = to_date_obj.strftime("%Y-%m-%d")

    endpoint, headers, params =  body_total_qty_report(from_date, to_date_plus_one) 
    total_qty = model(endpoint, headers, params).json()

    endpoint, headers, params = body_stock_levels()
    stock_levels = model(endpoint, headers, params).json()

    total_qty = group_qty_by_owner_and_facility(total_qty, devices_list)
    total_qty, corrections = reconcile_qty_ids_with_stocklevels(total_qty, stock_levels)

    stock_levels_grouped = group_stocklevels_by_owner_and_facility(stock_levels, devices_list)

    # Synchroniser les noms de produits
    total_qty, corrections_count = sync_product_names(total_qty, stock_levels_grouped)
    
    # Ajouter les facilities manquantes de devices_list
    total_qty, added_count = add_missing_facilities(total_qty, devices_list)
    
    json.dump(devices_list, open("devices_list.json", "w", encoding="utf-8"),
    indent=2, ensure_ascii=False)


    # # ================= Data Transformation ================

    # total_qty_Json = enrich_qty_with_stock_products(agg, stock_levels)
    # total_qty_Json = enrich_qty_with_stock_products2(total_qty_Json, stock_levels)

    # # ======================================================
    # transform_facility_json(devices_list)
    # print(stock_levels_grouped)
    try:
        generate_group_pdfs(total_qty, devices_list, stock_levels_grouped, from_date, to_date)
        return {"ok"}
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport de groupe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")




DATA_FILE = "Config/configJson.json"  # Ton fichier JSON

# --- Static files (HTML) + uploads (images) ---
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


app.mount("/static", StaticFiles(directory="static"), name="static")

# URL publique /uploads -> dossier ./uploads (persistant via volumes)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# URL publique /images -> dossier ./images
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.get("/items")
def get_items(user: str = Depends(require_auth)):
    """Retourne le contenu du JSON."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.put("/items")
def save_items(items: List[dict], user: str = Depends(require_auth)):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return {"saved": len(items)}

# --- Upload ---
@app.post("/upload")
async def upload(file: UploadFile = File(...), user: str = Depends(require_auth)):
    dst_path = os.path.join("uploads", file.filename)
    with open(dst_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # On retourne un chemin web-accessible pour l'afficher directement (<img src="/uploads/...">)
    return {"path": f"/uploads/{file.filename}"}


@app.get("/group-items")
def get_group_items(user: str = Depends(require_auth)):
    if not os.path.exists(GROUP_FILE):
        return []
    with open(GROUP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.put("/group-items")
def save_group_items(items: list[dict], user: str = Depends(require_auth)):
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return {"saved": len(items)}

# Page web d'édition des groupes
@app.get("/group-app")
def group_app(user: str = Depends(require_auth)):
    return FileResponse("static/group_table.html")

# --- REPORTS MANAGEMENT ENDPOINTS ---

@app.get("/reports")
def reports_management(user: str = Depends(require_auth)):
    """Page de gestion des rapports"""
    return FileResponse("static/reports.html")

@app.get("/api/reports/list")
def list_reports(user: str = Depends(require_auth)):
    """API pour lister tous les rapports avec métadonnées"""
    reports_dir = "Reports"
    reports = []

    if not os.path.exists(reports_dir):
        return reports

    for root, dirs, files in os.walk(reports_dir):
        for file in files:
            if file.endswith('.pdf'):
                file_path = os.path.join(root, file)
                stat = os.stat(file_path)

                # Extraire les informations du dossier parent
                folder_name = os.path.basename(root)

                # Déterminer le type de rapport basé sur le dossier
                report_type = "group" if folder_name.startswith("group") else "individual"

                # Extraire les dates du nom du dossier (format: "reports YYYY-MM-DD to YYYY-MM-DD")
                date_range = extract_date_range_from_folder(folder_name)

                # Nom affiché (sans extension)
                display_name = os.path.splitext(file)[0]

                reports.append({
                    "filename": file,
                    "name": display_name,
                    "type": report_type,
                    "size": stat.st_size,
                    "date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "date_range": date_range,
                    "folder": folder_name,
                    "path": file_path
                })

    # Trier par date de modification (plus récent en premier)
    reports.sort(key=lambda x: x['date'], reverse=True)

    return reports

def extract_date_range_from_folder(folder_name):
    """Extrait les dates depuis le nom du dossier"""
    import re

    # Pattern pour matcher "reports YYYY-MM-DD to YYYY-MM-DD" ou "group reports YYYY-MM-DD to YYYY-MM-DD"
    pattern = r'(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, folder_name)

    if match:
        from_date, to_date = match.groups()
        return {
            "from_date": from_date,
            "to_date": to_date,
            "formatted": f"Du {format_date_fr(from_date)} au {format_date_fr(to_date)}"
        }

    return None

def format_date_fr(date_str):
    """Formate une date YYYY-MM-DD en format français"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")
    except:
        return date_str

@app.get("/api/reports/download/{filename}")
def download_report(filename: str, user: str = Depends(require_auth)):
    """Télécharger un rapport PDF"""
    # Rechercher le fichier dans le dossier Reports et ses sous-dossiers
    reports_dir = "Reports"

    if not os.path.exists(reports_dir):
        raise HTTPException(status_code=404, detail="Dossier Reports non trouvé")

    # Chercher le fichier dans tous les sous-dossiers
    for root, dirs, files in os.walk(reports_dir):
        if filename in files:
            file_path = os.path.join(root, filename)
            if os.path.exists(file_path):
                return FileResponse(
                    file_path,
                    media_type="application/pdf",
                    filename=filename,
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )

    raise HTTPException(status_code=404, detail="Rapport non trouvé")

@app.get("/api/reports/preview/{filename}")
def preview_report(filename: str, user: str = Depends(require_auth)):
    """Prévisualiser un rapport PDF dans le navigateur"""
    # Rechercher le fichier dans le dossier Reports et ses sous-dossiers
    reports_dir = "Reports"

    if not os.path.exists(reports_dir):
        raise HTTPException(status_code=404, detail="Dossier Reports non trouvé")

    # Chercher le fichier dans tous les sous-dossiers
    for root, dirs, files in os.walk(reports_dir):
        if filename in files:
            file_path = os.path.join(root, filename)
            if os.path.exists(file_path):
                return FileResponse(
                    file_path,
                    media_type="application/pdf",
                    headers={"Content-Disposition": "inline"}
                )

    raise HTTPException(status_code=404, detail="Rapport non trouvé")

@app.delete("/api/reports/{filename}")
def delete_report(filename: str, user: str = Depends(require_auth)):
    """Supprimer un rapport PDF"""
    reports_dir = "Reports"

    if not os.path.exists(reports_dir):
        raise HTTPException(status_code=404, detail="Dossier Reports non trouvé")

    # Chercher le fichier dans tous les sous-dossiers
    for root, dirs, files in os.walk(reports_dir):
        if filename in files:
            file_path = os.path.join(root, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    return {"message": f"Rapport {filename} supprimé avec succès"}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

    raise HTTPException(status_code=404, detail="Rapport non trouvé")

@app.post("/api/reports/download-multiple")
async def download_multiple_reports(request: Request, user: str = Depends(require_auth)):
    """Télécharger plusieurs rapports dans une archive ZIP"""
    try:
        # Récupérer la liste des fichiers depuis le body de la requête
        body = await request.json()
        filenames = body.get("filenames", [])

        if not filenames:
            raise HTTPException(status_code=400, detail="Aucun fichier spécifié")

        reports_dir = "Reports"
        if not os.path.exists(reports_dir):
            raise HTTPException(status_code=404, detail="Dossier Reports non trouvé")

        # Créer un fichier temporaire pour l'archive ZIP
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_zip_path = temp_file.name

        # Créer l'archive ZIP
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            files_added = 0

            for filename in filenames:
                # Chercher le fichier dans tous les sous-dossiers
                file_found = False
                for root, dirs, files in os.walk(reports_dir):
                    if filename in files:
                        file_path = os.path.join(root, filename)
                        if os.path.exists(file_path):
                            # Ajouter le fichier au ZIP avec juste son nom (sans chemin)
                            zip_file.write(file_path, filename)
                            files_added += 1
                            file_found = True
                            break

                if not file_found:
                    logger.warning(f"Fichier non trouvé: {filename}")

        if files_added == 0:
            # Nettoyer le fichier temporaire
            os.unlink(temp_zip_path)
            raise HTTPException(status_code=404, detail="Aucun fichier trouvé")

        # Créer un nom pour l'archive basé sur la date
        archive_name = f"rapports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        # Retourner le fichier ZIP
        return FileResponse(
            temp_zip_path,
            media_type="application/zip",
            filename=archive_name,
            headers={"Content-Disposition": f"attachment; filename={archive_name}"},
            background=lambda: os.unlink(temp_zip_path)  # Nettoyer après envoi
        )

    except Exception as e:
        logger.error(f"Erreur lors de la création de l'archive: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de l'archive: {str(e)}")