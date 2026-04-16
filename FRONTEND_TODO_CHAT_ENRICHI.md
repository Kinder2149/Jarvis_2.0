# TODO Frontend — Module Chat Enrichi

## Contexte
Backend livré et testé (159/159 tests passent).
Reste à implémenter l'UI pour exploiter les nouvelles capacités.

---

## 1. chat.html — Affichage et gestion folder_path

### Modifications nécessaires

**Sidebar conversation** :
- Afficher le `folder_path` sous le titre de la conversation (si défini)
- Format : `📁 C:\Chemin\Vers\Dossier` (icône + chemin tronqué si trop long)
- Bouton "Définir dossier" si `folder_path` est null
- Bouton "Changer dossier" si `folder_path` est défini

**Modal "Définir dossier"** :
- Input text pour saisir le chemin (avec validation côté client)
- Bouton "Parcourir" (optionnel, utilise `<input type="file" webkitdirectory>` si supporté)
- Bouton "Valider" → appelle `PATCH /api/chat/conversations/{id}/folder?folder_path={path}`
- Bouton "Annuler"

**Indicateur dossier actif** :
- Dans la zone de saisie message, afficher une petite badge si un dossier est défini
- Exemple : `📁 Dossier actif : projet_name` (tronqué)

---

## 2. chat.html — Indicateur recherche web

### Modifications nécessaires

**Pendant l'envoi du message** :
- Si le message contient des mots-clés de recherche (`cherche`, `recherche`, `internet`, etc.)
- Afficher un indicateur : `🔍 Recherche en cours...` sous la zone de saisie
- Disparaît quand la réponse arrive

**Dans la bulle de réponse** :
- Si `web_search_used: true` dans la réponse de l'API
- Afficher une petite icône `🌐` à côté du message assistant
- Tooltip au survol : "Recherche web effectuée"

**Sources utilisées** (optionnel V2) :
- Si recherche web effectuée, afficher les sources en bas de la bulle
- Format : "Sources : [Titre 1](url1), [Titre 2](url2)"

---

## 3. settings.html — Clé web search

### Modifications nécessaires

**Section "Clés API"** :
- Ajouter un champ `web_search_key` après `google_key`
- Label : "Clé Brave Search (optionnel)"
- Type : `password` (masqué par défaut)
- Placeholder : "Laisser vide pour désactiver la recherche web"
- Info bulle : "Obtenez une clé gratuite sur https://brave.com/search/api/"

**Sauvegarde** :
- Inclure `web_search_key` dans l'objet `api_keys` envoyé à `POST /api/config`
- Afficher un message si la clé est vide : "⚠️ Recherche web désactivée"

---

## 4. Endpoints API utilisés

**Déjà implémentés (backend prêt)** :

```
POST   /api/chat/conversations
       Body: { project_id?, title?, folder_path? }
       → Crée conversation avec folder_path optionnel
       → Si project_id sans folder_path : hérite du path du projet

GET    /api/chat/conversations
       → Retourne liste avec folder_path inclus

GET    /api/chat/conversations/{id}
       → Retourne conversation avec folder_path

PATCH  /api/chat/conversations/{id}/folder?folder_path={path}
       → Met à jour le folder_path d'une conversation
       → Retourne { updated: true, folder_path: "..." }

POST   /api/chat/conversations/{id}/messages
       Body: { content: "..." }
       → Retourne { ..., web_search_used: true/false }
```

---

## 5. Logique JavaScript

### Détection mots-clés recherche (côté client)

```javascript
function shouldShowSearchIndicator(message) {
  const keywords = ['cherche', 'recherche', 'trouve', 'internet', 'web', 
                    'dernière version', 'actuellement', 'aujourd\'hui'];
  return keywords.some(kw => message.toLowerCase().includes(kw));
}
```

### Appel PATCH folder_path

```javascript
async function updateConversationFolder(convId, folderPath) {
  const response = await fetch(
    `/api/chat/conversations/${convId}/folder?folder_path=${encodeURIComponent(folderPath)}`,
    { method: 'PATCH' }
  );
  return response.json();
}
```

---

## 6. Tests manuels

### Test 1 : Définir folder_path
1. Créer une conversation sans projet
2. Cliquer "Définir dossier"
3. Saisir `C:\DEV\PROJETS\intelligence_artificielle\Jarvis-2.0`
4. Valider
5. Vérifier que le dossier s'affiche dans la sidebar

### Test 2 : Héritage depuis projet
1. Créer une conversation avec un projet
2. Vérifier que `folder_path` est automatiquement défini (path du projet)

### Test 3 : Recherche web
1. Configurer une clé Brave Search dans settings
2. Envoyer un message : "Cherche la dernière version de Python"
3. Vérifier l'indicateur `🔍 Recherche en cours...`
4. Vérifier l'icône `🌐` dans la réponse

### Test 4 : Recherche web désactivée
1. Retirer la clé Brave Search
2. Envoyer un message avec mot-clé recherche
3. Vérifier que la recherche est silencieusement désactivée (pas d'erreur)

---

## 7. Priorité d'implémentation

1. **P0** : Affichage folder_path dans sidebar
2. **P0** : Bouton "Définir dossier" + modal + PATCH
3. **P1** : Indicateur recherche web `🔍`
4. **P1** : Icône `🌐` si web_search_used
5. **P1** : Champ clé web search dans settings
6. **P2** : Affichage sources (optionnel)

---

## Notes techniques

- Le backend gère automatiquement la détection de fichiers à lire (`lis fichier.txt`)
- Le backend gère automatiquement la détection de recherche web (mots-clés)
- Le frontend n'a qu'à afficher les indicateurs visuels
- Aucune logique métier côté frontend, tout est dans le backend
