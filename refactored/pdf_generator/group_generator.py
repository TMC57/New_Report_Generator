"""
Générateur de PDF pour les rapports de groupe
Utilise le même template que les rapports individuels
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image as PILImage
from refactored.utils.logger import get_logger
from refactored.pdf_generator.consumption_charts import ConsumptionChartGenerator

logger = get_logger("Group_PDF_Generator")

class GroupPDFGenerator:
    """Générateur de PDF pour les rapports de groupe"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.uploads_dir = self.base_dir / "uploads"
        self.reports_dir = self.base_dir / "reports"
        
    def generate_all_group_pdfs(
        self,
        grouped_quantities: Dict[str, Any],
        grouped_stock: Dict[str, Any],
        group_configs: List[Dict[str, Any]],
        from_date: str,
        to_date: str
    ) -> List[str]:
        """
        Génère tous les PDFs de groupe
        
        Returns:
            Liste des chemins des PDFs générés
        """
        generated_pdfs = []
        
        # Créer un dictionnaire owner -> config pour un accès rapide
        config_by_owner = {cfg.get("owner"): cfg for cfg in group_configs}
        
        # Parcourir tous les owners avec des données
        for owner_data in grouped_quantities.get("owners", []):
            owner_name = owner_data.get("owner")
            
            # Récupérer la config de ce owner
            owner_config = config_by_owner.get(owner_name, {})
            
            # Ignorer les groupes avec "Croix rouge.jpg" (groupes non configurés)
            cover_picture = owner_config.get("cover_picture", "")
            if "Croix rouge" in cover_picture:
                logger.info(f"⏭️  Groupe '{owner_name}' ignoré (pas de photo de couverture)")
                continue
            
            try:
                # Générer le PDF pour ce groupe
                pdf_path = self._generate_single_group_pdf(
                    owner_name,
                    owner_data,
                    owner_config,
                    from_date,
                    to_date
                )
                generated_pdfs.append(pdf_path)
                logger.success(f"✅ PDF généré pour '{owner_name}': {pdf_path}")
            except Exception as e:
                logger.error(f"❌ Erreur lors de la génération du PDF pour '{owner_name}': {e}")
        
        return generated_pdfs
    
    def _generate_single_group_pdf(
        self,
        owner_name: str,
        owner_data: Dict[str, Any],
        owner_config: Dict[str, Any],
        from_date: str,
        to_date: str
    ) -> str:
        """
        Génère un PDF pour un groupe spécifique
        """
        # Créer le dossier de sortie
        output_folder = self.reports_dir / f"group_reports {from_date} to {to_date}"
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Nom du fichier PDF
        safe_owner_name = owner_name.replace("/", "-").replace("\\", "-")
        pdf_filename = f"Rapport_Groupe_{safe_owner_name}.pdf"
        pdf_path = output_folder / pdf_filename
        
        # Créer le document PDF - MÊME FORMAT QUE LES RAPPORTS INDIVIDUELS (paysage)
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=landscape(A4),
            leftMargin=0.5*cm,
            rightMargin=0.5*cm,
            topMargin=3*cm,
            bottomMargin=0.8*cm
        )
        
        # Éléments du PDF
        elements = []
        
        # Page de garde
        self._add_cover_page(elements, owner_name, owner_data, owner_config, from_date, to_date)
        
        # Page de graphique de consommation par facility
        self._add_facility_consumption_chart(elements, owner_name, owner_data, from_date, to_date)
        
        # Page de graphique de consommation totale par produit
        self._add_product_total_chart(elements, owner_name, owner_data, from_date, to_date)
        
        # Construire le PDF avec les logos
        doc.build(elements, onFirstPage=self._draw_first_page, onLaterPages=self._draw_logo)
        
        return str(pdf_path)
    
    def _add_cover_page(
        self,
        elements: List,
        owner_name: str,
        owner_data: Dict[str, Any],
        owner_config: Dict[str, Any],
        from_date: str,
        to_date: str
    ):
        """
        Ajoute la page de garde du rapport de groupe
        Même style que les rapports individuels
        """
        styles = getSampleStyleSheet()
        
        # Style pour le titre principal - MÊME QUE RAPPORTS INDIVIDUELS
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        from_date_formatted = datetime.strptime(from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        to_date_formatted = datetime.strptime(to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        elements.append(Spacer(1, 0.1*cm))
        
        # Titre avec période
        elements.append(Paragraph(
            f"RAPPORT DE CONSOMMATION DU {from_date_formatted} AU {to_date_formatted}".upper(),
            title_style
        ))
        elements.append(Spacer(1, 0.2*cm))
        
        # Nom du groupe
        elements.append(Paragraph(owner_name.upper(), title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Liste des facilities du groupe
        facilities = owner_data.get("facilities", [])
        if facilities:
            facility_names = [f.get("facilityName", "") for f in facilities]
            # Séparateur plus visible: " | " en gras
            facilities_text = " <b>|</b> ".join([f"<b>{name.upper()}</b>" for name in facility_names])
            
            # Style pour la liste des facilities - en gras
            facilities_style = ParagraphStyle(
                'FacilitiesList',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=11,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(facilities_text, facilities_style))
        
        elements.append(Spacer(1, 0.5*cm))
        
        # Photo de couverture
        cover_picture = owner_config.get("cover_picture", "")
        if cover_picture and "Croix rouge" not in cover_picture:
            # Enlever le préfixe /uploads/ si présent
            if cover_picture.startswith("/uploads/"):
                cover_picture = cover_picture[9:]
            
            cover_path = self.uploads_dir / cover_picture
            
            if cover_path.exists():
                try:
                    # Charger l'image pour obtenir ses dimensions réelles
                    with PILImage.open(cover_path) as pil_img:
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
                    
                    img = Image(str(cover_path), width=max_width, height=calculated_height)
                    elements.append(img)
                except Exception as e:
                    logger.warning(f"Impossible de charger l'image de couverture: {e}")
            else:
                logger.warning(f"Image de couverture introuvable: {cover_path}")
    
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
                logger.warning(f"Erreur lors du chargement du logo Würth: {e}")
        
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
                logger.warning(f"Erreur lors du chargement du logo TMH: {e}")
        
        canvas.restoreState()
    
    def _add_facility_consumption_chart(
        self,
        elements: List,
        owner_name: str,
        owner_data: Dict[str, Any],
        from_date: str,
        to_date: str
    ):
        """
        Ajoute une page avec le graphique de consommation par facility
        Axe X = facilities, barres groupées par produit
        """
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'ChartTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        # Nouvelle page
        elements.append(PageBreak())
        elements.append(Spacer(1, 0.5*cm))
        
        # Titre
        elements.append(Paragraph(
            "SUIVI DE LA CONSOMMATION TOTALE PAR SITE",
            title_style
        ))
        elements.append(Spacer(1, 0.3*cm))
        
        # Sous-titre avec période
        from_date_formatted = datetime.strptime(from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        to_date_formatted = datetime.strptime(to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        subtitle_style = ParagraphStyle(
            'ChartSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Période du {from_date_formatted} au {to_date_formatted}",
            subtitle_style
        ))
        elements.append(Spacer(1, 0.5*cm))
        
        # Préparer les données pour le graphique
        facilities_data = []
        for facility in owner_data.get("facilities", []):
            facility_info = {
                "facilityName": facility.get("facilityName", ""),
                "products": facility.get("products", [])
            }
            facilities_data.append(facility_info)
        
        # Debug: afficher les données
        logger.info(f"📊 Graphique pour {owner_name}: {len(facilities_data)} facilities")
        for fd in facilities_data:
            products_count = len(fd.get("products", []))
            logger.info(f"   → {fd.get('facilityName')}: {products_count} produits")
            for p in fd.get("products", [])[:3]:  # Afficher les 3 premiers
                logger.info(f"      - {p.get('name')}: qty={p.get('qty', 0)}")
        
        if not facilities_data:
            elements.append(Paragraph(
                "Aucune donnée de consommation disponible pour ce groupe.",
                subtitle_style
            ))
            return
        
        # Créer le graphique
        chart_gen = ConsumptionChartGenerator()
        chart_buffer = chart_gen.create_group_facility_chart(
            facilities_data,
            owner_name
        )
        
        # Ajouter le graphique au PDF (hauteur réduite)
        chart_img = Image(chart_buffer, width=26*cm, height=7*cm)
        elements.append(chart_img)
        elements.append(Spacer(1, 0.5*cm))  # Espace entre graphique et tableau
        
        # Récupérer les données agrégées pour le tableau
        facility_names, product_names, product_facility_qty = chart_gen.get_aggregated_facility_data(facilities_data)
        
        # Créer le tableau (lignes = produits, colonnes = facilities)
        if facility_names and product_names:
            # Entête: vide + noms des facilities
            header_row = ["PRODUIT"] + facility_names
            
            # Lignes de données
            table_data = [header_row]
            for product_name in product_names:
                row = [product_name.upper()]
                for fac_name in facility_names:
                    qty = product_facility_qty.get(product_name, {}).get(fac_name, 0)
                    qty_str = f"{qty:.2f} L".replace('.', ',')
                    row.append(qty_str)
                table_data.append(row)
            
            # Calculer les largeurs de colonnes
            num_cols = len(header_row)
            first_col_width = 4*cm
            remaining_width = 22*cm
            other_col_width = remaining_width / max(num_cols - 1, 1)
            col_widths = [first_col_width] + [other_col_width] * (num_cols - 1)
            
            # Créer le tableau
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                # Entête grisée
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.85, 0.85, 0.85)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                # Première colonne (noms produits)
                ('BACKGROUND', (0, 1), (0, -1), colors.Color(0.95, 0.95, 0.95)),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (0, -1), 8),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                # Données
                ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (1, 1), (-1, -1), 8),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Bordures
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.5*cm))  # Espace entre tableau et texte explicatif
        
        # Texte explicatif
        explanation_style = ParagraphStyle(
            'ChartExplanation',
            fontName='Helvetica',
            fontSize=8,
            alignment=TA_LEFT,
            textColor=colors.black
        )
        legend_text = "CE GRAPHIQUE ET CE TABLEAU PRÉSENTENT LA CONSOMMATION TOTALE PAR PRODUIT POUR CHAQUE SITE DU GROUPE SUR LA PÉRIODE SÉLECTIONNÉE.<br/>LES CONSOMMATIONS SONT EXPRIMÉES EN LITRES."
        
        elements.append(Paragraph(legend_text, explanation_style))
    
    def _add_product_total_chart(
        self,
        elements: List,
        owner_name: str,
        owner_data: Dict[str, Any],
        from_date: str,
        to_date: str
    ):
        """
        Ajoute une page avec le graphique de consommation totale par produit
        Axe X = produits, une barre par produit avec le total pour tout le owner
        """
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'ChartTitle2',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER
        )
        
        # Nouvelle page
        elements.append(PageBreak())
        
        # Espace pour centrer verticalement (page paysage A4 = ~21cm de hauteur utile)
        # Graphique ~10cm + titre ~1cm + sous-titre ~0.5cm + texte ~0.5cm = ~12cm
        # Espace restant = ~9cm, donc ~4cm en haut
        elements.append(Spacer(1, 3*cm))
        
        # Titre
        elements.append(Paragraph(
            "SUIVI DE LA CONSOMMATION TOTALE PAR PRODUIT",
            title_style
        ))
        elements.append(Spacer(1, 0.3*cm))
        
        # Sous-titre avec période
        from_date_formatted = datetime.strptime(from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        to_date_formatted = datetime.strptime(to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        subtitle_style = ParagraphStyle(
            'ChartSubtitle2',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"PÉRIODE DU {from_date_formatted} AU {to_date_formatted}",
            subtitle_style
        ))
        elements.append(Spacer(1, 0.5*cm))
        
        # Préparer les données pour le graphique
        facilities_data = []
        for facility in owner_data.get("facilities", []):
            facility_info = {
                "facilityName": facility.get("facilityName", ""),
                "products": facility.get("products", [])
            }
            facilities_data.append(facility_info)
        
        if not facilities_data:
            elements.append(Paragraph(
                "AUCUNE DONNÉE DE CONSOMMATION DISPONIBLE POUR CE GROUPE.",
                subtitle_style
            ))
            return
        
        # Créer le graphique
        chart_gen = ConsumptionChartGenerator()
        chart_buffer = chart_gen.create_group_product_total_chart(
            facilities_data,
            owner_name
        )
        
        # Ajouter le graphique au PDF
        chart_img = Image(chart_buffer, width=26*cm, height=10*cm)
        elements.append(chart_img)
        elements.append(Spacer(1, 0.5*cm))
        
        # Texte explicatif
        explanation_style = ParagraphStyle(
            'ChartExplanation2',
            fontName='Helvetica',
            fontSize=8,
            alignment=TA_LEFT,
            textColor=colors.black
        )
        legend_text = "CE GRAPHIQUE PRÉSENTE LA CONSOMMATION TOTALE PAR PRODUIT POUR L'ENSEMBLE DES SITES DU GROUPE SUR LA PÉRIODE SÉLECTIONNÉE.<br/>LES CONSOMMATIONS SONT EXPRIMÉES EN LITRES."
        
        elements.append(Paragraph(legend_text, explanation_style))
