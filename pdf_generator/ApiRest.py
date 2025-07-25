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

    generate_pdfs_by_facility(NewJson, from_date, to_date)

    # print(transform_facility_json(NewJson))

    # create_pdf(response.text)

    return {"ok"} 


@app.get("/total_list_of_facilities", tags=["Rapports"])
def total_list_of_facilities(
    pageNumber: int,
    pageSize: int,
    from_date: str,
    to_date: str,
    facility_id: Optional[int] = None,
    DeviceId: Optional[int] = None
):
    """
    TEST
    """
    
    return {"ok"}



# Crée le dossier 'uploads' s'il n'existe pas
os.makedirs("uploads", exist_ok=True)

# Crée le dossier 'static' s'il n'existe pas (pour la page HTML)
os.makedirs("static", exist_ok=True)

# Monter les fichiers statiques (HTML, CSS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/upload-image", tags=["Upload"])
async def upload_image(file: UploadFile = File(...)):
    upload_dir = "uploads"
    file_location = os.path.join(upload_dir, file.filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename}


@app.get("/dragdrop", response_class=HTMLResponse, include_in_schema=False)
def drag_drop_page():
    with open("static/dragdrop.html", "r", encoding="utf-8") as f:
        return f.read()