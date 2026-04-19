# PROCESS AMORÇAGE CLIENT — L'ATELIER CONNECTÉ
> Document de cadrage complet. À placer dans les ressources du projet.
> Décrit chaque phase, ses entrées, sorties, règles et décisions figées.
> Version 2 — 2026-04-14

---

## PRINCIPE FONDATEUR

**On montre une preuve avant de demander quoi que ce soit.**
La démo est construite avant le premier contact. Toujours.
Le prospect reçoit un lien fonctionnel qui ressemble à son univers et résout sa douleur visible.

---

## VUE D'ENSEMBLE DU FLOW

```
PROMPT LANCEMENT          CE PROJET (analyse + proposition)
        ↓                           ↓
  URL + observations    →   Analyse site (web_fetch)
                             Croisement stratégie
                             Évaluation prospect
                             Fiche client
                             Proposition d'impact
                                    ↓
                             VALIDATION UTILISATEUR
                                    ↓
                           PROMPT CASCADE produit
                                    ↓
                    DOSSIER CLIENT (CLAUDE.md + PROJET_CONTEXTE.md fourni par Claude + PROMPT_CASCADE)
                                    ↓
                              CASCADE CONSTRUIT
                                    ↓
                             DÉPLOIEMENT GITHUB
                                    ↓
                    [VÉRIFICATION] → Comparaison → Correction si besoin
                                    ↓
                         [DÉMO PRÊTE] → MAIL FINAL
```

---

## PHASE 1 — QUALIFICATION

### Critères de qualification

| Signal observé | Poids |
|---|---|
| Réservations / commandes gérées manuellement (tél, papier) | ★★★ Fort |
| Contenu qui change souvent sans outil dédié | ★★★ Fort |
| Présence Instagram active mais aucun outil de conversion | ★★ Moyen |
| Site existant mais daté, incomplet ou peu visité | ★★ Moyen |
| Pas de présence numérique du tout | ★ Faible (cycle long) |

**Seuil de lancement :** 2 signaux ★★ minimum ou 1 signal ★★★

### Signaux d'abandon (ne pas lancer de démo)
- Site récent et fonctionnel → pas de douleur visible
- Aucun signal numérique + cible peu mature → cycle trop long
- Activité trop niche ou trop informelle → valeur perçue faible

**Règle :** Si le prospect ne passe pas le seuil, le dire clairement plutôt que construire pour rien.

---

## PHASE 2 — ANALYSE (dans ce projet, via web_fetch)

### Ce qu'on extrait du site

**Identité visuelle :**
- Couleurs hex de chaque élément (fond, texte, accent, boutons)
- Typographies : noms exacts (Google Fonts si identifiable)
- Logo : URL directe

**Textes réels (mot pour mot) :**
- Slogan ou accroche principale
- Présentation / histoire
- Noms des gérants
- Adresse complète
- Horaires jour par jour

**Contenu métier :**
- Menu / catalogue / programme / prestations avec vrais noms et prix

**Images :**
- URLs directes de 4 à 6 images utilisables (hero, équipe, ambiance, logo)

**Outils existants :**
- Outil de réservation, prise de commande, paiement en ligne, newsletter

### Ce qu'on évalue

- Douleur principale parmi les 7 douleurs cibles (CADRAGE_STRATEGIQUE.md)
- Écart entre fonctionnement actuel et ce qui pourrait être simplifié
- Impact immédiat réaliste à apporter

---

## PHASE 3 — PROPOSITION D'IMPACT (validée avant de construire)

### Format de la proposition

```
PROSPECT : [NOM] — [CATÉGORIE]
SCORE : ★★★ Chaud / ★★ Tiède / ★ Froid

DOULEUR PRINCIPALE : [formulée en conséquence métier — jamais en manque technique]
OUTIL PROPOSÉ : [description courte, en langage métier]
CE QUE LE PROSPECT VERRA EN 10 SECONDES : [promesse visible dès l'ouverture]
BÉNÉFICES DÉMONTRÉS DANS LA DÉMO :
  - [BÉNÉFICE 1]
  - [BÉNÉFICE 2]
  - [BÉNÉFICE 3]

SIGNAL D'ALERTE : [si présent — raison précise]
```

La proposition est soumise à validation. On ne construit rien avant retour.

---

## PHASE 4 — CRÉATION DE LA DÉMO (Cascade)

### Dossier de départ — étapes manuelles obligatoires

**Étape manuelle (avant d'ouvrir Windsurf) :**
1. Créer un dossier vide `[nom-client]/`
2. Copier le contenu de `1.Ressource_Clients/` dans ce dossier (templates de référence)
3. Y ajouter les 3 fichiers livrés par Claude : `CLAUDE.md` + `PROJET_CONTEXTE.md` + `PROMPT_CASCADE_[NOM].md`
4. Ouvrir Windsurf dans ce dossier → nouvelle session Cascade
5. Coller `PROMPT_CASCADE_[NOM].md` dans Cascade

Le dossier client doit contenir au minimum :
```
[nom-client]/
├── 1.Ressource_Clients/     ← copie des templates génériques (référence, lecture seule)
├── CLAUDE.md                ← généré depuis BASE/CLAUDE_MD_TEMPLATE.md (variables remplacées)
├── PROJET_CONTEXTE.md       ← fourni par Claude — Cascade ne le crée pas
└── PROMPT_CASCADE_[NOM].md  ← généré depuis BASE/PROMPT_CASCADE_RESTAURATION_TEMPLATE.md
```

**CLAUDE.md** : lu en premier par Cascade (Windsurf). Contient les règles absolues (anti-graphify, clés localStorage, ordre de construction). Généré en remplaçant `{{NOM_ETABLISSEMENT}}` et `{{NOM_SLUG}}` dans le template.

**PROJET_CONTEXTE.md** : fourni par Claude dans le dossier client. Cascade ne le crée pas. Si ce fichier est absent, Cascade doit s'arrêter et signaler : `[ERREUR] PROJET_CONTEXTE.md manquant — contacter Claude`.

**PROMPT_CASCADE_[NOM].md** : spec complète et auto-suffisante. Contient tout ce que Cascade a besoin de savoir — données client, structure HTML, HTML/CSS/JS des UX critiques, données démo, checklist. Généré en remplissant toutes les `{{VARIABLES}}` du template (aucune ne doit rester vide).

Cascade construit ensuite les 5 fichiers :
```
[nom-client]/
├── styles.css
├── index.html
├── script.js
├── admin.html
└── admin.js
```

### Règles de construction (embarquées dans PROMPT_CASCADE)

**Ordre de construction obligatoire (4 phases avec gate de confirmation) :**
1. `styles.css` — variables CSS + styles partagés → "Phase 1 terminée"
2. `index.html` + `script.js` — site public → "Phase 2 terminée"
3. `admin.html` — espace gérant (HTML) → "Phase 3 terminée"
4. `admin.js` — logique et données démo → "Phase 4 terminée"

**index.html — structure obligatoire (ordre exact) :**
1. `<header>` sticky — logo + nav + **bouton admin en haut à droite**
2. Hero (min 90vh) — image réelle + overlay opacité ≥ 0.40 + H1 + sous-titre + 2 CTA
3. Section Présentation — textes réels + photo équipe/ambiance
4. Section Notre carte — onglets, données depuis `menuCard` localStorage
5. Section Ardoise du jour — fond accent 8%, masquée si `disponible = false`
6. Section Réservation — cartes cliquables service + stepper couverts
7. Section Vente à emporter
8. Section Galerie
9. Footer — copyright + **AUCUN lien admin ici**

**Bouton admin :** Dans le `<header>` de index.html, **en haut à droite**. Ajouter aussi un lien discret `Espace gérant` dans le `<footer>`.

**Formulaire réservation — UX non-négociable :**
- Service : 2 cartes cliquables stylisées — jamais `<select>`, jamais radio brut visible
- Couverts : stepper boutons − et + — jamais `<input type="number">` visible
- Confirmation : inline 4s — jamais `alert()`

**admin.html — structure obligatoire :**
1. Écran de login (logo + input password + bouton) — visible au premier chargement
2. Dashboard hidden jusqu'au login réussi
3. 3 KPI (aujourd'hui / en attente / confirmées)
4. 2 onglets : Réservations (calendrier semaine + cartes) + Menu & Ardoise (ardoise complète + éditeur carte)
5. Mot de passe : `admin2024` (code en dur — pas de vrai backend)

**Données de démo :**
- 5 entrées codées en dur dans `admin.js` (DEMO_RESERVATIONS constant)
- Pas dans localStorage — injectées dynamiquement via `getReservations()`
- Statuts : 2 En attente · 2 Confirmées · 1 Annulée
- Données réalistes (vrais prénoms, messages variés dont allergies)

**Mécanique localStorage (clés exactes) :**
```
"actions_recues"     ← index écrit (réservations utilisateur), admin lit
"contenu_editable"   ← admin écrit (ardoise), index lit au rechargement
"menuCard"           ← admin écrit (carte des menus), index lit au rechargement
```

### Checklist QA (vérifier avant de déployer)

**Structure et navigation :**
- [ ] Hero visible sans scroll sur desktop 1280px — min-height 90vh — image réelle + overlay
- [ ] Bouton admin visible en haut à **droite** de la nav
- [ ] Lien discret « Espace gérant » présent dans le footer → `admin.html`
- [ ] Sections alternées bg-main / bg-alt (pas 2 adjacentes identiques)
- [ ] Favicon présent

**Formulaire réservation :**
- [ ] Service : 2 cartes cliquables stylisées (pas `<select>`, pas radio brut visible)
- [ ] Couverts : stepper boutons − et + (pas `<input type="number">` visible)
- [ ] Formulaire → confirmation inline 4s → aucun `alert()`
- [ ] Réservation soumise visible dans admin (clé `actions_recues`)

**Admin :**
- [ ] Login screen visible au premier chargement de admin.html
- [ ] Login fonctionne avec le mot de passe `admin2024`
- [ ] 5 données démo présentes sans avoir rien soumis (2 En attente, 2 Confirmées, 1 Annulée)
- [ ] Calendrier 7 jours affiché
- [ ] Filtres Déjeuner / Dîner / Tous fonctionnels
- [ ] Boutons Confirmer / Annuler → badge mis à jour sans rechargement
- [ ] Ardoise admin → mise à jour → visible sur index au rechargement
- [ ] Éditeur carte admin → sauvegarde → visible sur index au rechargement

**Contenu :**
- [ ] Aucun texte Lorem ipsum, placeholder ou générique visible
- [ ] Tous les textes sont réels (adresse, horaires, noms, menu)
- [ ] Aucun `alert()` dans le code

**Mobile :**
- [ ] Lisible et utilisable sur 390px (iPhone 12 / SE)

---

## PHASE 5 — DÉPLOIEMENT GITHUB PAGES

### Convention de nommage

```
Compte  : atelier-connecte
Repo    : [nom-client-minuscules-sans-espaces]
URL     : https://atelier-connecte.github.io/[nom-client]/
```

### Commandes

```bash
git init
git add .
git commit -m "Demo [Nom du Client]"
git branch -M main
git remote add origin [URL repo GitHub]
git push -u origin main
# Settings → Pages → main → /root → Save
```

---

## PHASE 6 — VÉRIFICATION DE FIDÉLITÉ (dans ce projet)

Revenir dans la même conversation avec les fichiers démo.
Claude recharge le site original (`web_fetch`) et compare :

| Point de contrôle | Attendu |
|---|---|
| Couleurs hex | Identiques au site original |
| Typographies | Mêmes polices exactes |
| Textes | 100% réels, aucun inventé |
| Images | URLs qui chargent effectivement |
| Impact visuel | Note /10 — compréhensible en 10s par un non-technicien |

Si corrections nécessaires → prompt de correction Cascade produit.
Si validé → passage direct au mail.

---

## PHASE 7 — PREMIER CONTACT

### Séquence de communication

```
J0   → Mail 1er contact avec démo (Template C de EMAILS_TEMPLATES.md)
J+7  → Relance canal secondaire (Template D) si pas de réponse
J+14 → Clore le prospect si toujours rien

Réponse reçue → Template E (proposition commerciale) — jamais avant
```

### Anatomie du mail qui fonctionne

1. Ancrage local — "Je suis passé devant..." (preuve que c'est personnel)
2. Observation factuelle sans juger — nommer la douleur sans critiquer
3. La démo — lien en évidence (preuve avant demande)
4. 3 à 4 bénéfices métier en liste courte
5. CTA léger — "20 min autour d'un café"
6. Signature complète

---

## DÉCISIONS FIGÉES

| Décision | Raison |
|---|---|
| Démo AVANT le 1er contact | On montre, on ne promet pas |
| Validation de la proposition avant de construire | Évite de construire pour un mauvais prospect |
| Tout dans une seule conversation | Cohérence, contexte conservé, pas de double flux |
| web_fetch ici (pas Claude internet externe) | Claude ce projet a les outils, inutile de multiplier |
| **CLAUDE.md obligatoire dans chaque dossier client** | Sans lui, Cascade lance graphify et ignore les règles |
| **PROMPT_CASCADE avec 4 phases et gates de confirmation** | Cascade codait tout en un bloc — phases = contrôle, admin.html ne peut plus être sauté |
| **PROMPT_CASCADE embarque le HTML/JS des UX critiques** | Cascade inventait radio/stepper à chaque fois |
| Bouton admin en haut à droite de l'index + lien discret « Espace gérant » en footer | Bouton header = visible dès l'arrivée ; lien footer = discret pour le gérant |
| 5 données démo codées en dur dans admin.js | Admin vide = démo sans valeur démonstrative |
| Données démo via DEMO_RESERVATIONS constant (pas localStorage) | localStorage vide au premier chargement = pas de démo |
| Clés localStorage : `actions_recues` + `contenu_editable` | Standard unique évite les bugs inter-fichiers |
| Raffinement visuel systématique | Sans ça le prospect ne se reconnaît pas |
| Offre jamais en 1er contact | Règle CADRAGE_STRATEGIQUE — toujours respectée |

---

*Version 4 — 2026-04-15 — CLAUDE.md obligatoire + phases Cascade + templates embarqués*
