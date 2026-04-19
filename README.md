# JARVIS

Interface locale d'orchestration de workflows IA multi-modèles.

## Démarrage

```bash
pip install -r requirements.txt
start.bat
```

L'application s'ouvre automatiquement sur `http://localhost:8000/app/index.html`

## Documentation

- `PROJET_CONTEXTE.md` : Source de vérité absolue
- `STACK_STANDARD.md` : Stack technique de référence
- `CHANGELOG.md` : Historique des missions

## Configuration

Accéder à `http://localhost:8000/app/settings.html` pour configurer les clés API.

## Installation Portable (sans Python)

Pour utiliser JARVIS sur un autre PC sans installer Python :

1. **Compiler l'exécutable standalone** :
   ```bash
   cd launcher
   build.bat
   ```
   Cela crée `dist/JARVIS.exe` (~50-100 MB, Python + dépendances inclus)

2. **Préparer le dossier portable** :
   - Copier `dist/JARVIS.exe`
   - Copier le dossier `frontend/`
   - Copier le dossier `backend/data/` (si vous voulez garder vos données)

3. **Déployer sur autre PC** :
   - Copier le dossier complet sur le nouveau PC
   - Double-clic sur `JARVIS.exe`
   - Le serveur démarre automatiquement et ouvre le navigateur

**Aucune installation Python requise** sur le PC cible ✅
