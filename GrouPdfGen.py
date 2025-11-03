# GroupPdfGen.py (remplace la fonction generate_group_pdfs par celle-ci)

# Standard library imports
import json
import os
import re
import textwrap
import unicodedata
from datetime import datetime
from io import BytesIO

# Third-party imports
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from matplotlib import colors as mcolors
from matplotlib import patches as mpatches
from matplotlib.patches import Rectangle

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate, FrameBreak, PageBreak, PageTemplate, 
    Frame, Image as RLImage, Paragraph, Spacer, Table, TableStyle
)

# Local imports
from colors_map import get_colors_for_products
from pdfGen import TOTAL_TABLE_WIDTH, draw_bottom_right_logo, distribute_elements_by_page, get_picture_path

matplotlib.use("Agg")

def _parse_liters_field(v) -> float:
    """Extrait un float en litres depuis '41.233 L', '-8.64 L', '6.0E-4 L', 123.4, etc."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    m = re.search(r'[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?', s)
    if not m:
        return 0.0
    num = m.group(0).replace(',', '.')  # au cas où
    try:
        return float(num)
    except ValueError:
        return 0.0


def _fmt_liters(v: float) -> str:
    return f"{v:,.2f} L".replace(",", " ").replace(".", ",")

def generate_owner_totals_chart(owner_block: dict) -> BytesIO | None:
    """
    TOTAUX par produit (base = 1er mot) pour un owner (toutes facilities cumulées).
    - Barres: une par base produit
    - Remplace l'axe X par un tableau 2 lignes en bas:
        [noms produits]
        [quantités totales (L)]
    - Pas de graduations X
    """
    facilities = owner_block.get("facilities", []) or []
    if not facilities:
        return None

    # Bases de produits (1er mot)
    product_bases = sorted({
        _base_product_name(p.get("name") or "")
        for f in facilities for p in (f.get("products") or [])
        if (p.get("name") or "").strip()
    })
    if not product_bases:
        return None

    # Totaux par base (en L)
    totals = {b: 0.0 for b in product_bases}
    for f in facilities:
        for p in (f.get("products") or []):
            b = _base_product_name(p.get("name") or "")
            if b:
                totals[b] += float(p.get("qty", 0) or 0) / 10000.0

    # Couleurs stables
    colors = get_colors_for_products(product_bases)
    color_map = {b: colors[i] for i, b in enumerate(product_bases)}

    x = np.arange(len(product_bases))
    heights = [totals[b] for b in product_bases]

    # Graphique compact (on libère de la place pour le tableau)
    fig, ax = plt.subplots(figsize=(10, 5))

    # Limiter la largeur des barres pour éviter qu'elles soient trop larges
    bar_width = min(0.25, 0.8 / max(len(product_bases), 1))
    ax.bar(x, heights, width=bar_width, color=[color_map[b] for b in product_bases])

    # Axe X: aucune graduation/label
    ax.set_xticks([])
    ax.tick_params(axis='x', which='both', length=0)

    # Axe Y + grille
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:,.2f} L".replace(",", " ").replace(".", ",")))
    # ax.set_ylabel("Quantité (L)")
    # ax.set_title("TOTAL DES CONSOMMATIONS PAR PRODUIT (toutes installations)")
    ax.grid(True, axis="y", linestyle="-", linewidth=0.8, color="black", alpha=0.3)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # --- Tableau 2 lignes en bas: [produits] / [totaux formatés] ---
    totals_fmt = [ _fmt_liters(totals[b]) for b in product_bases ]
    
    # Wrapper le texte des produits si nécessaire
    wrapped_products = []
    for product in product_bases:
        if len(product) > 15:  # Si le nom est trop long
            wrapped = textwrap.fill(product, width=15)
            wrapped_products.append(wrapped)
        else:
            wrapped_products.append(product)
    
    table2 = plt.table(
        cellText=[wrapped_products, totals_fmt],
        cellLoc="center",
        rowLoc="center",
        loc="bottom"
    )
    # Police + aération
    # Police + aération
    table2.auto_set_font_size(False)
    table2.set_fontsize(8)       # texte un peu plus grand
    table2.scale(1.0, 1.25)       # augmente taille globale du tableau

    # Calculer la hauteur maximale nécessaire pour toutes les cellules
    max_height_factor = 2.0  # facteur minimum
    base_height = None
    
    for (r, c), cell in table2.get_celld().items():
        if base_height is None:
            base_height = cell.get_height()
        text = cell.get_text().get_text()
        num_lines = text.count('\n') + 1
        height_factor = max(2.0, num_lines * 1.5)
        max_height_factor = max(max_height_factor, height_factor)
    
    # Appliquer la même hauteur à toutes les cellules
    for (r, c), cell in table2.get_celld().items():
        cell.set_height(base_height * max_height_factor)

    # -- Assombrir et définir l'épaisseur des bordures du tableau --
    for (r, c), cell in table2.get_celld().items():
        cell.set_linewidth(0.8)   # bordures plus visibles
        cell.set_edgecolor("black")  # bordures bien noires


    # Mesure réelle de la hauteur du tableau → marge basse adaptée
    fig.canvas.draw()
    bbox = table2.get_window_extent(fig.canvas.get_renderer())
    fig_h_px = fig.get_size_inches()[1] * fig.dpi
    table_frac = bbox.height / fig_h_px

    base_bottom = 0.16  # base sans tableau
    pad = 0.02
    bottom = base_bottom + table_frac + pad

    # Légende sous le graphe (facultative, on peut l'omettre car les produits sont dans le tableau)
    handles = [mpatches.Patch(color=color_map[b], label=b) for b in product_bases]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.25),  # plus éloignée du graphique
        ncol=min(6, len(product_bases)),
        frameon=False,
        labelspacing=0.4
    )
    # La légende rajoute un peu de hauteur: remesure rapidement
    fig.canvas.draw()
    bbox2 = table2.get_window_extent(fig.canvas.get_renderer())
    table_frac2 = bbox2.height / fig_h_px
    bottom = base_bottom + table_frac2 + 0.10  # +0.10 pour la légende

    # Marges finales (capées pour éviter d'écraser la zone du graphe)
    plt.subplots_adjust(left=0.06, right=0.99, top=0.90, bottom=min(0.55, bottom))

    # Export image
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    buf.seek(0)
    return buf


def build_owner_totals_table(owner_block: dict) -> Table:
    """
    Tableau 2 colonnes : [Produit (base)] | [Total (L)] pour l'owner (toutes facilities cumulées).
    Colonne 'Produit' à largeur dynamique avec wrap ; chiffres centrés.
    """
    facilities = owner_block.get("facilities", []) or []

    # Bases de produits
    product_bases = sorted({
        _base_product_name(p.get("name") or "")
        for f in facilities for p in (f.get("products") or [])
        if (p.get("name") or "").strip()
    })

    # Totaux par base
    totals = {}
    for b in product_bases:
        t = 0.0
        for f in facilities:
            for p in (f.get("products") or []):
                if _base_product_name(p.get("name") or "") == b:
                    t += float(p.get("qty", 0) or 0) / 10000.0
        totals[b] = t

    # Styles (Paragraph pour wrap si besoin)
    styles = getSampleStyleSheet()
    prod_style = ParagraphStyle(
        "prod_style_page3", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7, leading=10.5, alignment=TA_LEFT
    )
    head_style = ParagraphStyle(
        "head_style_page3", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=7, leading=11, alignment=TA_CENTER
    )

    data = [
        [Paragraph("Produits", head_style), Paragraph("Total (L)", head_style)]
    ]
    for b in product_bases:
        data.append([Paragraph(b, prod_style), _fmt_liters(totals[b])])

    # Largeurs dynamiques
    TOTAL_W = 25 * cm
    MIN_PROD_W, MAX_PROD_W = 4.0 * cm, 8.0 * cm

    def text_w(s: str) -> float:
        return pdfmetrics.stringWidth(s, "Helvetica", 8.5)

    longest_label = max(product_bases, key=lambda t: text_w(t), default="")
    needed_pts = text_w(longest_label) + 14
    needed_cm  = needed_pts / 28.3465
    prod_col_w = max(MIN_PROD_W, min(MAX_PROD_W, needed_cm))
    total_col_w = TOTAL_W - prod_col_w

    tbl = Table(data, colWidths=[prod_col_w, total_col_w], repeatRows=1)
    tbl.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),   # colonne 'Total' centrée
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),     # colonne 'Produits' à gauche
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return tbl


def build_group_consumption_table(owner_block: dict) -> Table:
    """Tableau Bases × Sites (valeurs en L), colonne 'Produits' à largeur dynamique + retours à la ligne."""
    facilities = owner_block.get("facilities", []) or []
    owner_name = owner_block.get("owner", "")
    facility_labels_raw = [_short_facility_name(f.get("facilityName", ""), owner_name) for f in facilities]

    # Bases de produits (1er mot)
    product_bases = sorted({
        _base_product_name(p.get("name") or "")
        for f in facilities for p in (f.get("products") or [])
        if (p.get("name") or "").strip()
    })

    # Styles pour permettre le wrap
    styles = getSampleStyleSheet()
    prod_style = ParagraphStyle(
        "prod_style", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7, leading=10.5,
        alignment=TA_LEFT
    )
    head_style = ParagraphStyle(
        "head_style", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=7, leading=11,
        alignment=TA_CENTER
    )

    # ---------- Données ----------
    # En-têtes (wrap possible si noms de sites longs)
    # Remplacer les espaces par des espaces insécables pour éviter la coupure
    header_row = [Paragraph("Produits", head_style)] + [Paragraph(lbl.replace(" ", "&nbsp;"), head_style) for lbl in facility_labels_raw]
    data = [header_row]

    # Corps
    for base in product_bases:
        row = [Paragraph(base, prod_style)]
        for fac in facilities:
            total_l = 0.0
            for p in (fac.get("products") or []):
                if _base_product_name(p.get("name") or "") == base:
                    total_l += float(p.get("qty", 0) or 0) / 10000.0
            row.append(_fmt_liters(total_l))
        data.append(row)

    # ---------- Largeurs dynamiques ----------
    TOTAL_W = 25 * cm               # largeur totale visée
    MIN_PROD_W = 6.0 * cm           # bornes pour la 1ère colonne
    MAX_PROD_W = 11.0 * cm

    # Estimer largeur nécessaire pour la 1ère col via la largeur du plus long libellé (Helvetica 8.5)
    def text_w(s: str) -> float:
        return pdfmetrics.stringWidth(s, "Helvetica", 8.5)

    longest = max([len(b) for b in product_bases], default=0)
    # meilleure estimation que la longueur brute : utilise stringWidth sur le plus long libellé
    longest_label = max(product_bases, key=lambda t: text_w(t), default="")
    needed_pts = text_w(longest_label) + 14  # + padding estimé
    needed_cm = needed_pts / 28.3465         # 1 cm ≈ 28.3465 points

    prod_col_w = max(MIN_PROD_W, min(MAX_PROD_W, needed_cm))
    n_sites = max(len(facility_labels_raw), 1)
    site_col_w = (TOTAL_W - prod_col_w) / n_sites
    col_widths = [prod_col_w] + [site_col_w] * len(facility_labels_raw)

    # ---------- Table ----------
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),

        # tailles de police : déjà portées par Paragraph, mais on garde un fallback uniforme
        ('FONTSIZE', (0, 0), (-1, -1), 7),

        # Alignements
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # valeurs
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # 1ère colonne à gauche (Paragraph le fait déjà, mais on force au cas où)
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),

        # Grille & respirations
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 5),     # aération verticale
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return tbl


def _short_facility_name(name: str, owner_name: str = "") -> str:
    """Simplifie les noms de facilities :
       - si '\t' présent → prend ce qui est après
       - sinon si '|' présent → prend ce qui est après
       - sinon → tout le nom
       - enlève les chiffres + espaces en début de chaîne
       - enlève le owner_name s'il est présent au début
    """
    if not name:
        return ""
    name = name.strip()

    # priorité au '\t'
    if "\t" in name:
        name = name.split("\t", 1)[1].strip()
    elif "|" in name:
        name = name.split("|", 1)[1].strip()

    # enlever le owner_name s'il est au début du nom
    if owner_name and len(owner_name) > 2:  # seulement si owner_name significatif
        # Essayer différentes variantes de l'owner_name
        owner_variants = [
            owner_name,
            owner_name.replace(" ", ""),  # sans espaces
            owner_name.split()[0] if " " in owner_name else owner_name,  # premier mot seulement
        ]
        
        for variant in owner_variants:
            if variant and name.upper().startswith(variant.upper()):
                name = name[len(variant):].strip()
                # enlever les séparateurs restants au début
                name = re.sub(r'^[-|,\s]+', '', name)
                break

    # enlever chiffres + espaces au début
    name = re.sub(r'^\d+\s*', '', name)
    return name



def generate_group_bar_chart(owner_block: dict) -> BytesIO | None:
    """
    Bar chart groupé PRODUITS × SITES :
      - Regroupe les produits par 'base' (1er mot)
      - Barres triées décroissantes à l'intérieur de chaque site
      - Axe X muet (ticks/labels supprimés)
      - Tableau 1D en bas avec seulement les noms des sites (police plus grande)
      - Légende standard des produits (par base), couleurs via colors_map
    """
    facilities = owner_block.get("facilities", []) or []
    if not facilities:
        return None

    # Labels sites
    owner_name = owner_block.get("owner", "")
    facility_labels = [_short_facility_name(f.get("facilityName", ""), owner_name) for f in facilities]
    n_sites = len(facility_labels)

    # ---- Regroupement par 'base' ----
    # product_bases = ensemble des bases
    product_bases = sorted({
        _base_product_name(p.get("name") or "")
        for fac in facilities for p in (fac.get("products") or [])
        if (p.get("name") or "").strip()
    })
    if not product_bases:
        return None
    n_prod = len(product_bases)

    # Quantités en L par site/base
    # quantities[fi][base] = litres
    quantities: list[dict[str, float]] = []
    for fac in facilities:
        agg: dict[str, float] = {base: 0.0 for base in product_bases}
        for p in (fac.get("products") or []):
            base = _base_product_name(p.get("name") or "")
            if base:
                agg[base] = agg.get(base, 0.0) + float(p.get("qty", 0) or 0) / 10000.0
        quantities.append(agg)

    # Couleurs cohérentes et légende
    colors = get_colors_for_products(product_bases)
    color_map = {base: colors[i] for i, base in enumerate(product_bases)}

    # Placement des barres
    group_width = 0.9
    left_pad    = 0.05
    bar_width   = max(group_width / max(n_prod, 1), 0.06)
    # Limiter la largeur maximale des barres pour éviter qu'elles soient trop larges
    bar_width   = min(bar_width, 0.15)

    fig, ax = plt.subplots(figsize=(11, 4))

    # Trace par site avec tri local décroissant (supprime les "trous")
    for fi in range(n_sites):
        sorted_bases = sorted(product_bases, key=lambda b: quantities[fi][b], reverse=True)
        for j, base in enumerate(sorted_bases):
            h   = quantities[fi][base]
            pos = fi + left_pad + j * bar_width
            ax.bar(pos, h, width=bar_width, align="edge", color=color_map[base])

    # Axe X muet
    ax.set_xticks([])
    ax.tick_params(axis='x', which='both', length=0)
    ax.set_xlim(0, n_sites)

    # Axe Y + grille
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:,.2f} L".replace(",", " ").replace(".", ",")))
    ax.grid(True, axis="y", linestyle="-", linewidth=0.8, color="black", alpha=0.3)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Légende (bases)
    handles = [mpatches.Patch(color=color_map[b], label=b) for b in product_bases]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.15),
              ncol=min(6, n_prod), frameon=False)

    # Tableau 1D des sites avec retour à la ligne automatique
    wrapped_labels = []
    for label in facility_labels:
        if len(label) > 15:  # Si le nom est trop long
            wrapped = textwrap.fill(label, width=12)
            wrapped_labels.append(wrapped)
        else:
            wrapped_labels.append(label)
    
    site_table = plt.table(cellText=[wrapped_labels], cellLoc="center", rowLoc="center", loc="bottom")
    # Ajuster la taille de police selon le nombre de facilities
    num_facilities = len(facility_labels)
    if num_facilities <= 5:
        font_size = 6
    elif num_facilities <= 10:
        font_size = 5
    elif num_facilities <= 15:
        font_size = 4
    else:
        font_size = 3
    site_table.auto_set_font_size(False); site_table.set_fontsize(font_size); site_table.scale(1.0, 1.35)
    # Calculer la hauteur maximale nécessaire pour toutes les cellules
    max_height_factor = 1.2  # facteur minimum réduit
    base_height = None
    
    for (r, c), cell in site_table.get_celld().items():
        if base_height is None:
            base_height = cell.get_height()
        text = cell.get_text().get_text()
        num_lines = text.count('\n') + 1
        height_factor = max(1.2, num_lines * 0.8)
        max_height_factor = max(max_height_factor, height_factor)
    
    # Appliquer la même hauteur à toutes les cellules et améliorer la lisibilité
    for (r, c), cell in site_table.get_celld().items():
        cell.set_height(base_height * max_height_factor)
        cell.set_linewidth(1.0)
        cell.set_edgecolor("black")
        # Améliorer la lisibilité pour l'impression
        cell.get_text().set_weight('bold')
        cell.get_text().set_color('black')

    # Ajuster la marge basse pour accueillir légende + tableau 1D
    plt.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.38)


    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    buf.seek(0)
    return buf


def _base_product_name(name: str) -> str:
    """Retourne la 'base' du produit = ce qu'il y a avant le '-' (normalisé en majuscules)."""
    return (name or "").strip().split("-", 1)[0].strip().upper()


def _sanitize_filename(s: str, max_len: int = 120) -> str:
    if not s:
        return "untitled"
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[\t\r\n]+", " ", s)
    s = re.sub(r'[<>:\"/\\|?*]+', "_", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace(" ", "_")[:max_len]

def _read_group_config() -> list[dict]:
    for path in (os.path.join("Config","GroupConfigJson.json"),
                 os.path.join("config","GroupConfigJson.json")):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f) or []
    return []

def _make_email_link(email: str) -> str:
    if email and email != "N/A":
        return f'<font color="blue"><u><a href="mailto:{email}">{email}</a></u></font>'
    return "N/A"

def _build_owner_footer(owner_row: dict):
    centered_style = ParagraphStyle(name="centered_style", alignment=TA_CENTER, fontSize=10)
    inv = owner_row.get("inventory_monitoring_manager", {}) or {}
    cust = owner_row.get("customer_technical_relay_manager", {}) or {}
    ref = owner_row.get("file_referent", {}) or {}

    data = [[
        Paragraph(
            "Responsable suivi des stocks<br/>Würth<br/>"
            f"<b>{inv.get('full_name', 'N/A')}</b><br/>"
            f"{_make_email_link(inv.get('mail_adresse', 'N/A'))}<br/>"
            f"<b>{inv.get('phone_number', 'N/A')}</b>", centered_style
        ),
        Paragraph(
            "Responsable relais technique<br/>client<br/>"
            f"<b>{cust.get('full_name', 'N/A')}</b><br/>"
            f"{_make_email_link(cust.get('mail_adresse', 'N/A'))}<br/>"
            f"<b>{cust.get('phone_number', 'N/A')}</b>", centered_style
        ),
        Paragraph(
            "Référent dossier Würth<br/>"
            f"<b>{ref.get('full_name', 'N/A')}</b><br/>"
            f"{_make_email_link(ref.get('mail_adresse', 'N/A'))}<br/>"
            f"<b>{ref.get('phone_number', 'N/A')}</b>", centered_style
        ),
    ]]

    table = Table(data, colWidths=[6*cm, 6*cm, 6*cm])
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBEFORE", (1, 0), (1, 0), 0.5, colors.black),
        ("LINEAFTER", (1, 0), (1, 0), 0.5, colors.black),
    ]))
    return table

def generate_group_stock_chart(owner_stock_block: dict) -> BytesIO | None:
    facilities = (owner_stock_block or {}).get("facilities", []) or []
    if not facilities:
        return None

    owner_name = owner_stock_block.get("owner", "")
    facility_labels = [_short_facility_name(f.get("facilityName", ""), owner_name) for f in facilities]
    
    # Ajouter "Groupe" à la fin
    facility_labels.append("Groupe")
    n_sites = len(facility_labels)

    product_bases = sorted({
        _base_product_name(p.get("name") or "")
        for fac in facilities for p in (fac.get("products") or [])
        if (p.get("name") or "").strip()
    })
    if not product_bases:
        return None
    n_prod = len(product_bases)

    # 👉 stocks en L (parser remainingQuantity)
    quantities = []
    group_totals = {b: 0.0 for b in product_bases}
    
    for fac in facilities:
        agg = {b: 0.0 for b in product_bases}
        for p in (fac.get("products") or []):
            base = _base_product_name(p.get("name") or "")
            if base:
                stock_value = _parse_liters_field(p.get("remainingQuantity"))
                agg[base] += stock_value
                group_totals[base] += stock_value
        quantities.append(agg)
    
    # Ajouter les totaux du groupe à la fin
    quantities.append(group_totals)

    colors = get_colors_for_products(product_bases)
    color_map = {b: colors[i] for i, b in enumerate(product_bases)}

    group_width = 0.9
    left_pad    = 0.05
    bar_width   = max(group_width / max(n_prod, 1), 0.06)
    # Limiter la largeur maximale des barres pour éviter qu'elles soient trop larges
    bar_width   = min(bar_width, 0.15)

    fig, ax = plt.subplots(figsize=(10, 5))

    # barres triées localement
    for fi in range(n_sites):
        sorted_bases = sorted(product_bases, key=lambda b: quantities[fi][b], reverse=True)
        for j, b in enumerate(sorted_bases):
            h   = quantities[fi][b]
            pos = fi + left_pad + j * bar_width
            ax.bar(pos, h, width=bar_width, align="edge", color=color_map[b])

    ax.set_xticks([]); ax.tick_params(axis='x', which='both', length=0)
    ax.set_xlim(0, n_sites)

    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:,.2f} L".replace(",", " ").replace(".", ",")))
    ax.grid(True, axis="y", linestyle="-", linewidth=0.8, color="black", alpha=0.3)
    for s in ax.spines.values():
        s.set_visible(False)

    handles = [mpatches.Patch(color=color_map[b], label=b) for b in product_bases]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.28),
              ncol=min(6, n_prod), frameon=False, labelspacing=0.4)

    # Tableau 1D des sites avec retour à la ligne automatique
    wrapped_labels = []
    for label in facility_labels:
        if len(label) > 15:  # Si le nom est trop long
            wrapped = textwrap.fill(label, width=12)
            wrapped_labels.append(wrapped)
        else:
            wrapped_labels.append(label)
    
    site_table = plt.table(cellText=[wrapped_labels], cellLoc="center", rowLoc="center", loc="bottom")
    # Ajuster la taille de police selon le nombre de facilities
    num_facilities = len(facility_labels)
    if num_facilities <= 5:
        font_size = 6
    elif num_facilities <= 10:
        font_size = 5
    elif num_facilities <= 15:
        font_size = 4
    else:
        font_size = 3
    site_table.auto_set_font_size(False); site_table.set_fontsize(font_size); site_table.scale(1.0, 1.35)
    # Calculer la hauteur maximale nécessaire pour toutes les cellules
    max_height_factor = 1.2  # facteur minimum réduit
    base_height = None
    
    for (r, c), cell in site_table.get_celld().items():
        if base_height is None:
            base_height = cell.get_height()
        text = cell.get_text().get_text()
        num_lines = text.count('\n') + 1
        height_factor = max(1.2, num_lines * 0.8)
        max_height_factor = max(max_height_factor, height_factor)
    
    # Appliquer la même hauteur à toutes les cellules
    for (r, c), cell in site_table.get_celld().items():
        cell.set_height(base_height * max_height_factor)

    fig.canvas.draw()
    bbox = site_table.get_window_extent(fig.canvas.get_renderer())
    fig_h_px = fig.get_size_inches()[1] * fig.dpi
    table_frac = bbox.height / fig_h_px
    bottom = min(0.42, 0.18 + table_frac + 0.02)
    plt.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=bottom)

    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight", dpi=300); plt.close(fig); buf.seek(0)
    return buf


def build_group_stock_table(owner_stock_block: dict) -> Table:
    facilities = (owner_stock_block or {}).get("facilities", []) or []
    owner_name = (owner_stock_block or {}).get("owner", "")
    facility_labels = [_short_facility_name(f.get("facilityName", ""), owner_name) for f in facilities]
    
    # Ajouter "Groupe" à la fin
    facility_labels.append("Groupe")

    product_bases = sorted({
        _base_product_name(p.get("name") or "")
        for f in facilities for p in (f.get("products") or [])
        if (p.get("name") or "").strip()
    })

    styles = getSampleStyleSheet()
    prod_style = ParagraphStyle("prod_style_stock", parent=styles["Normal"],
                                fontName="Helvetica", fontSize=7, leading=10.5, alignment=TA_LEFT)
    head_style = ParagraphStyle("head_style_stock", parent=styles["Normal"],
                                fontName="Helvetica-Bold", fontSize=7, leading=11, alignment=TA_CENTER)

    # Remplacer les espaces par des espaces insécables pour éviter la coupure
    data = [[Paragraph("Produits", head_style)] + [Paragraph(lbl.replace(" ", "&nbsp;"), head_style) for lbl in facility_labels]]

    for base in product_bases:
        row = [Paragraph(base, prod_style)]
        group_total = 0.0
        
        # Calculer pour chaque facility + cumul groupe
        for fac in facilities:
            total_l = 0.0
            for p in (fac.get("products") or []):
                if _base_product_name(p.get("name") or "") == base:
                    stock_value = _parse_liters_field(p.get("remainingQuantity"))
                    total_l += stock_value
                    group_total += stock_value
            row.append(_fmt_liters(total_l))
        
        # Ajouter le total groupe à la fin
        row.append(_fmt_liters(group_total))
        data.append(row)

    TOTAL_W = 25 * cm
    MIN_PROD_W, MAX_PROD_W = 4.0 * cm, 8.0 * cm

    def text_w(s: str) -> float:
        return pdfmetrics.stringWidth(s, "Helvetica", 8.5)

    longest_label = max(product_bases, key=lambda t: text_w(t), default="")
    needed_pts = text_w(longest_label) + 14
    needed_cm  = needed_pts / 28.3465
    prod_col_w = max(MIN_PROD_W, min(MAX_PROD_W, needed_cm))
    n_sites = max(len(facility_labels), 1)
    site_col_w = (TOTAL_W - prod_col_w) / n_sites
    col_widths = [prod_col_w] + [site_col_w] * len(facility_labels)

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return tbl



def generate_group_pdfs(total_qty: dict,
                        devices_list: dict,
                        stock_levels_grouped: dict,
                        from_date: str,
                        to_date: str) -> int:
    """
    Génère un PDF par owner (défini dans ./Config/GroupConfigJson.json).
    - Page 1 : logo + image de couverture (depuis le JSON) + titres.
    - Page 2 : graphique barres groupées (X=sites, Y=quantités L, barres=produits).
    - Pages 3 & 4 : placeholders.
    - Footer collé en bas (frame dédiée) avec les infos du JSON (managers / référent).
    """
    # --- Charger la config groupe (owners) ---
    group_config = _read_group_config()

    # --- Index des owners depuis total_qty pour accéder rapidement au bloc owner -> facilities -> products ---
    owners_index = {}
    for ob in (total_qty or {}).get("owners", []) or []:
        owners_index[ob.get("owner")] = ob

    owners_stock_index = {}
    for ob in (stock_levels_grouped or {}).get("owners", []) or []:
        owners_stock_index[ob.get("owner")] = ob
    

    # --- Dossier de sortie (même logique que pdfGen.generate_pdfs_by_facility) ---
    DATA_ROOT = os.getenv("DATA_ROOT", "./Reports")
    folder_name = f"group reports {from_date} to {to_date}"
    output_dir = os.path.join(DATA_ROOT, folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # --- Styles & assets ---
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h2_style = styles["Heading2"]
    normal_style = styles["Normal"]

    TMH_logo_path = "images/Logo - Orsy e wash.png"
    tmh_logo = RLImage(TMH_logo_path, width=26.43/2.5*cm, height=4/2.5*cm)

    from_dt = datetime.strptime(from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    to_dt   = datetime.strptime(to_date,   "%Y-%m-%d").strftime("%d/%m/%Y")

    # --- Frames IDENTIQUES à pdfGen.py ---
    PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
    main_frame   = Frame(2*cm, 3*cm, PAGE_WIDTH - 3*cm, PAGE_HEIGHT - 3*cm, id='main_frame')
    footer_frame = Frame(2*cm, -0.2*cm, PAGE_WIDTH - 3*cm, 3.5*cm, id='footer_frame')
    page_template = PageTemplate(id='TwoFrames', frames=[main_frame, footer_frame], onPage=draw_bottom_right_logo)

    # --- Pour chaque owner du JSON de groupe : produire un PDF ---
    for owner_row in group_config:
        owner_name = owner_row.get("owner") or "OWNER"
        
        # --- Filtrer les groupes avec "Croix rouge.jpg" ---
        cover_picture = owner_row.get("cover_picture", "")
        if cover_picture.endswith("Croix rouge.jpg"):
            print(f"⚠️  Ignorer le groupe '{owner_name}' (image: Croix rouge.jpg)")
            continue
        
        safe_owner = _sanitize_filename(owner_name)

        # Récupérer le bloc owner pour extraire le premier facility_id
        owner_data_temp = owners_index.get(owner_name) or {"facilities": []}
        first_facility_id = ""
        if owner_data_temp.get("facilities"):
            first_facility_id = str(owner_data_temp["facilities"][0].get("facilityId", ""))

        pdf_path = os.path.join(output_dir, f"Rapports de consommation_{first_facility_id}_{safe_owner}.pdf")

        # Footer spécifique owner
        owner_footer = _build_owner_footer(owner_row)

        # Titres
        title = Paragraph(f"RAPPORT DE CONSOMMATION DU {from_dt} au {to_dt}", title_style)
        title2 = Paragraph(f"GROUPE {owner_name}", title_style)
        # title3 = Paragraph(f"GROUPE {owner_name}", title_style)

        titlePage2 = Paragraph(f"REPARTITION DES CONSOMMATIONS DE PRODUITS / SITE", title_style)
        titlePage3 = Paragraph(f"TOTAL DES REPARTITIONS DES CONSOMMATIONS DE PRODUITS", title_style)

        subtitle = Paragraph(f"Période du {from_dt} au {to_dt}", h2_style)

        # Image de couverture (via get_picture_path) — on fabrique un config_data minimal
        _FID = -1  # id fictif uniquement pour utiliser get_picture_path
        group_cfg_for_image = [{
            "facilityId": _FID,
            "cover_picture": owner_row.get("cover_picture", "")
        }]
        cover_path, cover_w, cover_h = get_picture_path(_FID, group_cfg_for_image, "cover_picture")
        cover_img = RLImage(cover_path, cover_w, cover_h)

        # Récup bloc owner (facilities/products) pour la page 2 (graphe)
        owner_data = owners_index.get(owner_name) or {"facilities": []}

        facilities_line = " - ".join(_short_facility_name(f.get("facilityName", ""), owner_name) 
                             for f in owner_data.get("facilities", []))
        title3 = Paragraph(facilities_line, title_style)

        # === Pages dict (sera aplati via distribute_elements_by_page) ===
        pages: dict[int, list] = {}

        # ---------------- Page 1 : Logo + Cover + Titres ----------------
        pages[1] = [
            Spacer(1, 0.1*cm), tmh_logo, Spacer(1, 0.5*cm), title, Spacer(1, 0.3*cm), title2, Spacer(1, 0.3*cm), title3, Spacer(1, 0.3*cm),
            cover_img,
            FrameBreak(),
            owner_footer
        ]

        # ---------------- Page 2 : Graphe barres groupées ----------------

        # ---------------- Page 2 : Logo + graphe + tableau + footer ----------------
        buf_chart = generate_group_bar_chart(owner_data)
        if buf_chart:
            chart_img = RLImage(buf_chart, width=25*cm, height=9*cm)
            table_flowable = build_group_consumption_table(owner_data)

            pages[2] = [
                Spacer(1, 0.1*cm), tmh_logo, Spacer(1, 0.8*cm), titlePage2, Spacer(1, 0.1*cm),
                chart_img,
                Spacer(1, 0.3*cm),
                table_flowable,
                FrameBreak(),
                owner_footer
            ]
        else:
            pages[2] = [
                Spacer(1, 0.1*cm), tmh_logo, Spacer(1, 0.6*cm),
                Paragraph("Aucune donnée disponible pour cet owner.", normal_style),
                FrameBreak(),
                owner_footer
            ]



        # ---------------- Pages 3 & 4 : placeholders ----------------
        # ---------------- Page 3 : tableau de consommations + footer ----------------
        # ---------------- Page 3 : Totaux par produit (graphe + tableau) ----------------
        buf_totals = generate_owner_totals_chart(owner_data)
        totals_table = build_owner_totals_table(owner_data)

        if buf_totals:
            totals_img = RLImage(buf_totals, width=25*cm, height=9*cm)  # un peu plus compact
            pages[3] = [
                Spacer(1, 0.1*cm), tmh_logo, Spacer(1, 2*cm), titlePage3, Spacer(1, 0.4*cm),
                totals_img,
                Spacer(1, 0.4*cm),
                # totals_table,
                FrameBreak(),
                owner_footer
            ]
        else:
            pages[3] = [
                Spacer(1, 0.1*cm), tmh_logo, Spacer(1, 0.8*cm),
                title, Spacer(1, 0.3*cm), subtitle,
                Spacer(1, 0.6*cm),
                Paragraph("Aucune donnée (totaux) disponible pour cet owner.", normal_style),
                FrameBreak(),
                owner_footer
            ]

                # ---------------- Page 4 : État des stocks (même compo que page 2) ----------------
        owner_stock = owners_stock_index.get(owner_name) or {"facilities": []}
        # Récupérer le currentTime global
        ts = stock_levels_grouped.get("currentTime")
        if ts:
            # convertit le timestamp ms en datetime lisible
            dt_cur = datetime.fromtimestamp(ts / 1000.0)
            current_time_str = dt_cur.strftime("%d/%m/%Y %H:%M")
        else:
            current_time_str = "N/A"
        titlePage4 = Paragraph(f"ÉTAT DES STOCKS GROUPE AU {current_time_str}", title_style)

        buf_stock_chart = generate_group_stock_chart(owner_stock)
        stock_table = build_group_stock_table(owner_stock)

        if buf_stock_chart:
            stock_img = RLImage(buf_stock_chart, width=25*cm, height=9*cm)
            pages[4] = [
                Spacer(1, 0.1*cm), tmh_logo, Spacer(1, 0.3*cm), titlePage4, 
                stock_img,
                Spacer(1, 0.4*cm),
                stock_table,
                FrameBreak(),
                owner_footer
            ]
        else:
            pages[4] = [
                Spacer(1, 0.1*cm), tmh_logo, Spacer(1, 0.8*cm),
                title, Spacer(1, 0.3*cm), subtitle,
                Spacer(1, 0.6*cm),
                Paragraph("Aucune donnée de stock disponible pour cet owner.", normal_style),
                FrameBreak(),
                owner_footer
            ]


        # --- Aplatir en flowables dans l'ordre des pages ---
        elements = distribute_elements_by_page(pages)

        # --- Construire le document ---
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

        print(f"[Group PDF] Généré pour owner '{owner_name}' → {pdf_path}")

    return 0
