# Test Manuel — Module Chat Enrichi (DB + Backend)

## Contexte
Enrichissement du module Chat avec 3 nouveaux champs :
- `internet_access` : Active/désactive la recherche web
- `context_summary` : Résumé automatique de la conversation
- `model` : Modèle LLM spécifique à la conversation

**Backend modifié** :
- `backend/database.py` : Migrations pour 3 colonnes
- `backend/routers/chat.py` : Schémas + endpoints (POST, GET, PATCH, POST update-summary)
- `backend/services/chat_service.py` : Logique internet_access, context_summary, model, auto-update résumé
- `tests/integration/test_api_projects.py` : Tests route-mission

---

## Test 1 : Migrations DB (colonnes ajoutées)

**Étapes** :
1. Arrêter le serveur si actif
2. Lancer : `python -c "from backend.database import init_db; init_db()"`
3. Vérifier que les migrations s'exécutent sans erreur

**Résultat attendu** :
- Aucune erreur `sqlite3.OperationalError`
- Les colonnes `internet_access`, `context_summary`, `model` sont créées dans `conversations`
- Valeurs par défaut : `internet_access=0`, `context_summary=''`, `model=''`

**Vérification** :
```bash
sqlite3 backend/data/jarvis.db "PRAGMA table_info(conversations);"
```
Colonnes attendues : id, project_id, title, folder_path, internet_access, context_summary, model, created_at, updated_at

---

## Test 2 : POST /conversations avec nouveaux champs

**Étapes** :
1. Démarrer le serveur : `python -m uvicorn backend.main:app --reload`
2. Créer une conversation avec `internet_access` et `model` :
```bash
curl -X POST http://localhost:8000/api/chat/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Enrichi", "internet_access": true, "model": "anthropic/claude-haiku-4.5"}'
```

**Résultat attendu** :
- Status 200
- Réponse contient : `"internet_access": true`, `"model": "anthropic/claude-haiku-4.5"`, `"context_summary": ""`

---

## Test 3 : GET /conversations (liste) retourne nouveaux champs

**Étapes** :
1. Lister les conversations :
```bash
curl http://localhost:8000/api/chat/conversations
```

**Résultat attendu** :
- Chaque conversation contient : `internet_access`, `context_summary`, `model`
- Valeurs par défaut si anciennes conversations : `false`, `""`, `""`

---

## Test 4 : GET /conversations/{id} retourne nouveaux champs

**Étapes** :
1. Récupérer une conversation spécifique :
```bash
curl http://localhost:8000/api/chat/conversations/1
```

**Résultat attendu** :
- Réponse contient : `internet_access`, `context_summary`, `model`
- Messages de la conversation inclus

---

## Test 5 : PATCH /conversations/{id} (mise à jour générique)

**Étapes** :
1. Mettre à jour plusieurs champs :
```bash
curl -X PATCH http://localhost:8000/api/chat/conversations/1 \
  -H "Content-Type: application/json" \
  -d '{"internet_access": false, "model": "google/gemini-2.0-flash-001", "folder_path": "C:/DEV/TEST"}'
```

**Résultat attendu** :
- Status 200
- Réponse contient les valeurs mises à jour
- Seuls les champs fournis sont modifiés

---

## Test 6 : PATCH /conversations/{id}/folder (rétrocompatibilité)

**Étapes** :
1. Mettre à jour uniquement `folder_path` (ancien endpoint) :
```bash
curl -X PATCH "http://localhost:8000/api/chat/conversations/1/folder?folder_path=C:/DEV/NOUVEAU"
```

**Résultat attendu** :
- Status 200
- `folder_path` mis à jour
- Autres champs inchangés

---

## Test 7 : Recherche web conditionnée sur internet_access

**Pré-requis** : Clé Brave Search configurée dans `app_config`

**Étapes** :
1. Créer conversation avec `internet_access=false`
2. Envoyer message : "Cherche la dernière version de Python"
3. Vérifier logs backend

**Résultat attendu** :
- Aucune recherche web effectuée (même si patterns détectés)
- Pas d'appel à l'API Brave Search
- `web_search_used: false` dans la réponse

**Étapes (internet_access=true)** :
1. Mettre à jour : `PATCH /conversations/1` avec `{"internet_access": true}`
2. Envoyer même message
3. Vérifier logs backend

**Résultat attendu** :
- Recherche web effectuée si patterns détectés
- `web_search_used: true` dans la réponse

---

## Test 8 : context_summary injecté dans le prompt

**Étapes** :
1. Mettre à jour manuellement le résumé :
```bash
curl -X PATCH http://localhost:8000/api/chat/conversations/1 \
  -H "Content-Type: application/json" \
  -d '{"context_summary": "Conversation sur Python. Utilisateur cherche infos version 3.12."}'
```
2. Envoyer un message dans cette conversation
3. Vérifier logs backend (system prompt construit)

**Résultat attendu** :
- Section `📋 RÉSUMÉ DE CETTE CONVERSATION :` présente dans le system prompt
- Résumé injecté entre `global_context` et `preset`
- Si `context_summary` vide → section absente

---

## Test 9 : Modèle spécifique à la conversation (conv_model)

**Étapes** :
1. Créer conversation avec `model="google/gemini-2.0-flash-001"`
2. Envoyer un message
3. Vérifier logs backend : `🤖 [CHAT_SERVICE] Modèle: ...`

**Résultat attendu** :
- Le modèle utilisé est `google/gemini-2.0-flash-001` (priorité sur config globale)
- Si `model=""` → utilise le modèle de `config.chat.model`

---

## Test 10 : POST /conversations/{id}/update-summary (génération résumé)

**Pré-requis** : Conversation avec au moins 5 messages

**Étapes** :
1. Appeler l'endpoint :
```bash
curl -X POST http://localhost:8000/api/chat/conversations/1/update-summary
```

**Résultat attendu** :
- Status 200
- Réponse : `{"summary": "...", "ok": true}`
- Le résumé est généré par le LLM (model_type='routing')
- `context_summary` mis à jour dans la DB
- Logs : `📋 [CHAT] Résumé mis à jour pour conversation 1`

**Cas erreur (conversation vide)** :
- Réponse : `{"summary": "", "ok": true, "message": "Aucun message à résumer"}`

---

## Test 11 : Auto-update résumé tous les 10 messages

**Étapes** :
1. Créer une nouvelle conversation
2. Envoyer 10 messages successifs
3. Vérifier logs backend après le 10e message

**Résultat attendu** :
- Après le 10e message : log `📋 [CHAT_SERVICE] Déclenchement auto-update résumé pour conversation X (10 messages)`
- Tâche asyncio créée pour appeler `update_conversation_summary`
- Résumé généré automatiquement en arrière-plan
- Pas d'erreur bloquante si génération échoue (warning dans logs)

---

## Test 12 : Tests route-mission (test_api_projects.py)

**Étapes** :
1. Lancer les tests :
```bash
pytest tests/integration/test_api_projects.py::TestRouteMission -v
```

**Résultat attendu** :
- `test_route_mission_projet_inexistant` : 404
- `test_route_mission_sans_mission` : 400
- `test_route_mission_projet_non_code` : 404
- Tous les tests passent

---

## Checklist finale

- [ ] Migrations DB exécutées sans erreur
- [ ] POST /conversations retourne `internet_access`, `context_summary`, `model`
- [ ] GET /conversations (liste) retourne nouveaux champs
- [ ] GET /conversations/{id} retourne nouveaux champs
- [ ] PATCH /conversations/{id} met à jour champs fournis
- [ ] PATCH /conversations/{id}/folder rétrocompatible
- [ ] Recherche web désactivée si `internet_access=false`
- [ ] Recherche web activée si `internet_access=true`
- [ ] `context_summary` injecté dans le system prompt
- [ ] `conv_model` utilisé en priorité sur config globale
- [ ] POST /conversations/{id}/update-summary génère résumé
- [ ] Auto-update résumé tous les 10 messages
- [ ] Tests route-mission passent (3/3)

---

## Notes

- Si `context_summary` est `None` ou `""` → ne pas injecter de section vide dans le prompt
- Le PATCH /conversations/{id} doit être rétrocompatible (folder_path seul doit fonctionner)
- Ne pas casser les tests existants sur les conversations
- L'auto-update du résumé ne doit pas bloquer l'envoi du message (asyncio.create_task)
