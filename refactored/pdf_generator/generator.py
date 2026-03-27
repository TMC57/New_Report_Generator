import os
from pathlib import Path
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import cm
from reportlab.lib import colors
from PIL import Image as PILImage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
import io
import re
import unicodedata
from refactored.config.settings import REPORTS_OUTPUT_DIR, REFACTORED_DIR

def normalize_product_name(name: str) -> str:
    """Normalise un nom de produit pour le matching"""
    if not name:
        return ""
    # Retirer les accents
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    # Majuscules, retirer espaces et tirets
    name = name.upper().replace(" ", "").replace("-", "")
    return name

def get_excel_product_name(api_product_name: str, facility_data: dict) -> str:
    """
    Mappe un nom de produit API vers le nom Excel correspondant
    
    Args:
        api_product_name: Nom du produit depuis l'API (ex: "WNC50 - Zone 1")
        facility_data: Données de la facility contenant les produits Excel
        
    Returns:
        Nom du produit Excel ou le nom API si pas de match
    """
    # Extraire tous les produits Excel de la facility
    excel_products = []
    
    # Produits par zone
    for zone_num in range(1, 6):
        for prod_type in ["lavant", "sechant", "jantes", "mousse"]:
            key = f"produit_{prod_type}_zone{zone_num}"
            excel_name = facility_data.get(key)
            if excel_name:
                excel_products.append((prod_type, excel_name))
    
    # Produits globaux (sans zone)
    for prod_type in ["lavant", "sechant", "jantes", "mousse"]:
        key = f"produit_{prod_type}"
        excel_name = facility_data.get(key)
        if excel_name:
            excel_products.append((prod_type, excel_name))
    
    # Normaliser le nom API
    normalized_api = normalize_product_name(api_product_name)
    
    # Chercher le meilleur match
    for prod_type, excel_name in excel_products:
        if not excel_name:
            continue
        
        normalized_excel = normalize_product_name(excel_name)
        
        # Match direct
        if normalized_api in normalized_excel:
            return excel_name
        
        # Match spécial pour autoséchant
        if prod_type == "sechant":
            if "AUTOSECHANT" in normalized_api or "SECHANT" in normalized_api:
                return excel_name
        
        # Match par numéro WNC
        api_wnc_match = re.search(r'WNC\s*(\d+)', normalized_api, re.IGNORECASE)
        excel_wnc_match = re.search(r'WNC\s*(\d+)', normalized_excel, re.IGNORECASE)
        if api_wnc_match and excel_wnc_match:
            api_wnc_num = api_wnc_match.group(1)
            excel_wnc_num = excel_wnc_match.group(1)
            if api_wnc_num == excel_wnc_num:
                # Vérifier aussi UC/ULTRACONCENTRÉ
                if "UC" in normalized_api and "ULTRACONCENTRE" in normalized_excel:
                    return excel_name
                if "UC" not in normalized_api and "ULTRACONCENTRE" not in normalized_excel:
                    return excel_name
    
    # Pas de match trouvé, retourner le nom API
    return api_product_name

class PDFGenerator:
    """Générateur de PDF utilisant ReportLab"""
    
    def __init__(self):
        self.output_dir = REPORTS_OUTPUT_DIR
        self.config_dir = REFACTORED_DIR / "config"
        self.base_dir = REFACTORED_DIR
        
    def generate_facility_report(self, facility_data: dict, from_date: str, to_date: str) -> str:
        """
        Génère un rapport PDF pour une facility
        
        Args:
            facility_data: Données complètes de la facility (depuis FacilityService)
            from_date: Date de début (YYYY-MM-DD)
            to_date: Date de fin (YYYY-MM-DD)
            
        Returns:
            Chemin du PDF généré
        """
        facility_id = facility_data.get("facility_id")
        print(f"📄 Début génération PDF pour facility {facility_id}")
        
        folder_name = f"reports {from_date} to {to_date}"
        output_dir = self.output_dir / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        client_number = facility_data.get("client_number", facility_id)
        client_name = (facility_data.get("client_name") or "Unknown").replace(" ", "_")
        
        pdf_filename = f"Rapports_de_consommation_E-wash_{client_name}_{client_number}.pdf"
        pdf_path = output_dir / pdf_filename
        
        print(f"📄 Création du PDF: {pdf_path}")
        self._create_pdf(facility_data, from_date, to_date, str(pdf_path))
        
        print(f"✅ PDF créé avec succès: {pdf_path}")
        return str(pdf_path)
    
    def _create_pdf(self, facility_data: dict, from_date: str, to_date: str, output_path: str):
        """Crée le PDF avec ReportLab"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            leftMargin=0.5*cm,
            rightMargin=0.5*cm,
            topMargin=3*cm,
            bottomMargin=0.8*cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        story.extend(self._create_cover_page(facility_data, from_date, to_date, title_style))
        
        story.append(PageBreak())
        
        story.extend(self._create_dilution_page(facility_data, styles))
        
        # Pages de débit moyen par zone
        story.extend(self._create_flowrate_pages(facility_data, from_date, to_date, styles))
        
        # Pas de PageBreak ici car le premier graphique a déjà son PageBreak
        story.extend(self._create_consumption_pages(facility_data, from_date, to_date, styles))
        
        # Tableaux zonés uniquement si plus d'une zone
        zones = facility_data.get("zones", ["GLOBAL"])
        if len(zones) > 1:
            # 1. Tableau quotidien par zone (PREMIER)
            story.extend(self._create_daily_average_by_zone_table(facility_data, from_date, to_date, styles))
            # 2. Tableau total par zone (SECOND)
            story.extend(self._create_daily_total_by_zone_table(facility_data, from_date, to_date, styles))
        # 3. Tableau quotidien global
        story.extend(self._create_daily_consumption_tables(facility_data, from_date, to_date, styles))
        # 4. Tableau mensuel unique
        story.extend(self._create_monthly_consumption_table(facility_data, from_date, to_date, styles))
        # 5. Tableau des produits livrés
        story.extend(self._create_delivered_products_table(facility_data, from_date, to_date, styles))
        
        doc.build(story, onFirstPage=self._draw_first_page, onLaterPages=self._draw_logo)
    
    def _create_cover_page(self, facility_data: dict, from_date: str, to_date: str, title_style):
        """Crée la page de garde"""
        elements = []
        
        from_date_formatted = datetime.strptime(from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        to_date_formatted = datetime.strptime(to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        client_number = facility_data.get("client_number")
        client_name = facility_data.get("client_name") or facility_data.get("facility_name") or "Unknown"
        address = facility_data.get("address") or ""
        
        if client_number:
            client_text = f"{client_number} - {client_name.upper()}"
        else:
            client_text = client_name.upper()
        
        if address:
            client_text += f" - {address.upper()}"
        
        elements.append(Spacer(1, 0.1*cm))
        
        elements.append(Paragraph(
            f"RAPPORT DE CONSOMMATION DU {from_date_formatted} AU {to_date_formatted}".upper(),
            title_style
        ))
        elements.append(Spacer(1, 0.2*cm))
        
        elements.append(Paragraph(client_text, title_style))
        elements.append(Spacer(1, 0.2*cm))
        
        serial_numbers = [d.get("serial_number", "") for d in facility_data.get("devices", [])]
        if serial_numbers:
            router_text = ("N°ROUTEUR(S): " + " / ".join(serial_numbers)).upper()
            elements.append(Paragraph(router_text, title_style))
            elements.append(Spacer(1, 0.5*cm))
        
        cover_picture_path = facility_data.get("cover_picture_path", "")
        if cover_picture_path:
            img_path = self.base_dir / cover_picture_path.lstrip("/")
            if img_path.exists():
                try:
                    # Charger l'image pour obtenir ses dimensions réelles
                    with PILImage.open(img_path) as pil_img:
                        img_width, img_height = pil_img.size
                        ratio = img_height / img_width
                    
                    # Définir la largeur maximale et calculer la hauteur proportionnelle
                    max_width = 16*cm
                    calculated_height = max_width * ratio
                    
                    # Limiter la hauteur maximale pour ne pas déborder
                    max_height = 10*cm
                    if calculated_height > max_height:
                        calculated_height = max_height
                        max_width = calculated_height / ratio
                    
                    img = Image(str(img_path), width=max_width, height=calculated_height)
                    elements.append(img)
                except Exception as e:
                    print(f"Erreur lors du chargement de l'image de la facility: {e}")
        
        # Le footer sera dessiné en position absolue dans _draw_first_page_footer
        
        return elements
    
    def _create_dilution_page(self, facility_data: dict, styles):
        """Crée la page d'informations Excel avec tableau à 2 colonnes"""
        elements = []
        
        # Debug: afficher les données Excel reçues
        print("\n" + "="*80)
        print("DEBUG: Données Excel dans _create_dilution_page")
        print("="*80)
        print(f"installation_date: {facility_data.get('installation_date')}")
        print(f"zone_number: {facility_data.get('zone_number')}")
        print(f"router_number: {facility_data.get('router_number')}")
        print(f"last_intervention: {facility_data.get('last_intervention')}")
        print(f"produit_lavant: {facility_data.get('produit_lavant')}")
        print(f"dilution_lavant: {facility_data.get('dilution_lavant')}")
        print(f"couleur_buse_lavant: {facility_data.get('couleur_buse_lavant')}")
        print("="*80 + "\n")
        
        title_style = ParagraphStyle(
            'InfoTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph("INFORMATIONS DE DILUTION".upper(), title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Tableau à 2 colonnes : Nom de la colonne | Valeur
        table_data = []
        
        # Fonction helper pour formater les valeurs
        def format_value(val):
            if val is None or val == "":
                return "-"
            return str(val).upper()
        
        def format_dilution(val):
            """Convertit une dilution en pourcentage (ex: 0.098 -> 9,80%)"""
            if val is None or val == "":
                return "-"
            try:
                # Multiplier par 100 pour avoir le vrai pourcentage
                dilution_num = float(val) * 100
                # Formater avec 2 décimales et virgule
                return f"{dilution_num:.2f}%".replace('.', ',')
            except (ValueError, TypeError):
                return str(val).upper()
        
        # Informations générales
        table_data.append(["DATE INSTALLATION", format_value(facility_data.get("installation_date"))])
        table_data.append(["N° DE ZONE DE LAVAGE", format_value(facility_data.get("zone_number"))])
        table_data.append(["N° DE ROUTEUR", format_value(facility_data.get("router_number"))])
        table_data.append(["DATE DERNIÈRE INTERVENTION", format_value(facility_data.get("last_intervention"))])
        
        # Marqueur pour les séparateurs de zones
        zone_separators = [3]  # Après les infos générales (ligne 3)
        
        # Zone 1 (principale)
        zone1_start = len(table_data)
        if facility_data.get("produit_lavant"):
            table_data.append(["PRODUIT LAVANT", format_value(facility_data.get("produit_lavant"))])
            table_data.append(["DILUTION LAVANT", format_dilution(facility_data.get("dilution_lavant"))])
            table_data.append(["COULEUR BUSE LAVANT", format_value(facility_data.get("couleur_buse_lavant"))])
        
        if facility_data.get("produit_sechant"):
            table_data.append(["PRODUIT SÉCHANT", format_value(facility_data.get("produit_sechant"))])
            table_data.append(["DILUTION SÉCHANT", format_dilution(facility_data.get("dilution_sechant"))])
            table_data.append(["COULEUR BUSE SÉCHANT", format_value(facility_data.get("couleur_buse_sechant"))])
        
        if facility_data.get("autre_produit_lavant"):
            table_data.append(["AUTRE PRODUIT LAVANT", format_value(facility_data.get("autre_produit_lavant"))])
            table_data.append(["AUTRE DILUTION LAVANT", format_dilution(facility_data.get("autre_dilution_lavant"))])
            table_data.append(["AUTRE COULEUR BUSE LAVANT", format_value(facility_data.get("autre_couleur_buse_lavant"))])
        
        if facility_data.get("produit_jantes"):
            table_data.append(["PRODUIT JANTES", format_value(facility_data.get("produit_jantes"))])
            table_data.append(["DILUTION JANTES", format_dilution(facility_data.get("dilution_jantes"))])
        
        # Zone 2
        zone2_start = len(table_data)
        if facility_data.get("produit_lavant_zone2"):
            if zone2_start > zone1_start:
                zone_separators.append(zone2_start - 1)
            table_data.append(["PRODUIT LAVANT ZONE 2", format_value(facility_data.get("produit_lavant_zone2"))])
            table_data.append(["DILUTION LAVANT ZONE 2", format_dilution(facility_data.get("dilution_lavant_zone2"))])
            table_data.append(["COULEUR BUSE LAVANT ZONE 2", format_value(facility_data.get("couleur_buse_lavant_zone2"))])
        
        if facility_data.get("produit_sechant_zone2"):
            table_data.append(["PRODUIT SÉCHANT ZONE 2", format_value(facility_data.get("produit_sechant_zone2"))])
            table_data.append(["DILUTION SÉCHANT ZONE 2", format_dilution(facility_data.get("dilution_sechant_zone2"))])
            table_data.append(["COULEUR BUSE SÉCHANT ZONE 2", format_value(facility_data.get("couleur_buse_sechant_zone2"))])
        
        if facility_data.get("autre_produit_lavant_zone2"):
            table_data.append(["AUTRE PRODUIT LAVANT ZONE 2", format_value(facility_data.get("autre_produit_lavant_zone2"))])
            table_data.append(["AUTRE DILUTION LAVANT ZONE 2", format_dilution(facility_data.get("autre_dilution_lavant_zone2"))])
            table_data.append(["AUTRE COULEUR BUSE LAVANT ZONE 2", format_value(facility_data.get("autre_couleur_buse_lavant_zone2"))])
        
        # Zone 3
        zone3_start = len(table_data)
        if facility_data.get("produit_lavant_zone3"):
            if zone3_start > zone2_start:
                zone_separators.append(zone3_start - 1)
            table_data.append(["PRODUIT LAVANT ZONE 3", format_value(facility_data.get("produit_lavant_zone3"))])
            table_data.append(["DILUTION LAVANT ZONE 3", format_dilution(facility_data.get("dilution_lavant_zone3"))])
            table_data.append(["COULEUR BUSE LAVANT ZONE 3", format_value(facility_data.get("couleur_buse_lavant_zone3"))])
        
        if facility_data.get("produit_sechant_zone3"):
            table_data.append(["PRODUIT SÉCHANT ZONE 3", format_value(facility_data.get("produit_sechant_zone3"))])
            table_data.append(["DILUTION SÉCHANT ZONE 3", format_dilution(facility_data.get("dilution_sechant_zone3"))])
            table_data.append(["COULEUR BUSE SÉCHANT ZONE 3", format_value(facility_data.get("couleur_buse_sechant_zone3"))])
        
        # Zone 4
        zone4_start = len(table_data)
        if facility_data.get("produit_lavant_zone4"):
            if zone4_start > zone3_start:
                zone_separators.append(zone4_start - 1)
            table_data.append(["PRODUIT LAVANT ZONE 4", format_value(facility_data.get("produit_lavant_zone4"))])
            table_data.append(["DILUTION LAVANT ZONE 4", format_dilution(facility_data.get("dilution_lavant_zone4"))])
            table_data.append(["COULEUR BUSE LAVANT ZONE 4", format_value(facility_data.get("couleur_buse_lavant_zone4"))])
        
        if facility_data.get("produit_sechant_zone4"):
            table_data.append(["PRODUIT SÉCHANT ZONE 4", format_value(facility_data.get("produit_sechant_zone4"))])
            table_data.append(["DILUTION SÉCHANT ZONE 4", format_dilution(facility_data.get("dilution_sechant_zone4"))])
            table_data.append(["COULEUR BUSE SÉCHANT ZONE 4", format_value(facility_data.get("couleur_buse_sechant_zone4"))])
        
        # Zone 5
        zone5_start = len(table_data)
        if facility_data.get("produit_lavant_zone5"):
            if zone5_start > zone4_start:
                zone_separators.append(zone5_start - 1)
            table_data.append(["PRODUIT LAVANT ZONE 5", format_value(facility_data.get("produit_lavant_zone5"))])
            table_data.append(["DILUTION LAVANT ZONE 5", format_dilution(facility_data.get("dilution_lavant_zone5"))])
            table_data.append(["COULEUR BUSE LAVANT ZONE 5", format_value(facility_data.get("couleur_buse_lavant_zone5"))])
        
        if facility_data.get("produit_sechant_zone5"):
            table_data.append(["PRODUIT SÉCHANT ZONE 5", format_value(facility_data.get("produit_sechant_zone5"))])
            table_data.append(["DILUTION SÉCHANT ZONE 5", format_dilution(facility_data.get("dilution_sechant_zone5"))])
            table_data.append(["COULEUR BUSE SÉCHANT ZONE 5", format_value(facility_data.get("couleur_buse_sechant_zone5"))])
        
        if table_data:
            # Tableau élargi avec colonnes définies
            table = Table(table_data, colWidths=[10*cm, 14*cm])
            table.hAlign = 'CENTER'  # Centrer le tableau sur la page
            
            # Style de base
            style_commands = [
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),  # En-tête (colonne gauche) gris neutre
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),  # Données (colonne droite) en blanc
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]
            
            # Ajouter des lignes épaisses entre les zones
            for separator_row in zone_separators:
                if separator_row < len(table_data) - 1:
                    style_commands.append(('LINEBELOW', (0, separator_row), (-1, separator_row), 2.5, colors.black))
            
            table.setStyle(TableStyle(style_commands))
            
            elements.append(table)
            elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_daily_average_by_zone_table(self, facility_data: dict, from_date: str, to_date: str, styles):
        """Crée les tableaux de consommation quotidienne moyenne par lavage - une page par zone"""
        elements = []
        
        title_style = ParagraphStyle(
            'DailyAverageTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        zone_style = ParagraphStyle(
            'ZoneSubtitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=TA_CENTER
        )
        
        # Style pour les noms de produits (permet le retour à la ligne)
        product_name_style = ParagraphStyle(
            'ProductName',
            fontName='Helvetica',
            fontSize=8,
            leading=9,
            alignment=TA_LEFT
        )
        
        # Convertir les dates
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        products = facility_data.get("products", [])
        zones = facility_data.get("zones", ["GLOBAL"])
        
        # Créer les tableaux pour toutes les zones sur la même page
        elements.append(PageBreak())
        # Spacer pour centrer verticalement le contenu
        elements.append(Spacer(1, 1*cm))
        
        for zone_idx, zone in enumerate(zones):
            # Filtrer les produits de cette zone
            zone_products = [p for p in products if p.get("zone") == zone or (p.get("zone") is None and zone == "GLOBAL")]
            
            if not zone_products:
                continue
            
            # Titre avec la zone (pas de PageBreak entre les zones)
            elements.append(Paragraph(f"CONSOMMATION MENSUELLE TOTALE - JOUR PAR JOUR - {zone.upper()}", title_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # Première quinzaine (jours 1-15)
            month_str = start_date.strftime("%m")
            first_half_data = [["PRODUIT"] + [f"{d:02d}/{month_str}" for d in range(1, 16)]]
            
            for product in zone_products:
                product_name = product.get("name", "")
                daily_quantities = product.get("daily_quantities", [])
                
                # Mapper vers le nom Excel
                excel_name = get_excel_product_name(product_name, facility_data)
                # Utiliser Paragraph pour permettre le retour à la ligne
                row = [Paragraph(excel_name.upper(), product_name_style)]
                for day in range(1, 16):
                    date_str = start_date.replace(day=day).strftime("%Y-%m-%d")
                    qty_data = next((q for q in daily_quantities if q.get("date") == date_str), None)
                    if qty_data:
                        qty_raw = qty_data.get("qty", 0)
                        qty_l = qty_raw / 10000
                        row.append(f"{qty_l:.2f}L".replace('.', ','))
                    else:
                        row.append("-")
                
                first_half_data.append(row)
            
            if len(first_half_data) > 1:
                available_width = 28.7*cm
                product_col_width = 6*cm
                col_width = (available_width - product_col_width) / 15
                table = Table(first_half_data, colWidths=[product_col_width] + [col_width]*15)
                table.hAlign = 'CENTER'
                style_list = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # En-tête gris neutre
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Données en blanc
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]
                # Griser les week-ends avec un gris plus foncé
                for day in range(1, 16):
                    date_obj = start_date.replace(day=day)
                    if date_obj.weekday() >= 5:
                        col_index = day
                        style_list.append(('BACKGROUND', (col_index, 1), (col_index, -1), colors.HexColor('#D3D3D3')))  # Gris plus foncé pour week-ends
                table.setStyle(TableStyle(style_list))
                elements.append(table)
                elements.append(Spacer(1, 0.3*cm))
                
            # Deuxième quinzaine
            if start_date.month == 12:
                next_month = start_date.replace(year=start_date.year + 1, month=1, day=1)
            else:
                next_month = start_date.replace(month=start_date.month + 1, day=1)
            last_day = (next_month - timedelta(days=1)).day
            
            second_half_data = [["PRODUIT"] + [f"{d:02d}/{start_date.strftime('%m')}" for d in range(16, last_day + 1)]]
            
            for product in zone_products:
                product_name = product.get("name", "")
                daily_quantities = product.get("daily_quantities", [])
                
                # Mapper vers le nom Excel
                excel_name = get_excel_product_name(product_name, facility_data)
                # Utiliser Paragraph pour permettre le retour à la ligne
                row = [Paragraph(excel_name.upper(), product_name_style)]
                for day in range(16, last_day + 1):
                    try:
                        date_str = start_date.replace(day=day).strftime("%Y-%m-%d")
                        qty_data = next((q for q in daily_quantities if q.get("date") == date_str), None)
                        if qty_data:
                            qty_raw = qty_data.get("qty", 0)
                            qty_l = qty_raw / 10000
                            row.append(f"{qty_l:.2f}L".replace('.', ','))
                        else:
                            row.append("-")
                    except ValueError:
                        row.append("-")
                
                second_half_data.append(row)
            
            if len(second_half_data) > 1:
                days_count = last_day - 15
                available_width = 28.7*cm
                product_col_width = 6*cm
                col_width = (available_width - product_col_width) / days_count
                table = Table(second_half_data, colWidths=[product_col_width] + [col_width]*days_count)
                table.hAlign = 'CENTER'
                style_list = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # En-tête gris neutre
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Données en blanc
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]
                # Griser les week-ends avec un gris plus foncé
                for day in range(16, last_day + 1):
                    try:
                        date_obj = start_date.replace(day=day)
                        if date_obj.weekday() >= 5:
                            col_index = day - 15
                            style_list.append(('BACKGROUND', (col_index, 1), (col_index, -1), colors.HexColor('#D3D3D3')))  # Gris plus foncé pour week-ends
                    except ValueError:
                        pass
                table.setStyle(TableStyle(style_list))
                elements.append(table)
                elements.append(Spacer(1, 0.3*cm))
                
                # Texte explicatif pour les parties grisées (uniquement sous la 2ème partie)
                explanation_style = ParagraphStyle(
                    'TableExplanation',
                    fontName='Helvetica',
                    fontSize=8,
                    alignment=TA_CENTER,
                    textColor=colors.black
                )
                explanation = Paragraph("LES PARTIES GRISÉES CORRESPONDENT AUX WEEK-ENDS ET JOURS FÉRIÉS.", explanation_style)
                elements.append(explanation)
                elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_daily_consumption_tables(self, facility_data: dict, from_date: str, to_date: str, styles):
        """Crée les tableaux de consommation jour par jour (quinzaines)"""
        elements = []
        
        title_style = ParagraphStyle(
            'TableTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        text_style = ParagraphStyle(
            'TableText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_LEFT,
            leading=14
        )
        
        elements.append(PageBreak())
        # Spacer pour centrer verticalement le contenu (page A4 paysage ~21cm - marges)
        elements.append(Spacer(1, 3*cm))
        elements.append(Paragraph("CONSOMMATION MENSUELLE GLOBALE - TABLEAU JOUR PAR JOUR", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Convertir les dates
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        # Séparer en quinzaines
        mid_month = start_date.replace(day=15)
        
        products = facility_data.get("products", [])
        
        # Première quinzaine (jours 1-15)
        month_str = start_date.strftime("%m")
        first_half_data = [["PRODUIT"] + [f"{d:02d}/{month_str}" for d in range(1, 16)]]
        
        # Regrouper les produits par nom (ignorer la zone)
        import re
        products_by_name_first = {}
        for product in products:
            product_name_full = product.get("name", "")
            # Extraire le nom sans la zone (retirer " - ZONE X")
            product_name = re.sub(r'\s*-\s*ZONE\s+\d+\s*$', '', product_name_full, flags=re.IGNORECASE).strip()
            daily_quantities = product.get("daily_quantities", [])
            
            if product_name not in products_by_name_first:
                products_by_name_first[product_name] = {}
            
            # Additionner les quantités pour chaque jour
            for day in range(1, 16):
                date_str = start_date.replace(day=day).strftime("%Y-%m-%d")
                qty_data = next((q for q in daily_quantities if q.get("date") == date_str), None)
                if qty_data:
                    qty_raw = qty_data.get("qty", 0)
                    qty_l = qty_raw / 10000
                    if day not in products_by_name_first[product_name]:
                        products_by_name_first[product_name][day] = 0
                    products_by_name_first[product_name][day] += qty_l
        
        # Style pour les noms de produits (permet le retour à la ligne)
        product_name_style = ParagraphStyle(
            'ProductName',
            fontName='Helvetica',
            fontSize=8,
            leading=9,
            alignment=TA_LEFT
        )
        
        # Créer les lignes du tableau
        for product_name, daily_data in products_by_name_first.items():
            # Mapper vers le nom Excel
            excel_name = get_excel_product_name(product_name, facility_data)
            # Utiliser Paragraph pour permettre le retour à la ligne
            row = [Paragraph(excel_name.upper(), product_name_style)]
            for day in range(1, 16):
                if day in daily_data:
                    qty_l = daily_data[day]
                    row.append(f"{qty_l:.2f}L".replace('.', ','))
                else:
                    row.append("-")
            first_half_data.append(row)
        
        if len(first_half_data) > 1:
            # Utiliser la largeur maximale disponible (A4 landscape = 29.7cm - marges 1cm = 28.7cm)
            available_width = 28.7*cm
            product_col_width = 6*cm
            col_width = (available_width - product_col_width) / 15  # Reste divisé par 15 jours
            table = Table(first_half_data, colWidths=[product_col_width] + [col_width]*15)
            table.hAlign = 'CENTER'  # Centrer le tableau sur la page
            style_list = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # En-tête gris neutre
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Données en blanc
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]
            # Griser les week-ends avec un gris plus foncé
            for day in range(1, 16):
                date_obj = start_date.replace(day=day)
                if date_obj.weekday() >= 5:  # 5=samedi, 6=dimanche
                    col_index = day  # colonne = jour (car colonne 0 = nom produit)
                    style_list.append(('BACKGROUND', (col_index, 1), (col_index, -1), colors.HexColor('#D3D3D3')))  # Gris plus foncé pour week-ends
            table.setStyle(TableStyle(style_list))
            elements.append(table)
            elements.append(Spacer(1, 0.3*cm))
        
        # Deuxième quinzaine (jours 16-fin du mois)
        # Calculer le dernier jour du mois
        if start_date.month == 12:
            next_month = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            next_month = start_date.replace(month=start_date.month + 1, day=1)
        last_day = (next_month - timedelta(days=1)).day
        
        second_half_data = [["PRODUIT"] + [f"{d:02d}/{start_date.strftime('%m')}" for d in range(16, last_day + 1)]]
        
        # Regrouper les produits par nom (ignorer la zone)
        products_by_name_second = {}
        for product in products:
            product_name_full = product.get("name", "")
            # Extraire le nom sans la zone (retirer " - ZONE X")
            product_name = re.sub(r'\s*-\s*ZONE\s+\d+\s*$', '', product_name_full, flags=re.IGNORECASE).strip()
            daily_quantities = product.get("daily_quantities", [])
            
            if product_name not in products_by_name_second:
                products_by_name_second[product_name] = {}
            
            # Additionner les quantités pour chaque jour
            for day in range(16, last_day + 1):
                try:
                    date_str = start_date.replace(day=day).strftime("%Y-%m-%d")
                    qty_data = next((q for q in daily_quantities if q.get("date") == date_str), None)
                    if qty_data:
                        qty_raw = qty_data.get("qty", 0)
                        qty_l = qty_raw / 10000
                        if day not in products_by_name_second[product_name]:
                            products_by_name_second[product_name][day] = 0
                        products_by_name_second[product_name][day] += qty_l
                except ValueError:
                    pass
        
        # Créer les lignes du tableau
        for product_name, daily_data in products_by_name_second.items():
            # Mapper vers le nom Excel
            excel_name = get_excel_product_name(product_name, facility_data)
            # Utiliser Paragraph pour permettre le retour à la ligne
            row = [Paragraph(excel_name.upper(), product_name_style)]
            for day in range(16, last_day + 1):
                if day in daily_data:
                    qty_l = daily_data[day]
                    row.append(f"{qty_l:.2f}L".replace('.', ','))
                else:
                    row.append("-")
            second_half_data.append(row)
        
        if len(second_half_data) > 1:
            days_count = last_day - 15
            # Utiliser la largeur maximale disponible (A4 landscape = 29.7cm - marges 1cm = 28.7cm)
            available_width = 28.7*cm
            product_col_width = 6*cm
            col_width = (available_width - product_col_width) / days_count
            table = Table(second_half_data, colWidths=[product_col_width] + [col_width]*days_count)
            table.hAlign = 'CENTER'  # Centrer le tableau sur la page
            style_list = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # En-tête gris neutre
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Données en blanc
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]
            # Griser les week-ends avec un gris plus foncé
            for day in range(16, last_day + 1):
                try:
                    date_obj = start_date.replace(day=day)
                    if date_obj.weekday() >= 5:  # 5=samedi, 6=dimanche
                        col_index = day - 15  # colonne relative à la deuxième quinzaine
                        style_list.append(('BACKGROUND', (col_index, 1), (col_index, -1), colors.HexColor('#D3D3D3')))  # Gris plus foncé pour week-ends
                except ValueError:
                    pass
            table.setStyle(TableStyle(style_list))
            elements.append(table)
            elements.append(Spacer(1, 0.3*cm))
            
            # Texte explicatif pour les parties grisées (uniquement sous la 2ème partie)
            explanation_style = ParagraphStyle(
                'TableExplanation',
                fontName='Helvetica',
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.black
            )
            explanation = Paragraph("LES PARTIES GRISÉES CORRESPONDENT AUX WEEK-ENDS ET JOURS FÉRIÉS.", explanation_style)
            elements.append(explanation)
            elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_daily_total_by_zone_table(self, facility_data: dict, from_date: str, to_date: str, styles):
        """Crée le tableau de consommation quotidienne totale par produits - une page par zone"""
        elements = []
        
        title_style = ParagraphStyle(
            'DailyTotalTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        zone_style = ParagraphStyle(
            'ZoneSubtitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=TA_CENTER
        )
        
        text_style = ParagraphStyle(
            'ExplanationText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_LEFT,
            leading=14
        )
        
        # Style pour les noms de produits (permet le retour à la ligne)
        product_name_style = ParagraphStyle(
            'ProductName',
            fontName='Helvetica',
            fontSize=8,
            leading=9,
            alignment=TA_LEFT
        )
        
        products = facility_data.get("products", [])
        zones = facility_data.get("zones", ["GLOBAL"])
        
        # Créer les tableaux pour toutes les zones sur la même page
        elements.append(PageBreak())
        # Spacer pour centrer verticalement le contenu
        elements.append(Spacer(1, 2*cm))
        
        for zone_idx, zone in enumerate(zones):
            # Filtrer les produits de cette zone
            zone_products = [p for p in products if p.get("zone") == zone or (p.get("zone") is None and zone == "GLOBAL")]
            
            if not zone_products:
                continue
            
            # Titre avec la zone (pas de PageBreak entre les zones)
            elements.append(Paragraph(f"CONSOMMATION TOTALE MENSUELLE - {zone.upper()}", title_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # Récupérer les données mensuelles pour cette zone
            # Générer les en-têtes pour l'année en cours uniquement (janvier à décembre)
            end_date = datetime.strptime(to_date, "%Y-%m-%d")
            current_year = end_date.year
            current_month = end_date.month
            
            # Mois de janvier à décembre de l'année en cours
            month_headers = []
            months_list = []  # Liste des (year, month) pour la recherche
            for month in range(1, 13):
                month_headers.append(f"{month:02d}/{str(current_year)[-2:]}")
                months_list.append((current_year, month))
            
            table_data = [["PRODUIT"] + month_headers]
            
            # Pas de regroupement ici - garder les produits avec leurs zones
            for product in zone_products:
                product_name = product.get("name", "")
                monthly_quantities = product.get("monthly_quantities", [])
                
                # Mapper vers le nom Excel
                excel_name = get_excel_product_name(product_name, facility_data)
                # Utiliser Paragraph pour permettre le retour à la ligne
                row = [Paragraph(excel_name.upper(), product_name_style)]
                
                # Chercher les données pour chaque mois de l'année en cours
                for year, month in months_list:
                    # Si le mois est dans le futur, laisser la case vide
                    if month > current_month:
                        row.append("")
                        continue
                    month_data = next((m for m in monthly_quantities if m.get("year") == year and m.get("month") == month), None)
                    if month_data:
                        qty_raw = month_data.get("qty", 0)
                        # Convertir en litres (diviser par 10000)
                        qty_l = qty_raw / 10000
                        row.append(f"{qty_l:.2f}L".replace('.', ','))
                    else:
                        row.append("-")
                
                table_data.append(row)
            
            if len(table_data) > 1:
                # Utiliser la largeur maximale disponible (A4 landscape = 29.7cm - marges 1cm = 28.7cm)
                available_width = 28.7*cm
                product_col_width = 6*cm
                col_width = (available_width - product_col_width) / 12  # Reste divisé par 12 mois
                table = Table(table_data, colWidths=[product_col_width] + [col_width]*12)
                table.hAlign = 'CENTER'  # Centrer le tableau sur la page
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # En-tête gris neutre
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Données en blanc
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.5*cm))  # Espace entre les tableaux de zones
        
        return elements
    
    def _create_monthly_consumption_table(self, facility_data: dict, from_date: str, to_date: str, styles):
        """Crée le tableau de consommation globale mensuelle"""
        elements = []
        
        title_style = ParagraphStyle(
            'MonthlyTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        text_style = ParagraphStyle(
            'ExplanationText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_LEFT,
            leading=14
        )
        
        # Style pour les noms de produits (permet le retour à la ligne)
        product_name_style = ParagraphStyle(
            'ProductName',
            fontName='Helvetica',
            fontSize=8,
            leading=9,
            alignment=TA_LEFT
        )
        
        elements.append(PageBreak())
        # Spacer pour centrer verticalement le contenu
        elements.append(Spacer(1, 3*cm))
        elements.append(Paragraph("CONSOMMATION GLOBALE MENSUELLE", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        products = facility_data.get("products", [])
        
        # Récupérer les données mensuelles
        # Générer les en-têtes pour l'année en cours uniquement (janvier à décembre)
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        current_year = end_date.year
        current_month = end_date.month
        
        # Mois de janvier à décembre de l'année en cours
        month_headers = []
        months_list = []  # Liste des (year, month) pour la recherche
        for month in range(1, 13):
            month_headers.append(f"{month:02d}/{str(current_year)[-2:]}")
            months_list.append((current_year, month))
        
        table_data = [["PRODUIT"] + month_headers]
        
        # Regrouper les produits par nom (ignorer la zone)
        import re
        products_by_name = {}
        for product in products:
            product_name_full = product.get("name", "")
            # Extraire le nom sans la zone (retirer " - ZONE X")
            product_name = re.sub(r'\s*-\s*ZONE\s+\d+\s*$', '', product_name_full, flags=re.IGNORECASE).strip()
            monthly_quantities = product.get("monthly_quantities", [])
            
            if product_name not in products_by_name:
                products_by_name[product_name] = {}
            
            # Additionner les quantités pour chaque mois
            for month_data in monthly_quantities:
                year = month_data.get("year")
                month = month_data.get("month")
                qty_raw = month_data.get("qty", 0)
                if year and month:
                    key = (year, month)
                    if key not in products_by_name[product_name]:
                        products_by_name[product_name][key] = 0
                    # Convertir en litres (diviser par 10000)
                    qty_l = qty_raw / 10000
                    products_by_name[product_name][key] += qty_l
        
        # Créer les lignes du tableau
        for product_name, monthly_data in products_by_name.items():
            # Mapper vers le nom Excel
            excel_name = get_excel_product_name(product_name, facility_data)
            # Utiliser Paragraph pour permettre le retour à la ligne
            row = [Paragraph(excel_name.upper(), product_name_style)]
            
            # Chercher les données pour chaque mois de l'année en cours
            for year, month in months_list:
                key = (year, month)
                # Si le mois est dans le futur, laisser la case vide
                if month > current_month:
                    row.append("")
                elif key in monthly_data:
                    qty_l = monthly_data[key]
                    row.append(f"{qty_l:.2f}L".replace('.', ','))
                else:
                    row.append("-")
            
            table_data.append(row)
        
        if len(table_data) > 1:
            # Utiliser la largeur maximale disponible (A4 landscape = 29.7cm - marges 1cm = 28.7cm)
            available_width = 28.7*cm
            product_col_width = 6*cm
            col_width = (available_width - product_col_width) / 12  # Reste divisé par 12 mois
            table = Table(table_data, colWidths=[product_col_width] + [col_width]*12)
            table.hAlign = 'CENTER'  # Centrer le tableau sur la page
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # En-tête gris neutre
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Données en blanc
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            elements.append(table)
        
        return elements
    
    def _create_delivered_products_table(self, facility_data: dict, from_date: str, to_date: str, styles):
        """Crée le tableau des produits livrés (vide pour l'instant, données Odoo à venir)"""
        elements = []
        
        title_style = ParagraphStyle(
            'DeliveredTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        text_style = ParagraphStyle(
            'ExplanationText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_LEFT,
            leading=14
        )
        
        # Style pour les noms de produits (permet le retour à la ligne)
        product_name_style = ParagraphStyle(
            'ProductName',
            fontName='Helvetica',
            fontSize=8,
            leading=9,
            alignment=TA_LEFT
        )
        
        # Pas de PageBreak - on reste sur la même page que CONSOMMATION GLOBALE MENSUELLE
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("PRODUITS LIVRÉS", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Générer les en-têtes pour l'année en cours uniquement (janvier à décembre)
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        current_year = end_date.year
        current_month = end_date.month
        
        # Mois de janvier à décembre de l'année en cours
        month_headers = []
        for month in range(1, 13):
            month_headers.append(f"{month:02d}/{str(current_year)[-2:]}")
        
        # Créer un tableau avec les produits de la facility
        table_data = [["PRODUIT"] + month_headers]
        
        # Récupérer les produits et utiliser le mapping Excel
        products = facility_data.get("products", [])
        if products:
            for product in products:
                product_name = product.get("name", "")
                # Mapper vers le nom Excel
                excel_name = get_excel_product_name(product_name, facility_data)
                # Utiliser Paragraph pour permettre le retour à la ligne
                # Cases vides pour les mois futurs, "-" pour les mois passés sans données
                row = [Paragraph(excel_name.upper(), product_name_style)]
                for month in range(1, 13):
                    if month > current_month:
                        row.append("")  # Mois futur = case vide
                    else:
                        row.append("-")  # Mois passé sans données
                table_data.append(row)
        else:
            # Ajouter une ligne d'exemple si pas de produits
            example_row = [Paragraph("AUCUNE DONNÉE DISPONIBLE", product_name_style)]
            for month in range(1, 13):
                if month > current_month:
                    example_row.append("")
                else:
                    example_row.append("-")
            table_data.append(example_row)
        
        # Utiliser la largeur maximale disponible (A4 landscape = 29.7cm - marges 1cm = 28.7cm)
        available_width = 28.7*cm
        product_col_width = 6*cm
        col_width = (available_width - product_col_width) / 12  # Reste divisé par 12 mois
        table = Table(table_data, colWidths=[product_col_width] + [col_width]*12)
        table.hAlign = 'CENTER'  # Centrer le tableau sur la page
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # En-tête gris neutre
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Données en blanc
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(table)
        
        return elements
    
    def _draw_first_page(self, canvas, doc):
        """Dessine les logos et le footer pour la première page"""
        # Dessiner les logos normalement
        self._draw_logo(canvas, doc)
        
        # Dessiner le footer en position absolue en bas de page
        canvas.saveState()
        page_width, page_height = doc.pagesize
        
        # Texte du footer
        footer_text1 = "EN CAS DE PANNE SUR LE SYSTÈME VENTURI, CONTACTEZ LE SUPPORT TECHNIQUE AU 03 88 64 72 10."
        
        # Position du footer : 1.0cm du bas de la page
        y_position = 1.0*cm
        
        # Première ligne en noir
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.black)
        canvas.drawCentredString(page_width / 2, y_position + 0.4*cm, footer_text1)
        
        # Deuxième ligne avec email en bleu
        footer_text2_part1 = "UNE QUESTION SUR VOTRE CONTRAT ? CONTACTEZ NOTRE SUPPORT ADMINISTRATIF AU 03 88 64 85 79 OU PAR MAIL "
        footer_email = "SYSTEMES.SOLUTIONS@WURTH.FR"
        
        # Calculer les largeurs pour centrer correctement
        text_width_part1 = canvas.stringWidth(footer_text2_part1, 'Helvetica', 8)
        text_width_email = canvas.stringWidth(footer_email, 'Helvetica', 8)
        total_width = text_width_part1 + text_width_email
        
        # Position de départ pour centrer le tout
        start_x = (page_width - total_width) / 2
        
        # Dessiner la première partie en noir
        canvas.setFillColor(colors.black)
        canvas.drawString(start_x, y_position, footer_text2_part1)
        
        # Dessiner l'email en bleu
        canvas.setFillColor(colors.blue)
        canvas.drawString(start_x + text_width_part1, y_position, footer_email)
        
        canvas.restoreState()
    
    def _draw_logo(self, canvas, doc):
        """Dessine les logos Würth (gauche) et TMH (droite) en haut de chaque page"""
        canvas.saveState()
        
        page_width, page_height = doc.pagesize
        
        # Logo Würth à gauche
        wurth_logo_path = self.base_dir / "images" / "Würth_logo.png"
        if wurth_logo_path.exists():
            try:
                with PILImage.open(wurth_logo_path) as img:
                    img_width, img_height = img.size
                    ratio = img_height / img_width
                
                logo_width = 4.5*cm
                logo_height = logo_width * ratio
                
                x = 0.8*cm
                y = page_height - logo_height - 0.8*cm
                
                canvas.drawImage(str(wurth_logo_path), x, y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Erreur lors du chargement du logo Würth: {e}")
        
        # Logo TMH au centre
        tmh_logo_path = self.base_dir / "images" / "Logo - Solution de lavage connecté.png"
        if tmh_logo_path.exists():
            try:
                with PILImage.open(tmh_logo_path) as img:
                    img_width, img_height = img.size
                    ratio = img_height / img_width
                
                logo_width = 12*cm
                logo_height = logo_width * ratio
                
                x = (page_width - logo_width) / 2
                y = page_height - logo_height - 0.7*cm
                
                canvas.drawImage(str(tmh_logo_path), x, y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Erreur lors du chargement du logo TMH: {e}")
        
        canvas.restoreState()
    
    def _create_flowrate_pages(self, facility_data: dict, from_date: str, to_date: str, styles):
        """Crée les pages de débit moyen par zone"""
        from .consumption_charts import ConsumptionChartGenerator
        
        elements = []
        chart_gen = ConsumptionChartGenerator()
        
        title_style = ParagraphStyle(
            'FlowrateTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        text_style = ParagraphStyle(
            'FlowrateText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_LEFT,
            leading=14
        )
        
        # Récupérer les données flowrate
        flowrate_data = facility_data.get("flowrate_data", {})
        
        if not flowrate_data:
            # Pas de données flowrate, ne rien générer
            return elements
        
        # Récupérer les zones
        zones = facility_data.get("zones", ["GLOBAL"])
        
        # Regrouper TOUTES les données flowrate de tous les devices
        all_events = {"data": {"results": []}}
        for device_id, events_data in flowrate_data.items():
            if isinstance(events_data, dict):
                data = events_data.get("data")
                if isinstance(data, dict) and "results" in data:
                    all_events["data"]["results"].extend(data["results"])
                elif isinstance(data, list):
                    all_events["data"]["results"].extend(data)
        
        if not all_events["data"]["results"]:
            return elements
        
        # Créer une page par zone - le filtrage par produit se fait dans create_flowrate_chart
        for zone in zones:
            # Créer le graphique pour cette zone (le filtrage par nom de produit se fait dans create_flowrate_chart)
            chart_buf = chart_gen.create_flowrate_chart(
                all_events,
                "",  # Pas de serial number
                zone,
                from_date,
                to_date
            )
            
            if chart_buf:
                # Nouvelle page pour cette zone
                elements.append(PageBreak())
                
                # Titre de la page
                elements.append(Paragraph("DÉBIT MOYEN JOURNALIER", title_style))
                elements.append(Spacer(1, 0.3*cm))
                
                # Texte explicatif avec ZONE en gras - zone contient déjà "Zone X"
                # Donc on affiche juste la zone en gras
                explanation_text = f"GRAPHIQUE DE DÉBIT POUR LA <b>{zone.upper()}</b>"
                elements.append(Paragraph(explanation_text, text_style))
                elements.append(Spacer(1, 0.5*cm))
                
                # Ajouter le graphique (même taille que les graphiques de consommation)
                img = Image(chart_buf, width=24*cm, height=12*cm)
                img.hAlign = 'CENTER'
                elements.append(img)
                elements.append(Spacer(1, 0.3*cm))
                
                # Texte explicatif détaillé
                explanation_style = ParagraphStyle(
                    'FlowrateExplanation',
                    fontName='Helvetica',
                    fontSize=8,
                    alignment=TA_LEFT,
                    textColor=colors.black
                )
                detailed_explanation = (
                    "LES PARTIES GRISÉES CORRESPONDENT AUX WEEK-ENDS ET JOURS FÉRIÉS.<br/>"
                    "LES CONSOMMATIONS SONT EXPRIMÉES EN ML PAR UTILISATION DANS LA JOURNÉE. "
                    "EXEMPLE : UN POINT À 200 ML SIGNIFIE QU'IL A FALLU EN MOYENNE 200 ML POUR LAVER CHAQUE VOITURE DANS LA JOURNÉE"
                )
                elements.append(Paragraph(detailed_explanation, explanation_style))
                elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_consumption_pages(self, facility_data: dict, from_date: str, to_date: str, styles):
        """Crée les pages de suivi de consommation par zone"""
        from .consumption_charts import ConsumptionChartGenerator
        
        elements = []
        chart_gen = ConsumptionChartGenerator()
        
        title_style = ParagraphStyle(
            'ConsumptionTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        text_style = ParagraphStyle(
            'ConsumptionText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_LEFT,
            leading=14
        )
        
        zones = facility_data.get("zones", ["GLOBAL"])
        products = facility_data.get("products", [])
        
        # Grouper par zone : un graphique par zone avec tous les produits
        for zone in zones:
            zone_products = [p for p in products if p.get("zone") == zone or (p.get("zone") is None and zone == "GLOBAL")]
            
            if not zone_products:
                continue
            
            # Préparer les données pour le graphique multi-produits
            products_data = []
            for product in zone_products:
                daily_quantities = product.get("daily_quantities", [])
                if daily_quantities:
                    products_data.append({
                        "name": product.get("name", "Produit inconnu"),
                        "daily_data": daily_quantities
                    })
            
            if not products_data:
                continue
            
            # Nouvelle page pour chaque zone pour éviter que le titre soit séparé du graphique
            elements.append(PageBreak())
            
            # Titre de la section
            elements.append(Paragraph(
                f"SUIVI DE LA CONSOMMATION QUOTIDIENNE TOTALE PAR PRODUITS",
                title_style
            ))
            elements.append(Spacer(1, 0.5*cm))
            
            elements.append(Paragraph(
                f"<b>ZONE:</b> {zone.upper()} | <b>PRODUITS:</b> {len(products_data)} PRODUIT(S)",
                text_style
            ))
            elements.append(Spacer(1, 0.3*cm))
            
            # Créer le graphique avec tous les produits de la zone
            chart_buffer = chart_gen.create_multi_product_chart(
                products_data,
                zone,
                from_date,
                to_date
            )
            
            chart_img = Image(chart_buffer, width=24*cm, height=12*cm)
            elements.append(chart_img)
            elements.append(Spacer(1, 0.3*cm))
            
            # Texte explicatif avec le même style que sous les tableaux
            explanation_style = ParagraphStyle(
                'ChartExplanation',
                fontName='Helvetica',
                fontSize=8,
                alignment=TA_LEFT,
                textColor=colors.black
            )
            legend_text = "LES PARTIES GRISÉES CORRESPONDENT AUX WEEK-ENDS ET JOURS FÉRIÉS.<br/>LES CONSOMMATIONS SONT EXPRIMÉES EN LITRES. LE GRAPHIQUE VOUS PERMET DE SUIVRE LES PICS D'ACTIVITÉ SUR LE MOIS."
            
            elements.append(Paragraph(legend_text, explanation_style))
            elements.append(Spacer(1, 0.5*cm))
        
        return elements
