# INFRA-02 — METHODO : consolidation en source unique

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

Le dossier METHODO existe à deux endroits identiques :
- `C:\DEV\METHODO\` — source originale, chemin référencé dans le code
- `C:\DEV\PROJETS\intelligence_artificielle\Jarvis-2.0\temp\METHODO\` — copie créée lors d'une session de travail

Les deux dossiers sont **identiques** (vérification faite). La copie dans `temp/` est un doublon sans valeur. Le code (`backend/routers/chat.py`, `backend/schemas/config.py`) pointe vers `C:\DEV\METHODO\` — c'est le bon chemin.

Deuxième problème : `C:\DEV\METHODO\informations utilisateur\PROFIL_UTILISATEUR.md` contient un profil basé sur un ancien projet (Ultimate Frisbee Manager). Ce profil est périmé et ne reflète pas le contexte JARVIS.

---

## Objectif

1. Supprimer `temp/METHODO/` (doublon)
2. Réécrire `PROFIL_UTILISATEUR.md` avec le bon profil
3. Vérifier que `JARVIS_INDEX.md` dans `C:\DEV\METHODO\` est correct

---

## Action 1 — Supprimer le doublon

Supprimer intégralement le dossier :
```
C:\DEV\PROJETS\intelligence_artificielle\Jarvis-2.0\temp\METHODO\
```

Vérifier que `temp/` contient encore : `1.Ressource CLients/`, `ancienne mission/`, `verify_migration.py` et les fichiers INFRA-*/SPEC-* créés lors des sessions récentes — ne supprimer que le sous-dossier `METHODO/`.

---

## Action 2 — Réécrire PROFIL_UTILISATEUR.md

Remplacer intégralement le contenu de :
```
C:\DEV\METHODO\informations utilisateur\PROFIL_UTILISATEUR.md
```

Par ce contenu :

```markdown
# PROFIL UTILISATEUR — Kinder

## Rôle et contexte
Non-développeur. Pilote par vision fonctionnelle et résultats attendus.
Construit JARVIS comme outil principal pour orchestrer ses projets IA.
Stack active : JARVIS (localhost:8000) + Cascade (Windsurf) en fallback.

## Comment il formule ses demandes
- En français exclusivement, jamais en termes techniques
- Par le résultat attendu : "je veux que ça marche" plutôt que "modifier le service X"
- Par comparaison : "comme ça", "exactement pareil que..."
- Utilise des captures d'écran pour les problèmes visuels

## Ce qu'il ne voit pas seul
- Les dépendances entre couches (UI / Logique / Données)
- L'impact d'un changement sur plusieurs fichiers simultanément
- La distinction entre un bug et une fonctionnalité manquante
- La différence frontend / backend

## Règles absolues pour l'IA qui lui répond
- Répondre en français, sans jargon technique
- Si non testable manuellement → mission incomplète, ne pas valider
- Mission complexe → toujours cadrer via le chat JARVIS AVANT le module code
- Proposer UNE option avec sa justification — jamais une liste de choix à arbitrer
- Si demande floue → poser UNE seule question, la plus importante
- Jamais supposer, jamais compléter les blancs sans demander

## Ce qu'il exprime bien
- Les problèmes visuels (couleurs, tailles, lisibilité)
- L'expérience utilisateur ("les boutons sont trop gros")
- Les priorités : il identifie ce qui bloque vs ce qui est cosmétique
- La cohérence : il veut que les interfaces soient uniformes
```

---

## Action 3 — Vérifier JARVIS_INDEX.md

Ouvrir `C:\DEV\METHODO\JARVIS_INDEX.md` et vérifier que :

1. La section "Fichiers injectés TOUJOURS" contient exactement ces deux lignes de tableau :
   - `` `REGLES/REGLES_GLOBALES.md` ``
   - `` `informations utilisateur/PROFIL_UTILISATEUR.md` ``

2. La section "Fichiers injectés SI projet sélectionné" contient :
   - Source : `{chemin_projet}/PROJET_CONTEXTE.md`

3. La section "Fichiers EXCLUS" contient au minimum :
   - `_ARCHIVES/`
   - `TEMPLATES/`
   - `prompts/`
   - `REGLES/REGLES_CASCADE_SETTINGS.md`

Si tout est correct → ne rien modifier. Si des chemins sont cassés → corriger uniquement les chemins.

---

## Ce qu'on ne touche pas

- `C:\DEV\METHODO\REGLES\REGLES_GLOBALES.md` — ne pas modifier
- `C:\DEV\METHODO\prompts\` — ne pas modifier
- Le code backend — le chemin par défaut `C:\DEV\METHODO` est déjà correct dans `backend/schemas/config.py`
- `backend/data/config.json` — ne pas modifier

---

## Test manuel (3 étapes)

1. Vérifier que `temp/METHODO/` n'existe plus dans le projet Jarvis
2. Démarrer JARVIS et ouvrir une conversation dans le Chat (`http://localhost:8000/app/chat.html`)
3. Regarder `backend/data/jarvis.log` → chercher une ligne contenant `REGLES_GLOBALES` chargé → doit apparaître sans warning "absent"

---

## FIN DE MISSION

- [ ] Build sans erreur
- [ ] Test manuel 3 étapes validé
- [ ] `temp/METHODO/` supprimé
- [ ] `PROFIL_UTILISATEUR.md` réécrit
- [ ] Aucun fichier créé hors périmètre
