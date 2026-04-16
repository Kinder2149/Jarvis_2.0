# TEST MANUEL — Clôture Module Chat

## Objectif
Vérifier que start.bat fonctionne et que project_id est nullable.

## Étapes

### 1. Test start.bat
1. Double-cliquer sur `start.bat` à la racine du projet
2. Vérifier que :
   - Une fenêtre CMD minimisée s'ouvre
   - Le serveur uvicorn démarre sur le port 8000
   - Le navigateur s'ouvre automatiquement sur `http://localhost:8000/app/index.html`

### 2. Test project_id nullable
1. Aller sur `http://localhost:8000/app/chat.html`
2. Créer une nouvelle conversation sans projet (bouton "Nouvelle conversation")
3. Vérifier que la conversation se crée sans erreur
4. Envoyer un message dans cette conversation
5. Vérifier que le message s'envoie et reçoit une réponse

### 3. Vérification base de données
1. Ouvrir `backend/data/jarvis.db` avec un client SQLite
2. Exécuter : `SELECT * FROM conversations WHERE project_id IS NULL`
3. Vérifier qu'au moins une conversation existe avec `project_id = NULL`

## Résultat attendu
✅ start.bat lance le serveur et ouvre le navigateur
✅ Conversations sans projet fonctionnent
✅ project_id nullable confirmé en base
