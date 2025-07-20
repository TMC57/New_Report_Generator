from datetime import datetime, timedelta
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


def generate_table(facility, from_date: str, to_date: str):
    def build_table(title, date_range_slice, index_offset):
        table_data = []

        # Titre
        table_data.append([title] + [""] * len(date_range_slice))

        # Ligne d'en-tête : jours
        header_row = ["Produit"] + [d.strftime("%d/%m") for d in date_range_slice]
        table_data.append(header_row)

        # Données
        for name, p in zip(product_names, products):
            daily_dict = {entry["date"]: entry["qty"] for entry in p["dailyQuantities"]}
            row = [name]
            for i, date in enumerate(date_range_slice):
                qty_ml = daily_dict.get(date.isoformat(), 0)
                row.append(f"{qty_ml / 10000:.2f} L" if qty_ml != 0 else "") # laisser la cellule vide si 0
            table_data.append(row)

        rl_table = Table(table_data, repeatRows=2)

        style = TableStyle([
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 1), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('SPAN', (0, 0), (-1, 0)),  # Titre fusionné
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ])
        rl_table.setStyle(style)
        return rl_table

    # Préparation des données
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).date() for i in range((end - start).days + 1)]
    products = facility["products"]
    product_names = [p.get("name", "Unknown Product") for p in products]
    facility_name = facility["facilityName"]

    # Séparation en deux si nécessaire
    if len(date_range) > 15:
        first_part = date_range[:15]
        second_part = date_range[15:]

        table1 = build_table(f"{facility_name} – Jours 1 à 15", first_part, 0)
        table2 = build_table(f"{facility_name} – Jours 16 à {len(date_range)}", second_part, 16)

        return [table1, table2]
    else:
        table = build_table(f"{facility_name} – Consommation quotidienne", date_range, 0)
        return [table]
