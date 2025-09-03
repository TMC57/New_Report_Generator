from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from colors_map import get_color_for_product  # mapping couleurs commun
import matplotlib.ticker as mticker


def _events_series_by_product(events_json: dict):
    print(events_json)
    """
    Regroupe par pompe (pumpIdx) et retourne:
      - series: { "<pumpIdx>": [(ts_ms, value), ...], ... }
      - first_name: { "<pumpIdx>": "<nom produit le PLUS RÉCENT pour cette pompe>", ... }
    """
    rows = []
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

    series = {}                 # pumpKey -> [(ts, val)]
    latest_name_by_pump = {}    # pumpKey -> (latest_ts, name)

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

        key = (str(pump) if pump is not None else "")
        series.setdefault(key, []).append((ts, val))

        # Mémoriser le NOM le plus RÉCENT par timestamp
        prev = latest_name_by_pump.get(key)
        if prev is None or ts >= prev[0]:
            latest_name_by_pump[key] = (ts, name)

    # Trier chaque série par temps croissant
    for k in list(series.keys()):
        series[k].sort(key=lambda x: x[0])

    # Construire le dict attendu first_name (label)
    first_name = {k: v[1] for k, v in latest_name_by_pump.items()}

    # Si jamais pas de timestamp fiable, fallback: parcourir à l’envers et prendre le 1er vu
    if not first_name and rows:
        for r in reversed(rows):
            pump = pick(r, "pumpIdx", "pump", "pumpIndex", default=None)
            key = (str(pump) if pump is not None else "")
            if key and key not in first_name:
                nm = pick(r, "productName", "product", "name")
                if nm:
                    first_name[key] = nm

    return series, first_name




def generate_device_scatter(events_json: dict, title: str):
    """
    Scatter + line par POMPE (ignore les noms pour le regroupement),
    mais affiche dans la légende: "Pompe N — <premier nom produit rencontré>".
    Y en mL (données divisées par 10 comme avant).
    """
    series, first_name = _events_series_by_product(events_json)
    if not series:
        return None

    fig, ax = plt.subplots(figsize=(12, 6))

    for pump_idx, pts in series.items():
        xs = [mdates.date2num(datetime.fromtimestamp(ts / 1000.0)) for ts, _ in pts]
        ys = [v / 10.0 for _, v in pts]   # données d’origine en cL → mL
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}ml"))

        # Numéro de pompe: 0 -> 1, sinon +1
        try:
            pump_num = int(pump_idx) + 1
        except Exception:
            pump_num = "?"

        prod_name = first_name.get(pump_idx, "Produit")
        label = f"Pompe {pump_num} — {prod_name}"

        # Couleur: on peut utiliser la couleur liée au nom du produit (mapping commun)
        try:
            color = get_color_for_product(prod_name)
            ax.plot(xs, ys, marker='o', linewidth=3, markersize=8, label=label, color=color)
        except Exception:
            # fallback sans couleur dédiée
            ax.plot(xs, ys, marker='o', linewidth=3, markersize=8, label=label)

    ax.set_title(title)
    ax.grid(True, axis='y', linestyle='-', linewidth=0.8, color='black', alpha=0.3)

    # Légende en max 3 colonnes
    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,
        frameon=False
    )

    # Axe X = dates lisibles (toutes les journées)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))  # ajouter "\n%H:%M" si besoin de l'heure
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
