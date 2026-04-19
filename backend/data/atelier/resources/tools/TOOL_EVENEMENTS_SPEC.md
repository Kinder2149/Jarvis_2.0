# TOOL SPEC — ÉVÉNEMENTS & PRIVATISATIONS

> Statut : **Optionnel** — activé sur signal observé.
> Ce fichier définit le standard UX/fonctionnel. Cascade l'applique, ne le réinvente pas.

---

## DOULEUR RÉSOLUE

> Formulée en langage métier, pas technique.

"Vos soirées thématiques et privatisations, vous les gérez par téléphone ou sur Instagram. Vous n'avez pas de page dédiée pour annoncer les prochains événements, et les demandes de privatisation arrivent de partout sans aucune structure."

---

## DÉCLENCHEUR D'ACTIVATION

Activer si au moins un de ces signaux est observé :
- Soirées thématiques visibles sur Instagram ou le site (soirées vigneronnes, dîners accordés, repas de fêtes)
- Mention de privatisation, séminaires, repas d'entreprise
- Posts réguliers d'événements sur les réseaux sans formulaire de demande

---

## INFORMATIONS GÉRÉES

### Événements (créés par l'admin)

**Structure localStorage `evenements` :**

```json
[
  {
    "id": "evt-1",
    "titre": "Soirée vigneronne — Bourgogne",
    "date": "2026-05-10",
    "description": "Une sélection de 6 vins de Bourgogne accompagnés de mets du terroir. Présentation par notre sommelier.",
    "places": 24,
    "prix": "45,00 €",
    "statut": "visible",
    "inscrits": 8
  }
]
```

| Champ | Type | Obligatoire |
|---|---|---|
| Titre | text | oui — max 80 car. |
| Date | date | oui |
| Description | textarea | oui — max 300 car. |
| Nombre de places | number | oui |
| Prix par personne | text (ex: "45,00 €") | non — si vide : "Entrée libre" |
| Statut | toggle | oui — "visible" / "masqué" |

### Demandes (soumises par les visiteurs)

Stockées dans `actions_recues` avec `type: "evenement"` ou `type: "privatisation"`.

| Champ | Type | Obligatoire |
|---|---|---|
| Type | select | oui — "Événement spécifique" / "Privatisation" |
| Événement concerné | select dynamique | si type = Événement |
| Prénom | text | oui |
| Téléphone | tel | oui |
| Date souhaitée | date | si type = Privatisation |
| Nombre de personnes | stepper | oui |
| Message / occasion | textarea | non |

---

## AFFICHAGE INDEX.HTML

### Section "Prochains événements"

- Positionnée après la section Notre carte, avant Réservation
- Fond : `--bg-main`
- Titre : `<h2>Prochains événements</h2>`
- **Si aucun événement visible : section entièrement masquée** (display: none) — jamais "Aucun événement prévu"
- Si 1 événement : carte large centrée
- Si 2-3 événements : grille 2 colonnes sur desktop, 1 colonne mobile
- Si + de 3 : afficher les 3 prochains uniquement

**Carte événement :**

```
┌──────────────────────────────────────────┐
│  [DATE en évidence — ex: SAM. 10 MAI]    │
│  Soirée vigneronne — Bourgogne           │
│  Une sélection de 6 vins...              │
│  45 € par personne  ·  [N] places restantes │
│  [Je participe / Me renseigner]          │
└──────────────────────────────────────────┘
```

- Date : mise en forme lisible (pas de format ISO brut)
- Places restantes = places - inscrits confirmés
- Bouton CTA : "Je participe" si événement avec places · "Me renseigner" si privatisation
- Clic → ouvre le formulaire de demande (scroll ou modal simple)

### Formulaire de demande

- Champ "Type" : 2 cartes stylisées "Participer à un événement" / "Privatisation"
- Si "Événement" : select avec la liste des événements visibles
- Confirmation inline 4s après envoi

---

## AFFICHAGE ADMIN.HTML — Onglet Événements

### Vue liste des événements

```
┌──────────────────────────────────────────────────────────┐
│  Événements                              [+ Nouvel événement] │
├──────────────────────────────────────────────────────────┤
│  Soirée vigneronne — Bourgogne  SAM. 10 MAI              │
│  8 inscrits / 24 places · 45 €/pers.  [●Visible] [Modifier] [×] │
│                                                          │
│  Dîner de la Saint-Valentin        VEN. 14 FÉV.          │
│  12 inscrits / 20 places · 65 €/pers. [○Masqué] [Modifier] [×] │
└──────────────────────────────────────────────────────────┘
```

- Toggle Visible/Masqué : mise à jour immédiate sur index
- Modifier : formulaire inline (pas de page séparée)
- Supprimer : confirmation requise

### Demandes reçues (dans l'onglet Réservations principal)

Les demandes événements et privatisations apparaissent dans la liste des réservations avec un badge `[Événement]` ou `[Privatisation]` pour les différencier des réservations classiques. Même traitement : En attente / Confirmer / Annuler.

---

## DONNÉES DÉMO TYPE (3 événements)

```json
[
  {
    "id": "evt-demo-1",
    "titre": "Soirée vigneronne — Vins du Rhône",
    "date": "[J+14]",
    "description": "Une sélection de 5 vins de la vallée du Rhône, accompagnés de planches de charcuterie et fromages. Présentation par notre sommelière.",
    "places": 20,
    "prix": "38,00 €",
    "statut": "visible",
    "inscrits": 6
  },
  {
    "id": "evt-demo-2",
    "titre": "Dîner accord mets & vins — Printemps",
    "date": "[J+21]",
    "description": "Un menu 4 services pensé en accord avec notre sélection de vins de saison.",
    "places": 16,
    "prix": "55,00 €",
    "statut": "visible",
    "inscrits": 4
  },
  {
    "id": "evt-demo-3",
    "titre": "Atelier dégustation débutants",
    "date": "[J+28]",
    "description": "Apprenez à déguster et identifier les arômes. Accessible à tous, aucune connaissance requise.",
    "places": 12,
    "prix": "28,00 €",
    "statut": "masqué",
    "inscrits": 0
  }
]
```

> Adapter les titres/descriptions selon l'univers du client (vignoble, bistrot, restaurant gastronomique...).

---

## VARIABLES À SUBSTITUER DANS LE PROMPT_CASCADE

```
{{EVENEMENTS_INITIAUX}}   → JSON des 3 événements démo adaptés au client
```

---

## CHECKLIST QA SPÉCIFIQUE

- [ ] Section Événements masquée sur index si aucun événement visible
- [ ] Places restantes calculées dynamiquement (places - inscrits)
- [ ] Toggle Visible/Masqué admin → mise à jour immédiate index
- [ ] Demandes événements distinguées des réservations classiques (badge)
- [ ] Formulaire demande : select événements chargé dynamiquement depuis localStorage
- [ ] Confirmation inline 4s — pas d'alert

---

*Créé le 2026-04-15 — Outil Événements V1 — Restauration*
