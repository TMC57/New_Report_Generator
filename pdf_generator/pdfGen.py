from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors

import matplotlib
matplotlib.use("Agg")
import os   
import re
from tables import generate_table
from BarCharts import generate_bar_chart
from PieCharts import generate_pie_chart


def get_footer_table():
    """
    Retourne un tableau de 3 colonnes à insérer en bas de page.
    Le contenu est du texte sélectionnable dans le PDF.
    """
    data = [
        ["Responsable suivi des stocks\nWürth\nSylvestre Wodi\nWodi.Sylvestre@wurth.fr\n06 86 38 50 20",
         "Responsable relais technique\nclient\nMaman Adrien\namaman@citroencorbeil.fr",
         "Référent dossier Würth\nDavid Darfeuille\ndavid.darfeuille@wurth.fr\n06 17 15 71 49"]
    ]

    col_widths = [6 * cm, 6 * cm, 6 * cm]

    style = TableStyle([
        # Alignement et style global
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),

        # Bordure gauche de "Texte 2"
        ("LINEBEFORE", (1, 0), (1, 0), 0.5, colors.black),
        # Bordure droite de "Texte 2"
        ("LINEAFTER", (1, 0), (1, 0), 0.5, colors.black),
    ])

    table = Table(data, colWidths=col_widths)
    table.setStyle(style)

    return table

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
        facility_title = Paragraph(facility_name, title_style)
        report_title = Paragraph(f"RAPPORT DE CONSOMMATION DU {from_date} AU {to_date}", title_style)

        bar_chart = Image(generate_bar_chart(facility, ZoneNbr, from_date, to_date), width=22*cm, height=12*cm)
        pie_chart = Image(generate_pie_chart(facility, from_date, to_date), width=14*cm, height=14*cm)

        tables = generate_table(facility, from_date, to_date)  # liste de 1 ou 2 tableaux

        TMH_logo_path = "images/Logo - Orsy e wash.png"
        TMH_logo_img = Image(TMH_logo_path, width=26.43/2.5*cm, height=4/2.5*cm)  # ajuste les dimensions si nécessaire

        # WURTH_logo_path = "images/Würth_logo.png"
        # WURTH_logo_img = Image(WURTH_logo_path, width=14.06593406593407*cm, height=3*cm)  # ajuste les dimensions si nécessaire

        # Page planning
        pages = {
            1: [TMH_logo_img, Spacer(1, 0.5*cm), report_title, Spacer(1, 0.2*cm), facility_title, Spacer(1, 0.5*cm), bar_chart],
            2: [TMH_logo_img, Spacer(1, 0.5*cm), facility_title, Spacer(1, 3*cm), bar_chart],
            3: [TMH_logo_img, Spacer(1, 0.5*cm), facility_title, Spacer(1, 1*cm), pie_chart],
            4: [TMH_logo_img, Spacer(1, 0.5*cm), facility_title, Spacer(1, 1*cm)] + tables + [Spacer(1, 0.5 * cm)],  # tous les tableaux sur une seule page
        }

        # Générer les blocs à partir de la page 2
        page_number = 2
        for i in range(ZoneNbr):
            pages[page_number] = [TMH_logo_img, Spacer(1, 0.5*cm), facility_title, Spacer(1, 3*cm), bar_chart, Spacer(1, 0.5*cm), get_footer_table()]
            pages[page_number + 1] = [TMH_logo_img, Spacer(1, 0.5*cm), facility_title, Spacer(1, 1*cm), pie_chart]
            pages[page_number + 2] = [TMH_logo_img, Spacer(1, 0.5*cm), facility_title, Spacer(1, 2*cm)] + tables + [Spacer(1, 0.5*cm)]
            page_number += 3

        elements = distribute_elements_by_page(pages)

        # Crée le PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(A4),
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=0.5*cm,
            bottomMargin=0  # Aucune marge en bas
        )

        def draw_bottom_right_logo(canvas, doc):
            logo_path = "images/Würth_logo.png"
            logo = ImageReader(logo_path)

            logo_width = 4.688644688644689*cm
            logo_height = 1*cm

            page_width, page_height = doc.pagesize
            x = page_width - logo_width - 0.8*cm  # marge de la droite
            y = 1 * cm  # marge dud bas

            canvas.drawImage(logo, x, y, logo_width, logo_height, preserveAspectRatio=True, mask='auto')


        doc.build(elements, onFirstPage=draw_bottom_right_logo, onLaterPages=draw_bottom_right_logo)

    print("PDFs générés dans le dossier 'reports/'")
    return 0
