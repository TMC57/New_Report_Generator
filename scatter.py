from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from colors_map import get_color_for_product  # mapping couleurs commun
import matplotlib.ticker as mticker


def _events_series_by_product(events_json: dict):
    """
    Retourne {product_name: [(ts_ms, value), ...], ...}
    Tolérant sur les clés ('productName'/'product', 'timestamp'/'eventDate'/'createDate', 'value'/'flowRate'/'qty').
    """
    rows = []
    # La réponse CM2W varie : parfois 'data' direct, parfois 'data' -> 'results'
    data = events_json.get("data")
    if isinstance(data, dict) and "results" in data:
        rows = data.get("results", [])
    elif isinstance(data, list):
        rows = data
    elif isinstance(events_json, list):
        rows = events_json
    else:
        rows = []

    def pick(d, *keys, default=None):
        for k in keys:
            if k in d:
                return d[k]
        return default

    series = {}
    for r in rows:
        name = pick(r, "productName", "product", "name") or "Produit"
        pump = pick(r, "pumpIdx", "pump", "pumpIndex", default=None)
        ts   = pick(r, "timestamp", "eventDate", "createDate", "date", "time")
        val  = pick(r, "value", "flowRate", "qty", "quantity", "v")
        if ts is None or val is None:
            continue
        try:
            ts = int(ts)
            val = float(val)
        except Exception:
            continue

        key = (str(name), str(pump) if pump is not None else "")
        series.setdefault(key, []).append((ts, val))

    # trier chaque série par temps
    for k in list(series.keys()):
        series[k].sort(key=lambda x: x[0])
    return series

def generate_device_scatter(events_json: dict, title: str):
    """
    Scatter + line par produit sur le même graphe. Retourne un BytesIO PNG.
    """
    series = _events_series_by_product(events_json)
    if not series:
        return None

    fig, ax = plt.subplots(figsize=(12, 6))
    for (product_name, pump_idx), pts in series.items():
        xs = [mdates.date2num(datetime.fromtimestamp(ts / 1000.0)) for ts, _ in pts]
        ys = [v / 10.0 for _, v in pts]   # les données sont en cL → conversion en mL
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}ml"))
        c = get_color_for_product(product_name)

        # Correction de l’index : même 0 → Pompe 1, sinon +1
        try:
            pump_num = int(pump_idx) + 1
        except Exception:
            pump_num = None

        label = f"Pompe {pump_num} — {product_name}" if pump_num else product_name

        ax.plot(
            xs, ys,
            marker='o',
            linewidth=3,
            markersize=8,
            label=label,
            color=c
        )



    ax.set_title(title)
    # ax.set_xlabel("Date/heure")
    # ax.set_ylabel("Débit")
    ax.grid(True, axis='y', linestyle='-', linewidth=0.8, color='black', alpha=0.3)
    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,       # max 3 éléments par ligne
        frameon=False
    )

    # X = dates bien lisibles
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m")) #\n%H:%M a rajouter si on veut l'heure
    fig.autofmt_xdate()

    # look propre
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf