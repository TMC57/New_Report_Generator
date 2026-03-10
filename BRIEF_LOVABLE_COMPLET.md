# Brief Complet pour Lovable - Refonte Frontend Application Rapports

## 🎯 Objectif

Moderniser le frontend de l'application de génération de rapports **en préservant TOUTES les fonctionnalités existantes**.

**Liberté créative :** Vous pouvez complètement refaire le design et l'UX, MAIS toutes les fonctionnalités actuelles doivent être conservées et fonctionner de la même manière.

---

## ⚠️ IMPORTANT - Ce qui DOIT être préservé

### 1. **Chargement et affichage des données existantes**
- Les configurations facilities stockées dans `Config/configJson.json` doivent s'afficher automatiquement au chargement
- Les configurations groupes stockées dans `Config/GroupConfigJson.json` doivent s'afficher
- Les rapports PDF existants dans le dossier `Reports/` doivent être listés

### 2. **Édition et sauvegarde**
- Toute modification dans les tableaux doit être sauvegardée dans les fichiers JSON
- Les logos uploadés doivent être sauvegardés dans `/uploads/` et le chemin stocké dans le JSON
- Après sauvegarde, les données doivent persister (rechargement de page = données toujours là)

### 3. **Génération de rapports**
- Les formulaires de génération doivent envoyer les bonnes dates au backend
- La génération peut prendre plusieurs minutes (afficher un loader)
- Après génération, la liste des rapports doit se rafraîchir automatiquement

---

## 📁 Structure des Fichiers JSON Existants

### `Config/configJson.json` (Configuration Facilities)

```json
[
  {
    "facilityId": 123,
    "facilityName": "Site de Production Paris",
    "logo": "/uploads/logo_paris.png",
    "address": "123 Rue de la Paix\n75001 Paris",
    "contact": "Jean Dupont",
    "email": "contact@site-paris.com",
    "phone": "+33 1 23 45 67 89",
    "additionalInfo": "Informations complémentaires..."
  }
]
```

**Champs :**
- `facilityId` : ID numérique (lecture seule, vient de l'API externe)
- `facilityName` : Nom (lecture seule, vient de l'API externe)
- `logo` : Chemin vers l'image uploadée (éditable)
- `address` : Adresse multi-lignes (éditable)
- `contact` : Nom du contact (éditable)
- `email` : Email (éditable)
- `phone` : Téléphone (éditable)
- `additionalInfo` : Texte libre (éditable)

### `Config/GroupConfigJson.json` (Configuration Groupes)

```json
[
  {
    "owner": "TMH Corporation",
    "facilities": [
      { "facilityId": 123, "facilityName": "Site Paris" },
      { "facilityId": 456, "facilityName": "Site Lyon" }
    ],
    "logo": "/uploads/logo_tmh.png",
    "groupInfo": "Informations sur le groupe TMH..."
  }
]
```

**Champs :**
- `owner` : Nom du propriétaire (lecture seule)
- `facilities` : Liste des facilities du groupe (lecture seule)
- `logo` : Chemin vers l'image uploadée (éditable)
- `groupInfo` : Texte libre (éditable)

---

## 🔌 API Backend (Python FastAPI sur port 8000)

### Endpoints Configuration Facilities

**GET /items**
- Retourne : `Array<FacilityConfig>`
- Utilisation : Charger les configurations au démarrage de la page

**PUT /items**
- Body : `Array<FacilityConfig>` (tableau complet)
- Retourne : `{ saved: number }`
- Utilisation : Sauvegarder toutes les modifications

### Endpoints Configuration Groupes

**GET /group-items**
- Retourne : `Array<GroupConfig>`

**PUT /group-items**
- Body : `Array<GroupConfig>` (tableau complet)
- Retourne : `{ saved: number }`

### Endpoints Rapports

**GET /api/reports/list**
- Retourne : `Array<Report>`
- Structure Report :
```json
{
  "filename": "rapport_client_abc.pdf",
  "name": "Rapport Client ABC",
  "type": "individual",
  "size": 2621440,
  "date": "2026-03-08T17:45:23",
  "date_range": {
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "formatted": "Du 01/01/2024 au 31/01/2024"
  }
}
```

**GET /api/reports/download/{filename}**
- Télécharge le PDF

**GET /api/reports/preview/{filename}**
- Affiche le PDF dans le navigateur

**DELETE /api/reports/{filename}**
- Supprime un rapport

**POST /api/reports/download-multiple**
- Body : `{ filenames: string[] }`
- Retourne : Fichier ZIP

**GET /Reports_generation?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&facility_id=123**
- Génère un rapport individuel
- ⚠️ Peut prendre 2-5 minutes

**GET /Group_Reports_generation?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD**
- Génère un rapport de groupe
- ⚠️ Peut prendre 2-5 minutes

### Endpoints Upload

**POST /upload**
- Body : FormData avec le fichier
- Retourne : `{ path: "/uploads/filename.png" }`

---

## 📋 Fonctionnalités Détaillées par Page

### Page 1 : Rapports

**Section Génération :**
- 2 date pickers (from_date, to_date)
- Input optionnel facility_id (nombre)
- 2 boutons : "Générer rapport individuel" / "Générer rapport de groupe"
- Modal de chargement pendant la génération (2-5 min)
- Auto-refresh de la liste après génération

**Section Liste des Rapports :**
- Tableau avec colonnes : Checkbox, Nom, Type (badge), Période, Date création, Taille, Actions
- Barre de recherche (filtre par nom)
- Filtre par type (Tous / Individuels / Groupes)
- Tri cliquable sur toutes les colonnes
- Pagination (10 par page)
- Sélection multiple avec checkboxes
- Actions par rapport : Télécharger, Aperçu, Supprimer
- Actions groupées : Télécharger sélection (ZIP), Supprimer sélection
- Bouton Actualiser

### Page 2 : Config Facilities

**Tableau éditable :**
- Colonnes : ID (readonly), Nom (readonly), Logo (upload), Adresse (textarea), Contact (input), Email (input), Téléphone (input), Infos (textarea)
- Upload de logo avec drag & drop + prévisualisation
- Bouton "Sauvegarder" en haut
- **CRITIQUE** : Les données doivent se charger depuis `/items` au démarrage
- **CRITIQUE** : Après sauvegarde, les données doivent persister

### Page 3 : Config Groupes

**Tableau éditable :**
- Colonnes : Propriétaire (readonly), Facilities (readonly, liste), Logo (upload), Informations (textarea)
- Upload de logo avec drag & drop
- Bouton "Sauvegarder" en haut
- **CRITIQUE** : Les données doivent se charger depuis `/group-items` au démarrage

---

## 🎨 Design & Charte Graphique

**Couleurs TMH Corporation :**
- Bleu principal : `#38BDF8` / `#0EA5E9`
- Orange accent : `#FB923C` / `#FDBA74`
- Gris : `#64748B` / `#CBD5E1`

**Stack Recommandé :**
- React + TypeScript
- TailwindCSS + shadcn/ui
- Lucide React (icônes)
- React Query (gestion API)
- React Hook Form + Zod (formulaires)

**Vous êtes LIBRE de :**
- ✅ Changer complètement le design
- ✅ Réorganiser la mise en page
- ✅ Améliorer l'UX
- ✅ Ajouter des animations
- ✅ Utiliser d'autres composants UI

**Vous DEVEZ :**
- ❌ Garder TOUTES les fonctionnalités
- ❌ Charger les données existantes au démarrage
- ❌ Sauvegarder les modifications dans les JSON
- ❌ Gérer les uploads de logos correctement
- ❌ Gérer les longues générations de rapports

---

## 🔧 Configuration Technique

### Proxy Vite (déjà configuré)

Le frontend React tourne sur **port 8080**, le backend Python sur **port 8000**.

Vite redirige automatiquement :
- `/api/*` → `http://localhost:8000`
- `/items` → `http://localhost:8000`
- `/group-items` → `http://localhost:8000`
- `/upload` → `http://localhost:8000`
- `/uploads/*` → `http://localhost:8000`
- `/Reports_generation` → `http://localhost:8000`
- `/Group_Reports_generation` → `http://localhost:8000`

**Utilisez des chemins relatifs dans les appels API** (pas de `http://localhost:8000`).

---

## 📝 Code de Référence - Ancien Frontend

### Exemple : Chargement des Facilities (ancien code)

```javascript
// Ancien code HTML/JS qui FONCTIONNAIT
async function loadFacilities() {
  const response = await fetch('/items');
  const data = await response.json();
  // data est un array d'objets facility
  renderTable(data);
}

// Au chargement de la page
window.addEventListener('DOMContentLoaded', loadFacilities);
```

### Exemple : Sauvegarde des Facilities (ancien code)

```javascript
async function saveFacilities() {
  const allData = collectAllTableData(); // Array complet
  
  const response = await fetch('/items', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(allData)
  });
  
  if (response.ok) {
    alert('Sauvegardé !');
  }
}
```

### Exemple : Upload de Logo (ancien code)

```javascript
async function uploadLogo(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/upload', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  return data.path; // Ex: "/uploads/logo.png"
}
```

---

## ✅ Checklist de Validation

Avant de livrer, vérifiez que :

- [ ] Les données se chargent automatiquement au démarrage de chaque page
- [ ] Les modifications sont sauvegardées dans les JSON
- [ ] Après F5 (rechargement), les données modifiées sont toujours là
- [ ] Les logos s'uploadent et s'affichent correctement
- [ ] La génération de rapports fonctionne (avec loader pendant 2-5 min)
- [ ] La liste des rapports se rafraîchit après génération
- [ ] Le téléchargement de rapports fonctionne
- [ ] L'aperçu PDF s'ouvre dans un nouvel onglet
- [ ] La suppression de rapports fonctionne
- [ ] La sélection multiple et téléchargement ZIP fonctionnent
- [ ] La recherche et les filtres fonctionnent
- [ ] Le tri par colonnes fonctionne
- [ ] La pagination fonctionne

---

## 🚀 Workflow de Développement

1. **Démarrer le backend Python** (terminal 1) :
```bash
cd c:\Users\Thomas\Documents\Report_generator
python main.py
```

2. **Démarrer le frontend React** (terminal 2) :
```bash
cd c:\Users\Thomas\Documents\Report_generator\exact-render-buddy-96
npm run dev
```

3. **Tester** sur http://localhost:8080

---

## 📦 Fichiers à Fournir

Pour aider Lovable, vous pouvez leur donner :

1. **Ce brief** (BRIEF_LOVABLE_COMPLET.md)
2. **Les fichiers JSON existants** :
   - `Config/configJson.json`
   - `Config/GroupConfigJson.json`
3. **L'ancien code HTML** (pour référence) :
   - `static/reports.html`
   - `static/table.html`
   - `static/group_table.html`

---

## 💡 Points d'Attention Critiques

### 1. Chargement Initial des Données
**PROBLÈME ACTUEL** : Le nouveau frontend ne charge pas les données au démarrage.

**SOLUTION REQUISE** :
```typescript
// React Query - charger au montage du composant
const { data: facilities } = useQuery({
  queryKey: ['facilities'],
  queryFn: async () => {
    const res = await fetch('/items');
    return res.json();
  }
});

// Les données doivent s'afficher automatiquement dans le tableau
```

### 2. Sauvegarde Complète
**IMPORTANT** : Lors de la sauvegarde, envoyer TOUT le tableau, pas juste les modifications.

```typescript
// ✅ CORRECT
await fetch('/items', {
  method: 'PUT',
  body: JSON.stringify(allFacilities) // Tableau complet
});

// ❌ INCORRECT
await fetch('/items', {
  method: 'PUT',
  body: JSON.stringify(modifiedFacilities) // Juste les modifs
});
```

### 3. Timeout pour Génération
Les endpoints de génération peuvent prendre 2-5 minutes :

```typescript
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 600000); // 10 min

await fetch('/Reports_generation?...', {
  signal: controller.signal
});
```

### 4. Chemins Relatifs pour le Proxy
```typescript
// ✅ CORRECT - le proxy Vite redirige vers le backend
await fetch('/items');

// ❌ INCORRECT - contourne le proxy
await fetch('http://localhost:8000/items');
```

---

## 🎯 Résumé pour Lovable

**Votre mission :**
Créer un frontend React moderne et élégant qui :
1. Charge les données existantes depuis les JSON via l'API
2. Permet d'éditer ces données dans des tableaux
3. Sauvegarde les modifications dans les JSON
4. Gère l'upload de logos
5. Génère des rapports PDF (avec loader longue durée)
6. Liste, filtre, trie et gère les rapports générés

**Vous avez carte blanche sur :**
- Le design visuel
- L'organisation des pages
- Les composants UI
- Les animations
- L'UX

**Vous devez respecter :**
- Toutes les fonctionnalités listées ci-dessus
- Les endpoints API (ne pas les modifier)
- La structure des données JSON
- Le chargement automatique des données au démarrage

---

Bon développement ! 🚀
