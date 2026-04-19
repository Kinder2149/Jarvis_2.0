# TOOL SPEC — RÉSERVATIONS

> Statut : **Obligatoire** — toujours présent pour la catégorie Restauration.
> Ce fichier définit le standard UX/fonctionnel. Cascade l'applique, ne le réinvente pas.

---

## DOULEUR RÉSOLUE

> Formulée en langage métier, pas technique.

"Vous gérez les réservations par téléphone — quand vous êtes en service, vous ne pouvez pas décrocher. Des demandes tombent le soir ou le week-end, vous les voyez le lendemain. Et vous n'avez aucun endroit pour voir d'un coup d'œil ce qui est pris ou libre."

---

## DÉCLENCHEUR D'ACTIVATION

- Toujours activé pour la catégorie Restauration.
- Signal confirmant la douleur : mention "réservation par téléphone", aucun outil de réservation détecté sur le site original.

---

## INFORMATIONS GÉRÉES

### Côté client (formulaire index.html)

| Champ | Type | Obligatoire | Contrainte |
|---|---|---|---|
| Prénom | text | oui | min 2 caractères |
| Téléphone | tel | oui | format français accepté |
| Date souhaitée | date | oui | min = aujourd'hui (attribut `min` dynamique) |
| Service | radio stylisé | oui | 2 options : "Déjeuner" / "Dîner" |
| Nombre de couverts | stepper | oui | min 1, max 12, défaut 2 |
| Message / allergie | textarea | non | max 300 caractères, placeholder : "Allergie, occasion spéciale..." |

### Côté admin (localStorage + affichage)

| Champ stocké | Source | Usage |
|---|---|---|
| id | généré (Date.now()) | identifiant unique |
| prenom | formulaire | affichage carte |
| telephone | formulaire | affichage + action rapide |
| date | formulaire | filtrage calendrier |
| service | formulaire | filtrage déjeuner/dîner |
| couverts | formulaire | affichage carte |
| message | formulaire | affichage carte |
| statut | admin | "En attente" / "Confirmée" / "Annulée" |
| source | système | "demo" pour les entrées pré-chargées |

---

## AFFICHAGE INDEX.HTML

**Section id="reservation"**

- Titre : `<h2>Réserver une table</h2>` (libellé adapté selon le client)
- Fond : `--bg-alt`
- Positionnée après la section Présentation (section 5 dans la structure standard)

**Formulaire :**
- Service : 2 cartes cliquables côte à côte, fond `--bg-main`, bordure `--border-soft`, bordure `--accent` quand sélectionné — jamais un `<select>` ni un radio HTML brut
- Stepper couverts : boutons `−` et `+` encadrant la valeur, fond `--card-bg` — jamais `<input type="number">` visible
- Bouton submit : fond `--accent`, texte blanc, libellé "Réserver ma table" ou équivalent métier
- Message de confirmation : inline sous le bouton, fond `--accent` à 15% opacité, texte `--accent`, visible 4 secondes puis disparaît — jamais `alert()`
- Si blocage capacité (outil Capacités actif) : afficher "Ce service est complet pour cette date" en rouge inline

---

## AFFICHAGE ADMIN.HTML — Onglet Réservations

**Vue par défaut : calendrier semaine + liste du jour**

### Calendrier semaine (7 colonnes)

- 7 jours à partir d'aujourd'hui
- Chaque colonne : nom du jour (lun, mar...) + numéro + point de couleur si réservation(s)
- Colonne sélectionnée : fond `--accent` léger, bordure `--accent`
- Clic → charge la liste des réservations du jour sélectionné

### Filtres service

- 2 boutons : "Déjeuner" / "Dîner" / "Tous" (defaut : Tous)
- Filtrent les cartes affichées sous le calendrier

### Carte de réservation

```
┌─────────────────────────────────────────────────┐
│  [Heure estimée ou service] · [N] pers.          │
│  Prénom NOM                                      │
│  📞 Téléphone                                    │
│  💬 Message (si présent)                         │
│                          [Badge statut]          │
│  [✓ Confirmer]  [✗ Annuler]                     │
└─────────────────────────────────────────────────┘
```

- Badge statut : "En attente" → `--warning`, "Confirmée" → `--success`, "Annulée" → `--danger`
- Bouton "Confirmer" désactivé si statut = Confirmée
- Bouton "Annuler" désactivé si statut = Annulée
- Changement de statut → mise à jour localStorage → badge mis à jour sans rechargement de page
- Si EmailJS activé : "Confirmer" déclenche l'envoi email client (une seule fois, flag `clientConfirmationSent`)

### État vide

- Message : "Aucune réservation pour cette sélection." (jamais un tableau ou liste vide)

---

## DONNÉES DÉMO TYPE (5 entrées obligatoires)

Voir `CATEGORIES_CLIENT.md` → section Restauration → "Données démo type — Réservations".

Règles :
- 2 En attente · 2 Confirmées · 1 Annulée
- Dates dans les 4 prochains jours (J+1 à J+4)
- Messages variés (un vide, un court, un avec allergie, un avec occasion)
- Prénoms réalistes (pas "Jean Dupont", pas "Test")

---

## VARIABLES À SUBSTITUER DANS LE PROMPT_CASCADE

```
{{NOM_ETABLISSEMENT}}   → libellé dans les confirmations et titres
{{CAPACITE_DEJEUNER}}   → nombre de couverts max le midi (ex: 20)
{{CAPACITE_DINER}}      → nombre de couverts max le soir (ex: 25)
{{EMAILJS_ACTIVE}}      → true / false
{{EMAILJS_PUBLIC_KEY}}  → si EmailJS activé
{{EMAILJS_SERVICE_ID}}  → si EmailJS activé
{{EMAILJS_TPL_CLIENT}}  → si EmailJS activé
```

---

## CHECKLIST QA SPÉCIFIQUE

- [ ] Radio "Service" : 2 cartes stylisées, pas de radio HTML brut visible
- [ ] Stepper couverts : boutons − et +, pas d'input number visible
- [ ] Date minimum = aujourd'hui (calculé dynamiquement au chargement)
- [ ] Confirmation inline 4s — aucun `alert()`
- [ ] 5 données démo pré-chargées au premier accès admin
- [ ] Statuts 2/2/1 respectés dans les démo data
- [ ] Calendrier semaine affiché par défaut, jour sélectionné = aujourd'hui
- [ ] Boutons Confirmer/Annuler désactivés quand déjà dans cet état
- [ ] Si EmailJS actif : email envoyé une seule fois par confirmation

---

*Créé le 2026-04-15 — Outil Réservations V1 — Restauration*
