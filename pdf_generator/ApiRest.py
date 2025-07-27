from typing import Optional
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pdfGen import generate_pdfs_by_facility
from model import model, body_total_qty_report
from app import get_total_qty_every_days, get_total_qty_every_month
import logging
from datetime import datetime, timedelta
from Json_parameter import transform_facility_json
import os
import shutil
import json
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List

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

@app.get("/")
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

    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
    to_date_plus_one = to_date_obj.strftime("%Y-%m-%d")

    endpoint, headers, params =  body_total_qty_report(from_date, to_date_plus_one, facility_id)    
    response = model(endpoint, headers, params)

    # ================= Data Transformation ================
    NewJson = get_total_qty_every_days(response.json(), from_date, to_date, facility_id)
    NewJson = get_total_qty_every_month(NewJson, to_date, facility_id)
    # ======================================================

    transform_facility_json(NewJson)

    generate_pdfs_by_facility(NewJson, from_date, to_date)


    # create_pdf(response.text)

    return {"ok"} 


from fastapi import UploadFile, File

DATA_FILE = "configJson.json"  # Ton fichier JSON

# --- Static files (HTML) + uploads (images) ---
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/items")
def get_items():
    """Retourne le contenu du JSON."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.put("/items")
def save_items(items: List[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return {"saved": len(items)}

# --- Upload ---
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    dst_path = os.path.join("uploads", file.filename)
    with open(dst_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # On retourne un chemin web-accessible pour l'afficher directement (<img src="/uploads/...">)
    return {"path": f"/uploads/{file.filename}"}