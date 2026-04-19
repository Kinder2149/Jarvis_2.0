# TOOL SPEC — MENU & ARDOISE

> Statut : **Obligatoire** — toujours présent pour la catégorie Restauration.
> Fusion de : Carte des menus (structure permanente) + Ardoise du jour (mise à jour quotidienne).
> Ce fichier définit le standard UX/fonctionnel. Cascade l'applique, ne le réinvente pas.

---

## DOULEUR RÉSOLUE

> Formulée en langage métier, pas technique.

"Votre carte change régulièrement mais vous ne pouvez pas la mettre à jour vous-même — il faut appeler quelqu'un. Et l'ardoise du jour, vous la changez dans votre tête ou sur un tableau, mais vos clients ne la voient jamais avant de venir."

---

## DÉCLENCHEUR D'ACTIVATION

- Toujours activé pour la catégorie Restauration.
- Signal confirmant la douleur : menu affiché sur le site original mais clairement daté, ou aucun menu visible.

---

## DEUX COMPOSANTS DE L'OUTIL

### Composant A — Carte des menus (structure permanente)

La carte complète du restaurant : catégories, plats, prix. Change rarement (saisons, refonte).

### Composant B — Ardoise du jour (mise à jour quotidienne)

Ce qui est "en avant" aujourd'hui. Change tous les jours ou toutes les semaines. Affiché en évidence sur la page d'accueil.

---

## INFORMATIONS GÉRÉES

### Composant A — Carte des menus

**Structure localStorage `menuCard` :**

```json
{
  "categories": [
    {
      "id": "cat-1",
      "nom": "Entrées",
      "ordre": 1,
      "plats": [
        {
          "id": "plat-1",
          "nom": "Terrine de foie gras maison",
          "prix": "14,00 €",
          "description": "Chutney de figues, brioche toastée",
          "disponible": true
        }
      ]
    }
  ]
}
```

| Champ | Type | Obligatoire |
|---|---|---|
| Nom de la catégorie | text | oui |
| Ordre d'affichage | number | oui (géré automatiquement) |
| Nom du plat | text | oui |
| Prix | text (ex: "14,00 €") | oui |
| Description courte | text | non — max 100 car. |
| Disponible | boolean | oui — toggle |

### Composant B — Ardoise du jour

**Structure localStorage dans `contenu_editable.ardoise` :**

```json
{
  "ardoise": {
    "disponible": true,
    "entree": { "nom": "Velouté de butternut", "prix": "8,00 €" },
    "plat": { "nom": "Filet de bœuf, sauce au poivre", "prix": "22,00 €", "note": "Cuisson selon votre goût" },
    "dessert": { "nom": "Tarte tatin maison", "prix": "7,00 €" },
    "formule": { "active": true, "prix": "32,00 €", "label": "Entrée + Plat + Dessert" }
  }
}
```

| Champ | Type | Obligatoire |
|---|---|---|
| Disponible aujourd'hui | toggle | oui |
| Plat du jour (nom) | text | oui si disponible |
| Plat du jour (prix) | text | oui si disponible |
| Note / cuisson | text | non — max 80 car. |
| Entrée du jour (nom + prix) | text | non |
| Dessert du jour (nom + prix) | text | non |
| Formule (active, prix, label) | composite | non |

---

## AFFICHAGE INDEX.HTML

### Section "Notre carte"

- Positionnée après la section Présentation
- Fond : `--bg-main`
- Titre : `<h2>Notre carte</h2>` (ou "La carte", "Notre menu" selon le vocabulaire du client)
- Affichage : onglets de catégories (si ≥ 3 catégories) ou sections empilées (si ≤ 2)
- Chaque plat : nom + prix en gras + description en texte secondaire
- Plat non disponible : barré visuellement, pas supprimé

### Section "Ardoise du jour"

- Positionnée juste AVANT la section réservation (entre Notre carte et Réservation)
- Fond : `--accent` à 8-10% opacité (`rgba` calculé depuis `--accent`)
- Badge "Aujourd'hui" en haut à gauche — fond `--accent`, texte blanc
- Affichage si `disponible = true` :
  - Ligne entrée (si renseignée) : libellé + prix
  - Ligne plat (obligatoire) : nom en gras + note + prix mis en évidence
  - Ligne dessert (si renseignée) : libellé + prix
  - Ligne formule (si active) : "Entrée + Plat + Dessert — 32€" en encart dédié
- Si `disponible = false` : **section entièrement masquée** (display: none) — jamais "Ardoise non disponible"

---

## AFFICHAGE ADMIN.HTML — Onglet Menu & Ardoise

**2 sous-sections dans un seul onglet, accessibles par boutons toggle :**

### Sous-section 1 — Ardoise du jour

> En haut de l'onglet — c'est ce que le gérant utilisera TOUS LES JOURS.

```
┌─────────────────────────────────────────────────┐
│  Ardoise du jour                  [◯ Disponible] │
├─────────────────────────────────────────────────┤
│  Plat du jour *                                  │
│  [________________________]  [_______€]          │
│  Note (cuisson, accompagnement...)               │
│  [________________________]                      │
│                                                  │
│  Entrée du jour (optionnel)                      │
│  [________________________]  [_______€]          │
│                                                  │
│  Dessert du jour (optionnel)                     │
│  [________________________]  [_______€]          │
│                                                  │
│  ┌─ Formule ────────────────────────────────┐   │
│  │  [◯ Activer la formule]                  │   │
│  │  Libellé : [________________________]    │   │
│  │  Prix    : [_______€]                    │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  [Mettre à jour l'ardoise]                      │
│  ✓ Ardoise mise à jour ! (4s, puis disparaît)  │
└─────────────────────────────────────────────────┘
```

- Toggle "Disponible" : si désactivé, masque la section ardoise sur index sans rechargement
- Bouton "Mettre à jour l'ardoise" → sauvegarde localStorage → confirmation inline 4s
- Prévisualisation simple en dessous du formulaire (lecture seule)

### Sous-section 2 — Carte des menus

> En dessous — utilisé moins souvent (changements saisonniers).

```
┌─────────────────────────────────────────────────┐
│  Carte des menus                [+ Catégorie]   │
├─────────────────────────────────────────────────┤
│  ▼ Entrées                      [Modifier] [×]  │
│     Terrine de foie gras  14€   [Modifier] [×]  │
│     Carpaccio de saint-ja...     [Modifier] [×]  │
│     [+ Ajouter un plat]                         │
│                                                  │
│  ▼ Plats                        [Modifier] [×]  │
│     ...                                         │
└─────────────────────────────────────────────────┘
```

- Catégories réordonnables (drag ou flèches haut/bas)
- Chaque plat : inline edit (clic "Modifier" → champs en place) + toggle disponibilité
- Suppression de catégorie : confirmation requise ("Supprimer cette catégorie et tous ses plats ?")
- Sauvegarde : bouton "Enregistrer la carte" → localStorage → confirmation inline

---

## DONNÉES DÉMO TYPE

### Ardoise démo par défaut (à personnaliser selon le vrai menu du client)

```json
{
  "disponible": true,
  "entree": { "nom": "Velouté de butternut, crème fraîche", "prix": "8,00 €" },
  "plat": { "nom": "Magret de canard, jus de cerise", "prix": "21,00 €", "note": "Cuisson selon votre goût" },
  "dessert": { "nom": "Fondant au chocolat, glace vanille", "prix": "7,00 €" },
  "formule": { "active": true, "prix": "31,00 €", "label": "Entrée + Plat + Dessert" }
}
```

### Carte démo par défaut (à remplacer par la vraie carte extraite du site)

3 catégories minimum : Entrées (3 plats), Plats (4 plats), Desserts (3 plats).
Utiliser la vraie carte du client si extraite en Phase 2 — jamais des plats génériques si le site original les fournit.

---

## VARIABLES À SUBSTITUER DANS LE PROMPT_CASCADE

```
{{NOM_ETABLISSEMENT}}     → utilisé dans les confirmations
{{MENU_CATEGORIES}}       → JSON des catégories et plats réels (extrait Phase 2)
{{ARDOISE_INITIALE}}      → JSON de l'ardoise démo par défaut
```

---

## CHECKLIST QA SPÉCIFIQUE

- [ ] Toggle "Disponible" ardoise : section masquée sur index sans rechargement de page
- [ ] Formulaire ardoise : sauvegarde + confirmation inline 4s
- [ ] Prévisualisation ardoise visible sous le formulaire
- [ ] Carte : catégories affichées avec vraies données du client (pas génériques)
- [ ] Plat non disponible : barré sur index, pas supprimé
- [ ] Modification carte admin → visible sur index au rechargement
- [ ] Section ardoise sur index : fond accent léger, badge "Aujourd'hui"
- [ ] Section ardoise masquée si disponible = false (display: none)

---

*Créé le 2026-04-15 — Outil Menu & Ardoise V1 — Restauration*
