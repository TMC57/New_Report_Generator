"""
Module pour créer les graphiques de consommation avec matplotlib
"""
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
import io
from typing import List, Dict, Tuple, Optional
from refactored.utils.product_colors import get_color_service
import matplotlib.ticker as mticker


class ConsumptionChartGenerator:
    """Générateur de graphiques de consommation"""
    
    # Jours fériés français 2025-2026 (à compléter selon les besoins)
    FRENCH_HOLIDAYS = [
        "2025-01-01", "2025-04-21", "2025-05-01", "2025-05-08", "2025-05-29",
        "2025-06-09", "2025-07-14", "2025-08-15", "2025-11-01", "2025-11-11",
        "2025-12-25",
        "2026-01-01", "2026-04-06", "2026-05-01", "2026-05-08", "2026-05-14",
        "2026-05-25", "2026-07-14", "2026-08-15", "2026-11-01", "2026-11-11",
        "2026-12-25"
    ]
    
    def __init__(self):
        self.holidays = set(self.FRENCH_HOLIDAYS)
    
    def is_weekend_or_holiday(self, date_str: str) -> bool:
        """Vérifie si une date est un week-end ou un jour férié"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        is_weekend = date.weekday() >= 5  # 5=samedi, 6=dimanche
        is_holiday = date_str in self.holidays
        return is_weekend or is_holiday
    
    def create_consumption_chart(
        self,
        daily_data: List[Dict],
        product_name: str,
        zone: str,
        from_date: str,
        to_date: str
    ) -> io.BytesIO:
        """
        Crée un graphique de consommation quotidienne
        
        Args:
            daily_data: Liste de {date: str, qty: float}
            product_name: Nom du produit
            zone: Nom de la zone
            from_date: Date de début (YYYY-MM-DD)
            to_date: Date de fin (YYYY-MM-DD)
            
        Returns:
            BytesIO contenant l'image PNG du graphique
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Convertir les dates limites
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        # Préparer les données en filtrant par la fourchette de dates
        dates = []
        quantities = []
        
        for item in daily_data:
            date_str = item.get("date")
            qty = item.get("qty", 0)
            if date_str:
                item_date = datetime.strptime(date_str, "%Y-%m-%d")
                # FILTRER: ne garder que les dates dans la fourchette
                if start_date <= item_date <= end_date:
                    dates.append(item_date)
                    # Diviser par 10 comme dans l'ancien projet (scatter.py ligne 92)
                    quantities.append(qty / 10)
        
        if not dates:
            # Pas de données, créer un graphique vide
            ax.text(0.5, 0.5, "Aucune donnée disponible", 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            return buf
        
        # Griser les week-ends et jours fériés
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            if self.is_weekend_or_holiday(date_str):
                ax.axvspan(current_date, current_date + timedelta(days=1), 
                          color='lightgray', alpha=0.3, zorder=0)
            current_date += timedelta(days=1)
        
        # Obtenir la couleur spécifique du produit
        color_service = get_color_service()
        product_color = color_service.get_color_for_product(product_name)
        if not product_color:
            product_color = '#0066cc'  # Couleur par défaut
            print(f"⚠️ Couleur par défaut pour '{product_name}': {product_color}")
        else:
            print(f"✅ Couleur trouvée pour '{product_name}': {product_color}")
        
        # Tracer la courbe de consommation
        ax.plot(dates, quantities, marker='o', linewidth=3, markersize=5, 
               color=product_color, label=product_name)
        
        # Calculer et afficher la moyenne et la médiane
        if quantities:
            # Moyenne
            mean_qty = np.mean(quantities)
            mean_str = f'{mean_qty:.1f}'.replace('.', ',')
            ax.axhline(y=mean_qty, color='orange', linestyle='-.', linewidth=1.5,
                      label=f'Moyenne: {mean_str} mL')
            
            # Médiane
            median_qty = np.median(quantities)
            median_str = f'{median_qty:.1f}'.replace('.', ',')
            ax.axhline(y=median_qty, color='green', linestyle='--', linewidth=1.5,
                      label=f'Médiane: {median_str} mL')
            
            # Calculer les valeurs normales (entre Q1 et Q3)
            q1 = np.percentile(quantities, 25)
            q3 = np.percentile(quantities, 75)
            # Formater avec virgules au lieu de points
            q1_str = f'{q1:.1f}'.replace('.', ',')
            q3_str = f'{q3:.1f}'.replace('.', ',')
            ax.axhspan(q1, q3, color='green', alpha=0.1, zorder=0,
                      label=f'Plage normale (Q1-Q3): {q1_str}-{q3_str} mL')
        
        # Configuration des axes
        ax.set_xlabel('', fontsize=11, fontweight='bold')  # Pas de label 'Date'
        ax.set_ylabel('', fontsize=11, fontweight='bold')  # Pas de label sur l'axe Y
        # Pas de titre dans le graphique (il est déjà au-dessus)
        
        # Format des dates sur l'axe X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        
        # Calculer l'intervalle pour avoir maximum 20 ticks
        num_days = (end_date - start_date).days + 1
        if num_days > 0:
            tick_interval = max(1, num_days // 20)
        else:
            tick_interval = 1
        
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=tick_interval))
        plt.xticks(rotation=45, ha='right')
        
        # Retirer les bordures (spines)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        
        # Augmenter l'épaisseur des lignes des axes (ticks)
        ax.tick_params(axis='both', which='major', width=2, length=6)
        
        # Ajouter 'ml' aux valeurs de l'axe Y avec espaces pour les milliers (format français)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,} ml'.replace(',', ' ')))
        
        # Grille avec lignes plus épaisses
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=1.5)
        
        # Légende en dessous du graphique
        ax.legend(loc='lower center', fontsize=11, bbox_to_anchor=(0.5, -0.25), ncol=2)
        
        # Ajuster la mise en page
        plt.tight_layout()
        
        # Sauvegarder dans un buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        return buf
    
    def create_multi_product_chart(
        self,
        products_data: List[Dict],
        zone: str,
        from_date: str,
        to_date: str
    ) -> io.BytesIO:
        """
        Crée un graphique avec plusieurs produits pour une même zone
        
        Args:
            products_data: Liste de {name: str, daily_data: List[Dict]}
            zone: Nom de la zone
            from_date: Date de début (YYYY-MM-DD)
            to_date: Date de fin (YYYY-MM-DD)
            
        Returns:
            BytesIO contenant l'image PNG du graphique
        """
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Convertir les dates limites
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        # Griser les week-ends et jours fériés
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            if self.is_weekend_or_holiday(date_str):
                ax.axvspan(current_date, current_date + timedelta(days=1), 
                          color='lightgray', alpha=0.3, zorder=0)
            current_date += timedelta(days=1)
        
        # Service de couleurs pour les produits
        color_service = get_color_service()
        default_colors = color_service.get_default_colors()
        
        # Tracer chaque produit
        for idx, product_info in enumerate(products_data):
            product_name = product_info.get("name", "Produit inconnu")
            daily_data = product_info.get("daily_data", [])
            
            # Filtrer et préparer les données
            dates = []
            quantities = []
            
            for item in daily_data:
                date_str = item.get("date")
                qty = item.get("qty", 0)
                if date_str:
                    item_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if start_date <= item_date <= end_date:
                        dates.append(item_date)
                        # Division par 10 pour convertir cL en mL (comme scatter.py ligne 92)
                        quantities.append(qty / 10)
            
            if dates:
                # Obtenir la couleur spécifique du produit ou utiliser une couleur par défaut
                color = color_service.get_color_for_product(product_name)
                if not color:
                    color = default_colors[idx % len(default_colors)]
                    print(f"⚠️ Couleur par défaut pour '{product_name}': {color}")
                else:
                    print(f"✅ Couleur trouvée pour '{product_name}': {color}")
                
                # Tracer la courbe du produit
                ax.plot(dates, quantities, marker='o', linewidth=3, markersize=5, 
                       color=color, label=product_name)
                
                # Calculer et afficher la moyenne pour ce produit
                if quantities:
                    mean_qty = np.mean(quantities)
                    mean_str = f'{mean_qty:.1f}'.replace('.', ',')
                    ax.axhline(y=mean_qty, color=color, linestyle='-.', linewidth=1.5,
                              label=f'Moyenne {product_name}: {mean_str} mL')
        
        # Configuration des axes
        ax.set_xlabel('', fontsize=11, fontweight='bold')  # Pas de label 'Date'
        ax.set_ylabel('', fontsize=11, fontweight='bold')  # Pas de label sur l'axe Y
        # Pas de titre dans le graphique (il est déjà au-dessus)
        
        # Format des dates sur l'axe X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        
        # Calculer l'intervalle pour avoir maximum 20 ticks
        num_days = (end_date - start_date).days + 1
        if num_days > 0:
            tick_interval = max(1, num_days // 20)
        else:
            tick_interval = 1
        
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=tick_interval))
        plt.xticks(rotation=45, ha='right')
        
        # Retirer les bordures (spines)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        
        # Augmenter l'épaisseur des lignes des axes (ticks)
        ax.tick_params(axis='both', which='major', width=2, length=6)
        
        # Ajouter 'ml' aux valeurs de l'axe Y avec espaces pour les milliers (format français)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,} ml'.replace(',', ' ')))
        
        # Grille avec lignes plus épaisses
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=1.5)
        
        # Légende en dessous du graphique
        ax.legend(loc='lower center', fontsize=11, bbox_to_anchor=(0.5, -0.25), ncol=2)
        
        # Ajuster la mise en page
        plt.tight_layout()
        
        # Sauvegarder dans un buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        return buf
    
    def calculate_statistics(self, daily_data: List[Dict]) -> Dict:
        """Calcule les statistiques de consommation"""
        quantities = [item.get("qty", 0) for item in daily_data if item.get("qty")]
        
        if not quantities:
            return {
                "median": 0,
                "mean": 0,
                "q1": 0,
                "q3": 0,
                "min": 0,
                "max": 0
            }
        
        return {
            "median": np.median(quantities),
            "mean": np.mean(quantities),
            "q1": np.percentile(quantities, 25),
            "q3": np.percentile(quantities, 75),
            "min": np.min(quantities),
            "max": np.max(quantities)
        }
    
    def create_flowrate_chart(
        self,
        events_data: Dict,
        device_serial: str,
        zone: str,
        from_date: str,
        to_date: str
    ) -> Optional[io.BytesIO]:
        """
        Crée un graphique de débit (flowrate) pour un device
        Basé sur l'ancien scatter.py
        
        Args:
            events_data: Données d'événements de débit depuis l'API
            device_serial: Numéro de série du device
            zone: Nom de la zone
            from_date: Date de début (YYYY-MM-DD)
            to_date: Date de fin (YYYY-MM-DD)
            
        Returns:
            BytesIO contenant l'image PNG du graphique ou None si pas de données
        """
        # Extraire les données par pompe
        series, pump_names = self._extract_flowrate_series(events_data)
        
        if not series:
            return None
        
        # Créer le graphique
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Convertir les dates limites
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        # Griser les week-ends et jours fériés
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            if self.is_weekend_or_holiday(date_str):
                ax.axvspan(current_date, current_date + timedelta(days=1), 
                          color='lightgray', alpha=0.3, zorder=0)
            current_date += timedelta(days=1)
        
        # Service de couleurs
        color_service = get_color_service()
        
        # Tracer chaque pompe
        for pump_idx, pts in series.items():
            # Convertir timestamps en dates
            dates = [datetime.fromtimestamp(ts / 1000.0) for ts, _ in pts]
            # Valeurs en mL (division par 10 comme dans l'ancien code)
            values = [v / 10.0 for _, v in pts]
            
            # Numéro de pompe (0 -> 1, etc.)
            try:
                pump_num = int(pump_idx) + 1
            except Exception:
                pump_num = "?"
            
            # Nom du produit pour cette pompe
            prod_name = pump_names.get(pump_idx, "Produit")
            label = prod_name  # Seulement le nom du produit, sans "Pompe X —"
            
            # Obtenir la couleur du produit
            color = color_service.get_color_for_product(prod_name)
            if not color:
                color = color_service.get_default_colors()[int(pump_idx) % len(color_service.get_default_colors())]
            
            # Tracer la courbe
            ax.plot(dates, values, marker='o', linewidth=3, markersize=8, 
                   label=label, color=color)
        
        # Configuration du graphique (pas de titre, il est sur la page)
        
        # Grille
        ax.grid(True, axis='y', linestyle='-', linewidth=0.8, 
               color='black', alpha=0.3)
        
        # Format de l'axe Y (mL)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{int(x):,} ml".replace(',', ' '))
        )
        
        # Format de l'axe X (dates)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        plt.xticks(rotation=45, ha='right')
        
        # Légende en dessous
        ax.legend(
            loc='lower center',
            bbox_to_anchor=(0.5, -0.25),
            ncol=3,
            fontsize=11,
            frameon=False
        )
        
        # Retirer les bordures
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Ajuster la mise en page
        plt.tight_layout()
        
        # Sauvegarder dans un buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        return buf
    
    def _extract_flowrate_series(self, events_data: Dict) -> Tuple[Dict, Dict]:
        """
        Extrait les séries de données par pompe depuis les événements
        
        Args:
            events_data: Données d'événements de l'API
            
        Returns:
            Tuple (series, pump_names) où:
            - series: {pump_idx: [(timestamp, value), ...]}
            - pump_names: {pump_idx: product_name}
        """
        # Extraire les lignes de données
        rows = []
        data = events_data.get("data")
        if isinstance(data, dict) and "results" in data:
            rows = data.get("results", [])
        elif isinstance(data, list):
            rows = data
        elif isinstance(events_data, list):
            rows = events_data
        
        series = {}  # pump_idx -> [(ts, val)]
        latest_name_by_pump = {}  # pump_idx -> (latest_ts, name)
        
        for r in rows:
            # Extraire les champs (plusieurs noms possibles)
            name = (r.get("productName") or r.get("product") or 
                   r.get("name") or "Produit")
            pump = r.get("pumpIdx") or r.get("pump") or r.get("pumpIndex")
            ts = (r.get("timestamp") or r.get("eventDate") or 
                 r.get("createDate") or r.get("date") or r.get("time"))
            val = (r.get("value") or r.get("flowRate") or 
                  r.get("qty") or r.get("quantity") or r.get("v"))
            
            if ts is None or val is None:
                continue
            
            try:
                ts = int(ts)
                val = float(val)
            except Exception:
                continue
            
            # Clé de pompe
            key = str(pump) if pump is not None else ""
            series.setdefault(key, []).append((ts, val))
            
            # Mémoriser le nom le plus récent par timestamp
            prev = latest_name_by_pump.get(key)
            if prev is None or ts >= prev[0]:
                latest_name_by_pump[key] = (ts, name)
        
        # Trier chaque série par temps croissant
        for k in list(series.keys()):
            series[k].sort(key=lambda x: x[0])
        
        # Construire le dict des noms
        pump_names = {k: v[1] for k, v in latest_name_by_pump.items()}
        
        return series, pump_names
