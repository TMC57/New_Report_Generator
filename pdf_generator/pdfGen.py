from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle,
    BaseDocTemplate,
    PageTemplate,
    Frame,
    FrameBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from PIL import Image as PILImage

import matplotlib
matplotlib.use("Agg")

import os
import re
import warnings
import json

from tables import generate_table, generate_monthly_table
from BarCharts import generate_bar_chart
from PieCharts import generate_pie_chart_and_legend

import tempfile




def get_footer_table(facility_id, config_data):
    """
    Retourne un tableau de 3 colonnes à insérer en bas de page.
    Le contenu est du texte sélectionnable dans le PDF.
    """
    config_item = next((item for item in config_data if item["facilityId"] == facility_id), None)
    if config_item:
        facility_config = {
            "primary_company_brand": config_item.get("primary_company_brand"),
            "cover_picture": config_item.get("cover_picture"),
            "material_picture": config_item.get("material_picture"),
            "inventory_monitoring_manager": config_item.get("inventory_monitoring_manager", {}),
            "customer_technical_relay_manager": config_item.get("customer_technical_relay_manager", {}),
            "file_referent": config_item.get("file_referent", {}),
        }
    else:
        facility_config = {}  # ou un dict par défaut

    customer_manager = facility_config.get("customer_technical_relay_manager", {})
    inventory_manager = facility_config.get("inventory_monitoring_manager", {})
    file_referent = facility_config.get("file_referent", {})


    # print(f"\nvoici le nom du mail : {mail}\n")


    def make_email_link(email):
        if email and email != "N/A":
            return f'<font color="blue"><u><a href="mailto:{email}">{email}</a></u></font>'
        return "N/A"

    def make_email_link(email):
        if email and email != "N/A":
            return f'<font color="blue"><u><a href="mailto:{email}">{email}</a></u></font>'
        return "N/A"
    
    centered_style = ParagraphStyle(name="centered_style", alignment=TA_CENTER, fontSize=10)

    data = [
        [
            Paragraph(
                f"Responsable suivi des stocks<br/>Würth<br/>"
                f"<b>{inventory_manager.get('full_name', 'N/A')}</b><br/>"
                f"{make_email_link(inventory_manager.get('mail_adresse', 'N/A'))}<br/>"
                f"<b>{inventory_manager.get('phone_number', 'N/A')}</b>",
                centered_style
            ),
            Paragraph(
                f"Responsable relais technique<br/>client<br/>"
                f"<b>{customer_manager.get('full_name', 'N/A')}</b><br/>"
                f"{make_email_link(customer_manager.get('mail_adresse', 'N/A'))}<br/>"
                f"<b>{customer_manager.get('phone_number', 'N/A')}</b>",
                centered_style
            ),
            Paragraph(
                f"Référent dossier Würth<br/>"
                f"<b>{file_referent.get('full_name', 'N/A')}</b><br/>"
                f"{make_email_link(file_referent.get('mail_adresse', 'N/A'))}<br/>"
                f"<b>{file_referent.get('phone_number', 'N/A')}</b>",
                centered_style 
            )
        ]
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

def get_picture_path(facility_id, config_data, picture_name):
    config_item = next((item for item in config_data if item["facilityId"] == facility_id), None)
    picture_path = config_item[picture_name] if config_item else "images/full.png"
    if picture_path == "":
        picture_path = "images/upload-error.png"
    # picture_path = picture_path.replace("\\", "/")
    if picture_path.startswith("/"):
        picture_path = picture_path[1:]
    with PILImage.open(picture_path) as img:
        original_width, original_height = img.size

    ratio = original_width / original_height

    max_width = 20*cm
    max_height = 11*cm    

    if max_width / max_height > ratio:
    # Limite hauteur
        final_height = max_height
        final_width = max_height * ratio
    else:
        # Limite largeur
        final_width = max_width
        final_height = max_width / ratio

    return picture_path, final_width, final_height
    

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

def defineRouterNbr(devices_list):
    devices_nbr = 0
    for facility in devices_list['data']:
        devices_nbr += len(facility['devices'])
    return devices_nbr

def get_serial_numbers(devices_list):
    serial_numbers = []
    for facility in devices_list['data']:
        for device in facility['devices']:
            serial_numbers.append(device['serialNumber'])
    return serial_numbers

def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def page_manager(**kwargs):
    pages = {
        1: [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 1*cm), kwargs.get("report_title"), Spacer(1, 0.2*cm), kwargs.get("facility_title"), Spacer(1, 0.5*cm), kwargs.get("cover_picture")],
        2: [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 1*cm), kwargs.get("page_2_title"), Spacer(1, 0.5*cm), kwargs.get("image_text_table")],
        3: [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 2*cm), kwargs.get("bar_chart_title"), Spacer(1, 0.3*cm), kwargs.get("bar_chart")],
        4: [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 2*cm), kwargs.get("bar_chart_title"), Spacer(1, 0.3*cm), kwargs.get("bar_chart")],
        5: [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 2*cm), kwargs.get("pie_chart_title"), Spacer(1, 0.3*cm), kwargs.get("pie_chart_img"), Spacer(1, 0.2*cm), kwargs.get("legend_img")],
        6: [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 3*cm)] + kwargs.get("tables"),
        7: [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 3*cm)] + kwargs.get("tables_year"),
    }
    page_number = 3
    for i in range(kwargs.get("RouterNbr")):
        pages[page_number] = [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 0.5*cm), kwargs.get("bar_chart_title"), Spacer(1, 0.5*cm), kwargs.get("bar_chart")]
        pages[page_number + 1] = [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 0.5*cm), kwargs.get("pie_chart_title"), Spacer(1, 0.2*cm), kwargs.get("pie_chart_img"), Spacer(1, 0.2*cm), kwargs.get("legend_img")]
        pages[page_number + 2] = [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 0.5*cm)] + kwargs.get("tables")
        pages[page_number + 2] = [Spacer(1, 0.1*cm), kwargs.get("TMH_logo_img"), Spacer(1, 0.5*cm)] + kwargs.get("tables_year")
        page_number += 4
    return pages

def draw_bottom_right_logo(canvas, doc):
    logo_path = "images/Würth_logo.png"
    logo = ImageReader(logo_path)

    logo_width = 4.688644688644689*cm
    logo_height = 1*cm

    page_width, page_height = doc.pagesize
    x = page_width - logo_width - 0.8*cm
    y = 1 * cm

    canvas.drawImage(logo, x, y, logo_width, logo_height, preserveAspectRatio=True, mask='auto')

def generate_pdfs_by_facility(json_data: dict, devices_list, from_date: str, to_date: str):

    os.makedirs("reports", exist_ok=True)


    RouterNbr = defineRouterNbr(devices_list)

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    subtitle_style = styles["Heading2"]
    normal_style = styles["Normal"]

    with open("configJson.json", "r", encoding="utf-8") as f:
        config_data = json.load(f)

    for facility in json_data["data"]["results"]:
        facility_id = facility["facilityId"]
        sanitized_name = sanitize_filename(facility["facilityName"])
        pdf_path = f"reports/rapport_{sanitized_name}_{facility_id}.pdf"


        # Crée les composants (exemple)
        facility_title = Paragraph(facility["facilityName"], title_style)
        report_title = Paragraph(f"RAPPORT DE CONSOMMATION DU {from_date} AU {to_date}", title_style)
        page_2_title = Paragraph(f"DILUTION DES PRODUITS AU {from_date} ", title_style)
        bar_chart_title = Paragraph(f"CONSOMMATION MENSUELLE DE PRODUITS - ZONE X", title_style)
        pie_chart_title = Paragraph(f"CONSOMMATION MOYENNE QUOTIDIENNE QXXXXX", title_style)

        cover_picture_path, final_width, final_height = get_picture_path(facility_id, config_data, "cover_picture")
        material_picture_path,final_width, final_height = get_picture_path(facility_id, config_data, "material_picture")

        cover_picture = Image(cover_picture_path, final_width, final_height)
        material_picture = Image(material_picture_path, final_width, final_height)

        material_picture_left = Table([[material_picture]], hAlign='LEFT')
        texte_droite = Table([[Paragraph("• PRESSION D’EAU RELEVÉ :<br/> 3,1 BARS<br/><br/>• WNC: 3,9%<br/>Buse Jaune", subtitle_style)]], hAlign='RIGHT')

        row = [material_picture_left, texte_droite]
        image_text_table = Table([row], colWidths=[8*cm, 12*cm])  # ajuste les largeurs

        image_text_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), 
            ("ALIGN", (1, 0), (1, 0), "LEFT"),  
            ("LEFTPADDING", (1, 0), (1, 0), 150),  # 👈 espace entre l'image et le texte
            ("RIGHTPADDING", (1, 0), (1, 0), 0),    
        ]))


        bar_chart = Image(generate_bar_chart(facility, RouterNbr, from_date, to_date), width=25*cm, height=12*cm)
        buf_pie, buf_legend = generate_pie_chart_and_legend(facility, from_date, to_date)

        # Sauvegarder en fichiers temporaires
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_pie, tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_leg:

            f_pie.write(buf_pie.getbuffer())
            f_pie.flush()

            f_leg.write(buf_legend.getbuffer())
            f_leg.flush()

            # Créer les images reportlab
            pie_chart_img = Image(f_pie.name, width=9*cm, height=9*cm)
            legend_img = Image(f_leg.name, width=15*cm, height=2.5*cm)

        tables = generate_table(facility, from_date, to_date)  # liste de tableaux
        tables_year = generate_monthly_table(facility)  # liste de tableaux

        TMH_logo_path = "images/Logo - Orsy e wash.png"
        TMH_logo_img = Image(TMH_logo_path, width=26.43/2.5*cm, height=4/2.5*cm)

        pages = page_manager(TMH_logo_img=TMH_logo_img,report_title=report_title, facility_title=facility_title, cover_picture=cover_picture,
                            page_2_title=page_2_title, image_text_table=image_text_table, bar_chart_title=bar_chart_title,
                            bar_chart=bar_chart, pie_chart_title=pie_chart_title, pie_chart_img=pie_chart_img, legend_img=legend_img,
                            tables=tables, tables_year=tables_year, RouterNbr=RouterNbr)

        # Maintenant on ajoute le footer (tableau) dans chaque page où on veut le footer
        # Pour l’exemple, je vais juste l’ajouter sur toutes les pages générées :
        for key in pages:
            pages[key].append(FrameBreak())        # Basculer dans la frame footer
            pages[key].append(get_footer_table(facility_id, config_data))  # Ton tableau footer

        elements = distribute_elements_by_page(pages)

        # Création du BaseDocTemplate avec 2 frames
        PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
        main_frame = Frame(2*cm, 3*cm, PAGE_WIDTH - 3*cm, PAGE_HEIGHT - 3*cm, id='main_frame')
        footer_frame = Frame(2*cm, -0.2*cm, PAGE_WIDTH - 3*cm, 3*cm, id='footer_frame')
        page_template = PageTemplate(id='TwoFrames', frames=[main_frame, footer_frame], onPage=draw_bottom_right_logo)

        doc = BaseDocTemplate(
            pdf_path,
            pagesize=landscape(A4),
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=0.5*cm,
            bottomMargin=0                                                                      
        )
        doc.addPageTemplates([page_template])
        doc.build(elements)

    print("PDFs générés dans le dossier 'reports/'")
    return 0
