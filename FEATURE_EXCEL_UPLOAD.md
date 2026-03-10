# 📊 Fonctionnalité Upload Excel - Listing clients Orsye-Wash

## 🎯 Objectif

Permettre l'upload d'un fichier Excel "Listing clients Orsye-Wash.xlsx" via une interface drag & drop sur le frontend. Ce fichier est **obligatoire** pour lancer la génération de rapports et contient des informations complémentaires sur les clients.

---

## ✅ Implémentation complétée

### **1. Frontend - Zone Drag & Drop**

**Fichier :** `static/reports.html`

**Emplacement :** Section "Génération de nouveaux rapports", avant les champs de dates

**Fonctionnalités :**
- ✅ Zone drag & drop visuelle avec icône 📁
- ✅ Click pour sélectionner un fichier
- ✅ Validation de l'extension (.xlsx, .xls)
- ✅ Upload automatique au backend lors de la sélection
- ✅ Affichage du nom du fichier + nombre de facilities détectées
- ✅ Bouton "Supprimer" pour retirer le fichier
- ✅ Indicateur de chargement pendant l'upload
- ✅ Messages de succès/erreur

**Validation :**
- Le fichier Excel est **requis** avant de pouvoir générer un rapport
- Message d'erreur si tentative de génération sans fichier : 
  > ❌ Veuillez d'abord uploader le fichier Excel "Listing clients Orsye-Wash.xlsx"

---

### **2. Backend - Endpoint Upload**

**Fichier :** `ApiRest.py`

**Endpoint :** `POST /upload-excel-listing`

**Fonctionnement :**
1. Reçoit le fichier Excel uploadé
2. Valide l'extension (.xlsx ou .xls)
3. Sauvegarde temporairement le fichier
4. Parse le fichier avec `excel_parser.py`
5. Stocke les données parsées dans `uploads/excel_listing_data.json`
6. Retourne le nombre de facilities trouvées

**Réponse :**
```json
{
  "success": true,
  "filename": "Listing clients Orsye-Wash.xlsx",
  "facilities_count": 150,
  "message": "Fichier Excel parsé avec succès. 150 facilities trouvées."
}
```

---

### **3. Parser Excel**

**Fichier :** `excel_parser.py`

**Fonction principale :** `parse_listing_clients_excel(file_path: str) -> Dict[int, dict]`

**Colonnes extraites du fichier Excel :**
- `N° client` (utilisé comme facility_id)
- `Client (automatique)` → `client_name`
- `Groupe (automatique)` → `group`
- `Date installation` → `installation_date`
- `N° de zone de lavage` → `zone_number`
- `Adresse (automatique)` → `address`
- `N° de routeur` → `router_number`
- `Date dernière intervention` → `last_intervention`
- `Produit lavant` → `cleaning_product`

**Format de sortie :**
```python
{
  1070657992: {
    'client_name': 'MOLITOR AUTOMOBILES NISSAN',
    'group': 0,
    'installation_date': None,
    'zone_number': None,
    'address': ' ',
    'router_number': None,
    'last_intervention': None,
    'cleaning_product': None
  },
  # ... autres facilities
}
```

**Stockage :** Les données sont sauvegardées dans `uploads/excel_listing_data.json` pour utilisation ultérieure lors de la génération de rapports.

---

## 📦 Dépendances ajoutées

**Fichier :** `requirements.txt`

```txt
# Excel Processing
openpyxl==3.1.5
```

**Installation :**
```bash
pip install openpyxl
```

---

## 🔄 Workflow complet

1. **Utilisateur ouvre la page `/reports`**
2. **Upload du fichier Excel :**
   - Drag & drop ou click pour sélectionner
   - Validation de l'extension
   - Upload automatique vers `/upload-excel-listing`
   - Parsing du fichier par `excel_parser.py`
   - Stockage dans `uploads/excel_listing_data.json`
   - Affichage du succès avec nombre de facilities

3. **Génération de rapport :**
   - Vérification de la présence du fichier Excel uploadé
   - Si absent → message d'erreur
   - Si présent → génération autorisée
   - Les données Excel sont disponibles dans `uploads/excel_listing_data.json`

---

## 🎨 Interface utilisateur

### **Zone drag & drop (vide) :**
```
┌─────────────────────────────────────┐
│            📁                       │
│  Glissez-déposez le fichier Excel  │
│       ou cliquez pour sélectionner  │
└─────────────────────────────────────┘
```

### **Zone drag & drop (fichier uploadé) :**
```
┌─────────────────────────────────────┐
│            ✅                       │
│  Listing clients Orsye-Wash.xlsx    │
│         (150 facilities)            │
│       [Bouton Supprimer]            │
└─────────────────────────────────────┘
```

---

## 🚀 Prochaines étapes (TODO)

### **Phase 2 - Intégration dans la génération**

1. **Enrichir les données de facilities** avec les informations Excel
   - Utiliser `enrich_facility_data()` de `excel_parser.py`
   - Ajouter les données Excel aux rapports PDF

2. **Nouvelle page dilution** (cahier des charges)
   - Utiliser `installation_date`, `last_intervention`, `cleaning_product`
   - Afficher dilution et code couleur des buses
   - Calculer "1L de produit = X lavages"

3. **Enrichir page de garde**
   - Ajouter numéro client, code postal, ville
   - Mapper l'installation si plusieurs routeurs

---

## 📝 Notes techniques

- **Stockage temporaire :** Les données Excel sont stockées dans un fichier JSON plutôt qu'en session pour éviter les problèmes de mémoire
- **Sécurité :** Validation stricte de l'extension pour éviter l'upload de fichiers malveillants
- **Performance :** Le parsing est fait une seule fois à l'upload, pas à chaque génération
- **UX :** Feedback visuel immédiat avec indicateur de chargement et messages de succès/erreur

---

## ✅ Checklist de validation

- [x] Zone drag & drop fonctionnelle
- [x] Validation de l'extension
- [x] Upload automatique au backend
- [x] Parsing du fichier Excel
- [x] Stockage des données parsées
- [x] Validation obligatoire avant génération
- [x] Messages d'erreur clairs
- [x] Affichage du nombre de facilities
- [x] Bouton supprimer fonctionnel
- [x] Dépendance openpyxl ajoutée
- [ ] Intégration des données Excel dans les rapports PDF
- [ ] Tests avec fichier réel
- [ ] Documentation utilisateur

---

**Date de création :** Mars 2026  
**Statut :** ✅ Implémentation frontend/backend complétée - En attente d'intégration dans la génération PDF
