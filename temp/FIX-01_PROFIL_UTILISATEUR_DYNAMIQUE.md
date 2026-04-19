# FIX-01 — Profil utilisateur dynamique dans les paramètres

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

Le fichier `PROFIL_UTILISATEUR.md` (à `{methodo_path}/informations utilisateur/PROFIL_UTILISATEUR.md`)
est la source de vérité du profil injecté dans le chat. Mais il n'est modifiable qu'en ouvrant le fichier
manuellement. L'utilisateur doit pouvoir le lire et le modifier directement depuis les Paramètres JARVIS.

La relation est **bidirectionnelle** : le fichier est la source unique. L'interface lit le fichier → l'affiche
→ l'utilisateur modifie → sauvegarde → le fichier est réécrit. Pas de DB intermédiaire.

---

## Objectif

1. Ajouter deux routes backend pour lire/écrire ce fichier
2. Ajouter une section dans l'onglet "Chat & Présets" des Paramètres pour afficher et éditer le contenu

---

## Fichier 1 — `backend/routers/config.py`

### Ajouter deux nouvelles routes à la fin du fichier

```python
@router.get("/profil_utilisateur")
def get_profil_utilisateur():
    """Lit le contenu de PROFIL_UTILISATEUR.md depuis le dossier METHODO."""
    from backend.database import get_connection as _get_conn
    from pathlib import Path as _Path
    
    # Lire methodo_path depuis la DB
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = 'methodo_path'")
    row = cursor.fetchone()
    conn.close()
    
    methodo_path = (row["value"] if row and row["value"] else "") or "C:\\DEV\\METHODO"
    profil_path = _Path(methodo_path) / "informations utilisateur" / "PROFIL_UTILISATEUR.md"
    
    if not profil_path.exists():
        return {"content": "", "path": str(profil_path), "exists": False}
    
    try:
        content = profil_path.read_text(encoding="utf-8")
        return {"content": content, "path": str(profil_path), "exists": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture profil : {e}")


@router.post("/profil_utilisateur")
def save_profil_utilisateur(data: ConfigValue):
    """Écrit le contenu dans PROFIL_UTILISATEUR.md."""
    from backend.database import get_connection as _get_conn
    from pathlib import Path as _Path
    
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = 'methodo_path'")
    row = cursor.fetchone()
    conn.close()
    
    methodo_path = (row["value"] if row and row["value"] else "") or "C:\\DEV\\METHODO"
    profil_path = _Path(methodo_path) / "informations utilisateur" / "PROFIL_UTILISATEUR.md"
    
    try:
        profil_path.parent.mkdir(parents=True, exist_ok=True)
        profil_path.write_text(data.value, encoding="utf-8")
        return {"message": "Profil sauvegardé", "path": str(profil_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur écriture profil : {e}")
```

`ConfigValue` est déjà importé en haut du fichier (utilisé par les autres routes). Ne pas l'importer une seconde fois.

---

## Fichier 2 — `frontend/settings.html`

### Ajouter une section dans l'onglet "Chat & Présets" (id="tab-chat")

Chercher la div `<div class="models-actions">` qui contient `btn-save-chat`.
Juste **avant** cette div, insérer :

```html
<div class="chat-config-row">
  <label class="chat-config-label">Profil utilisateur (PROFIL_UTILISATEUR.md)</label>
  <textarea id="chat-profil-utilisateur" class="input-field" rows="12"
    placeholder="Chargement..."></textarea>
  <span class="text-muted chat-config-hint">
    Injecté dans chaque conversation chat. Décrivez qui vous êtes, vos préférences,
    vos règles de travail. Ce texte est sauvegardé directement dans le fichier PROFIL_UTILISATEUR.md.
  </span>
</div>
```

### Modifier le bouton de sauvegarde existant

Le bouton `btn-save-chat` sauvegarde déjà la config chat. Il doit aussi sauvegarder le profil.
Chercher la fonction JS qui gère ce bouton (dans le `<script>` de settings.html ou dans un fichier JS associé).

Ajouter dans la **fonction de chargement** de l'onglet chat (là où on charge `chat-methodo-path`, `chat-session-note`, etc.) :

```javascript
// Charger le contenu du profil utilisateur
fetch('/api/config/profil_utilisateur')
  .then(r => r.json())
  .then(data => {
    const ta = document.getElementById('chat-profil-utilisateur');
    if (ta) ta.value = data.content || '';
  })
  .catch(() => {});
```

Ajouter dans la **fonction de sauvegarde** (handler du bouton `btn-save-chat`), après la sauvegarde normale de la config chat :

```javascript
// Sauvegarder le profil utilisateur
const profilContent = document.getElementById('chat-profil-utilisateur')?.value || '';
fetch('/api/config/profil_utilisateur', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({value: profilContent})
})
.then(r => r.json())
.then(() => {
  // Silencieux — la confirmation globale de sauvegarde suffit
})
.catch(err => console.warn('Erreur sauvegarde profil:', err));
```

### Charger le profil au chargement de la page

Dans le bloc d'initialisation de settings.html (là où les autres onglets sont chargés au démarrage),
ajouter l'appel de chargement du profil au moment où l'onglet chat est activé ou au chargement initial.

Si la page charge tous les onglets au démarrage : ajouter le fetch dans le bloc d'init global.
Si la page charge les onglets à la demande (au clic) : ajouter le fetch dans le handler du clic sur l'onglet "Chat & Présets".

---

## Ce qu'on ne touche pas

- La logique d'injection dans `chat_service.py` — elle lit déjà le fichier, rien à changer
- La DB — le profil n'est pas stocké en SQLite, le fichier est la source unique
- Les autres onglets des Paramètres

---

## Test manuel (3 étapes)

1. Ouvrir Paramètres → onglet "Chat & Présets" → la zone "Profil utilisateur" doit afficher le contenu
   actuel de `C:\DEV\METHODO\informations utilisateur\PROFIL_UTILISATEUR.md`
2. Modifier une ligne dans la zone → cliquer "Sauvegarder" → ouvrir le fichier dans l'explorateur
   → la modification doit être présente dans le fichier
3. Modifier le fichier directement → recharger la page Paramètres → la modification doit apparaître
   dans la zone textarea

---

## FIN DE MISSION

- [ ] Build sans erreur
- [ ] Test manuel 3 étapes validé
- [ ] Route GET `/api/config/profil_utilisateur` fonctionnelle
- [ ] Route POST `/api/config/profil_utilisateur` fonctionnelle
- [ ] Textarea visible dans l'onglet "Chat & Présets"
- [ ] Chargement et sauvegarde bidirectionnels fonctionnels
- [ ] Aucun fichier créé hors périmètre
- [ ] Aucune dépendance ajoutée
