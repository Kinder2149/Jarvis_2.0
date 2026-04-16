# Test Manuel — Module Chat Enrichi

## Contexte
Backend livré (159/159 tests passent).
Frontend implémenté : folder_path UI + indicateur recherche web + clé Brave Search.

---

## Test 1 : Définir folder_path sur conversation sans projet

**Étapes** :
1. Ouvrir `http://localhost:8000/app/chat.html`
2. Cliquer "+ Nouvelle conversation" (sans sélectionner de projet)
3. Cliquer sur le bouton "📁 Définir" dans la sidebar
4. Saisir : `C:\DEV\PROJETS\intelligence_artificielle\Jarvis-2.0`
5. Valider

**Résultat attendu** :
- Le chemin s'affiche sous le titre de la conversation (tronqué à 30 chars)
- Format : `📁 ...intelligence_artificielle\Jarvis-2.0`
- Le bouton devient "📁 [...]"
- Si conversation vide : bandeau info "📂 Dossier lié : [chemin]"

---

## Test 2 : Héritage folder_path depuis projet

**Étapes** :
1. Sélectionner un projet dans le dropdown
2. Créer une nouvelle conversation
3. Vérifier que `folder_path` est automatiquement défini

**Résultat attendu** :
- Le chemin du projet s'affiche automatiquement
- Mention "(projet)" à côté du chemin
- Pas besoin de définir manuellement

---

## Test 3 : Modifier folder_path existant

**Étapes** :
1. Sur une conversation avec folder_path défini
2. Cliquer sur le bouton "📁 [...]"
3. Modifier le chemin ou laisser vide pour retirer
4. Valider

**Résultat attendu** :
- Le chemin est mis à jour dans la sidebar
- Si vide : le chemin disparaît, bouton redevient "📁 Définir"
- Toast "Dossier défini" ou "Dossier retiré"

---

## Test 4 : Recherche web avec clé configurée

**Pré-requis** : Clé Brave Search configurée dans settings

**Étapes** :
1. Ouvrir `http://localhost:8000/app/settings.html`
2. Saisir une clé Brave Search (ou laisser vide pour test suivant)
3. Sauvegarder
4. Retourner sur chat.html
5. Envoyer un message : "Cherche la dernière version de Python"

**Résultat attendu** :
- Pendant l'envoi : "⏳ JARVIS réfléchit..."
- Après 2 secondes : "🔍 Recherche effectuée" (si clé valide)
- Dans la bulle réponse : icône 🌐 en bas à droite
- Tooltip au survol : "Sources web utilisées"

---

## Test 5 : Recherche web sans clé (désactivée)

**Pré-requis** : Pas de clé Brave Search

**Étapes** :
1. Retirer la clé Brave Search dans settings
2. Envoyer un message avec mot-clé recherche : "Quelle est la version actuelle de FastAPI ?"

**Résultat attendu** :
- Pas d'erreur bloquante
- Indicateur normal "⏳ JARVIS réfléchit..."
- Pas d'icône 🌐 dans la réponse
- La recherche est silencieusement désactivée

---

## Test 6 : Lecture fichier local (backend automatique)

**Pré-requis** : Conversation avec folder_path défini

**Étapes** :
1. Envoyer un message : "Lis le fichier README.md"
2. Attendre la réponse

**Résultat attendu** :
- JARVIS lit le fichier automatiquement (backend)
- La réponse contient le contenu du fichier
- Pas d'indicateur spécial côté frontend (logique backend)

---

## Test 7 : Bandeau info dossier (conversation vide)

**Étapes** :
1. Créer une nouvelle conversation
2. Définir un folder_path
3. Ne pas envoyer de message

**Résultat attendu** :
- Bandeau discret affiché :
  ```
  📂 Dossier lié : [chemin]
  JARVIS peut lire les fichiers si tu lui demandes.
  ```
- Disparaît dès le premier message envoyé

---

## Test 8 : Persistance clé Brave Search

**Étapes** :
1. Configurer une clé Brave Search dans settings
2. Sauvegarder
3. Recharger la page settings
4. Vérifier que le champ affiche "Clé enregistrée (masquée)"

**Résultat attendu** :
- La clé est masquée (commence par "...")
- Le placeholder devient "Clé enregistrée (masquée)"
- La clé n'est pas écrasée lors de la sauvegarde

---

## Checklist finale

- [ ] Affichage folder_path dans sidebar (tronqué 30 chars)
- [ ] Bouton "📁 Définir" / "📁 [...]" fonctionnel
- [ ] Prompt natif pour saisir/modifier chemin
- [ ] Héritage automatique depuis projet
- [ ] Mention "(projet)" si hérité
- [ ] Bandeau info dossier (conversation vide)
- [ ] Indicateur "🔍 Recherche effectuée" (2 secondes)
- [ ] Icône 🌐 dans bulle réponse si web_search_used
- [ ] Tooltip "Sources web utilisées"
- [ ] Champ clé Brave Search dans settings
- [ ] Lien "Obtenir une clé gratuite"
- [ ] Persistance clé (masquée après sauvegarde)
- [ ] Recherche désactivée gracieusement sans clé

---

## Notes

- Tous les tests doivent passer sans erreur console
- Les 159 tests backend doivent toujours passer
- Aucun rechargement de page nécessaire pour les interactions folder_path
- Le backend gère automatiquement la détection de fichiers et recherche web
