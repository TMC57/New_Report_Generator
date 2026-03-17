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
        
        # Ajouter 'L' aux valeurs de l'axe Y avec espaces pour les milliers (format français)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.1f} L'.replace('.', ',')))
        
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
        
        # Calculer le nombre de jours et la largeur des barres
        num_days = (end_date - start_date).days + 1
        num_products = len(products_data)
        bar_width = 0.8 / max(num_products, 1)  # Largeur des barres
        
        # Tracer chaque produit en barres
        for idx, product_info in enumerate(products_data):
            product_name = product_info.get("name", "PRODUIT INCONNU")
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
                
                # Décaler les barres pour qu'elles soient entre les graduations (+0.5 jour)
                # et décaler pour chaque produit si plusieurs produits
                product_offset = (idx - num_products / 2 + 0.5) * bar_width
                bar_dates = [d + timedelta(days=0.5 + product_offset) for d in dates]
                
                # Tracer les barres du produit (pas de moyenne)
                ax.bar(bar_dates, quantities, width=bar_width * 0.9, 
                       color=color, label=product_name.upper(), alpha=0.8)
        
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
        
        # Ajouter 'L' aux valeurs de l'axe Y avec espaces pour les milliers (format français)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.1f} L'.replace('.', ',')))
        
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
        print(f"\n{'='*60}")
        print(f"🔍 create_flowrate_chart appelé pour zone: {zone}")
        print(f"{'='*60}")
        
        # Debug: afficher le nombre de résultats dans events_data
        results_count = 0
        if isinstance(events_data, dict):
            data = events_data.get("data")
            if isinstance(data, dict) and "results" in data:
                results_count = len(data.get("results", []))
                # Afficher les noms de produits uniques
                product_names = set()
                for r in data.get("results", []):
                    pn = r.get("productName", "")
                    if pn:
                        product_names.add(pn)
                print(f"   📊 {results_count} événements flowrate, produits uniques: {product_names}")
        
        # Extraire les données par pompe
        series, pump_names = self._extract_flowrate_series(events_data)
        
        if not series:
            return None
        
        # Filtrer les séries par zone si une zone spécifique est demandée
        if zone and zone != "GLOBAL":
            import re
            # Extraire le numéro de zone demandé (ex: "ZONE 2" -> "2")
            requested_zone_match = re.search(r'(\d+)', zone)
            requested_zone_num = requested_zone_match.group(1) if requested_zone_match else None
            
            print(f"🔍 Filtrage flowrate pour zone: {zone} (num={requested_zone_num})")
            print(f"   Produits disponibles: {list(pump_names.values())}")
            
            filtered_series = {}
            filtered_pump_names = {}
            for pump_idx, pts in series.items():
                prod_name = pump_names.get(pump_idx, "")
                # Extraire le numéro de zone du nom du produit (ex: "WNC50 - Zone 1" -> "1")
                product_zone_match = re.search(r'Zone\s*(\d+)', prod_name, re.IGNORECASE)
                product_zone_num = product_zone_match.group(1) if product_zone_match else None
                
                print(f"   → Produit '{prod_name}' zone_num={product_zone_num} vs requested={requested_zone_num}")
                
                if product_zone_num and requested_zone_num:
                    # Comparer les numéros de zone
                    if product_zone_num == requested_zone_num:
                        filtered_series[pump_idx] = pts
                        filtered_pump_names[pump_idx] = prod_name
                        print(f"     ✅ INCLUS")
                    else:
                        print(f"     ❌ EXCLU (zone {product_zone_num} != {requested_zone_num})")
                elif not product_zone_num:
                    # Produit sans zone spécifiée - ne pas l'inclure dans les zones spécifiques
                    print(f"     ❌ EXCLU (pas de zone dans le nom)")
            
            print(f"   Résultat filtrage: {len(filtered_series)} produits")
            
            # Toujours utiliser les séries filtrées (même si vide)
            series = filtered_series
            pump_names = filtered_pump_names
        
        if not series:
            print(f"   ⚠️ Aucun produit pour la zone {zone}, pas de graphique")
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
        
        # Tracer chaque produit
        default_colors = color_service.get_default_colors()
        for idx, (product_name, pts) in enumerate(series.items()):
            # Convertir timestamps en dates
            dates = [datetime.fromtimestamp(ts / 1000.0) for ts, _ in pts]
            # Valeurs en mL (division par 10 comme dans l'ancien code)
            values = [v / 10.0 for _, v in pts]
            
            # Nom du produit en majuscules
            label = product_name.upper()
            
            # Obtenir la couleur du produit
            color = color_service.get_color_for_product(product_name)
            if not color:
                color = default_colors[idx % len(default_colors)]
            
            # Tracer la courbe
            ax.plot(dates, values, marker='o', linewidth=3, markersize=8, 
                   label=label, color=color)
            
            # Ajouter la ligne de moyenne en pointillé
            if values:
                avg_value = sum(values) / len(values)
                ax.axhline(y=avg_value, color=color, linestyle='--', linewidth=2, alpha=0.7)
        
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
        Extrait les séries de données par produit depuis les événements
        
        Args:
            events_data: Données d'événements de l'API
            
        Returns:
            Tuple (series, pump_names) où:
            - series: {product_name: [(timestamp, value), ...]}
            - pump_names: {product_name: product_name}
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
        
        series = {}  # product_name -> [(ts, val)]
        
        for r in rows:
            # Extraire les champs (plusieurs noms possibles)
            name = (r.get("productName") or r.get("product") or 
                   r.get("name") or "Produit")
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
            
            # Clé = nom du produit (pour regrouper par produit, pas par pompe)
            key = name
            series.setdefault(key, []).append((ts, val))
        
        # Trier chaque série par temps croissant
        for k in list(series.keys()):
            series[k].sort(key=lambda x: x[0])
        
        # Construire le dict des noms (clé = nom du produit)
        pump_names = {k: k for k in series.keys()}
        
        return series, pump_names
