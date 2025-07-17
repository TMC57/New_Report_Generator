import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
import matplotlib.ticker as ticker


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
