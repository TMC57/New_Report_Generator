# 🔄 Projet Refactorisé - Génération de Rapports E-Wash

## 📁 Structure du projet

```
refactored/
├── models/              # Modèles de données (dataclasses)
│   ├── facility.py      # Modèle Facility complet
│   ├── device.py        # Modèle Device/Routeur
│   ├── product.py       # Modèle Product
│   └── consumption.py   # Modèles de consommation
├── services/            # Services métier
│   ├── cm2w_service.py       # Récupération données CM2W API
│   ├── excel_service.py      # Enrichissement Excel
│   ├── config_service.py     # Configuration locale
│   └── facility_service.py   # Service principal de consolidation
├── utils/               # Utilitaires
│   ├── logger.py        # Logger avec mode debug
│   ├── cache.py         # Système de cache
│   └── validators.py    # Validations
├── api/                 # Nouveaux endpoints FastAPI
│   └── routes.py        # Routes refactorisées
└── config/              # Configuration
    └── settings.py      # Settings centralisés
```

## 🎯 Objectifs

1. **Source unique de vérité** : Toutes les données d'une facility dans un seul modèle
2. **Traçabilité** : Mode debug pour suivre chaque étape de récupération/traitement
3. **Validation** : Vérifier que toutes les données nécessaires sont présentes
4. **Performance** : Cache et optimisation des appels API
5. **Maintenabilité** : Code propre, testé, documenté

## 🚀 Migration progressive

Le nouveau système cohabite avec l'ancien. On migre page par page des rapports.
