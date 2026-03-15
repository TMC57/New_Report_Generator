# Architecture du Projet Refactorisé

## 📁 Structure des Dossiers

```
refactored/
├── api/                    # Routes FastAPI
│   ├── routes.py          # Endpoints de génération de rapports
│   └── upload_routes.py   # Endpoints de gestion des uploads
├── cache/                  # Cache des données de facilities (JSON)
├── config/                 # Configurations
│   ├── configJson.json    # Configuration des facilities
│   └── settings.py        # Paramètres globaux
├── images/                 # Images du système (logos)
│   ├── Würth_logo.png
│   └── Logo - Solution de lavage connecté.png
├── models/                 # Modèles de données
│   ├── device.py
│   ├── facility.py
│   └── product.py
├── pdf_generator/          # Génération de PDFs
│   ├── generator.py       # Générateur principal
│   └── consumption_charts.py  # Graphiques matplotlib
├── reports/                # PDFs générés (organisés par date)
├── services/               # Services métier
│   ├── cm2w_service.py    # API CM2W
│   ├── config_service.py  # Gestion des configs
│   ├── excel_service.py   # Données Excel
│   └── facility_service.py # Agrégation des données
├── uploads/                # Fichiers uploadés
│   ├── excel_listings/    # Fichiers Excel et données parsées
│   └── *.jpg, *.png       # Images des facilities
└── utils/                  # Utilitaires
    └── logger.py          # Système de logs
```

## 🔄 Flux de Données

### 1. Récupération des Données
```
Frontend → API Routes → Facility Service → CM2W Service
                                        → Excel Service
                                        → Config Service
```

### 2. Génération de PDF
```
Facility Service → PDF Generator → ReportLab
                                → Matplotlib (graphiques)
                                → Images (refactored/uploads/)
                                → Logos (refactored/images/)
```

### 3. Upload de Fichiers
```
Frontend → Upload Routes → refactored/uploads/
                        → refactored/uploads/excel_listings/
```

## 📦 Ressources Indépendantes

Le projet refactorisé est **100% autonome** et ne dépend d'aucune ressource de l'ancien projet :

### Images Système
- **Emplacement** : `refactored/images/`
- **Contenu** : Logos Würth, TMH, etc.
- **Utilisation** : Générateur PDF

### Images Facilities
- **Emplacement** : `refactored/uploads/`
- **Contenu** : Photos des facilities uploadées via le frontend
- **Format** : JPG, PNG, WEBP
- **Accès** : `/uploads/{filename}`

### Données Excel
- **Emplacement** : `refactored/uploads/excel_listings/`
- **Fichiers** :
  - `listing_data.json` : Données clients parsées
  - `metadata.json` : Métadonnées du fichier Excel
- **Accès** : Endpoints `/api/v2/uploads/excel-*`

### Configurations
- **Emplacement** : `refactored/config/`
- **Fichiers** :
  - `configJson.json` : Configuration des facilities
  - `settings.py` : Paramètres globaux

## 🌐 Endpoints API

### Génération de Rapports
- `GET /api/v2/reports-generation-v2` : Génère les rapports PDF
  - Paramètres : `from_date`, `to_date`, `facility_id` (optionnel)
  - Génération en temps réel (un PDF par facility)

### Gestion des Uploads
- `POST /api/v2/uploads/facility-image` : Upload image de facility
- `POST /api/v2/uploads/material-image` : Upload image de matériel
- `POST /api/v2/uploads/excel-listing` : Upload fichier Excel
- `POST /api/v2/uploads/excel-data` : Sauvegarde données Excel parsées
- `GET /api/v2/uploads/images` : Liste toutes les images
- `GET /api/v2/uploads/excel-status` : Statut des données Excel
- `DELETE /api/v2/uploads/image/{filename}` : Supprime une image

### Gestion des Rapports
- `GET /api/reports/list` : Liste tous les rapports générés
- `GET /api/reports/download/{filename}` : Télécharge un rapport
- `GET /api/reports/preview/{filename}` : Prévisualise un rapport
- `DELETE /api/reports/{filename}` : Supprime un rapport

## 🔧 Services

### CM2WService
- Récupération des données depuis l'API CM2W
- Gestion des devices, stocks, quantités

### FacilityService
- Agrégation des données de toutes les sources
- Création du modèle `FacilityData` complet
- Sauvegarde en cache JSON

### ExcelService
- Chargement des données Excel
- Enrichissement des données facilities

### ConfigService
- Chargement des configurations locales
- Gestion des images et métadonnées

## 📊 Modèles de Données

### FacilityData
Modèle unifié contenant :
- Informations de base (ID, nom, owner)
- Données Excel (client_number, client_name, address)
- Configuration locale (images, contacts)
- Devices
- Products avec consommations quotidiennes/mensuelles
- Stock products
- Zones

### Device
- device_id, serial_number, zone

### ProductConsumption
- product_id, name, total_qty, zone
- daily_quantities, monthly_quantities

## 🎨 Génération PDF

### Structure du PDF
1. **Page de garde**
   - Logos Würth et TMH (en-tête)
   - Titre du rapport
   - Informations client
   - Numéros de routeurs
   - Photo de la facility (ratio conservé)
   - Footer avec contacts

2. **Page blanche** (avec logos)

3. **Pages de consommation** (par zone et produit)
   - Graphique matplotlib
   - Tableau de données
   - Texte explicatif
   - Shading week-ends/jours fériés

### Ressources Utilisées
- Logos : `refactored/images/`
- Photos facilities : `refactored/uploads/`
- Sortie : `refactored/reports/reports {from_date} to {to_date}/`

## 🚀 Déploiement

Le projet refactorisé peut être déployé **indépendamment** de l'ancien projet car :
- ✅ Toutes les ressources sont dans `refactored/`
- ✅ Tous les endpoints sont préfixés `/api/v2/`
- ✅ Aucune dépendance vers l'ancien code
- ✅ Configuration autonome

## 📝 Notes Importantes

1. **Chemins absolus** : Tous les chemins commencent par `refactored/`
2. **Uploads** : Les images uploadées vont dans `refactored/uploads/`
3. **Cache** : Les données JSON sont dans `refactored/cache/`
4. **Reports** : Les PDFs sont dans `refactored/reports/`
5. **Compatibilité** : L'ancien `/uploads` est monté sur `/uploads-old` pour compatibilité
