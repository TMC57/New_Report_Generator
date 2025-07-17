from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import textwrap
import os

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

    os.makedirs("pictures", exist_ok=True)   
    fig.savefig("pictures/test.png", format='png', bbox_inches='tight')

    plt.close(fig)
    buf.seek(0)
    return buf

