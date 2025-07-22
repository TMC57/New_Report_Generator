import matplotlib.pyplot as plt
from datetime import datetime, timedelta
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

    filtered_names = []
    filtered_totals = []
    for name, total in zip(product_names, totals):
        if total > 0:
            filtered_names.append(name)
            filtered_totals.append(total)

    def format_liters(pct, all_vals):
        total_ml = sum(all_vals)
        value_ml = pct * total_ml / 100
        value_l = value_ml / 10000
        return f"{value_l:.1f} L"

    fig, pie_ax = plt.subplots(figsize=(5, 5), constrained_layout=True)

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
    pie_ax.margins(0)

    # Légende sous le graphique
    # pie_ax.legend(
    #     wedges,
    #     filtered_names,
    #     loc='upper center',
    #     bbox_to_anchor=(0.5, -0.1),  # centre sous le camembert
    #     fontsize=11,
    #     frameon=False,
    #     ncol=3  # nombre de colonnes pour la légende
    # )

    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    return buf
