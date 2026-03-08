# EXEMPLES PROJETS — JARVIS 2.0

**Version** : 1.0  
**Date** : 6 mars 2026  
**Statut** : REFERENCE

---

## 🎯 OBJECTIF

Ce document présente 3 exemples concrets de projets créés avec JARVIS 2.0.

Chaque exemple montre :
- Le prompt utilisateur
- La réponse JARVIS attendue
- Le code généré
- Les tests à effectuer

---

## 📝 EXEMPLE 1 : TODO LIST SIMPLE

### Prompt Utilisateur

```
Je veux une TODO list simple avec Python FastAPI.

Fonctionnalités :
- Ajouter une tâche
- Marquer comme terminée
- Supprimer une tâche
- Lister toutes les tâches

Stockage : fichier JSON
```

### Réponse JARVIS (Phase 1 : Analyse)

```
OK, je comprends ton besoin. Voici ce que je propose :

ARCHITECTURE :
- Backend : Python + FastAPI (ta stack préférée)
- BDD : Fichier JSON (simple, pas de serveur BDD)
- Frontend : HTML/CSS/JS vanilla (interface simple)

FICHIERS À CRÉER :
- backend/main.py : API FastAPI avec routes CRUD
- backend/models.py : Modèle Task (Pydantic v2)
- backend/storage.py : Stockage JSON (save/load)
- frontend/index.html : Interface TODO list
- frontend/app.js : Logique CRUD
- tests/test_tasks.py : Tests pytest
- requirements.txt : fastapi, uvicorn, pydantic, pytest

STACK UTILISÉE :
✅ Python/FastAPI (ta stack préférée)

Tu valides cette architecture ?
```

### Code Généré (Extraits)

**backend/models.py** :
```python
from pydantic import BaseModel
from datetime import datetime

class Task(BaseModel):
    id: str
    title: str
    completed: bool = False
    created_at: datetime
```

**backend/storage.py** :
```python
import json
from pathlib import Path

class JsonStorage:
    def __init__(self, filepath: str = "tasks.json"):
        self.filepath = Path(filepath)
    
    def save(self, tasks: list[dict]) -> None:
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    
    def load(self) -> list[dict]:
        if not self.filepath.exists():
            return []
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
```

**backend/main.py** :
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import Task
from storage import JsonStorage
import uuid
from datetime import datetime

app = FastAPI()
storage = JsonStorage()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/tasks")
async def list_tasks():
    return storage.load()

@app.post("/tasks")
async def create_task(task: Task):
    tasks = storage.load()
    task.id = str(uuid.uuid4())
    task.created_at = datetime.now()
    tasks.append(task.model_dump())
    storage.save(tasks)
    return task

@app.put("/tasks/{task_id}")
async def update_task(task_id: str, completed: bool):
    tasks = storage.load()
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = completed
            storage.save(tasks)
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    tasks = storage.load()
    tasks = [t for t in tasks if t["id"] != task_id]
    storage.save(tasks)
    return {"message": "Task deleted"}
```

### Tests Guidés

```
MAINTENANT ON TESTE :

1. LANCE LE BACKEND :
   cd TODO_List
   python backend/main.py

2. OUVRE LE FRONTEND :
   Ouvre frontend/index.html dans ton navigateur

3. TESTE LES FONCTIONNALITÉS :
   - Ajoute une tâche "Faire les courses"
   - Marque-la comme terminée (coche)
   - Supprime-la (croix)

4. RÉSULTAT ATTENDU :
   - Interface : Tâche apparaît, se coche, disparaît
   - Logs backend : POST /tasks 200, PUT /tasks/{id} 200, DELETE /tasks/{id} 200
   - Fichier tasks.json : Créé avec les données

Ça marche ou tu as une erreur ?
```

---

## 🔐 EXEMPLE 2 : SITE AVEC AUTHENTIFICATION

### Prompt Utilisateur

```
Je veux un site avec inscription/connexion.

Fonctionnalités :
- Page inscription (email + mot de passe)
- Page connexion
- Page profil (accessible uniquement si connecté)
- Déconnexion

Auth : Supabase
```

### Réponse JARVIS (Phase 1 : Analyse)

```
OK, je comprends ton besoin. Voici ce que je propose :

ARCHITECTURE :
- Frontend : HTML/CSS/JS vanilla (3 pages)
- Backend : Python + FastAPI (ta stack préférée)
- BDD : PostgreSQL via Supabase (production)
- Auth : Supabase Auth (JWT RS256)

FICHIERS À CRÉER :
- frontend/index.html : Page connexion
- frontend/register.html : Page inscription
- frontend/profile.html : Page profil (protégée)
- frontend/auth.js : Logique auth Supabase
- backend/main.py : API FastAPI
- backend/auth.py : Middleware vérification JWT
- .env.example : Variables Supabase

INFOS NÉCESSAIRES :
- Clé API Supabase (je te guide pour la récupérer)
- URL projet Supabase

STACK UTILISÉE :
✅ Python/FastAPI + Supabase Auth (ta stack préférée)

Tu valides cette architecture ?
```

### Configuration Supabase (Phase 4)

```
CONFIGURATION SUPABASE :

1. Va sur https://supabase.com
2. Crée un compte (gratuit)
3. Clique "New project"
4. Nom : "mon-site-auth"
5. Mot de passe BDD : [choisis un mot de passe fort]
6. Région : Europe West (Ireland)
7. Clique "Create project" (attends 2 min)

8. Copie ces informations (Settings > API) :
   - Project URL : https://xxxxx.supabase.co
   - anon public key : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

9. Crée fichier .env à la racine :
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

10. Redémarre le serveur backend

Tu as récupéré les infos ?
```

### Code Généré (Extraits)

**frontend/auth.js** :
```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://xxxxx.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
const supabase = createClient(supabaseUrl, supabaseKey)

// Inscription
async function signUp(email, password) {
    const { data, error } = await supabase.auth.signUp({
        email: email,
        password: password
    })
    if (error) throw error
    return data
}

// Connexion
async function signIn(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({
        email: email,
        password: password
    })
    if (error) throw error
    return data
}

// Déconnexion
async function signOut() {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
}

// Récupérer utilisateur connecté
async function getUser() {
    const { data: { user } } = await supabase.auth.getUser()
    return user
}
```

**backend/auth.py** :
```python
from fastapi import HTTPException, Header
import jwt
import os

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

async def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Tests Guidés

```
MAINTENANT ON TESTE :

1. LANCE LE BACKEND :
   cd mon-site-auth
   python backend/main.py

2. OUVRE LE FRONTEND :
   Ouvre frontend/register.html dans ton navigateur

3. TESTE INSCRIPTION :
   - Email : test@example.com
   - Mot de passe : Test1234!
   - Clique "S'inscrire"

4. TESTE CONNEXION :
   - Va sur index.html
   - Email : test@example.com
   - Mot de passe : Test1234!
   - Clique "Se connecter"

5. TESTE PAGE PROFIL :
   - Tu dois être redirigé vers profile.html
   - Tu dois voir ton email affiché

6. TESTE DÉCONNEXION :
   - Clique "Se déconnecter"
   - Tu dois être redirigé vers index.html

7. RÉSULTAT ATTENDU :
   - Interface : Inscription OK, connexion OK, profil affiché, déconnexion OK
   - Logs backend : POST /auth/signup 200, POST /auth/signin 200
   - Supabase Dashboard : Utilisateur créé visible dans "Authentication > Users"

Ça marche ou tu as une erreur ?
```

---

## 📱 EXEMPLE 3 : APPLICATION MOBILE (FLUTTER)

### Prompt Utilisateur

```
Je veux une app mobile de gestion de notes.

Fonctionnalités :
- Créer une note (titre + contenu)
- Lister toutes les notes
- Modifier une note
- Supprimer une note

Stockage : Local (SQLite)
Plateforme : Android + iOS
```

### Réponse JARVIS (Phase 1 : Analyse)

```
OK, je comprends ton besoin. Voici ce que je propose :

ARCHITECTURE :
- Mobile : Flutter/Dart (multi-plateforme Android + iOS)
- BDD : SQLite local (sqflite package)
- Pas de backend (app 100% offline)

FICHIERS À CRÉER :
- lib/main.dart : Point d'entrée app
- lib/screens/home_screen.dart : Écran liste notes
- lib/screens/note_screen.dart : Écran création/édition note
- lib/models/note.dart : Modèle Note
- lib/services/database_service.dart : Service SQLite
- pubspec.yaml : Dépendances (sqflite, path)

STACK UTILISÉE :
✅ Flutter/Dart (ta stack mobile préférée)

Tu valides cette architecture ?
```

### Code Généré (Extraits)

**lib/models/note.dart** :
```dart
class Note {
  int? id;
  String title;
  String content;
  DateTime createdAt;

  Note({
    this.id,
    required this.title,
    required this.content,
    required this.createdAt,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'content': content,
      'createdAt': createdAt.toIso8601String(),
    };
  }

  factory Note.fromMap(Map<String, dynamic> map) {
    return Note(
      id: map['id'],
      title: map['title'],
      content: map['content'],
      createdAt: DateTime.parse(map['createdAt']),
    );
  }
}
```

**lib/services/database_service.dart** :
```dart
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/note.dart';

class DatabaseService {
  static Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    String path = join(await getDatabasesPath(), 'notes.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) {
        return db.execute(
          'CREATE TABLE notes(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, createdAt TEXT)',
        );
      },
    );
  }

  Future<List<Note>> getNotes() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query('notes');
    return List.generate(maps.length, (i) => Note.fromMap(maps[i]));
  }

  Future<void> insertNote(Note note) async {
    final db = await database;
    await db.insert('notes', note.toMap());
  }

  Future<void> updateNote(Note note) async {
    final db = await database;
    await db.update('notes', note.toMap(), where: 'id = ?', whereArgs: [note.id]);
  }

  Future<void> deleteNote(int id) async {
    final db = await database;
    await db.delete('notes', where: 'id = ?', whereArgs: [id]);
  }
}
```

### Tests Guidés

```
MAINTENANT ON TESTE :

1. LANCE L'APP :
   cd notes_app
   flutter run

2. CHOISIS DEVICE :
   - Émulateur Android (si installé)
   - Ou navigateur Chrome (flutter run -d chrome)

3. TESTE CRÉATION NOTE :
   - Clique bouton "+" (FloatingActionButton)
   - Titre : "Ma première note"
   - Contenu : "Ceci est un test"
   - Clique "Enregistrer"

4. TESTE LISTE NOTES :
   - Tu dois voir la note dans la liste
   - Titre + extrait contenu affichés

5. TESTE MODIFICATION :
   - Clique sur la note
   - Modifie titre : "Note modifiée"
   - Clique "Enregistrer"
   - Vérifie changement dans liste

6. TESTE SUPPRESSION :
   - Swipe gauche sur la note
   - Clique "Supprimer"
   - Note disparaît de la liste

7. RÉSULTAT ATTENDU :
   - Interface : Création OK, liste OK, modification OK, suppression OK
   - Logs Flutter : INSERT, SELECT, UPDATE, DELETE SQL
   - BDD SQLite : Fichier notes.db créé dans app data

Ça marche ou tu as une erreur ?
```

---

## 🎓 POINTS CLÉS

### Communication avec JARVIS

**✅ Bon prompt** :
```
Je veux une TODO list avec Python FastAPI.
Fonctionnalités : ajouter, marquer terminée, supprimer.
Stockage : JSON.
```

**❌ Mauvais prompt** :
```
Fais-moi un truc pour gérer des tâches.
```

### Validation Architecture

**Toujours valider** avant génération :
- Vérifier stack proposée
- Vérifier fichiers listés
- Demander modifications si besoin

**Exemple** :
```
Utilisateur : Change SQLite par PostgreSQL

JARVIS : OK, je modifie :
- BDD : PostgreSQL via Supabase (au lieu de SQLite)
- Fichier : backend/database.py (connexion PostgreSQL)
- Dépendances : psycopg2-binary

Tu valides cette modification ?
```

### Tests Manuels

**Toujours tester** :
1. Interface (comportement attendu)
2. Logs backend (requêtes HTTP)
3. Données (fichier JSON, BDD)

**Si erreur** : Copier message complet et l'envoyer à JARVIS.

---

## 📚 RESSOURCES

**Documentation JARVIS** :
- `GUIDE_DEMARRAGE_RAPIDE.md` : Installation et premier projet
- `docs/JARVIS CONFIG/` : Configuration complète agents

**Stack Documentation** :
- FastAPI : https://fastapi.tiangolo.com
- Supabase : https://supabase.com/docs
- Flutter : https://docs.flutter.dev

---

**Bon développement avec JARVIS ! 🚀**
