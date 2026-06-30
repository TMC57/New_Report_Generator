# Système d'Alertes de Consommation

## Vue d'ensemble

Le système d'alertes surveille automatiquement les facilities sans consommation de produits et envoie des notifications par email lorsque de nouvelles alertes sont détectées.

## Fonctionnalités

### 1. **Vérification quotidienne automatique**
- Exécution tous les jours à **9h00** (heure de Paris)
- Vérifie les facilities selon les paramètres configurés
- Compare avec les alertes précédentes pour détecter les nouvelles

### 2. **Paramètres persistants**
- **Seuil d'inactivité** : 1 à 365 jours (défaut: 10 jours)
- **Filtre facilities** : Option pour vérifier uniquement les 64 facilities du fichier Excel uploadé
- Les paramètres sont sauvegardés automatiquement dans `config/alerts_config.json`

### 3. **Notifications par email**
- Envoi automatique d'emails HTML formatés
- Uniquement pour les **nouvelles** alertes (facilities qui n'étaient pas en alerte avant)
- Support de plusieurs destinataires
- Gestion des emails via l'interface web

## Configuration SMTP

Pour activer l'envoi d'emails, définissez ces variables d'environnement dans votre fichier `.env` :

```env
# Configuration SMTP pour les emails d'alerte
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-application
SMTP_FROM=alerts@e-wash.fr
```

### Exemple avec Gmail

1. Créez un compte Gmail dédié ou utilisez un compte existant
2. Activez la validation en 2 étapes sur le compte
3. Générez un "Mot de passe d'application" :
   - Allez dans Paramètres Google → Sécurité
   - Validation en 2 étapes → Mots de passe des applications
   - Créez un nouveau mot de passe pour "Mail"
4. Utilisez ce mot de passe dans `SMTP_PASSWORD`

### Exemple avec un serveur SMTP personnalisé

```env
SMTP_HOST=mail.votre-domaine.com
SMTP_PORT=587
SMTP_USER=alerts@votre-domaine.com
SMTP_PASSWORD=votre-mot-de-passe
SMTP_FROM=alerts@votre-domaine.com
```

## Utilisation de l'interface

### Page Alertes (`/alerts`)

#### Section "Paramètres de vérification"
- **Seuil d'inactivité** : Nombre de jours sans consommation (1-365)
- **Uniquement facilities du fichier Excel** : Active/désactive le filtre sur les 64 facilities
- Cliquez sur "Appliquer" pour sauvegarder et lancer une vérification
- Les paramètres sont persistants et utilisés pour la vérification quotidienne

#### Section "Notifications par email"
- **Ajouter un email** : Entrez une adresse et cliquez sur "+"
- **Liste des emails** : Voir tous les destinataires configurés
- **Supprimer** : Cliquez sur l'icône poubelle pour retirer un email
- **Avertissement** : Si le service SMTP n'est pas configuré, un message jaune s'affiche

#### Section "Statistiques"
- Nombre de facilities vérifiées
- Nombre d'alertes actives
- Seuil d'inactivité appliqué
- Date de dernière vérification

#### Section "Facilities sans consommation"
- Liste détaillée de toutes les facilities en alerte
- Affiche l'ID, le nom, le groupe et le nombre de jours d'inactivité

## Fichiers de configuration

### `config/alerts_config.json`
```json
{
  "inactivity_days": 10,
  "only_configured": true,
  "schedule_time": "09:00",
  "notification_emails": [
    "admin@exemple.com",
    "manager@exemple.com"
  ],
  "last_check_date": "2026-06-30T09:00:00",
  "last_alerts": [...]
}
```

**⚠️ Important** : Ce fichier est dans `.gitignore` pour ne pas écraser votre configuration lors des mises à jour.

## API Endpoints

### `GET /api/alerts/inactive-facilities`
Récupère les facilities sans consommation
- Query params: `days` (1-365), `only_configured` (bool)
- Utilise les valeurs sauvegardées si non spécifiées

### `GET /api/alerts/config`
Récupère la configuration actuelle

### `PUT /api/alerts/config`
Met à jour la configuration
```json
{
  "inactivity_days": 15,
  "only_configured": true
}
```

### `GET /api/alerts/emails`
Liste les emails de notification

### `POST /api/alerts/emails`
Ajoute un email
```json
{
  "email": "nouveau@exemple.com"
}
```

### `DELETE /api/alerts/emails/{email}`
Supprime un email

### `POST /api/alerts/test-email`
Envoie un email de test aux destinataires configurés

## Scheduler

Le scheduler démarre automatiquement avec l'application FastAPI :
- **Démarrage** : Au lancement de l'application (`startup_event`)
- **Arrêt** : À l'arrêt de l'application (`shutdown_event`)
- **Heure d'exécution** : 9h00 tous les jours (timezone Europe/Paris)

### Logs du scheduler
```
[SCHEDULER] Demarrage du scheduler...
[SCHEDULER] Scheduler demarre - Prochaine execution a 09:00
[SCHEDULER] Demarrage de la verification quotidienne
[SCHEDULER] Parametres: seuil=10j, only_configured=True
[SCHEDULER] 5 alertes detectees
[SCHEDULER] 2 nouvelle(s) alerte(s)
[SCHEDULER] Envoi d'email a 3 destinataire(s)
[SCHEDULER] Verification terminee avec succes
```

## Logique de détection des nouvelles alertes

1. Le système vérifie toutes les facilities (ou uniquement celles du fichier Excel)
2. Identifie celles sans consommation depuis X jours
3. Compare avec les alertes de la vérification précédente (stockées dans `last_alerts`)
4. **Nouvelles alertes** = facilities qui n'étaient PAS en alerte avant
5. Envoie un email uniquement s'il y a de nouvelles alertes
6. Sauvegarde les alertes actuelles pour la prochaine comparaison

## Exemple d'email envoyé

L'email contient :
- **Sujet** : `[E-Wash] X nouvelle(s) alerte(s) de consommation`
- **Corps HTML** avec :
  - Nombre de nouvelles alertes
  - Tableau détaillé (ID, Nom, Groupe, Jours d'inactivité)
  - Total des alertes actives
  - Date et heure de vérification

## Dépannage

### Les emails ne sont pas envoyés
1. Vérifiez que les variables SMTP sont définies dans `.env`
2. Vérifiez que le service Docker a accès au fichier `.env`
3. Consultez les logs : `docker compose logs -f`
4. Testez avec l'endpoint `/api/alerts/test-email`

### Le scheduler ne s'exécute pas
1. Vérifiez les logs au démarrage de l'application
2. Cherchez `[SCHEDULER] Scheduler demarre`
3. Le scheduler utilise le timezone `Europe/Paris`

### Les paramètres ne sont pas sauvegardés
1. Vérifiez que le dossier `config/` existe et est accessible en écriture
2. Consultez les logs pour les erreurs de sauvegarde
3. Le fichier `alerts_config.json` doit être créé automatiquement

## Rebuild Docker

Après modification de la configuration :

```bash
cd c:\Users\Thomas\Documents\Report_generator\refactored
docker compose down
docker compose build --no-cache
docker compose up -d
```

Consultez les logs :
```bash
docker compose logs -f
```
