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
from typing import List, Dict, Tuple
from refactored.utils.product_colors import get_color_service


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
        
        # Calculer et afficher la médiane
        if quantities:
            median_qty = np.median(quantities)
            # Formater avec virgule au lieu de point
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
        
        # Légende plus grande
        ax.legend(loc='upper left', fontsize=11)
        
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
                
                ax.plot(dates, quantities, marker='o', linewidth=3, markersize=5, 
                       color=color, label=product_name)
        
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
        
        # Légende plus grande
        ax.legend(loc='upper left', fontsize=11)
        
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
