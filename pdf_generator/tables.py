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

        table1 = build_table(f"Consommation quotidienne jours 1 à 15", first_part, 0)
        table2 = build_table(f"Consommation quotidienne jours 16 à {len(date_range)}", second_part, 16)

        return [table1, table2]
    else:
        table = build_table(f"{facility_name} – Consommation quotidienne", date_range, 0)
        return [table]



def generate_monthly_table(facility, split_every: int = 12):
    """
    Génère un ou plusieurs tableaux ReportLab à partir des MonthlyQuantities d'une facility.
    
    - facility : dict de la facility (avec facility["products"][..]["MonthlyQuantities"])
    - split_every : nombre max de colonnes par tableau (défaut: 12)
    """
    def chunk(lst, size):
        for i in range(0, len(lst), size):
            yield lst[i:i+size]

    def build_table(title, months_chunk):
        table_data = []

        # Titre
        table_data.append([title] + [""] * len(months_chunk))

        # En-tête
        header_row = ["Produit"] + [datetime.strptime(m, "%Y-%m").strftime("%m/%Y") for m in months_chunk]
        table_data.append(header_row)

        # Lignes produits
        for name, p in zip(product_names, products):
            monthly_dict = {entry["month"]: entry["qty"] for entry in p.get("MonthlyQuantities", [])}
            row = [name]
            for m in months_chunk:
                qty_ml = monthly_dict.get(m, 0)
                row.append(f"{qty_ml / 10000:.2f} L" if qty_ml != 0 else "")
            table_data.append(row)

        rl_table = Table(table_data, repeatRows=2)
        style = TableStyle([
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 1), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (0, -1), colors.whitesmoke),
            ('ROWHEIGHT', (0, 1), (-1, 1), 40),
            ('SPAN', (0, 0), (-1, 0)),  # Titre fusionné
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ])
        rl_table.setStyle(style)
        return rl_table

    # Récupérer tous les mois uniques à partir de MonthlyQuantities
    products = facility["products"]
    all_months = set()
    for p in products:
        for entry in p.get("MonthlyQuantities", []):
            all_months.add(entry["month"])

    # Trier les mois par ordre chronologique
    months = sorted(all_months, key=lambda m: datetime.strptime(m, "%Y-%m"))

    product_names = [p.get("name", "Unknown Product") for p in products]
    facility_name = facility["facilityName"]

    # Génération (avec découpage si nécessaire)
    tables = []
    for months_chunk in chunk(months, split_every):
        title = (f"Consommation mensuelle "
                 f"{datetime.strptime(months_chunk[0], '%Y-%m').strftime('%m/%Y')} → "
                 f"{datetime.strptime(months_chunk[-1], '%Y-%m').strftime('%m/%Y')}")
        tables.append(build_table(title, months_chunk))

    return tables
