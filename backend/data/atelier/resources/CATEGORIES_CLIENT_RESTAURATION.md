# CATÉGORIES CLIENT — L'ATELIER CONNECTÉ

> Specs UX et données par catégorie de prospect.
> Lire la section correspondante avant de produire un PROMPT_CASCADE.
> Une catégorie = un vocabulaire, des champs, des outils, des données démo.

---

## RESTAURATION ✅ Développée

### Identité de la catégorie

| Signal principal | Réservations manuelles, menu qui change souvent |
|---|---|
| Douleur typique | Appels manqués le soir, carte à jour impossible sans webmaster |
| Ce qu'on démontre | Réservation en ligne + admin tout-en-un |

### Outils disponibles

| Outil | Statut | Déclencheur d'activation |
|---|---|---|
| Réservations | **Obligatoire** | Toujours présent |
| Menu & Ardoise | **Obligatoire** | Toujours présent |
| Événements | Optionnel | Signal observé : soirées thématiques, privatisations, repas événementiels |
| Avis clients | Optionnel | Signal observé : peu de présence Google Maps, avis positifs non valorisés |
| Vente à emporter | Optionnel | Signal observé : mention "à emporter", traiteur, plats du jour à récupérer |

### Vocabulaire admin

| Terme générique | Restauration |
|---|---|
| Action reçue | Réservation |
| Quantité | Couverts |
| Période AM | Déjeuner |
| Période PM | Dîner |
| Contenu éditeur | Carte des menus + Ardoise |
| KPI 1 | Demandes aujourd'hui |
| KPI 2 | En attente de confirmation |
| KPI 3 | Confirmées cette semaine |
| Bouton accès admin | 🔒 Espace Gérant |
| Titre login | Espace Gérant — [NOM_ETABLISSEMENT] |

### Champs formulaire — Réservations

| Champ | Type | Obligatoire | Règle |
|---|---|---|---|
| Prénom | text | oui | min 2 car. |
| Téléphone | tel | oui | format français |
| Date souhaitée | date | oui | min = aujourd'hui |
| Service | radio stylisé | oui | "Déjeuner" / "Dîner" |
| Nombre de couverts | stepper | oui | min 1, max 12 |
| Message / allergie | textarea | non | max 300 car. |

> Le champ "Service" est un radio stylisé en 2 cartes cliquables — jamais un `<select>`.
> Le stepper couverts utilise des boutons `−` et `+` — jamais `<input type="number">` brut.

### Données démo type — Réservations (5 entrées obligatoires)

IDs fixes `"demo-1"` à `"demo-5"`. Dates calculées par `offsetDate(N)`. Service en minuscules sans accent.

```javascript
const DEMO_RESERVATIONS = [
  {
    id: "demo-1", prenom: "Marie D.", telephone: "06 12 34 56 78",
    date: offsetDate(1), service: "diner", couverts: "2",
    message: "Anniversaire de mariage, si possible une table en retrait",
    statut: "En attente", source: "demo"
  },
  {
    id: "demo-2", prenom: "Thomas B.", telephone: "07 65 43 21 09",
    date: offsetDate(1), service: "dejeuner", couverts: "4",
    message: "", statut: "Confirmée", source: "demo"
  },
  {
    id: "demo-3", prenom: "Sophie M.", telephone: "06 98 76 54 32",
    date: offsetDate(2), service: "diner", couverts: "6",
    message: "Une personne allergique aux crustacés",
    statut: "En attente", source: "demo"
  },
  {
    id: "demo-4", prenom: "Laurent F.", telephone: "07 11 22 33 44",
    date: offsetDate(3), service: "dejeuner", couverts: "2",
    message: "Menu dégustation si disponible",
    statut: "Confirmée", source: "demo"
  },
  {
    id: "demo-5", prenom: "Isabelle R.", telephone: "06 55 44 33 22",
    date: offsetDate(4), service: "diner", couverts: "8",
    message: "Repas d'entreprise", statut: "Annulée", source: "demo"
  }
];
```

> Statuts : 2 En attente · 2 Confirmées · 1 Annulée — toujours respecter cette répartition.
> `service` : `"dejeuner"` ou `"diner"` (minuscules, sans accents) — valeur interne stockée par le formulaire.
> `date` : format ISO calculé dynamiquement — `offsetDate(0)` = aujourd'hui, `offsetDate(1)` = demain, etc.

### Structure index.html — Restauration

```
1. Hero (min-height: 90vh)
   └── Image réelle du restaurant en fond, overlay rgba(0,0,0,0.45)
   └── Logo + H1 (nom établissement) + sous-titre (accroche réelle)
   └── CTA principal : "Réserver une table" → #reservation

2. Présentation (fond --bg-alt)
   └── Texte réel (histoire, gérants, ambiance)
   └── Photo équipe ou ambiance réelle

3. Ardoise du jour (fond --accent à 10% opacité) — si activé
   └── Badge "Aujourd'hui"
   └── Plat du jour + prix + description
   └── Entrée + dessert si renseignés
   └── Section masquée si toggle = non disponible

4. Notre carte (fond --bg-main)
   └── Catégories avec onglets ou sections
   └── Plats avec nom + prix (+ description si fournie)

5. Réservation (fond --bg-alt)
   └── H2 "Réserver une table" (id="reservation")
   └── Formulaire complet (voir champs ci-dessus)
   └── Message de confirmation inline (4s, fond --accent)

6. [Optionnel] Événements (fond --bg-main)
   └── Section masquée si aucun événement actif

7. [Optionnel] Avis clients (fond --bg-alt)
   └── Carousel 3 cartes

8. [Optionnel] Commander à emporter (fond --bg-main)
   └── Formulaire emporter

9. Infos pratiques (fond --bg-alt ou footer)
   └── Adresse + horaires + téléphone réels
   └── Lien Google Maps externe

10. Footer
    └── Copyright uniquement — aucun lien admin ici
```

---

*Créé le 2026-04-15 — Restauration V1 complète*
