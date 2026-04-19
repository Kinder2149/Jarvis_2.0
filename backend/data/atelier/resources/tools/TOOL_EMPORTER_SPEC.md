# TOOL SPEC — VENTE À EMPORTER

> Statut : **Optionnel** — activé sur signal observé.
> Ce fichier définit le standard UX/fonctionnel. Cascade l'applique, ne le réinvente pas.

---

## DOULEUR RÉSOLUE

> Formulée en langage métier, pas technique.

"Vos clients vous appellent pour commander à emporter. Vous devez noter la commande à la main, répéter les disponibilités, estimer une heure. Pendant un service chargé, le téléphone qui sonne pour une commande emporter c'est une interruption de trop."

---

## DÉCLENCHEUR D'ACTIVATION

Activer si au moins un de ces signaux est observé :
- Mention "à emporter", "à récupérer", "traiteur" sur le site ou l'Instagram
- Plats du jour proposés à emporter (boulangeries, bistrots, restauration rapide)
- Horaires de retrait visibles ou suggérés
- Commentaires clients mentionnant la vente à emporter

---

## INFORMATIONS GÉRÉES

### Commandes reçues (soumises par les visiteurs)

Stockées dans `actions_recues` avec `type: "emporter"`.

**Structure d'une commande :**

```json
{
  "id": "cmd-1",
  "prenom": "Julie D.",
  "telephone": "06 23 45 67 89",
  "heure": "12:30",
  "items": [
    { "nom": "Plat du jour", "quantite": 2 },
    { "nom": "Salade César", "quantite": 1 }
  ],
  "message": "Sans croutons pour la salade",
  "statut": "En attente",
  "type": "emporter",
  "source": "demo"
}
```

### Formulaire côté client (index.html)

| Champ | Type | Obligatoire | Règle |
|---|---|---|---|
| Prénom | text | oui | min 2 car. |
| Téléphone | tel | oui | format français |
| Heure de passage | select | oui | créneaux définis par l'admin |
| Articles | checkboxes | oui | min 1 sélectionné |
| Quantité par article | stepper | oui | min 1, max 10 |
| Message / précisions | textarea | non | max 200 car. |

---

## AFFICHAGE INDEX.HTML

### Section "Commander à emporter"

- Positionnée avant les Infos pratiques
- Fond : `--bg-main`
- Titre : `<h2>Commander à emporter</h2>`
- Sous-titre : "Commandez à l'avance, récupérez sans attendre."

**Liste des articles (checkboxes stylisées) :**

```
┌──────────────────────────────────────────────────┐
│  ☐  Plat du jour                        [−] 1 [+] │
│  ☐  Formule déjeuner (entrée + plat)    [−] 1 [+] │
│  ☐  Salade César                        [−] 1 [+] │
│  ☐  Dessert du jour                     [−] 1 [+] │
└──────────────────────────────────────────────────┘
```

- Checkbox stylisée : clic sur toute la ligne
- Quand cochée : fond `--accent` à 10% opacité, bordure `--accent`, stepper activé
- Quand décochée : stepper grisé (non interactif)
- La liste d'articles est chargée depuis localStorage `menuEmporter` (défini par l'admin)

**Sélecteur d'heure :**

- Select stylisé avec les créneaux disponibles
- Ex : "12:00", "12:15", "12:30", "12:45", "13:00", "13:15", "13:30"
- Créneaux définis par l'admin (pas en dur dans le code)

**Bouton submit :** "Valider ma commande"
**Confirmation inline :** "Commande reçue ! Nous vous confirmons par téléphone." — 4s puis persistant (pas de timeout)

---

## AFFICHAGE ADMIN.HTML — Onglet Emporter

### Vue des commandes

```
┌────────────────────────────────────────────────────────────┐
│  Commandes à emporter                   [X aujourd'hui]    │
├────────────────────────────────────────────────────────────┤
│  12:30 · Julie D.  📞 06 23 45 67 89                      │
│  × 2 Plat du jour · × 1 Salade César                      │
│  💬 Sans croutons pour la salade                          │
│                              [En attente ▾]  [Prête ✓]    │
│                                                            │
│  13:00 · Marc F.  📞 07 88 99 00 11                       │
│  × 1 Formule déjeuner                                      │
│                              [Prête ✓]  [Remise ✓]        │
└────────────────────────────────────────────────────────────┘
```

**Statuts des commandes :**

| Statut | Couleur | Sens |
|---|---|---|
| En attente | `--warning` | Commande reçue, pas encore préparée |
| En préparation | `--accent` | En cuisine |
| Prête | `--success` | À récupérer |
| Remise | gris | Client passé, archivée |

- Changement de statut : bouton dédié par statut suivant (pas de select)
- Ordre d'affichage : par heure croissante

### Sous-section — Gestion de la carte emporter

```
┌─────────────────────────────────────────────────┐
│  Articles disponibles           [+ Ajouter]     │
├─────────────────────────────────────────────────┤
│  Plat du jour              [●Dispo] [Modifier] [×] │
│  Formule déjeuner          [●Dispo] [Modifier] [×] │
│  Salade César              [○Indispo][Modifier] [×] │
└─────────────────────────────────────────────────┘
```

- Toggle Dispo/Indispo : retire l'article du formulaire public immédiatement
- L'article indisponible n'apparaît plus dans les checkboxes côté client

### Sous-section — Créneaux horaires

```
┌─────────────────────────────────────────────────┐
│  Créneaux de retrait         [+ Ajouter créneau] │
├─────────────────────────────────────────────────┤
│  Service Midi : 12:00  12:15  12:30  12:45  13:00 │
│                 13:15  13:30                     │
│  [Modifier les créneaux midi]                   │
│                                                  │
│  Service Soir : 19:00  19:30  20:00  20:30       │
│  [Modifier les créneaux soir]                   │
└─────────────────────────────────────────────────┘
```

---

## DONNÉES DÉMO TYPE (5 commandes)

```json
[
  {
    "id": "cmd-demo-1",
    "prenom": "Julie D.",
    "telephone": "06 23 45 67 89",
    "heure": "12:30",
    "items": [{ "nom": "Plat du jour", "quantite": 2 }, { "nom": "Salade César", "quantite": 1 }],
    "message": "Sans croutons pour la salade",
    "statut": "En attente",
    "type": "emporter",
    "source": "demo"
  },
  {
    "id": "cmd-demo-2",
    "prenom": "Marc F.",
    "telephone": "07 88 99 00 11",
    "heure": "13:00",
    "items": [{ "nom": "Formule déjeuner", "quantite": 1 }],
    "message": "",
    "statut": "Prête",
    "type": "emporter",
    "source": "demo"
  },
  {
    "id": "cmd-demo-3",
    "prenom": "Camille B.",
    "telephone": "06 44 55 66 77",
    "heure": "12:15",
    "items": [{ "nom": "Plat du jour", "quantite": 1 }, { "nom": "Dessert du jour", "quantite": 1 }],
    "message": "Allergie aux noix",
    "statut": "En préparation",
    "type": "emporter",
    "source": "demo"
  },
  {
    "id": "cmd-demo-4",
    "prenom": "Thomas R.",
    "telephone": "07 11 22 33 44",
    "heure": "12:45",
    "items": [{ "nom": "Formule déjeuner", "quantite": 2 }],
    "message": "",
    "statut": "Remise",
    "type": "emporter",
    "source": "demo"
  },
  {
    "id": "cmd-demo-5",
    "prenom": "Nathalie G.",
    "telephone": "06 77 88 99 00",
    "heure": "13:30",
    "items": [{ "nom": "Salade César", "quantite": 2 }, { "nom": "Dessert du jour", "quantite": 2 }],
    "message": "Pour deux, livraison à la caisse",
    "statut": "En attente",
    "type": "emporter",
    "source": "demo"
  }
]
```

---

## VARIABLES À SUBSTITUER DANS LE PROMPT_CASCADE

```
{{ARTICLES_EMPORTER}}    → JSON des articles disponibles (extraits du vrai menu)
{{CRENEAUX_MIDI}}        → tableau des créneaux midi ex: ["12:00","12:15","12:30","12:45","13:00","13:15","13:30"]
{{CRENEAUX_SOIR}}        → tableau des créneaux soir ex: ["19:00","19:30","20:00","20:30"] (vide si pas de service soir emporter)
```

---

## CHECKLIST QA SPÉCIFIQUE

- [ ] Checkboxes articles : clic sur toute la ligne (pas juste la case)
- [ ] Stepper quantité grisé si article non coché
- [ ] Créneaux chargés depuis localStorage (pas en dur)
- [ ] Article indisponible masqué du formulaire public immédiatement après toggle admin
- [ ] Statuts en 4 étapes : En attente → En préparation → Prête → Remise
- [ ] Confirmation inline persistante après commande (pas de timeout)
- [ ] 5 données démo avec statuts variés (1 En attente, 1 En préparation, 1 Prête, 1 Remise, 1 En attente)

---

*Créé le 2026-04-15 — Outil Emporter V1 — Restauration*
