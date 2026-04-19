# INFRA-03 — Graphify : intégration complète dans tous les cycles

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

Le support graphify existe déjà dans `context_manager.py` (flag `"graphify_report": true` dans `context_envelope`) et dans la majorité des pipelines. Mais deux trous critiques :

**Dans `pipelines.json` :**
- `session_start > orientation` : pas de `graphify_report`
- `session_end > cloture_docs` : pas de `graphify_report`
Ces deux steps sont les pivots de chaque cycle de travail — ce sont précisément ceux qui devraient lire le graphe en premier et en dernier.

**Dans le Chat (`chat_service.py`) :**
- Le chat n'injecte jamais le graphify report dans le system prompt
- Quand l'utilisateur pose une question sur l'architecture d'un projet → le chat répond sans connaissance du graphe

---

## Objectif

1. Ajouter `graphify_report` aux steps `session_start` et `session_end` dans `pipelines.json`
2. Injecter le graphify report dans le system prompt du Chat quand un projet est sélectionné
3. Ajouter un rappel de mise à jour graphify à la fin de `session_end`

---

## Action 1 — pipelines.json : compléter session_start et session_end

Fichier : `backend/data/pipelines.json`

Dans `session_start > steps > orientation > context_envelope`, ajouter la clé :
```json
"graphify_report": true
```

Dans `session_end > steps > cloture_docs > context_envelope`, ajouter la clé :
```json
"graphify_report": true
```

Ces deux modifications sont identiques aux autres pipelines qui ont déjà ce flag (bug_simple, mission_complexe, etc.).

---

## Action 2 — chat_service.py : injecter graphify dans le Chat

Fichier : `backend/services/chat_service.py`

### 2a — Nouvelle fonction `read_graphify_report`

Ajouter après la fonction `read_methodo_context` :

```python
def read_graphify_report(project_path: str, max_lines: int = 80) -> str:
    """Lit les premières lignes du GRAPH_REPORT.md du projet sélectionné.
    
    Args:
        project_path: Chemin absolu vers le dossier du projet
        max_lines: Nombre de lignes maximum à lire (évite de surcharger le contexte)
        
    Returns:
        String avec le résumé du graphe, ou "" si absent
    """
    if not project_path:
        return ""
    
    report_path = Path(project_path) / "graphify-out" / "GRAPH_REPORT.md"
    
    if not report_path.exists():
        return ""
    
    try:
        lines = report_path.read_text(encoding="utf-8").splitlines()
        excerpt = "\n".join(lines[:max_lines])
        return excerpt
    except Exception as e:
        logger.warning(f"Erreur lecture graphify report : {e}")
        return ""
```

### 2b — Modifier `build_system_prompt`

La signature actuelle est :
```python
def build_system_prompt(preset, methodo_context, session_note, project_context, folder_context=None, global_context="", context_summary=""):
```

Ajouter un paramètre `graphify_context: str = ""` à la fin :
```python
def build_system_prompt(preset, methodo_context, session_note, project_context, folder_context=None, global_context="", context_summary="", graphify_context=""):
```

Dans le corps de la fonction, après le bloc qui ajoute `project_context`, ajouter :
```python
    if graphify_context:
        parts.append("\n--- GRAPHE PROJET (structure et dépendances) ---")
        parts.append(graphify_context)
        parts.append("--- FIN GRAPHE ---\n")
```

### 2c — Appeler `read_graphify_report` dans `send_chat_message`

Dans la fonction `send_chat_message`, chercher l'endroit où `project_context` est construit (vers la ligne `methodo_path = config.get(...)`).

Après la ligne qui construit `project_context`, ajouter :
```python
    graphify_context = read_graphify_report(project_path) if project_path else ""
```

Puis passer `graphify_context=graphify_context` à l'appel de `build_system_prompt`.

---

## Action 3 — Rappel graphify en fin de session_end

Fichier : `backend/services/context_manager.py` (ou `pipeline_engine.py` — à identifier)

Dans la logique qui traite la clôture d'une session (`session_end`), après l'écriture des docs de clôture (`write_cloture_docs`), ajouter un log informatif :

```python
logger.info(
    "📊 [GRAPHIFY] Session terminée. Si des fichiers ont été modifiés, "
    "lancer : graphify . --update (changement mineur) ou graphify . (refactor/nouvelle feature)"
)
```

Ce log apparaît dans `backend/data/jarvis.log` et rappelle à l'utilisateur de maintenir le graphe à jour.

---

## Ce qu'on ne touche pas

- Le pipeline `atelier_restauration` — son contexte est volontairement différent (ressources métier propres)
- La logique d'exécution du graphify (pas d'appel automatique — trop lent)
- Les autres pipelines qui ont déjà `graphify_report: true` — ne pas re-modifier

---

## Test manuel (3 étapes)

1. Ouvrir le Chat, sélectionner le projet JARVIS, poser la question : "Quels sont les fichiers principaux de JARVIS ?"
   → La réponse doit mentionner des éléments cohérents avec la structure réelle du projet (signe que le graphe a été injecté)

2. Lancer un workflow `session_start` sur le projet JARVIS
   → Dans l'output de l'étape `orientation`, le modèle doit faire référence à des éléments du graphe

3. À la fin d'un `session_end`, chercher dans `backend/data/jarvis.log` la ligne `[GRAPHIFY] Session terminée`

---

## FIN DE MISSION

- [ ] Build sans erreur
- [ ] Test manuel 3 étapes validé
- [ ] `pipelines.json` : session_start et session_end ont `graphify_report: true`
- [ ] Chat injecte le graphe quand un projet est sélectionné
- [ ] Log de rappel graphify à la fin de session_end
- [ ] Aucun fichier créé hors périmètre
- [ ] Aucune dépendance ajoutée
