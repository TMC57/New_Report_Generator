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
import json
from datetime import datetime, timedelta


from tables import generate_table, generate_monthly_table
from BarCharts import generate_bar_chart
from PieCharts import generate_pie_chart_and_legend
from getDebit import login_session_cm2w, get_events

import copy


def _img(buf, w, h):
    if buf is None:
        return Paragraph("Aucun graphique disponible")
    try:
        buf.seek(0)
    except Exception:
        pass
    return Image(buf, width=w, height=h)


def _split_products_by_eau(facility: dict):
    """
    Retourne (eau_products, other_products) selon la présence de 'EAU' (insensible à la casse)
    dans le champ 'name'. Chaque produit est classé dans un seul des deux groupes.
    """
    prods = facility.get("products", [])
    eau, autres = [], []
    for p in prods:
        name = (p.get("name") or "")
        if "EAU" in name.upper():
            eau.append(p)
        else:
            autres.append(p)
    return eau, autres


def _natural_zone_key(z: str):
    m = re.search(r'(\d+)', z or "")
    return (int(m.group(1)) if m else 0, z or "")

def _detect_zones_for_facility(facility: dict) -> list[str]:
    # Priorité au champ JSON 'zone'
    explicit = {
        (p.get("zone") or "").strip().upper()
        for p in facility.get("products", [])
        if p.get("zone")
    }
    if explicit:
        return sorted(explicit, key=_natural_zone_key)
    # fallback compat : pas de zone -> une seule page "GLOBAL"
    return ["GLOBAL"]

def filter_facility_by_zone(facility: dict, zone: str) -> dict:
    """Retourne une copie de la facility avec uniquement les produits de la zone donnée.
       - 'GLOBAL' => TOUS les produits (pas seulement ceux sans zone)."""
    z = (zone or "GLOBAL").strip().upper()
    new_fac = copy.deepcopy(facility)

    if z == "GLOBAL":
        new_fac["products"] = facility.get("products", [])
    else:
        new_fac["products"] = [
            p for p in facility.get("products", [])
            if (p.get("zone") or "").strip().upper() == z
        ]
    return new_fac


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

def draw_bottom_right_logo(canvas, doc):
    logo_path = "images/Würth_logo.png"
    logo = ImageReader(logo_path)

    logo_width = 4.688644688644689*cm
    logo_height = 1*cm

    page_width, page_height = doc.pagesize
    x = page_width - logo_width - 0.8*cm
    y = 1 * cm

    canvas.drawImage(logo, x, y, logo_width, logo_height, preserveAspectRatio=True, mask='auto')


def get_serial_numbers_for_facility(devices_list, facility_id):
    serials = [
        dev["serialNumber"]
        for site in devices_list.get("data", [])
        if site.get("facilityId") == facility_id
        for dev in site.get("devices", [])
        if "serialNumber" in dev
    ]
    return list(dict.fromkeys(serials))  # supprime les doublons, préserve l’ordre

def get_deviceID_for_facility(devices_list, facility_id):
    serials = [
        dev["deviceId"]
        for site in devices_list.get("data", [])
        if site.get("facilityId") == facility_id
        for dev in site.get("devices", [])
        if "deviceId" in dev
    ]
    return list(dict.fromkeys(serials))  # supprime les doublons, préserve l’ordre

def _normalize_name(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().upper()


def build_stock_table_for_facility_zone(facility_id: int, fac_z: dict, stock_levels: dict):
    """Construit un tableau ReportLab des stocks pour les produits présents dans fac_z (rouge si stock <= 0)."""
    data_root = (stock_levels or {}).get("data", [])
    facility_entry = next((x for x in data_root if x.get("facilityId") == facility_id), None)
    if not facility_entry:
        return Paragraph("Aucun stock disponible pour ce site.", getSampleStyleSheet()["Normal"])

    fac_products = fac_z.get("products", [])
    names_in_table = {_normalize_name(p.get("name")) for p in fac_products}
    stock_products = facility_entry.get("products", [])

    rows = []
    for sp in stock_products:
        pname = sp.get("productName")
        if _normalize_name(pname) in names_in_table:
            remaining = sp.get("remainingQuantity", "")
            avg = sp.get("averageDailyConsumption", "")
            days = sp.get("remainingDays", "")
            rows.append([pname or "", remaining, avg, days])

    if not rows:
        return Paragraph("Aucun stock correspondant aux produits du tableau.", getSampleStyleSheet()["Normal"])

    data_tbl = [["Produit", "Stock restant", "Conso/jour moy.", "Jours restants"]] + rows
    tbl = Table(data_tbl, repeatRows=1, colWidths=[9*cm, 4*cm, 4*cm, 3*cm])

    style_cmds = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    # Colorer en rouge chaque "Stock restant" <= 0 (colonne 1)
    for i, row in enumerate(rows, start=1):  # +1 car il y a l'en-tête
        val = str(row[1])
        try:
            # retirer " L", espaces, etc.
            num = float(val.replace("L", "").replace(" ", "").replace(",", "."))
            if num <= 0:
                style_cmds.append(('TEXTCOLOR', (1, i), (1, i), colors.red))
        except Exception as e:
            pass  # si ça ne se convertit pas → on ignore


    tbl.setStyle(TableStyle(style_cmds))
    return tbl




def generate_pdfs_by_facility(json_data: dict, devices_list, stock_levels, from_date: str, to_date: str):
    print(stock_levels['currentTime'])

    os.makedirs("reports", exist_ok=True)

    # session, token = login_session_cm2w()
    # events = get_events(session, device_id=56753, from_ms=1751320800000, thru_ms=1753912800000)
    # print(events)

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

        serial_numbers = get_serial_numbers_for_facility(devices_list, facility_id)
        devices_serial_numbers = Paragraph(f"N°ROUTEUR(S): " + " / ".join(serial_numbers), title_style)


        get_deviceID_for_facility



        # 🔹 Détection simplifiée via champ JSON 'zone'
        zones_to_process = _detect_zones_for_facility(facility)
        print(f"{facility['facilityName']} → zones : {zones_to_process}")
        # is_global_only = (len(zones_to_process) == 1 and zones_to_process[0].upper() == "GLOBAL")


        # --- Création des composants communs (inchangé) ---
        facility_title = Paragraph(facility["facilityName"], title_style)
        report_title = Paragraph(f"RAPPORT DE CONSOMMATION DU {from_date} AU {to_date}", title_style)
        page_2_title = Paragraph(f"DILUTION DES PRODUITS AU {from_date} ", title_style)

        cover_picture_path, final_width, final_height = get_picture_path(facility_id, config_data, "cover_picture")
        material_picture_path,final_width, final_height = get_picture_path(facility_id, config_data, "material_picture")

        cover_picture = Image(cover_picture_path, final_width, final_height)
        material_picture = Image(material_picture_path, final_width, final_height)

        TMH_logo_path = "images/Logo - Orsy e wash.png"
        TMH_logo_img = Image(TMH_logo_path, width=26.43/2.5*cm, height=4/2.5*cm)

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

        # dictionnaire des pages
        pages = {}

        # ==================== pages fixes ====================

        pages[1] = [
            Spacer(1, 0.1*cm), TMH_logo_img, Spacer(1, 1*cm),
            report_title, Spacer(1, 0.2*cm), facility_title,
            Spacer(1, 0.2*cm), devices_serial_numbers,
            Spacer(1, 0.5*cm), cover_picture
        ]

        pages[2] = [
            Spacer(1, 0.1*cm), TMH_logo_img, Spacer(1, 1*cm),
            page_2_title, Spacer(1, 0.5*cm), image_text_table
        ]

        # ==================== pages dynamiques ====================

        current_page = 3
        for zone in zones_to_process:
            fac_z = filter_facility_by_zone(facility, zone)
            # --- BAR CHART(S) : split EAU vs hors EAU ---
            eau_products, other_products = _split_products_by_eau(fac_z)
            print(f"[DEBUG] Zone {zone} → EAU={len(eau_products)} / HORS_EAU={len(other_products)}")

            # 1) ==================== EAU uniquement si présent ====================
            if eau_products:
                fac_eau = {**fac_z, "products": eau_products}
                buf_bar_eau = generate_bar_chart(fac_eau, from_date, to_date)
                if buf_bar_eau:
                    bar_chart_img_eau = _img(buf_bar_eau, 25*cm, 12*cm)
                    pages[current_page] = [
                        Spacer(1, 0.1*cm), TMH_logo_img, Spacer(1, 2*cm),
                        Paragraph(f"CONSOMMATION MENSUELLE DE PRODUITS - {zone} (EAU)", title_style),
                        Spacer(1, 0.3*cm), bar_chart_img_eau
                    ]
                    current_page += 1

            # 2) ==================== HORS EAU uniquement si présent =================================
            if other_products:
                fac_autres = {**fac_z, "products": other_products}
                buf_bar_autres = generate_bar_chart(fac_autres, from_date, to_date)
                if buf_bar_autres:
                    bar_chart_img_autres = _img(buf_bar_autres, 25*cm, 12*cm)
                    pages[current_page] = [
                        Spacer(1, 0.1*cm), TMH_logo_img, Spacer(1, 2*cm),
                        Paragraph(f"CONSOMMATION MENSUELLE DE PRODUITS - {zone} (hors EAU)", title_style),
                        Spacer(1, 0.3*cm), bar_chart_img_autres
                    ]
                    current_page += 1

            # 3) ==================== Si aucune des deux catégories n’a de données ====================
            if not eau_products and not other_products:
                pages[current_page] = [
                    Spacer(1, 0.1*cm), TMH_logo_img, Spacer(1, 2*cm),
                    Paragraph(f"Aucune donnée pour {zone}", title_style)
                ]
                current_page += 1

            # ==================== PIE CHART + LEGEND (zone entière) ====================
            buf_pie, buf_legend = generate_pie_chart_and_legend(fac_z, from_date, to_date)
            pie_chart_img = _img(buf_pie, 9*cm, 9*cm)
            legend_img    = _img(buf_legend, 15*cm, 2.5*cm)

            pages[current_page] = [
                Spacer(1, 0.1*cm), TMH_logo_img, Spacer(1, 2*cm),
                Paragraph(f"RÉPARTITION DES CONSOMMATIONS - {zone}", title_style),
                Spacer(1, 0.3*cm), pie_chart_img, Spacer(1, 0.2*cm), legend_img
            ]
            current_page += 1

            # ==================== TABLES ====================
            tables = generate_table(fac_z, from_date, to_date)  # renvoie [table] ou [table1, table2]
            table_page_title = Paragraph(f"CONSOMMATION QUOTIDIENNE DE PRODUITS", title_style)
            pages[current_page] = [Spacer(1, 0.1*cm), TMH_logo_img, Spacer(1, 1.5*cm), table_page_title, Spacer(1, 0.5*cm)] + tables

            # ---- Titre "ÉTAT DES STOCKS AU {date}" + tableau des stocks
            stocks_title = f"ÉTAT DES STOCKS AU {datetime.fromtimestamp(int(stock_levels['currentTime']) / 1000).strftime('%d/%m/%Y')}"

            pages[current_page] += [
                Spacer(1, 0.5*cm),
                Paragraph(stocks_title, title_style),
                Spacer(1, 0.2*cm),
                build_stock_table_for_facility_zone(facility_id, fac_z, stock_levels)
            ]

            current_page += 1

            tables_year = generate_monthly_table(fac_z)
            table_month_page_title = Paragraph(f"CONSOMMATION MENSUELLE DE PRODUITS", title_style)
            pages[current_page] = [Spacer(1, 0.1*cm), TMH_logo_img, Spacer(1, 1.5*cm), table_month_page_title, Spacer(1, 1*cm)] + tables_year
            current_page += 1


        # 🔹 ==================== Ajouter le footer à chaque page ====================
        for key in pages:
            pages[key].append(FrameBreak())
            pages[key].append(get_footer_table(facility_id, config_data))

        elements = distribute_elements_by_page(pages)



        # ==================== Création du BaseDocTemplate avec 2 frames ====================
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

