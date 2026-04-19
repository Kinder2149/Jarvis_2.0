# INFRA-04 — Couche contexte globale : règles méthode dans le Module Code

> Lire PROJET_CONTEXTE.md en entier avant toute action.
> Cette mission est la plus complexe — lire en entier avant de commencer.

---

## Problème exact

Actuellement les règles de la méthode (`REGLES_GLOBALES.md`) sont injectées uniquement dans le Chat JARVIS. Le Module Code (pipelines) ne les reçoit jamais.

Résultat : quand un pipeline `mission_complexe` génère du code, le modèle ne sait pas :
- 3 couches max (UI / Logique / Données)
- Max 20 services/modules
- Zéro abstraction non demandée
- Zéro nouvelle dépendance sans demande explicite
- Modifier l'existant avant d'en créer du nouveau

Ces règles sont fondamentales — leur absence dans le Module Code est un risque fonctionnel direct.

---

## Objectif

Ajouter une couche "règles globales" injectée automatiquement dans les étapes clés des pipelines Module Code, sans surcharger les étapes d'exécution pure (correction, génération de code).

---

## Architecture cible

```
COUCHE 0 — Global (injecté par flag dans context_envelope)
  REGLES_GLOBALES.md + PROFIL_UTILISATEUR.md
  → Variable template : {{global_rules}}

COUCHE 1 — Projet (existant, inchangé)
  PROJET_CONTEXTE.md sections + STACK_STANDARD.md + file_list + graphify_report
  → Variables : {{projet_contexte}}, {{stack_standard}}, etc.

COUCHE 2 — Step (existant, inchangé)
  Outputs étapes précédentes + fichiers sélectionnés
  → Variables : {{previous_output_xxx}}, {{selected_files_content}}
```

---

## Fichiers à modifier

### 1. `backend/services/context_manager.py`

#### 1a — Nouvelle fonction `build_global_rules_context`

Ajouter en haut du fichier, après les imports :

```python
def build_global_rules_context(methodo_path: str) -> str:
    """Charge REGLES_GLOBALES.md et PROFIL_UTILISATEUR.md depuis le dossier METHODO.
    
    Returns:
        String concaténé des deux fichiers avec séparateurs, ou "" si METHODO absent.
    """
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    
    if not methodo_path:
        return ""
    
    methodo = Path(methodo_path)
    parts = []
    
    regles_path = methodo / "REGLES" / "REGLES_GLOBALES.md"
    if regles_path.exists():
        try:
            parts.append("=== RÈGLES MÉTHODE ===\n" + regles_path.read_text(encoding="utf-8"))
        except Exception as e:
            _logger.warning(f"Erreur lecture REGLES_GLOBALES.md : {e}")
    else:
        _logger.warning(f"REGLES_GLOBALES.md absent : {regles_path}")
    
    profil_path = methodo / "informations utilisateur" / "PROFIL_UTILISATEUR.md"
    if profil_path.exists():
        try:
            parts.append("=== PROFIL UTILISATEUR ===\n" + profil_path.read_text(encoding="utf-8"))
        except Exception as e:
            _logger.warning(f"Erreur lecture PROFIL_UTILISATEUR.md : {e}")
    else:
        _logger.warning(f"PROFIL_UTILISATEUR.md absent : {profil_path}")
    
    return "\n\n".join(parts)
```

#### 1b — Modifier `build_context_envelope`

Dans la fonction `build_context_envelope`, dans la branche principale (non-atelier), après la ligne `envelope["instructions"] = instructions`, ajouter :

```python
    # Couche globale : règles méthode
    if context_config.get("inject_global_rules", False):
        from backend.database import get_connection as _get_conn
        import json as _json
        # Lire methodo_path depuis la DB (table app_config, category='chat')
        try:
            _conn = _get_conn()
            _cursor = _conn.cursor()
            _cursor.execute("SELECT value FROM app_config WHERE key = 'methodo_path'")
            _row = _cursor.fetchone()
            _conn.close()
            _methodo_path = _row["value"] if _row and _row["value"] else ""
        except Exception:
            _methodo_path = ""
        envelope["global_rules"] = build_global_rules_context(_methodo_path)
    else:
        envelope["global_rules"] = ""
```

#### 1c — Modifier `inject_into_template`

Dans la fonction `inject_into_template`, après la ligne qui substitue `{{graphify_report}}`, ajouter :

```python
    result = result.replace("{{global_rules}}", envelope.get("global_rules", ""))
```

---

### 2. `backend/data/pipelines.json`

Ajouter `"inject_global_rules": true` dans le `context_envelope` des steps suivants (et uniquement ceux-là) :

**`session_start` :**
- `orientation` → ajouter `"inject_global_rules": true`

**`session_end` :**
- `cloture_docs` → ajouter `"inject_global_rules": true`

**`mission_complexe` :**
- `cadrage` → ajouter `"inject_global_rules": true`
- `document_mission` → ajouter `"inject_global_rules": true`
- Ne PAS ajouter sur `execution` et `correction` (trop verbeux, le contexte code prime)

**`nouveau_projet` :**
- `analyse_besoin` → ajouter `"inject_global_rules": true`
- `draft_projet_contexte` → ajouter `"inject_global_rules": true`

**`projet_existant` :**
- `scan_projet` → ajouter `"inject_global_rules": true`
- `audit_code` → ajouter `"inject_global_rules": true`

**`bug_simple` :**
- `analyse_bug` → ajouter `"inject_global_rules": true`
- Ne PAS ajouter sur `correction` (exécution pure)

**`atelier_restauration` :** Ne rien modifier. Le pipeline atelier a sa propre couche de contexte métier.

---

### 3. `backend/data/prompts.json`

Pour chaque step où `inject_global_rules: true` a été ajouté, vérifier si le template de prompt correspondant contient déjà `{{global_rules}}`. Si non, ajouter en début de template (avant le reste du contexte) :

```
{{global_rules}}

---

```

Steps concernés (chercher leurs prompts dans `prompts.json` par le nom du step) :
- `orientation`, `cloture_docs`, `cadrage`, `document_mission`, `analyse_besoin`, `draft_projet_contexte`, `scan_projet`, `audit_code`, `analyse_bug`

Si un template de prompt n'existe pas encore dans `prompts.json` pour ces steps → ne pas créer, logguer un warning et continuer.

---

## Ce qu'on ne touche pas

- Les steps `execution`, `correction`, `verification_*`, `selection_fichiers` — pas de règles globales (exécution pure)
- Le pipeline `atelier_restauration` — architecture contexte différente volontairement
- La logique du Chat — elle a déjà ses règles via `read_methodo_context`
- `backend/routers/` — aucune modification

---

## Test manuel (3 étapes)

1. Lancer un workflow `session_start` sur le projet JARVIS
   → Dans l'output de l'étape `orientation`, la réponse du modèle doit faire référence aux règles (ex: "3 couches", "20 modules max" ou autre élément de REGLES_GLOBALES.md)

2. Lancer un workflow `mission_complexe` avec une demande simple (ex: "ajouter un champ texte dans le formulaire de création de projet")
   → Dans l'output `cadrage`, le modèle doit citer les contraintes d'architecture

3. Vérifier dans `backend/data/jarvis.log` : si `C:\DEV\METHODO\` est absent ou mal configuré → un warning `REGLES_GLOBALES.md absent` doit apparaître (pas une erreur silencieuse)

---

## FIN DE MISSION

- [ ] Build sans erreur
- [ ] Test manuel 3 étapes validé
- [ ] `context_manager.py` : fonction `build_global_rules_context` ajoutée
- [ ] `context_manager.py` : flag `inject_global_rules` géré dans `build_context_envelope`
- [ ] `pipelines.json` : flag ajouté sur les steps listés uniquement
- [ ] `prompts.json` : `{{global_rules}}` ajouté en début des templates concernés
- [ ] Atelier non modifié
- [ ] Aucun fichier créé hors périmètre
- [ ] Aucune dépendance ajoutée
