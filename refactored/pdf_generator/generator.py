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
from refactored.config.settings import REPORTS_OUTPUT_DIR, REFACTORED_DIR

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
            leftMargin=0.8*cm,
            rightMargin=0.8*cm,
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
        
        story.append(PageBreak())
        
        story.extend(self._create_consumption_pages(facility_data, from_date, to_date, styles))
        
        story.extend(self._create_daily_consumption_tables(facility_data, from_date, to_date, styles))
        
        story.extend(self._create_monthly_consumption_table(facility_data, from_date, to_date, styles))
        
        doc.build(story, onFirstPage=self._draw_logo, onLaterPages=self._draw_logo)
    
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
        
        elements.append(Spacer(1, 0.3*cm))
        
        elements.append(Paragraph(
            f"RAPPORT DE CONSOMMATION DU {from_date_formatted} AU {to_date_formatted}",
            title_style
        ))
        elements.append(Spacer(1, 0.3*cm))
        
        elements.append(Paragraph(client_text, title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        serial_numbers = [d.get("serial_number", "") for d in facility_data.get("devices", [])]
        if serial_numbers:
            router_text = "N°ROUTEUR(S): " + " / ".join(serial_numbers).upper()
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
        
        elements.append(Spacer(1, 2*cm))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=title_style,
            fontSize=10,
            alignment=TA_CENTER,
            leading=14
        )
        
        footer_text = """EN CAS DE PANNE SUR LE SYSTÈME VENTURI, CONTACTEZ LE SUPPORT TECHNIQUE AU 03 88 64 72 10.<br/>
UNE QUESTION SUR VOTRE CONTRAT ? CONTACTEZ NOTRE SUPPORT ADMINISTRATIF AU 03 88 64 85 79 OU PAR MAIL <a href="mailto:systemes.solutions@wurth.fr" color="blue">SYSTEMES.SOLUTIONS@WURTH.FR</a>"""
        
        elements.append(Paragraph(footer_text, footer_style))
        
        return elements
    
    def _create_dilution_page(self, facility_data: dict, styles):
        """Crée la page de dilution avec tableau compact"""
        elements = []
        
        title_style = ParagraphStyle(
            'DilutionTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        text_style = ParagraphStyle(
            'DilutionText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_LEFT,
            leading=14
        )
        
        elements.append(Paragraph("INFORMATIONS DE DILUTION", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Tableau de dilution
        table_data = [
            ["Produit", "Dilution", "Code couleur buse", "Impact (1L = X lavages)"]
        ]
        
        products = facility_data.get("products", [])
        for product in products:
            product_name = product.get("name", "")
            # TODO: Récupérer les vraies données de dilution depuis la config ou l'API
            dilution = "À définir"
            color_code = "À définir"
            impact = "À définir"
            
            table_data.append([product_name, dilution, color_code, impact])
        
        if len(table_data) > 1:
            table = Table(table_data, colWidths=[8*cm, 4*cm, 5*cm, 5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.5*cm))
        
        # Informations supplémentaires
        installation_date = "À définir"  # TODO: Récupérer depuis les données
        last_nozzle_date = "À définir"  # TODO: Récupérer depuis les données
        
        info_text = f"""<b>Date d'installation sur site:</b> {installation_date}<br/>
<b>Date de dernière mise en place des buses:</b> {last_nozzle_date}"""
        
        elements.append(Paragraph(info_text, text_style))
        
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
        elements.append(Paragraph("CONSOMMATION MENSUELLE - TABLEAU JOUR PAR JOUR", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Convertir les dates
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        # Séparer en quinzaines
        mid_month = start_date.replace(day=15)
        
        products = facility_data.get("products", [])
        
        # Première quinzaine (jours 1-15)
        elements.append(Paragraph("<b>Première quinzaine</b>", text_style))
        elements.append(Spacer(1, 0.3*cm))
        
        first_half_data = [["Produit/Zone"] + [f"{d:02d}" for d in range(1, 16)]]
        
        for product in products:
            product_name = product.get("name", "")
            zone = product.get("zone", "")
            daily_quantities = product.get("daily_quantities", [])
            
            row = [f"{product_name}"]
            for day in range(1, 16):
                date_str = start_date.replace(day=day).strftime("%Y-%m-%d")
                qty_data = next((q for q in daily_quantities if q.get("date") == date_str), None)
                if qty_data:
                    qty_raw = qty_data.get("qty", 0)
                    # Diviser par 10 pour convertir cL en mL, puis par 1000 pour mL en L
                    qty_l = qty_raw / 10000
                    row.append(f"{qty_l:.1f}L")
                else:
                    row.append("-")
            
            first_half_data.append(row)
        
        if len(first_half_data) > 1:
            table = Table(first_half_data, colWidths=[6*cm] + [1.2*cm]*15)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.5*cm))
        
        # Deuxième quinzaine (jours 16-fin du mois)
        elements.append(Paragraph("<b>Deuxième quinzaine</b>", text_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Calculer le dernier jour du mois
        if start_date.month == 12:
            next_month = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            next_month = start_date.replace(month=start_date.month + 1, day=1)
        last_day = (next_month - timedelta(days=1)).day
        
        second_half_data = [["Produit/Zone"] + [f"{d:02d}" for d in range(16, last_day + 1)]]
        
        for product in products:
            product_name = product.get("name", "")
            zone = product.get("zone", "")
            daily_quantities = product.get("daily_quantities", [])
            
            row = [f"{product_name}"]
            for day in range(16, last_day + 1):
                try:
                    date_str = start_date.replace(day=day).strftime("%Y-%m-%d")
                    qty_data = next((q for q in daily_quantities if q.get("date") == date_str), None)
                    if qty_data:
                        qty_raw = qty_data.get("qty", 0)
                        # Diviser par 10 pour convertir cL en mL, puis par 1000 pour mL en L
                        qty_l = qty_raw / 10000
                        row.append(f"{qty_l:.1f}L")
                    else:
                        row.append("-")
                except ValueError:
                    row.append("-")
            
            second_half_data.append(row)
        
        if len(second_half_data) > 1:
            num_days = last_day - 15
            table = Table(second_half_data, colWidths=[6*cm] + [1.2*cm]*num_days)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            elements.append(table)
        
        return elements
    
    def _create_monthly_consumption_table(self, facility_data: dict, from_date: str, to_date: str, styles):
        """Crée le tableau de consommation totale mensuelle"""
        elements = []
        
        title_style = ParagraphStyle(
            'MonthlyTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        elements.append(PageBreak())
        elements.append(Paragraph("CONSOMMATION TOTALE MENSUELLE", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        products = facility_data.get("products", [])
        
        # Récupérer les données mensuelles
        table_data = [["Produit/Zone", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                       "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]]
        
        for product in products:
            product_name = product.get("name", "")
            zone = product.get("zone", "")
            monthly_quantities = product.get("monthly_quantities", [])
            
            row = [f"{product_name}"]
            
            for month in range(1, 13):
                month_data = next((m for m in monthly_quantities if m.get("month") == month), None)
                if month_data:
                    qty = month_data.get("qty", 0)
                    row.append(f"{qty:.0f}L")
                else:
                    row.append("-")
            
            table_data.append(row)
        
        if len(table_data) > 1:
            table = Table(table_data, colWidths=[6*cm] + [1.8*cm]*12)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            elements.append(table)
        
        return elements
    
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
                
                logo_width = 10*cm
                logo_height = logo_width * ratio
                
                x = (page_width - logo_width) / 2
                y = page_height - logo_height - 1.2*cm
                
                canvas.drawImage(str(tmh_logo_path), x, y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Erreur lors du chargement du logo TMH: {e}")
        
        canvas.restoreState()
    
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
            
            # Titre de la section
            elements.append(Paragraph(
                f"Suivi de la consommation quotidienne moyenne par lavage",
                title_style
            ))
            elements.append(Spacer(1, 0.5*cm))
            
            elements.append(Paragraph(
                f"<b>Zone:</b> {zone} | <b>Produits:</b> {len(products_data)} produit(s)",
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
            
            legend_text = """<b>Légende:</b><br/>
• <b>Zone grisée</b>: Week-ends et jours fériés<br/>
• <b>Courbes de couleur</b>: Chaque couleur représente un produit différent"""
            
            elements.append(Paragraph(legend_text, text_style))
            elements.append(Spacer(1, 0.5*cm))
        
        return elements
