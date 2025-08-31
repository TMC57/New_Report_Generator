import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from model import model, body_total_qty_report, body_devices_list, body_stock_levels
from DataTransform import get_total_qty_every_days, get_total_qty_every_month, enrich_json_with_zone, group_qty_by_owner_and_facility, enrich_qty_with_stock_products
from pdfGen import generate_pdfs_by_facility
from Json_parameter import transform_facility_json
from group_parameter import build_group_config_from_devices_list


GROUP_FILE = "GroupConfigJson.json"

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

# @app.get("/", tags=["Raports"])
# def read_root():
#     return {"message": "API opérationnelle"}

@app.get("/", include_in_schema=False)
def get_home():
    return FileResponse("static/table.html")

@app.get("/Reports_generation", tags=["Rapports"])
def  Total_Quantity_Report_grouped_by_facilities(
    # pageNumber: int,
    # pageSize: int,
    from_date: str,
    to_date: str,
    facility_id: Optional[int] = None,  
    # DeviceId: Optional[int] = None
):
    """
    Endpoint GET /report qui retourne des données de rapport.
    Les dates sont en format 'YYYY-MM-DD'.
    """ 

    endpoint, headers, params = body_devices_list(facility_id)
    devices_list = model(endpoint, headers, params).json()

    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
    to_date_plus_one = to_date_obj.strftime("%Y-%m-%d")

    endpoint, headers, params =  body_total_qty_report(from_date, to_date_plus_one, facility_id) 
    total_qty = model(endpoint, headers, params)

    agg = group_qty_by_owner_and_facility(total_qty.json(), devices_list)

    # Exemple: afficher le total par owner
    for o in agg["owners"]:
        print(o["owner"], "→", o["totalQty"])

    build_group_config_from_devices_list(devices_list)

    endpoint, headers, params = body_stock_levels(facility_id)
    stock_levels = model(endpoint, headers, params).json()
    # # ================= Data Transformation ================
    total_qty_Json = get_total_qty_every_days(total_qty.json(), from_date, to_date, facility_id)
    total_qty_Json = get_total_qty_every_month(total_qty_Json, to_date, facility_id)


    # ici

    total_qty_Json = enrich_qty_with_stock_products(total_qty_Json, stock_levels)

    print(stock_levels)

    total_qty_Json = enrich_json_with_zone(total_qty_Json)

    # # ======================================================
    transform_facility_json(devices_list)
    generate_pdfs_by_facility(total_qty_Json, devices_list, stock_levels, from_date, to_date)


    return {"ok"}

DATA_FILE = "configJson.json"  # Ton fichier JSON

# --- Static files (HTML) + uploads (images) ---
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/items", include_in_schema=False)
def get_items():
    """Retourne le contenu du JSON."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.put("/items", include_in_schema=False)
def save_items(items: List[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return {"saved": len(items)}

# --- Upload ---
@app.post("/upload", include_in_schema=False)
async def upload(file: UploadFile = File(...)):
    dst_path = os.path.join("uploads", file.filename)
    with open(dst_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # On retourne un chemin web-accessible pour l'afficher directement (<img src="/uploads/...">)
    return {"path": f"/uploads/{file.filename}"}


@app.get("/group-items", include_in_schema=False)
def get_group_items():
    if not os.path.exists(GROUP_FILE):
        return []
    with open(GROUP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.put("/group-items", include_in_schema=False)
def save_group_items(items: list[dict]):
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return {"saved": len(items)}

# Page web d’édition des groupes
@app.get("/group-app", include_in_schema=False)
def group_app():
    return FileResponse("static/group_table.html")