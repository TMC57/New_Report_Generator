# 🎨 Référence des couleurs produits E-Wash

**Source :** Cahier des charges - TR_ E-Wash - modifications des statistiques  
**Date :** Mars 2026

---

## 📋 Mapping complet des produits

| Dénomination produit | Abrégé | Référence | Code HEX | Nom couleur | Aperçu |
|---------------------|---------|-----------|----------|-------------|--------|
| WNC 40 Nettoyant carrosserie ultraconcentré 20 L | WNC 40 20 L | 089047020 | `#65C482` | Emerald | 🟢 |
| WNC 40 Nettoyant carrosserie 200L | WNC 40 200 L | 08904701 | `#65C482` | Emerald | 🟢 |
| WNC 50 Nettoyant carrosserie 200L | WNC 50 200 L | 08904711 | `#34A65F` | Medium jungle | 🟢 |
| WNC 60 Nettoyant carrosserie 200L | WNC 60 200 L | 0890473 | `#1F8A4B` | Sea green | 🟢 |
| WNC 70 Nettoyant pour carrosserie 200L | WNC 70 200 L | 0893048200 | `#0F6A33` | Dark emerald | 🟢 |
| WNC 31 Nettoyant carrosserie auto-séchant 25L | WNC 31 25 L | 0893010725 | `#F7C844` | Tuscan sun | 🟡 |
| WNC 31 Nettoyant carrosserie auto-séchant 200L | WNC 31 200 L | 0893010720 | `#F7C844` | Tuscan sun | 🟡 |
| Auto-séchant ultraconcentré 20L | Auto-séchant 20 L | 0893025020 | `#8698CB` | Wisteria blue | 🔵 |
| Auto-séchant prêt-à-l'emploi 200L | Auto-séchant 200 L | 0893025650 | `#8698CB` | Wisteria blue | 🔵 |
| Nettoyant jantes purple 200L | Purple | 0893477009 | `#7B3FA7` | Indigo bloom | 🟣 |
| Eau | Eau | - | `#90F1EF` | Soft cyan | 💧 |

---

## 🎨 Palette de couleurs par famille

### Famille WNC (Nettoyants carrosserie)
- **WNC 40** : `#65C482` - Emerald (vert clair)
- **WNC 50** : `#34A65F` - Medium jungle (vert moyen)
- **WNC 60** : `#1F8A4B` - Sea green (vert foncé)
- **WNC 70** : `#0F6A33` - Dark emerald (vert très foncé)
- **WNC 31** : `#F7C844` - Tuscan sun (jaune/or)

### Famille Auto-séchant
- **Auto-séchant** : `#8698CB` - Wisteria blue (bleu lavande)

### Produits spéciaux
- **Purple (Jantes)** : `#7B3FA7` - Indigo bloom (violet)
- **Eau** : `#90F1EF` - Soft cyan (cyan clair)

---

## 💻 Utilisation dans le code

Le mapping est défini dans `colors_map.py` :

```python
from colors_map import get_color_for_product, get_colors_for_products

# Pour un seul produit
color = get_color_for_product("WNC 40")  # Retourne "#65C482"

# Pour plusieurs produits
colors = get_colors_for_products(["WNC 40", "WNC 50", "Auto-séchant"])
# Retourne ["#65C482", "#34A65F", "#8698CB"]
```

---

## 📊 Fichiers utilisant ce mapping

1. **`colors_map.py`** - Définition du mapping
2. **`BarCharts.py`** - Graphiques barres (utilise `get_colors_for_products`)
3. **`scatter.py`** - Graphiques scatter (utilise `get_color_for_product`)
4. **`PieCharts.py`** - Graphiques camembert (utilise `get_colors_for_products`)
5. **`GrouPdfGen.py`** - Rapports groupés (utilise `get_colors_for_products`)

---

## ✅ Validation

- [x] Codes HEX mis à jour selon cahier des charges
- [x] Tous les produits du cahier des charges sont mappés
- [x] Matching insensible à la casse et aux espaces
- [x] Fallback déterministe pour produits non mappés
- [x] Compatible avec tous les graphiques existants

---

## 🔄 Prochaines étapes

Selon le cahier des charges, il faudra également implémenter :

1. **Textures par zone** (pour différencier les zones visuellement)
   - Zone 1 : Plein (Gris)
   - Zone 2 : Tirets (Gris)
   - Zone 3 : Pointillés (Gris)
   - Zone 4 : Striures (Gris)

2. **Noms standardisés** : Utiliser systématiquement les noms abrégés
