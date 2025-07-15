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

    # Filtrer les produits avec une consommation > 0
    filtered_names = []
    filtered_totals = []
    for name, total in zip(product_names, totals):
        if total > 0:
            filtered_names.append(name)
            filtered_totals.append(total)

    fig, ax = plt.subplots(figsize=(6, 6))

    wedges, texts, autotexts = ax.pie(
        filtered_totals,
        labels=None,  # On enlève les labels autour du camembert
        autopct='%1.1f%%',
        startangle=90,
        counterclock=False,
        wedgeprops={'edgecolor': 'black', 'linewidth': 0.2}  # ➜ bordures visibles
    )
    ax.set_title("Répartition par produit")

    # Légende en dessous
    ax.legend(
        wedges,
        filtered_names,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        frameon=False
    )

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf




def generate_bar_chart(facility, from_date: str, to_date: str, output_path: str):
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
            daily_data.append(
                {entry["date"]: entry["qty"] for entry in p["dailyQuantities"]}.get(date.isoformat(), 0)
            )
        data_by_product.append(daily_data)

    # Position de chaque groupe de barres par jour
    x = range(len(date_range))
    width = 0.8 / len(products)  # Largeur des barres, partagée entre les produits

    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, daily_data in enumerate(data_by_product):
        offset = [xi + i * width for xi in x]
        ax.bar(offset, daily_data, width=width, label=product_names[i])

    ax.set_xticks([xi + width * (len(products) / 2) for xi in x])
    ax.set_xticklabels(date_labels, rotation=45)
    ax.set_ylabel("Quantité consommée")
    ax.set_xlabel("Jour")
    ax.set_title(f"{facility['facilityName']} – Consommation quotidienne")
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=5, frameon=False)
    ax.yaxis.grid(True, linestyle='-', alpha=0.5)
    plt.tight_layout()

    plt.savefig(output_path)
    plt.close()


def sanitize_filename(name: str) -> str:
    # Supprime les caractères interdits dans les noms de fichiers Windows
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def generate_pdfs_by_facility(json_data: dict, from_date: str, to_date: str):
    """
    Génère un PDF par facilityId dans le dossier 'reports/'.
    Affiche en titre le nom de la facility, la période et insère un graphique.
    """
    os.makedirs("reports", exist_ok=True)
    os.makedirs("charts", exist_ok=True)

    for facility in json_data["data"]["results"]:
        facility_name = facility["facilityName"]
        facility_id = facility["facilityId"]

        sanitized_name = sanitize_filename(facility_name)
        pdf_path = f"reports/rapport_{sanitized_name}_{facility_id}.pdf"
        chart_path = f"charts/bar_chart_{sanitized_name}_{facility_id}.png"

        # Générer le graphique
        generate_bar_chart(facility, from_date, to_date, chart_path)

        # Créer le PDF
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4

        # Titre
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 3 * cm, facility_name)

        # Sous-titre
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, height - 4 * cm, f"RAPPORT DE CONSOMMATION DU {from_date} AU {to_date}")

        # Insérer l’image (centrée horizontalement)
        if os.path.exists(chart_path):
            image_width = width - 4 * cm
            image = ImageReader(chart_path)
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

            # Générer le camembert
            pie_chart_buffer = generate_pie_chart(facility, from_date, to_date)
            image = ImageReader(pie_chart_buffer)

            # Affiche l'image centrée
            img_width = 300
            img_height = 300
            x = (width - img_width) / 2
            y = height - 700  # Position verticale ajustable

            c.drawImage(image, x, y, width=img_width, height=img_height)

        c.showPage()
        c.save()

    print("PDFs générés dans le dossier 'reports/'")
    return(0)
