from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
import os
import re
import matplotlib   
matplotlib.use("Agg")   
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from reportlab.platypus import Image
from reportlab.lib.utils import ImageReader
from io import BytesIO
import matplotlib.ticker as ticker
import textwrap

def generate_table_chart(facility, from_date: str, to_date: str):
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).date() for i in range((end - start).days + 1)]
    date_labels = [d.strftime("%d/%m") for d in date_range]

    products = facility["products"]
    product_names = [p.get("name", "Unknown Product") for p in products]

    # Construction des données pour le tableau
    table_data = []

    # Ligne de titre
    full_title = ""  # f"{facility['facilityName']} – Consommation quotidienne (en litres)"
    title_row = [""] + [full_title] + [""] * (len(date_labels) - 1)
    table_data.append(title_row)

    # En-tête avec les dates
    header_row = [""] + date_labels
    table_data.append(header_row)

    # Données des produits
    for name, p in zip(product_names, products):
        daily_data = []
        daily_dict = {entry["date"]: entry["qty"] for entry in p["dailyQuantities"]}
        for date in date_range:
            qty_ml = daily_dict.get(date.isoformat(), 0)
            qty_l = f"{qty_ml / 1000:.1f} L"
            daily_data.append(qty_l)
        table_data.append([name] + daily_data)

    # Taille automatique selon le nombre de jours
    fig_width = max(8, len(date_range) * 0.8)
    fig_height = len(products) * 0.6 + 2

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')
    ax.axis('tight')

    table = ax.table(
        cellText=table_data,
        cellLoc='center',
        loc='center'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.2, 1.5)

    # Forcer la première colonne à être plus large
    col_widths = [0.15] + [0.05] * len(date_labels)
    for i, width in enumerate(col_widths):
        for row in range(len(table_data)):
            if (row, i) in table.get_celld():
                table[(row, i)].set_width(width)

    # Ajustement des cellules
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_fontsize(12)
            cell.set_linewidth(0)
            cell.set_facecolor('#FFFFFF')  # Titre
        elif row == 1 or col == 0:
            cell.set_facecolor('#E0E0E0')  # En-têtes
            cell.set_text_props(weight='bold')

    # Ajustement des hauteurs de lignes pour les noms longs
    for row in range(2, len(table_data)):
        name = table_data[row][0]
        max_width = 20
        wrapped_name = "\n".join(textwrap.wrap(name, width=max_width))
        num_lines = wrapped_name.count("\n") + 1
        table[(row, 0)].get_text().set_text(wrapped_name)

        # Détermine la hauteur selon le nombre de lignes
        if num_lines == 1:
            height = 0.08
            fontsize = 8
        elif num_lines == 2:
            height = 0.12
            fontsize = 7
        else:
            height = 0.15
            fontsize = 6

        # Appliquer à toutes les colonnes de la ligne
        for col in range(len(table_data[row])):
            cell = table[(row, col)]
            cell.set_height(height)
            if col == 0:
                cell.set_fontsize(fontsize)

    plt.subplots_adjust(top=0.95)

    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    fig.savefig("charts/test.png", format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf




def generate_pie_chart(facility, from_date: str, to_date: str):
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).date() for i in range((end - start).days + 1)]

    products = facility["products"]
    product_names = [p.get("name", "Unknown Product") for p in products]

    totals = []
    for p in products:
        total_qty = 0
        daily_qty_dict = {entry["date"]: entry["qty"] for entry in p["dailyQuantities"]}
        for date in date_range:
            total_qty += daily_qty_dict.get(date.isoformat(), 0)
        totals.append(total_qty)

    filtered_names = []
    filtered_totals = []
    for name, total in zip(product_names, totals):
        if total > 0:
            filtered_names.append(name)
            filtered_totals.append(total)

    def format_liters(pct, all_vals):
        total_ml = sum(all_vals)
        value_ml = pct * total_ml / 100
        value_l = value_ml / 1000
        return f"{value_l:.1f} L"

    # ✅ Figure plus large pour placer les deux éléments côte à côte
    fig = plt.figure(figsize=(7, 7))

    # ✅ Axe du camembert (à gauche)
    pie_ax = fig.add_axes([0.05, 0.1, 0.55, 0.8])  # [left, bottom, width, height]
    wedges, texts, autotexts = pie_ax.pie(
        filtered_totals,
        labels=None,
        autopct=lambda pct: format_liters(pct, filtered_totals),
        startangle=90,
        counterclock=False,
        wedgeprops={'edgecolor': 'black', 'linewidth': 0.2},
        normalize=True
    )
    pie_ax.set_aspect('equal')

    # ✅ Axe de la légende (à droite, centré verticalement)
    legend_ax = fig.add_axes([0.65, 0.1, 0.3, 0.8])
    legend_ax.axis('off')
    legend_ax.legend(
        wedges,
        filtered_names,
        loc='center',
        fontsize=11,
        frameon=False
    )

    fig.suptitle("CONSOMMATION TOTALE MENSUELLE", fontsize=14, y=0.85)

    buf = BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)  
    buf.seek(0)

    return buf


def generate_bar_chart(facility, from_date: str, to_date: str):
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).date() for i in range((end - start).days + 1)]
    date_labels = [d.strftime("%d/%m") for d in date_range]

    products = facility["products"]
    product_names = [p.get("name", "Unknown Product") for p in products]

    # Préparation des données
    data_by_product = []
    for p in products:
        daily_data = []
        for date in date_range:
            qty_ml = {entry["date"]: entry["qty"] for entry in p["dailyQuantities"]}.get(date.isoformat(), 0)
            daily_data.append(qty_ml / 1000)  # ➤ Convertir en litres
        data_by_product.append(daily_data)

    # Position de chaque groupe de barres par jour
    x = range(len(date_range))
    width = 0.8 / len(products)

    fig, ax = plt.subplots(figsize=(12, 6))

    for i, daily_data in enumerate(data_by_product):
        offset = [xi + i * width for xi in x]
        ax.bar(offset, daily_data, width=width, label=product_names[i])

    ax.set_xticks([xi + width * (len(products) / 2) for xi in x])
    ax.set_xticklabels(date_labels, rotation=45)

    # ➤ Formater l’axe Y avec le suffixe "L"
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{x:.0f} L"))

    ax.set_title(f"{facility['facilityName']} – Consommation quotidienne")
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=5, frameon=False)
    ax.yaxis.grid(True, linestyle='-', alpha=0.5)
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


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