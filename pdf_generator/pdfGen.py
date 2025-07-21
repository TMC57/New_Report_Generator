from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import landscape, A4

import matplotlib
matplotlib.use("Agg")
import os
import re
from tables import generate_table
from BarCharts import generate_bar_chart
from PieCharts import generate_pie_chart


def distribute_elements_by_page(pages_dict: dict[int, list]):
    """
    Distribue les éléments sur les pages spécifiées dans pages_dict.
    Exemple : {1: [titre], 2: [graphique]} → met les éléments à la bonne page avec les PageBreak nécessaires.
    """
    final_elements = []
    current_page = 1
    sorted_pages = sorted(pages_dict.keys())

    for i, target_page in enumerate(sorted_pages):
        # Ajoute des pages vides si on saute des numéros
        while current_page < target_page:
            final_elements.append(PageBreak())
            current_page += 1

        # Ajoute les éléments de la page
        final_elements.extend(pages_dict[target_page])
        
        # Si ce n’est pas la dernière page, ajoute un saut
        if i < len(sorted_pages) - 1:
            final_elements.append(PageBreak())
        
        current_page += 1

    return final_elements

def defineNbrZone(FacilityData):

    zone_set = set()
    
    for product in FacilityData.get("products", []):
        name = product.get("name", "")
        match = re.search(r'\bZone\s*(\d+)', name, re.IGNORECASE)
        if match:
            zone_number = match.group(1)
            zone_set.add(zone_number)
    return len(zone_set)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def generate_pdfs_by_facility(json_data: dict, from_date: str, to_date: str):
    """
    Génère un PDF par facilityId dans le dossier 'reports/'.
    Affiche en titre le nom de la facility, la période et insère un graphique + un tableau.
    """
    os.makedirs("reports", exist_ok=True)
    os.makedirs("pictures", exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    subtitle_style = styles["Heading2"]
    normal_style = styles["Normal"]

    for facility in json_data["data"]["results"]:
        facility_name = facility["facilityName"]
        facility_id = facility["facilityId"]
        sanitized_name = sanitize_filename(facility_name)
        pdf_path = f"reports/rapport_{sanitized_name}_{facility_id}.pdf"


        ZoneNbr = defineNbrZone(facility)


        # Crée les composants
        title = Paragraph(facility_name, title_style)
        subtitle = Paragraph(f"RAPPORT DU {from_date} AU {to_date}", title_style)

        bar_chart = Image(generate_bar_chart(facility, from_date, to_date), width=22*cm, height=12*cm)
        pie_chart = Image(generate_pie_chart(facility, from_date, to_date), width=14*cm, height=14*cm)

        tables = generate_table(facility, from_date, to_date)  # liste de 1 ou 2 tableaux

        # Page planning
        pages = {
            1: [title, Spacer(1, 0.5*cm), subtitle, Spacer(1, 0.5*cm), bar_chart],
            2: [title, Spacer(1, 3*cm), bar_chart],
            3: [title, Spacer(1, 1*cm), pie_chart],
            4: [title, Spacer(1, 2*cm)] + tables + [Spacer(1, 0.5 * cm)],  # tous les tableaux sur une seule page
        }

        # Générer les blocs à partir de la page 2
        page_number = 2
        for i in range(ZoneNbr):
            pages[page_number] = [title, Spacer(1, 3*cm), bar_chart]
            pages[page_number + 1] = [title, Spacer(1, 1*cm), pie_chart]
            pages[page_number + 2] = [title, Spacer(1, 2*cm)] + tables + [Spacer(1, 0.5*cm)]
            page_number += 3

        elements = distribute_elements_by_page(pages)

        # Crée le PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(A4),
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        doc.build(elements)

    print("PDFs générés dans le dossier 'reports/'")
    return 0
