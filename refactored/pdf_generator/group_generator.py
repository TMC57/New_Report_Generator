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
            facilities_text = " / ".join(facility_names)
            
            # Style plus petit pour la liste des facilities
            facilities_style = ParagraphStyle(
                'FacilitiesList',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(facilities_text.upper(), facilities_style))
        
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
