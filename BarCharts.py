import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
import matplotlib.ticker as ticker
from colors_map import get_colors_for_products  # <-- AJOUT
import matplotlib.dates as mdates

def generate_bar_chart(facility, from_date: str, to_date: str):
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")

    date_range = [(start + timedelta(days=i)).date() for i in range((end - start).days + 1)]
    date_labels = [d.strftime("%d/%m") for d in date_range]

    products = facility["products"]
    product_names = [p.get("name", "Unknown Product") for p in products]

    colors = get_colors_for_products(product_names)

    # Préparation des données
    data_by_product = []
    max_qty = 0
    for p in products:
        daily_data = []
        for date in date_range:
            qty_ml = {entry["date"]: entry["qty"] for entry in p["dailyQuantities"]}.get(date.isoformat(), 0)
            daily_data.append(qty_ml / 10000) # to divide per 1000 eventualy
        max_qty = max(max_qty, max(daily_data, default=0))
        data_by_product.append(daily_data)

    # Appliquer la conversion
    for i in range(len(data_by_product)):
        data_by_product[i] = [qty  for qty in data_by_product[i]]

    # Position de chaque groupe de barres par jour
    # -- après avoir construit date_range, products, etc. --

    x = range(len(date_range))  # une graduation par jour, à 0,1,2,...

    # largeur totale occupée par le groupe dans [jour, jour+1)
    group_width = 0.9           # 90% de l’espace d’un jour (laisse un petit gap)
    bar_width   = group_width / len(products)
    left_pad    = 0.05          # petit décalage "juste après" la graduation

    fig, ax = plt.subplots(figsize=(12, 6))

    for i, daily_data in enumerate(data_by_product):
        # position = début du jour + petit pad + décalage par produit
        pos = [xi + left_pad + i * bar_width for xi in x]
        ax.bar(pos, daily_data, width=bar_width, align='edge',
            label=product_names[i], color=colors[i])

    # ➜ graduations AU DÉBUT de chaque jour (pas au centre du groupe)
    ax.set_xticks(list(x))
    ax.set_xticklabels(date_labels, rotation=45)

    # cadrage pour laisser l’intervalle [0, nb_jours]
    ax.set_xlim(0, len(date_range))

    # (le reste de ton code inchangé)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, pos: f"{v:.2f}L"))
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=4, frameon=False)
    ax.grid(True, axis='y', linestyle='-', linewidth=0.8, color='black', alpha=0.3)
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.tight_layout()


    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf
