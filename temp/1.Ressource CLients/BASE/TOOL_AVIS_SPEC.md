# TOOL SPEC — AVIS CLIENTS

> Statut : **Optionnel** — activé sur signal observé.
> Ce fichier définit le standard UX/fonctionnel. Cascade l'applique, ne le réinvente pas.

---

## DOULEUR RÉSOLUE

> Formulée en langage métier, pas technique.

"Vos clients satisfaits vous le disent en partant, mais ça ne reste nulle part. Vous avez peut-être des avis Google, mais ils sont éparpillés et invisibles sur votre site. Les nouveaux clients qui arrivent sur votre page ne voient pas ce que les autres ont vécu."

---

## DÉCLENCHEUR D'ACTIVATION

Activer si au moins un de ces signaux est observé :
- Peu d'avis Google visibles (moins de 30) alors que l'établissement semble fréquenté
- Avis positifs présents mais non mis en avant sur le site
- Aucune section témoignages sur le site actuel
- Client qui valorise fortement le bouche-à-oreille dans son discours

---

## INFORMATIONS GÉRÉES

### Avis soumis (par les visiteurs)

**Structure localStorage `avis_clients` :**

```json
[
  {
    "id": "avis-1",
    "prenom": "Claire M.",
    "note": 5,
    "texte": "Une adresse rare — accueil chaleureux, carte courte mais parfaite. On reviendra !",
    "date": "2026-04-10",
    "statut": "visible",
    "source": "demo"
  }
]
```

| Champ | Type | Obligatoire |
|---|---|---|
| Prénom (affiché sous forme "Prénom I.") | text | oui |
| Note | étoiles 1→5 | oui |
| Avis | textarea | oui — min 20 car., max 300 car. |
| Accord d'affichage | checkbox | oui — bloquant si non coché |
| Date | auto (Date.now()) | — |
| Statut | admin seulement | "en_attente" / "visible" / "masqué" |

---

## AFFICHAGE INDEX.HTML

### Section "Ils nous font confiance"

- Positionnée avant les Infos pratiques (avant-dernière section)
- Fond : `--bg-alt`
- Titre : `<h2>Ils nous font confiance</h2>` (ou "Ce qu'ils en disent", "Vos avis")
- **Si aucun avis visible : section entièrement masquée**
- Si 1-2 avis : cartes côte à côte
- Si ≥ 3 avis : carousel (3 cartes visibles, navigation par points)

**Carte avis :**

```
┌──────────────────────────────────────────┐
│  ★★★★★                                  │
│  "Une adresse rare — accueil chaleureux, │
│   carte courte mais parfaite."           │
│                                          │
│  Claire M. · il y a 5 jours             │
└──────────────────────────────────────────┘
```

- Étoiles : couleur `--accent`
- Texte de l'avis entre guillemets, police légèrement en italique
- Prénom + date relative ("il y a X jours" — jamais la date brute ISO)
- Carte : fond `--card-bg`, bordure `--border-soft`

### Appel à l'action sous le carousel

```
Vous avez apprécié votre expérience ?
[Laisser un avis Google] [Partager votre avis ici]
```

- "Laisser un avis Google" → lien Google Maps du client, ouvre dans nouvel onglet
- "Partager votre avis ici" → scroll vers le formulaire de soumission (ancre)

### Formulaire de soumission (sous le carousel)

- Sélecteur d'étoiles : 5 étoiles cliquables, interactif (hover + clic)
- Textarea avis : placeholder "Racontez votre expérience..."
- Checkbox accord : "J'accepte que mon avis soit affiché sur ce site"
- Bouton "Publier mon avis" (visible uniquement si checkbox cochée)
- Confirmation inline : "Merci ! Votre avis sera visible après validation."
- Après envoi : formulaire masqué, confirmation affichée

---

## AFFICHAGE ADMIN.HTML — Onglet Avis

### Vue liste de modération

```
┌──────────────────────────────────────────────────────────┐
│  Avis clients                            [X en attente]  │
├──────────────────────────────────────────────────────────┤
│  ★★★★★  Claire M. · 10 avril 2026                       │
│  "Une adresse rare — accueil chaleureux..."              │
│                              [●Visible] [○Masquer]       │
│                                                          │
│  ★★★★☆  Pierre D. · 8 avril 2026                        │
│  "Très bon rapport qualité/prix..."                      │
│                              [○Masqué]  [●Afficher]      │
└──────────────────────────────────────────────────────────┘
```

- Badge compteur en haut : "X avis en attente de validation"
- Toggle Visible/Masqué : mise à jour immédiate index
- Les avis "en attente" (nouveaux non encore validés) apparaissent en premier avec bordure colorée
- Pas de suppression définitive — seulement masquer

---

## DONNÉES DÉMO TYPE (5 avis visibles)

```json
[
  {
    "id": "avis-demo-1",
    "prenom": "Claire M.",
    "note": 5,
    "texte": "Une adresse que l'on garde précieusement. Accueil chaleureux, carte courte mais parfaitement maîtrisée. On reviendra sans hésiter.",
    "date": "[J-5]",
    "statut": "visible",
    "source": "demo"
  },
  {
    "id": "avis-demo-2",
    "prenom": "Pierre D.",
    "note": 5,
    "texte": "Excellente découverte ! Les vins sont bien choisis et les accords mets-vins parfaitement pensés. Le service est aux petits soins.",
    "date": "[J-12]",
    "statut": "visible",
    "source": "demo"
  },
  {
    "id": "avis-demo-3",
    "prenom": "Sophie et Marc T.",
    "note": 4,
    "texte": "Très bonne soirée en amoureux. Cadre intime, cuisine soignée. Peut-être un peu bruyant le samedi soir, mais rien de rédhibitoire.",
    "date": "[J-18]",
    "statut": "visible",
    "source": "demo"
  },
  {
    "id": "avis-demo-4",
    "prenom": "Isabelle R.",
    "note": 5,
    "texte": "J'ai organisé un repas d'anniversaire pour 8 personnes. L'équipe a été aux petits soins du début à la fin. Merci !",
    "date": "[J-25]",
    "statut": "visible",
    "source": "demo"
  },
  {
    "id": "avis-demo-5",
    "prenom": "Thomas B.",
    "note": 4,
    "texte": "Bon rapport qualité-prix pour le quartier. La formule du déjeuner est particulièrement bien pensée.",
    "date": "[J-30]",
    "statut": "visible",
    "source": "demo"
  }
]
```

> [J-N] = N jours avant aujourd'hui. Cascade calcule dynamiquement.

---

## VARIABLES À SUBSTITUER DANS LE PROMPT_CASCADE

```
{{URL_GOOGLE_MAPS}}     → lien direct vers la page Google Maps du client (pour le bouton "Laisser un avis Google")
{{AVIS_DEMO}}           → JSON des 5 avis adaptés (vocabulaire selon type de restaurant)
```

---

## CHECKLIST QA SPÉCIFIQUE

- [ ] Section masquée sur index si aucun avis visible
- [ ] Étoiles interactives dans le formulaire (hover + clic)
- [ ] Checkbox accord obligatoire (bouton désactivé si non cochée)
- [ ] Après soumission : formulaire masqué, confirmation affichée
- [ ] Avis en attente visibles en premier dans l'admin (badge compteur)
- [ ] Toggle admin → mise à jour index immédiate
- [ ] Dates affichées en relatif ("il y a X jours") — jamais format ISO

---

*Créé le 2026-04-15 — Outil Avis V1 — Restauration*
