# TEST MANUEL — Migration Config SQLite

## ✅ Test 1 : Migration Auto (RÉUSSI)

**Résultat** :
- ✅ Migration auto effectuée au démarrage serveur
- ✅ Log : "Migration config.json → SQLite terminée"
- ✅ Backup créé : `backend/data/config.json.backup`
- ✅ `config.json` allégé (seulement `model_preferences`)
- ✅ Clé `openrouter_key` stockée dans table `app_config`
- ✅ API `/config/` retourne clé masquée `"...c3d5"` depuis SQLite

**Commandes exécutées** :
```bash
python -m uvicorn backend.main:app --reload --port 8000
curl http://localhost:8000/api/config/
python temp/verify_migration.py
```

---

## 🔄 Test 2 : Persistance Clés API (À FAIRE)

**Objectif** : Vérifier que les clés modifiées dans l'interface persistent après reload

**Étapes** :
1. Ouvrir http://localhost:8000/app/settings.html
2. Cliquer "✏️ Modifier" sur une clé API
3. Modifier la valeur (ex: ajouter "test" à la fin)
4. Cliquer "💾 Sauvegarder"
5. Vérifier toast "✅ Configuration sauvegardée"
6. Recharger la page (F5)
7. **Attendu** : Clé modifiée toujours affichée masquée

**Vérification backend** :
```bash
python temp/verify_migration.py
```
Attendu : Nouvelle valeur dans SQLite

---

## 🔄 Test 3 : Test Connexion Provider (À FAIRE)

**Objectif** : Vérifier que le test connexion lit bien depuis SQLite

**Étapes** :
1. Ouvrir http://localhost:8000/app/settings.html
2. Cliquer "🔌 Tester" sur OpenRouter
3. **Attendu** : Badge "✅ OK" ou "❌ Échec" (selon validité clé)

---

## 📦 Test 4 : Build Portable (À FAIRE)

**Objectif** : Compiler exe standalone et tester portabilité

**Étapes** :
```bash
cd launcher
build.bat
```

**Attendu** :
- Exe créé : `dist/JARVIS.exe` (~50-100 MB)
- Compilation sans erreur
- Messages affichés :
  - "Compilation exe standalone (Python + dependances inclus)..."
  - "Build terminé !"
  - Instructions déploiement portable

**Test exe** :
```bash
dist\JARVIS.exe
```
Attendu : Serveur démarre, navigateur s'ouvre

---

## 🚀 Test 5 : Portabilité (OPTIONNEL)

**Objectif** : Tester sur autre PC sans Python

**Étapes** :
1. Créer dossier `JARVIS_Portable/`
2. Copier `dist/JARVIS.exe`
3. Copier `frontend/`
4. Copier `backend/data/` (optionnel, pour garder données)
5. Transférer sur clé USB
6. Tester sur autre PC Windows (sans Python installé)
7. Double-clic `JARVIS.exe`

**Attendu** : Serveur démarre, interface fonctionne

---

## 📊 Résumé Tests

| Test | Statut | Résultat |
|------|--------|----------|
| Migration auto | ✅ RÉUSSI | Clés API migrées vers SQLite |
| Persistance clés | ⏳ À FAIRE | - |
| Test connexion | ⏳ À FAIRE | - |
| Build portable | ⏳ À FAIRE | - |
| Portabilité | ⏳ OPTIONNEL | - |
