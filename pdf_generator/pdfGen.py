from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os
import re
import matplotlib   
matplotlib.use("Agg")   
from reportlab.lib.utils import ImageReader

from tables    import generate_table_chart
from BarCharts import generate_bar_chart
from PieCharts import generate_pie_chart




def sanitize_filename(name: str) -> str:
    # Supprime les caractères interdits dans les noms de fichiers Windows
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def generate_pdfs_by_facility(json_data: dict, from_date: str, to_date: str):

    """
    Génère un PDF par facilityId dans le dossier 'reports/'.
    Affiche en titre le nom de la facility, la période et insère un graphique.
    """
    os.makedirs("reports", exist_ok=True)   

    for facility in json_data["data"]["results"]:
        facility_name = facility["facilityName"]
        facility_id = facility["facilityId"]

        sanitized_name = sanitize_filename(facility_name)
        pdf_path = f"reports/rapport_{sanitized_name}_{facility_id}.pdf"

        # Créer le PDF
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4

        # Titre
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 3 * cm, facility_name)

        # Sous-titre
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, height - 4 * cm, f"RAPPORT DE CONSOMMATION DU {from_date} AU {to_date}")

        # ================= Générer le graphique ===============================

        bar_chart_buffer = generate_bar_chart(facility, from_date, to_date)
        image = ImageReader(bar_chart_buffer)

        image_width = width - 4 * cm
        iw, ih = image.getSize()
        aspect = ih / iw
        image_height = image_width * aspect

        c.drawImage(
                image,
                x=2 * cm,
                y=height - 4 * cm - image_height - 1 * cm,  # En dessous du sous-titre
                width=image_width,
                height=image_height
        )

        # ================= Générer le camembert ===============================

        pie_chart_buffer = generate_pie_chart(facility, from_date, to_date)
        image = ImageReader(pie_chart_buffer)

        # Affiche l'image centrée
        img_width = 400
        img_height = 400
        x = (width - img_width) / 2
        y = height - 800  # Position verticale ajustable

        c.drawImage(image, x, y, width=img_width, height=img_height)

        # ================= Générer le tableau ===============================

        table_consumption_month = generate_table_chart(facility, from_date, to_date)
        image = ImageReader(table_consumption_month)

                # Affiche l'image centrée
        img_width = 300
        img_height = 300
        x = (width - img_width) / 2
        y = height - 500  # Position verticale ajustable

        c.drawImage(image, 50   , y, width=500, height=100)

        c.showPage()
        c.save()

    print("PDFs générés dans le dossier 'reports/'")
    return(0)