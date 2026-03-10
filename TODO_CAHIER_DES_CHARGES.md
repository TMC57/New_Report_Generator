# 📋 TODO LIST - Modifications Rapports E-Wash

**Objectif :** Livrer un premier exemple de rapport validé pour les envois de janvier

---

## 🎨 **1. UNIFORMISATION GÉNÉRALE** (Priorité HAUTE)

### 1.1 Mapping des couleurs produits ✅
- [x] Créer un fichier de configuration `product_colors.json` avec le mapping complet :
  - WNC 40 → `#65C482` (Emerald)
  - WNC 50 → `#34A65F` (Medium jungle)
  - WNC 60 → `#1F8A4B` (Sea green)
  - WNC 70 → `#0F6A33` (Dark emerald)
  - WNC 31 → `#F7C844` (Tuscan sun)
  - Auto-séchant → `#8698CB` (Wisteria blue)
  - Purple → `#7B3FA7` (Indigo bloom)
  - Eau → `#90F1EF` (Soft cyan)

### 1.2 Mapping des zones
- [ ] Implémenter les textures par zone :
  - Zone 1 → Plein (Gris)
  - Zone 2 → Tirets (Gris)
  - Zone 3 → Pointillés (Gris)
  - Zone 4 → Striures (Gris)

### 1.3 Uniformisation des noms
- [ ] Utiliser les noms abrégés standardisés (ex: "WNC 40 20 L")
- [ ] Arrondir toutes les valeurs à l'entier supérieur
- [ ] Uniformiser les unités (L pour litres, mL pour millilitres)

---

## 📄 **2. RAPPORT DE SITE - MODIFICATIONS**

### 2.1 Page de garde ✅ (Déjà fait partiellement)
- [x] Titre clair avec période bien définie
- [x] Footer en bas à gauche (déjà implémenté)
- [ ] Ajouter numéro client + code postal + ville
- [ ] Mapper l'installation si plusieurs routeurs (zones)

### 2.2 Page de dilution (Priorité HAUTE)
- [ ] **NOUVELLE PAGE** : Créer une page dédiée à la dilution
- [ ] Ajouter tableau compact avec :
  - Produits prévus dans le contrat
  - Date d'installation sur site
  - Date de dernière mise en place des buses
  - Infos buses : dilution et code couleur
  - **Impact** : "À cette dilution, 1L de produit = X lavages"

### 2.3 Page consommation quotidienne par routeur
- [ ] **Renommer** : "Suivi de la consommation quotidienne moyenne par lavage"
- [ ] Une page par zone (déjà implémenté ✅)
- [ ] Griser les jours fériés et week-ends
- [ ] Ajouter texte explicatif après légende :
  > "Les consommations sont exprimées en mL par utilisation dans la journée. Exemple : un point à 200 mL signifie qu'il a fallu en moyenne 200 mL pour laver chaque voiture dans la journée."
- [ ] Ajouter du texte pour aider le client (pics normaux, médiane, valeur normale)

### 2.4 Page consommation mensuelle de produits
- [ ] **Renommer** : "Suivi de la consommation quotidienne totale par produits"
- [ ] Une page par zone (déjà implémenté ✅)
- [ ] Ajouter texte explicatif :
  > "Les consommations sont exprimées en litres. Le graphique vous permet de suivre les pics d'activité sur le mois."

### 2.5 Page tableau jour par jour
- [ ] **Modifier structure** : Deux tableaux par produit
  - 1ère quinzaine (jours 1-15)
  - 2ème quinzaine (jours 16-31)
- [ ] Afficher par zone + compilé total
- [ ] Format : Produit + Zone en ligne, Jours en colonne

### 2.6 Page consommation totale mensuelle
- [x] Supprimer graphique camembert ✅ (Déjà fait)
- [ ] Garder tableau quantités mensuelles
- [ ] Afficher par produit ET par zone
- [ ] Format : Produit + Zone en ligne, Mois en colonne

### 2.7 Page état des stocks
- [ ] **Supprimer** le tableau d'état des stocks actuel
- [ ] **Ajouter** nouveau tableau avec :
  - Nombre de commandes par produit
  - Date de livraison la plus récente
- [ ] Suspendre temporairement l'envoi des alertes

### 2.8 Nouvelle page : Consommation d'eau
- [ ] **NOUVELLE PAGE** avant les consolidations
- [ ] Inclure rinçage des véhicules
- [ ] À définir avec TMH (proposition attendue)

---

## 📊 **3. RAPPORT GROUPE - MODIFICATIONS**

### 3.1 Page de garde
- [ ] Ajouter détail des sites :
  - N° client
  - Nom
  - Code postal
  - Ville
  - Produits utilisés

### 3.2 Page conso mensuelle
- [ ] **Renommer** : "Consommation mensuelle par site"
- [ ] Changer format : histogramme compilé (horizontal) au lieu de simple (vertical)
- [ ] Afficher par produit et par site

### 3.3 Page suivi conso mensuelles
- [ ] **NOUVEAU** : "Consommation mensuelle totale du site"
- [ ] Créer un tableau par produit avec détail des sites
- [ ] Format : Sites en ligne, Mois en colonne

---

## 🚨 **4. GESTION DES ANOMALIES** (Priorité HAUTE)

### 4.1 Détection des données manquantes
- [ ] **NE PAS ENVOYER** les rapports vides
- [ ] Implémenter système de détection de données manquantes
- [ ] Créer template email pour Würth avec :
  - Raison du manque de données
  - Solution préconisée

### 4.2 Marquage visuel des anomalies
- [ ] Mettre en rouge clair les jours sans données
- [ ] Version abrégée : "M" rouge foncé sur fond rouge clair
- [ ] Appliquer sur tous les graphiques et tableaux

---

## 📝 **5. AMÉLIORATION UX** (Priorité MOYENNE)

### 5.1 Titres et légendes
- [ ] Chaque graphique doit avoir :
  - Titre clair
  - Légende complète
  - Texte explicatif (ce que voit le client)

### 5.2 Textes d'aide
- [ ] Ajouter explications sur chaque page
- [ ] Guider le client dans l'interprétation des données

---

## 💰 **6. POINTS DIVERS** (À discuter)

### 6.1 Tarifs
- [ ] **BLOQUÉ** : Pas d'exposition des prix côté TMH
- [ ] Solution : Würth enrichit les données avec prix après génération
- [ ] À implémenter côté Würth uniquement

### 6.2 Export Excel
- [ ] Proposer nouveau gabarit Excel (en plus du PDF)
- [ ] À définir avec Vincent

---

## 📅 **PRIORISATION RECOMMANDÉE**

### **Phase 1 - URGENT** (Avant envoi rapports janvier)
1. ✅ Supprimer page camembert (FAIT)
2. Uniformisation couleurs produits
3. Page dilution (nouvelle)
4. Renommer titres des pages existantes
5. Ajouter textes explicatifs
6. Gestion rapports vides

### **Phase 2 - IMPORTANT** (Court terme)
1. Griser week-ends/jours fériés
2. Modifier structure tableaux (quinzaines)
3. Nouvelle page consommation d'eau
4. Marquage anomalies visuelles

### **Phase 3 - AMÉLIORATIONS** (Moyen terme)
1. Rapport groupe (modifications)
2. Textures zones
3. Export Excel
4. Optimisations UX

---

## 📌 **NOTES IMPORTANTES**

- **Deadline** : Premier exemple validé pour envoi rapports janvier
- **Contact** : Vincent pour questions techniques
- **Participants** : Ines, Fabien, Vincent
- **Données automatisées** : Ne pas ajouter de temps de traitement mensuel

---

## ✅ **DÉJÀ IMPLÉMENTÉ**

- [x] Suppression page camembert
- [x] Footer personnalisé première page
- [x] Logos Würth + TMH positionnés
- [x] Textes en majuscules
- [x] Polices uniformisées
- [x] Une page par zone (graphiques)
