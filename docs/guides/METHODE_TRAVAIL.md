# Méthode de Travail - JARVIS 2.0

Documentation de la méthode de travail no-code pour le développement et la maintenance de JARVIS 2.0.

## Principes Fondamentaux

### 1. Clarté et Simplicité

**Règle d'or** : Tout doit être compréhensible sans connaissances techniques approfondies.

- Noms de fichiers explicites (pas de `_simple`, `_nouveau`, `_v2`)
- Structure logique par fonctionnalité
- Documentation en français
- Pas de jargon technique inutile

### 2. Organisation Stricte

**Structure du projet** :
```
Jarvis-2.0/
├── backend/           # Serveur et logique métier
│   ├── chat/          # Tout ce qui concerne le chat
│   ├── agents/        # Agents IA et leurs configs
│   └── providers/     # Connexion aux services IA
├── frontend/          # Interface utilisateur
│   ├── index.html     # Page unique
│   ├── css/           # Styles
│   └── js/            # Logique frontend
├── docs/              # Documentation organisée
│   ├── api/           # Documentation API
│   ├── architecture/  # Architecture système
│   ├── guides/        # Guides (dont ce fichier)
│   └── archive/       # Docs anciennes mais utiles
└── _archived/         # Éléments archivés (BDD, RAG, etc.)
```

### 3. Pas de Doublons

**Interdictions** :
- ❌ Pas de fichiers `_simple.py` et `file.py` en même temps
- ❌ Pas de dossiers `config/` et `configs/`
- ❌ Pas de documentation éparpillée

**Solution** : Un seul fichier, un seul nom, une seule vérité.

## Organisation de la Documentation

### Structure en 4 Catégories

#### 1. `docs/api/`
**Contenu** : Documentation des routes API
**Fichiers** :
- `ROUTES_API.md` - Documentation complète et unique de l'API

**Règle** : Un seul fichier de référence API, toujours à jour.

#### 2. `docs/architecture/`
**Contenu** : Architecture du système
**Fichiers** :
- `ARCHITECTURE.md` - Architecture actuelle du système

**Règle** : Décrit comment le système fonctionne, pas comment il devrait fonctionner.

#### 3. `docs/guides/`
**Contenu** : Guides pratiques et méthodes
**Fichiers** :
- `METHODE_TRAVAIL.md` - Ce fichier
- `DEMARRAGE.md` - Guide de démarrage rapide

**Règle** : Guides accessibles, pas de technique pure.

#### 4. `docs/archive/`
**Contenu** : Documentation figée mais réutilisable
**Usage** : Référence pour réintégrer des fonctionnalités supprimées

**Règle** : Ne jamais modifier, seulement consulter.

## Conventions de Nommage

### Fichiers Backend

**Format** : `nom_descriptif.py`

**Exemples** :
- ✅ `storage.py` - Stockage des conversations
- ✅ `models.py` - Modèles de données
- ✅ `api.py` - Routes API
- ❌ `storage_simple.py` - Éviter les suffixes
- ❌ `api_v2.py` - Pas de versions dans le nom

### Fichiers Frontend

**Format** : `nom-descriptif.js` ou `nom-descriptif.css`

**Exemples** :
- ✅ `chat.js` - Logique principale du chat
- ✅ `agent-selector.js` - Composant sélection agent
- ✅ `chat.css` - Styles du chat
- ❌ `chat-new.js` - Éviter les suffixes
- ❌ `styles-v2.css` - Pas de versions

### Dossiers

**Format** : `nom_descriptif` (backend) ou `nom-descriptif` (frontend)

**Exemples** :
- ✅ `backend/chat/` - Module chat
- ✅ `backend/agents/configs/` - Configurations agents
- ✅ `frontend/js/components/` - Composants JS
- ❌ `backend/chat_module/` - Éviter les suffixes inutiles
- ❌ `frontend/old_components/` - Supprimer ou archiver

## Workflow de Développement

### Phase 1 : Planification

**Avant de coder** :
1. Définir clairement l'objectif
2. Lister les fichiers à modifier/créer
3. Identifier les dépendances
4. Valider la structure

**Questions à se poser** :
- Est-ce que ça respecte l'architecture actuelle ?
- Y a-t-il des doublons à éviter ?
- La documentation devra-t-elle être mise à jour ?

### Phase 2 : Implémentation

**Ordre d'exécution** :
1. **Nettoyage** : Supprimer les fichiers obsolètes
2. **Structure** : Créer les dossiers nécessaires
3. **Backend** : Implémenter la logique métier
4. **Frontend** : Créer l'interface utilisateur
5. **Documentation** : Mettre à jour les docs

**Règles** :
- Un changement à la fois
- Tester après chaque modification majeure
- Documenter au fur et à mesure

### Phase 3 : Documentation

**Fichiers à mettre à jour** :
- `README.md` si changement majeur
- `docs/api/ROUTES_API.md` si nouvelle route
- `docs/architecture/ARCHITECTURE.md` si changement structure
- Ce fichier si nouvelle méthode

**Format** :
- Français uniquement
- Exemples concrets
- Pas de jargon technique

### Phase 4 : Validation

**Checklist** :
- [ ] Pas de doublons (fichiers, dossiers, code)
- [ ] Nommage cohérent
- [ ] Documentation à jour
- [ ] Code testé manuellement
- [ ] Structure respectée

## Gestion des Changements

### Ajout de Fonctionnalité

**Processus** :
1. Planifier l'architecture
2. Créer les fichiers dans la bonne structure
3. Implémenter le backend
4. Créer le frontend
5. Documenter dans `docs/api/` ou `docs/guides/`

**Exemple** : Ajouter un système de tags
```
backend/chat/tags.py          # Logique tags
frontend/js/components/tags.js # Interface tags
docs/api/ROUTES_API.md         # Documenter les routes
```

### Suppression de Fonctionnalité

**Processus** :
1. Identifier tous les fichiers concernés
2. Archiver si potentiellement réutilisable
3. Supprimer définitivement sinon
4. Mettre à jour la documentation

**Règle** : Archiver dans `_archived/` ou `docs/archive/`, jamais dans le code actif.

### Refactoring

**Processus** :
1. Planifier la nouvelle structure
2. Créer les nouveaux fichiers
3. Migrer le code
4. Supprimer les anciens fichiers
5. Mettre à jour tous les imports
6. Mettre à jour la documentation

**Règle** : Pas de période de transition avec ancien et nouveau code coexistant.

## Logique No-Code

### Principe

**Objectif** : Permettre à quelqu'un sans compétences techniques de comprendre :
- Ce que fait le système
- Comment il est organisé
- Comment le modifier

### Application

**Documentation** :
- Expliquer le "quoi" et le "pourquoi", pas le "comment"
- Utiliser des schémas et exemples
- Éviter le code dans les explications

**Structure** :
- Noms de dossiers explicites
- Hiérarchie logique
- Séparation claire des responsabilités

**Exemples** :

✅ **Bon** :
```
backend/chat/          # Tout ce qui concerne le chat
  ├── api.py           # Routes pour communiquer avec le frontend
  ├── storage.py       # Sauvegarde des conversations
  └── models.py        # Structure des données
```

❌ **Mauvais** :
```
backend/
  ├── api_routes.py
  ├── data_layer.py
  ├── schemas.py
```

## Utilisation avec l'IA

### Donner des Instructions Claires

**Format recommandé** :
```
Objectif : [Ce que tu veux accomplir]

Contraintes :
- Pas de doublons
- Respecter la structure actuelle
- Documentation en français

Fichiers concernés :
- [Liste des fichiers]

Actions :
1. [Action 1]
2. [Action 2]
```

### Valider le Plan

**Avant l'exécution** :
- L'IA doit présenter un plan
- Vérifier qu'il respecte les principes
- Valider avant de commencer

### Suivi de l'Exécution

**Pendant** :
- L'IA doit mettre à jour le plan
- Vérifier chaque étape
- Arrêter si déviation

## Maintenance

### Nettoyage Régulier

**Fréquence** : Après chaque fonctionnalité majeure

**Actions** :
- Supprimer les fichiers inutilisés
- Vérifier les doublons
- Mettre à jour la documentation
- Archiver ce qui doit l'être

### Mise à Jour Documentation

**Quand** : À chaque changement

**Fichiers prioritaires** :
1. `docs/api/ROUTES_API.md` - Si routes modifiées
2. `docs/architecture/ARCHITECTURE.md` - Si structure modifiée
3. `README.md` - Si changement majeur

### Archivage

**Quand archiver** :
- Fonctionnalité supprimée mais potentiellement réutilisable
- Documentation obsolète mais référence utile
- Code remplacé mais logique intéressante

**Où archiver** :
- Code : `_archived/`
- Documentation : `docs/archive/`

**Format** :
```
_archived/
  └── nom_fonctionnalite_YYYYMMDD/
      ├── README.md  # Pourquoi archivé, comment réintégrer
      └── [fichiers]
```

## Résumé des Règles

### À Faire ✅

1. Un seul fichier par fonction
2. Noms explicites sans suffixes
3. Documentation en français
4. Structure par fonctionnalité
5. Archiver avant de supprimer
6. Mettre à jour la documentation
7. Tester manuellement
8. Valider le plan avant d'exécuter

### À Éviter ❌

1. Doublons (fichiers, dossiers, code)
2. Suffixes `_simple`, `_new`, `_v2`
3. Code et documentation en anglais
4. Structure technique incompréhensible
5. Suppression sans archivage
6. Documentation obsolète
7. Modifications sans tests
8. Exécution sans plan validé

## Sauvegarde en Mémoire

Cette méthode doit être sauvegardée en mémoire de l'IA pour :
- Référence systématique lors de chaque tâche
- Application automatique des principes
- Cohérence dans le temps

**Tags mémoire** : `methode_travail`, `no_code`, `organisation`, `jarvis_2.0`

---

**Version** : 1.0  
**Date** : 18 mars 2026  
**Auteur** : Kinder2149
