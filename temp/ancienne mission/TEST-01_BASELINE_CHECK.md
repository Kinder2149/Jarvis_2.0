# TEST-01 — Vérification baseline + état du serveur

> Lire PROJET_CONTEXTE.md en entier avant toute action.
> Ne modifier aucun fichier de code ou de test dans cette mission.

---

## Objectif

Vérifier que la base existante est stable avant d'écrire les nouveaux tests.
Cette mission ne crée rien — elle diagnostique uniquement.

---

## ÉTAPE 1 — Vérifier que le serveur tourne

```bash
curl -s http://localhost:8000/api/projects | python -c "import json,sys; d=json.load(sys.stdin); print(f'Serveur OK — {len(d)} projets')"
```

Si le serveur ne répond pas :
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
# Attendre 3 secondes puis retester
```

---

## ÉTAPE 2 — Lancer les tests unitaires + intégration

```bash
pytest tests/ --ignore=tests/live --ignore=tests/frontend -q 2>&1
```

Résultat attendu : **162+ passed, 0 failed**

Si des tests échouent : noter exactement lesquels et **STOP — revenir vers Claude avec le rapport**.

---

## ÉTAPE 3 — Lancer les tests E2E existants (Playwright)

```bash
pytest tests/test_frontend_e2e.py -v 2>&1
```

Résultat attendu : **41 passed** (ou quelques skipped si pas de données)

Si des tests FAIL (pas skip) : noter exactement lesquels et **STOP — revenir vers Claude**.

---

## ÉTAPE 4 — Inventaire des données disponibles

Exécuter ces requêtes et noter les résultats :

```bash
python -c "
import requests, json
api = 'http://localhost:8000/api'

# Projets
projects = requests.get(f'{api}/projects/').json()
print(f'Projets : {len(projects)}')

# Sessions par statut
from collections import Counter
statuses = Counter()
for p in projects:
    sessions = requests.get(f'{api}/projects/{p[\"id\"]}/sessions').json()
    for s in sessions:
        statuses[s['status']] += 1
print(f'Sessions par statut : {dict(statuses)}')

# Prospects Atelier
prospects = requests.get(f'{api}/atelier/prospects').json()
print(f'Prospects Atelier : {len(prospects)}')
has_session_status = all('session_status' in p for p in prospects) if prospects else 'N/A'
print(f'session_status dans prospects : {has_session_status}')

# Conversations
convs = requests.get(f'{api}/chat/conversations').json()
print(f'Conversations : {len(convs)}')
"
```

Ce rapport est critique pour TEST-02 : certains tests seront skippés si les données manquent.

---

## RAPPORT ATTENDU

```
BASELINE CHECK — [date]
═══════════════════════════════════════
Tests unitaires/intégration : [N]/162 passed, [N] failed
Tests E2E Playwright        : [N]/41 passed, [N] skipped, [N] failed

DONNÉES DISPONIBLES :
  Projets        : [N]
  Sessions       :
    COMPLETED      : [N]
    ABORTED        : [N]
    WAITING_VALID  : [N]
    RUNNING        : [N]
  Prospects Atelier : [N]
  session_status dans /atelier/prospects : OUI/NON
  Conversations  : [N]

VERDICT : ✅ Prêt pour TEST-02  /  ❌ Problème à résoudre
```

Si VERDICT ❌ : décrire le problème et **revenir vers Claude avant de continuer**.
