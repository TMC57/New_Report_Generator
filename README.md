# Application de Génération de Rapports - TMH Corporation

## 🚀 Lancement de l'Application

**Une seule commande pour tout démarrer :**

```bash
python main.py
```

Cette commande lance automatiquement :
1. ✅ Le backend Python FastAPI (port 8000)
2. ✅ Le frontend React (port 8080)
3. ✅ Ouvre le navigateur sur http://localhost:8080

## 📁 Structure du Projet

```
Report_generator/
├── main.py                          # Point d'entrée - lance backend + frontend
├── ApiRest.py                       # API REST FastAPI
├── pixel-perfect-replica-50/        # Frontend React moderne
│   ├── src/
│   │   ├── pages/                   # Pages React (Rapports, Facilities, Groupes)
│   │   ├── lib/api.ts              # Appels API vers le backend
│   │   └── components/             # Composants UI
│   └── vite.config.ts              # Config proxy vers backend
├── Config/
│   ├── configJson.json             # Configuration des facilities
│   └── GroupConfigJson.json        # Configuration des groupes
├── Reports/                         # Rapports PDF générés
└── uploads/                         # Logos uploadés
```

## 🔧 Architecture Technique

### Backend (Python FastAPI)
- **Port :** 8000
- **Framework :** FastAPI + Uvicorn
- **Fonctions :**
  - Génération de rapports PDF (ReportLab + Matplotlib)
  - API REST pour le frontend
  - Gestion des configurations (JSON)
  - Upload de fichiers

### Frontend (React + TypeScript)
- **Port :** 8080
- **Framework :** React + Vite
- **UI :** TailwindCSS + shadcn/ui
- **Fonctions :**
  - Interface moderne pour gérer les rapports
  - Configuration des facilities et groupes
  - Upload de logos avec drag & drop
  - Génération de rapports avec loader

### Communication
Le proxy Vite redirige automatiquement les appels API du frontend (port 8080) vers le backend (port 8000).

## 📋 Fonctionnalités

### Page Rapports
- Génération de rapports individuels ou de groupe
- Liste avec recherche, filtres et tri
- Téléchargement, aperçu, suppression
- Sélection multiple et export ZIP

### Page Config Facilities
- Tableau éditable avec toutes les facilities
- Upload de logos (cover_picture, material_picture)
- Gestion des contacts (managers, référents)
- Sauvegarde persistante dans `Config/configJson.json`

### Page Config Groupes
- Gestion des groupes de facilities
- Upload de logos de groupe
- Informations de groupe éditables
- Sauvegarde dans `Config/GroupConfigJson.json`

## 🛠️ Développement

### Installation des dépendances

**Backend Python :**
```bash
pip install -r requirements.txt
```

**Frontend React :**
```bash
cd pixel-perfect-replica-50
npm install
```

### Lancement manuel (développement)

**Terminal 1 - Backend :**
```bash
python main.py
```

**Terminal 2 - Frontend :**
```bash
cd pixel-perfect-replica-50
npm run dev
```

## 📦 Endpoints API Principaux

### Configuration
- `GET /items` - Récupérer les facilities
- `PUT /items` - Sauvegarder les facilities
- `GET /group-items` - Récupérer les groupes
- `PUT /group-items` - Sauvegarder les groupes

### Rapports
- `GET /api/reports/list` - Liste des rapports
- `GET /Reports_generation?from_date=...&to_date=...&facility_id=...` - Générer rapport individuel
- `GET /Group_Reports_generation?from_date=...&to_date=...` - Générer rapport de groupe
- `GET /api/reports/download/{filename}` - Télécharger un rapport
- `DELETE /api/reports/{filename}` - Supprimer un rapport

### Upload
- `POST /upload` - Upload de fichier (logo)

## 🎨 Technologies Utilisées

**Backend :**
- FastAPI
- Uvicorn
- ReportLab (génération PDF)
- Matplotlib (graphiques)
- Pillow (images)

**Frontend :**
- React 18
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui
- React Query
- Lucide React (icônes)

## 📝 Notes Importantes

- Les rapports peuvent prendre 2-5 minutes à générer (appels API externes)
- Les données sont persistées dans les fichiers JSON du dossier `Config/`
- Les logos sont stockés dans le dossier `uploads/`
- Le frontend utilise un proxy Vite pour communiquer avec le backend (pas de CORS)

## 🚀 Production

Pour build le frontend en production :
```bash
cd pixel-perfect-replica-50
npm run build
```

Les fichiers statiques seront dans `pixel-perfect-replica-50/dist/`
