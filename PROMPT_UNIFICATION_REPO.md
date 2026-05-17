# MISSION — Unification et nettoyage du dépôt Jarvis 2.0

## Contexte

Tu travailles sur le projet **Jarvis 2.0** situé dans ce dossier local.
Le dépôt distant est `origin` (GitHub : Kinder2149/Jarvis_2.0).
L'objectif est de repartir sur une base propre : **un seul dépôt, une seule branche `main`**, locale et distante identiques, aucune perte de travail.

---

## Ta mission en 5 phases

### PHASE 1 — Diagnostic complet

Exécute ces commandes et analyse chaque résultat avant de passer à la suivante.

```bash
# État du dossier de travail
git status

# Branches locales existantes
git branch -v

# Branches distantes existantes
git fetch origin
git branch -r

# Commits locaux non poussés sur toutes les branches locales
git log --oneline origin/main..HEAD

# Commits distants non récupérés en local
git log --oneline HEAD..origin/main

# Historique complet des 10 derniers commits sur toutes les branches
git log --oneline --all --graph -20
```

**Après chaque commande, identifie :**
- Y a-t-il des fichiers modifiés non commités ?
- Y a-t-il des commits locaux que le distant n'a pas ?
- Y a-t-il des commits distants que le local n'a pas ?
- Combien de branches locales et distantes existent en dehors de `main` ?

---

### PHASE 2 — Sécurisation du travail local

**Règle absolue : ne rien perdre.**

#### Cas A — Fichiers modifiés non commités (git status non vide)
Si `git status` montre des fichiers modifiés ou non suivis :

```bash
# Mettre de côté les modifications en cours
git stash push -m "sauvegarde-avant-unification-$(date +%Y%m%d-%H%M)"

# Vérifier que le stash est bien créé
git stash list
```

#### Cas B — Commits locaux non poussés
Si `git log --oneline origin/main..HEAD` montre des commits que le distant n'a pas :

```bash
# Pousser ces commits vers origin AVANT toute fusion
git push origin HEAD:main
```

Si le push est refusé (divergence), utilise :
```bash
git push origin HEAD:refs/heads/backup-local-$(date +%Y%m%d)
```
Cela crée une branche de sauvegarde distante — aucun commit ne sera perdu.

---

### PHASE 3 — Fusionner toutes les branches dans main

Pour chaque branche locale et distante qui existe en dehors de `main`, analyse ses commits uniques et décide si elle contient du travail utile.

#### Pour chaque branche locale `<nom-branche>` :

```bash
# Voir ce que cette branche a de plus que main
git log --oneline main..<nom-branche>
```

Si la branche contient des commits que main n'a pas → la fusionner :
```bash
git checkout main
git merge <nom-branche> --no-edit
```

Si la branche ne contient rien de plus que main → elle sera supprimée en phase 4 sans fusion.

#### Pour chaque branche distante `origin/<nom-branche>` :

```bash
# Voir ce que la branche distante a de plus que main local
git log --oneline main..origin/<nom-branche>
```

Si elle contient des commits utiles → la récupérer :
```bash
git fetch origin <nom-branche>
git merge origin/<nom-branche> --no-edit
```

#### Cas particulier — branche `claude/personal-org-agent-xPTGr`
Cette branche distante contient un commit utile : `PROMPT_AGENT_ORGANISEUR.md`.
Elle doit être fusionnée dans main si ce fichier n'est pas déjà présent localement.

```bash
# Vérifier si le fichier est déjà là
ls PROMPT_AGENT_ORGANISEUR.md

# Si absent, récupérer la branche distante et fusionner
git fetch origin claude/personal-org-agent-xPTGr
git merge origin/claude/personal-org-agent-xPTGr --no-edit
```

---

### PHASE 4 — Synchroniser main local ↔ distant

Une fois toutes les fusions faites :

```bash
# Récupérer les derniers commits distants de main
git fetch origin main

# Fusionner si le distant a des commits que le local n'a pas
git merge origin/main --no-edit

# Pousser main local vers le distant
git push origin main
```

Vérifie que local et distant sont identiques :
```bash
git log --oneline -5
git log --oneline origin/main -5
```
Les deux listes doivent être identiques.

---

### PHASE 5 — Nettoyage : supprimer toutes les branches sauf main

#### Supprimer les branches locales (sauf main) :
```bash
# Lister toutes les branches locales hors main
git branch | grep -v "^\* main$" | grep -v "^  main$"

# Supprimer chacune (remplace <nom> par chaque branche trouvée)
git branch -d <nom>

# Si -d refuse (branche non fusionnée), utilise -D seulement si tu as confirmé
# en PHASE 3 qu'elle ne contient rien d'unique
git branch -D <nom>
```

#### Supprimer les branches distantes (sauf main) :
```bash
# Lister les branches distantes
git branch -r | grep -v "origin/main" | grep -v "origin/HEAD"

# Supprimer chacune (remplace <nom> par chaque branche distante trouvée, sans le préfixe "origin/")
git push origin --delete <nom>
```

#### Supprimer le stash si tout est bon :
```bash
# Vérifier le stash
git stash list

# Si le stash de sauvegarde n'est plus utile (son contenu est déjà dans main)
git stash drop stash@{0}

# Si le stash contient du travail à récupérer, le réappliquer d'abord
git stash pop
```

---

### PHASE 6 — Vérification finale

```bash
# État final attendu
git status
# → "On branch main, nothing to commit, working tree clean"

git branch -a
# → Seuls "main" et "origin/main" doivent apparaître

git log --oneline -5
# → Même résultat que :
git log --oneline origin/main -5

# Confirmer que PROMPT_AGENT_ORGANISEUR.md est présent
ls PROMPT_AGENT_ORGANISEUR.md
```

**Résultat attendu :**
- Une seule branche locale : `main`
- Une seule branche distante : `origin/main`
- Local et distant identiques (même commit HEAD)
- Aucun fichier modifié non commité
- `PROMPT_AGENT_ORGANISEUR.md` présent à la racine

---

## Règles de sécurité — à respecter absolument

1. **Ne jamais faire `git reset --hard` sans avoir stashe ou poussé avant**
2. **Ne jamais faire `git push --force`** — si un push est refusé, créer une branche de sauvegarde distante plutôt
3. **Vérifier `git log --oneline main..<branche>`** avant de supprimer une branche — si elle a des commits uniques et non fusionnés, fusionner d'abord
4. **En cas de conflit de fusion** : résoudre manuellement, ne pas utiliser `--strategy=ours` sans analyser
5. **Signaler toute situation ambiguë** avant d'agir — demander confirmation si un choix peut entraîner une perte

---

## Rapport de fin de mission

Une fois terminé, produis un rapport avec :
- Liste des branches supprimées
- Liste des commits fusionnés depuis chaque branche
- État final : commit HEAD local = commit HEAD distant = quel hash
- Fichiers présents à la racine du projet (ls)
- Confirmation que PROMPT_AGENT_ORGANISEUR.md est lisible et non vide
