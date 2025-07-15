
from typing import Optional
from fastapi import FastAPI
from pdfGen import generate_pdfs_by_facility
from bodys import body_total_qty_report
from model import model
from app import get_total_qty_every_days
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("uvicorn.error")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API opérationnelle"}

@app.get("/total-qty-report")
def  Total_Quantity_Report_grouped_by_facilities(
    pageNumber: int,
    pageSize: int,
    from_date: str,
    to_date: str,
    facility_id: Optional[int] = None,  
    DeviceId: Optional[int] = None
):
    """
    Endpoint GET /report qui retourne des données de rapport.
    Les dates sont en format 'YYYY-MM-DD'.
    """ 

    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
    to_date_plus_one = to_date_obj.strftime("%Y-%m-%d")

    endpoint, headers, params =  body_total_qty_report(from_date=from_date, to_date=to_date_plus_one)    
    response = model(endpoint, headers, params)
    NewJson = get_total_qty_every_days(response.json(), from_date, to_date)  
    generate_pdfs_by_facility(NewJson, from_date, to_date)

    # create_pdf(response.text)

    return {"ok"} 


@app.get("/total_list_of_facilities")
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
    return("OK")    