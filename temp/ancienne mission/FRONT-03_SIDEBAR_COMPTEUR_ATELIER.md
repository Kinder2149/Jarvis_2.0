# FRONT-03 — Compteur sidebar Atelier : session_status réel

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

Dans `frontend/assets/js/sidebar.js`, la fonction `getAtelierActiveCount()` :

```js
async function getAtelierActiveCount() {
  try {
    const prospects = await window.API.getProspects();
    return prospects.filter(p => p.statut === 'en_analyse').length;
  } catch (e) {
    return 0;
  }
}
```

Elle compte les **prospects dont le statut kanban est `en_analyse`**, pas les **sessions pipeline en WAITING_VALIDATION**. Ces deux choses sont différentes :
- Un prospect est `en_analyse` pendant toute la durée du pipeline (RUNNING, WAITING_VALIDATION, même parfois FAILED)
- Ce qu'on veut afficher dans la sidebar = le nombre de sessions qui **attendent une action de l'utilisateur** (WAITING_VALIDATION)

Le badge résultant est donc trompeur.

---

## Objectif

**Backend** : modifier `GET /atelier/prospects` pour inclure `session_status` dans chaque prospect (via JOIN SQLite avec la table `sessions`).

**Frontend** : modifier `getAtelierActiveCount()` pour compter les prospects dont `session_status === 'WAITING_VALIDATION'`.

---

## Fichiers à modifier

1. `backend/routers/atelier.py`
2. `frontend/assets/js/sidebar.js`

---

## Modifications détaillées

### 1. `backend/routers/atelier.py` — ajouter session_status dans la liste

Dans la fonction `list_prospects()`, modifier la requête SQL pour joindre la table `sessions` :

```python
@router.get("/prospects")
def list_prospects():
    """Liste tous les prospects avec leur session_status si une session existe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*,
               s.status AS session_status
        FROM prospects p
        LEFT JOIN sessions s ON s.id = p.session_id
        ORDER BY p.updated_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    prospects = []
    for row in rows:
        prospects.append({
            "id": row["id"],
            "session_id": row["session_id"],
            "session_status": row["session_status"],  # ← nouveau champ
            "nom": row["nom"],
            "categorie": row["categorie"],
            "url": row["url"],
            "statut": row["statut"],
            "score": row["score"],
            "form_data": row["form_data"],
            "fiche": row["fiche"],
            "proposition": row["proposition"],
            "demo_path": row["demo_path"],
            "demo_url": row["demo_url"],
            "notes": row["notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })
    
    return prospects
```

`session_status` sera `null` si le prospect n'a pas encore de session (p.session_id IS NULL ou session inexistante).

### 2. `sidebar.js` — modifier `getAtelierActiveCount`

```js
async function getAtelierActiveCount() {
  try {
    const prospects = await window.API.getProspects();
    return prospects.filter(p => p.session_status === 'WAITING_VALIDATION').length;
  } catch (e) {
    return 0;
  }
}
```

Le badge dans la sidebar affiche maintenant le nombre réel de sessions qui attendent une action humaine.

---

## Tests manuels

1. Redémarrer le serveur (modification backend)
2. **Cas 0 attente** : aucun pipeline en WAITING_VALIDATION → badge Atelier absent ou `0` ✓
3. **Cas N attentes** : lancer un pipeline Atelier → le laisser bloquer au step 0 (form saisie) → badge sidebar doit afficher `1`
4. Soumettre le formulaire → pipeline reprend → badge passe à `0` (plus en WAITING_VALIDATION) ✓
5. Vérifier que `GET /atelier/prospects` en DevTools Network renvoie `session_status` dans chaque prospect
6. Prospects sans session → `session_status: null` dans la réponse ✓

---

## FIN DE MISSION

- [ ] Build OK (backend redémarre sans erreur)
- [ ] `GET /atelier/prospects` retourne `session_status` pour chaque prospect
- [ ] Badge sidebar compte les WAITING_VALIDATION réels (pas les en_analyse)
- [ ] PROJET_CONTEXTE.md section 8 et CHANGELOG.md mis à jour
