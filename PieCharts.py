import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
import numpy as np
from colors_map import get_colors_for_products  # <-- AJOUT
import math

def generate_pie_chart_and_legend(facility, from_date: str, to_date: str):
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

    # Couleurs cohérentes alignées sur les noms filtrés
    filtered_colors = get_colors_for_products(filtered_names) 

    def format_liters(pct, all_vals):
        total_ml = sum(all_vals)
        value_ml = pct * total_ml / 100
        value_l = value_ml / 10000
        return f"{value_l:.2f}L"

    # --- Image du camembert sans légende ---   
    fig_pie, pie_ax = plt.subplots(figsize=(5, 5), constrained_layout=True)

    if not filtered_totals or math.isclose(sum(filtered_totals), 0.0, rel_tol=0.0, abs_tol=1e-12):
        pie_ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center", fontsize=12)
        pie_ax.axis("off")

        buf_pie = BytesIO()
        fig_pie.savefig(buf_pie, format='png', bbox_inches='tight')
        plt.close(fig_pie)
        buf_pie.seek(0)

        fig_legend, legend_ax = plt.subplots(figsize=(5, 2.3), dpi=150)
        legend_ax.axis('off')
        buf_legend = BytesIO()
        fig_legend.savefig(
            buf_legend,
            format='png',
            bbox_inches='tight',
            dpi=150,
            facecolor='white',
            edgecolor='none',
            pad_inches=0.1
        )
        plt.close(fig_legend)
        buf_legend.seek(0)

        return buf_pie, buf_legend  

    # ✅ Cas normal : on trace le camembert
    wedges, texts, autotexts = pie_ax.pie(
        filtered_totals,
        labels=None,  # noms mis dans la légende
        autopct=lambda pct: format_liters(pct, filtered_totals),
        startangle=90,
        counterclock=False,
        wedgeprops={'edgecolor': 'black', 'linewidth': 0.2},
        normalize=True,
        pctdistance=0.50,            # éloigne les nombres du centre
        textprops={'fontsize': 14},  # nombres plus gros
        colors=filtered_colors       # <<< synchro couleurs
    )

    pie_ax.set_aspect('equal')
    pie_ax.margins(0)

    # --- paramètres centrés ---
    SMALL_PCT = 4.0     # petite tranche
    BASE_R    = 0.50    # position "proche du centre"
    PUSH_R    = 0.75    # un peu plus loin si petite tranche ou voisine
    R_MIN     = 0.50    # ne pas rentrer plus que ça
    R_MAX     = 0.90    # ne pas sortir plus que ça (reste visuellement "dedans")
    DR_OUT    = 0.03    # pas de poussée vers l’extérieur
    DR_IN     = 0.01    # petit pas vers l’intérieur (pour l’autre étiquette)
    GAP_PX    = 6       # écart mini entre boîtes
    MAX_IT    = 100     # itérations max

    # --- % par tranche ---
    total = float(sum(filtered_totals))
    pcts  = [100.0 * v / total for v in filtered_totals]
    n     = len(wedges)

    # 1) placement initial, proche du centre (et style bbox pour CHAQUE étiquette)
    for i, (w, t) in enumerate(zip(wedges, autotexts)):
        if not t.get_text():
            continue
        theta = np.deg2rad((w.theta1 + w.theta2) * 0.5)
        left_small  = pcts[(i - 1) % n] < SMALL_PCT
        self_small  = pcts[i]           < SMALL_PCT
        right_small = pcts[(i + 1) % n] < SMALL_PCT
        r0 = PUSH_R if (self_small or left_small or right_small) else BASE_R
        r  = min(max(r0, R_MIN), R_MAX)
        x, y = r * np.cos(theta), r * np.sin(theta)
        t.set_position((x, y))
        t.set_ha('center'); t.set_va('center')
        t.set_bbox(dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.65))

    # 2) anti-chevauchement itératif
    fig_pie.canvas.draw()
    renderer = fig_pie.canvas.get_renderer()

    def bboxes_px(texts):
        out = []
        for tt in texts:
            if not tt.get_text():
                out.append(None); continue
            out.append(tt.get_window_extent(renderer=renderer))
        return out

    def overlap(a, b, gap=0):
        return not (a.x1 + gap <= b.x0 or b.x1 + gap <= a.x0 or
                    a.y1 + gap <= b.y0 or b.y1 + gap <= a.y0)

    thetas = [np.deg2rad((w.theta1 + w.theta2) * 0.5) for w in wedges]
    iters = 0
    changed = True
    while changed and iters < MAX_IT:
        changed = False
        bbs = bboxes_px(autotexts)
        for i in range(n):
            if not autotexts[i].get_text() or bbs[i] is None: 
                continue
            for j in range(i+1, n):
                if not autotexts[j].get_text() or bbs[j] is None: 
                    continue
                if overlap(bbs[i], bbs[j], GAP_PX):
                    # index petite/grande
                    k_small = i if pcts[i] < pcts[j] else j
                    k_big   = j if k_small == i else i

                    # pousse la petite vers l’extérieur (jusqu’à R_MAX)
                    xk, yk = autotexts[k_small].get_position()
                    rk = min(np.hypot(xk, yk) + DR_OUT, R_MAX)
                    autotexts[k_small].set_position((rk*np.cos(thetas[k_small]), rk*np.sin(thetas[k_small])))

                    # et rentre très légèrement la grande (jusqu’à R_MIN)
                    xb, yb = autotexts[k_big].get_position()
                    rb = max(np.hypot(xb, yb) - DR_IN, R_MIN)
                    autotexts[k_big].set_position((rb*np.cos(thetas[k_big]), rb*np.sin(thetas[k_big])))

                    changed = True
        if changed:
            fig_pie.canvas.draw()
        iters += 1

    # (facultatif) repasser un bbox propre sur chaque label après ajustements
    for t in autotexts:
        if t.get_text():
            t.set_bbox(dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.65))

    # Export des buffers
    buf_pie = BytesIO()
    fig_pie.savefig(buf_pie, format='png', bbox_inches='tight')
    plt.close(fig_pie)
    buf_pie.seek(0)

    # --- Image de la légende seule avec qualité améliorée ---
    fig_legend, legend_ax = plt.subplots(figsize=(5, 2.3), dpi=150)
    legend_ax.axis('off')  # pas d'axes visibles

    # Calculer le nombre de colonnes optimal
    num_items = len(filtered_names)
    ncol = min(3, num_items) if num_items <= 6 else min(4, num_items)

    legend = legend_ax.legend(
        wedges, filtered_names,
        loc='center',
        fontsize=12,        # Police plus grande
        frameon=False,
        ncol=ncol,
        columnspacing=1.5,  # Espacement entre colonnes
        handlelength=1.5,   # Longueur des échantillons de couleur
        handletextpad=0.8,  # Espacement entre couleur et texte
        borderpad=0.5       # Marge interne
    )

    # Améliorer le rendu de la légende
    for text in legend.get_texts():
        text.set_fontweight('normal')
        text.set_fontfamily('sans-serif')

    buf_legend = BytesIO()
    fig_legend.savefig(
        buf_legend,
        format='png',
        bbox_inches='tight',
        dpi=150,           # Haute résolution
        facecolor='white', # Fond blanc
        edgecolor='none',  # Pas de bordure
        pad_inches=0.1     # Petite marge
    )
    plt.close(fig_legend)
    buf_legend.seek(0)

    return buf_pie, buf_legend