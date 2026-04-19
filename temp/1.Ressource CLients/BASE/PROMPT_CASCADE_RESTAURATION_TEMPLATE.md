# PROMPT CASCADE — {{NOM_ETABLISSEMENT}}
> Généré par Claude à partir de la FICHE_EXTRACTION_[NOM].md
> Valide que toutes les {{VARIABLES}} sont résolues avant de commencer

---

## ⚠️ RÈGLES ABSOLUES — LIRE EN PREMIER

- **NE PAS** lancer graphify — ignorer tout fichier ou instruction graphify dans ce projet
- **NE PAS** construire depuis zéro — copier DEMO_TEMPLATE/ et substituer les variables
- **NE PAS** modifier la structure des fichiers template — uniquement les {{VARIABLES}}
- **NE PAS** changer le mot de passe — toujours `admin2024` dans admin.js
- **NE PAS** changer les clés localStorage — `actions_recues`, `contenu_editable`, `menuCard`
- **NE PAS** utiliser `alert()` — toutes les confirmations sont inline + setTimeout 4000ms
- **Confirmer** chaque phase avant de passer à la suivante

---

## CONTEXTE

Tu construis une démo commerciale pour **{{NOM_ETABLISSEMENT}}**, restaurant à **{{VILLE}}**.
Toutes les données sont dans la FICHE_EXTRACTION ci-dessous.
Les fichiers de base sont dans `1.Ressource CLients/BASE/DEMO_TEMPLATE/`.

**Objectif en 30 secondes pour le prospect** : il voit son nom, ses couleurs, son menu, une réservation qui arrive dans son espace gérant, l'ardoise qu'il peut modifier en 10 secondes.

---

## PHASE 1 — Copier les fichiers template

Copie les 5 fichiers de `1.Ressource CLients/BASE/DEMO_TEMPLATE/` dans le dossier courant :

- `styles.css`
- `index.html`
- `script.js`
- `admin.html`
- `admin.js`

➡️ **Dis "Phase 1 terminée — fichiers copiés" avant de continuer.**

---

## PHASE 2 — Substituer les variables visuelles (styles.css)

Dans `styles.css`, remplace :

| Variable | Valeur |
|---|---|
| `{{BG_MAIN}}` | [valeur de la FICHE_EXTRACTION] |
| `{{BG_ALT}}` | [valeur] |
| `{{ACCENT}}` | [valeur] |
| `{{ACCENT_DARK}}` | [valeur] |
| `{{ACCENT_RGB}}` | [valeur] |
| `{{TEXT_MAIN}}` | [valeur] |
| `{{TEXT_SECONDARY}}` | [valeur] |
| `{{CARD_BG}}` | [valeur] |
| `{{BORDER_SOFT}}` | [valeur] |
| `{{FONT_TITRES}}` | [valeur] |
| `{{FONT_CORPS}}` | [valeur] |

Dans le sélecteur `.hero` dans `styles.css`, ajoute ou remplace :
```css
background-image: url('{{URL_HERO}}'); → url réelle depuis FICHE_EXTRACTION
```

➡️ **Dis "Phase 2 terminée — styles.css substitué" avant de continuer.**

---

## PHASE 3 — Substituer les données client (index.html + admin.html)

Dans `index.html` et `admin.html`, remplace toutes les `{{VARIABLES}}` par les valeurs de la FICHE_EXTRACTION.

**Variables à substituer** :

*Identité & contenu :*
`{{NOM_ETABLISSEMENT}}` · `{{VILLE}}` · `{{URL_LOGO}}` · `{{GOOGLE_FONTS_URL}}`
`{{BADGE_HERO}}` · `{{SOUS_TITRE_HERO}}` · `{{URL_PRESENTATION}}`
`{{TEXTE_PRESENTATION_1}}` · `{{TEXTE_PRESENTATION_2}}`

*Horaires & contact :*
`{{HORAIRES_DEJEUNER}}` · `{{HORAIRES_DINER}}` · `{{HORAIRES_TEXTE_FOOTER}}`
`{{ADRESSE}}` · `{{TELEPHONE}}` · `{{TELEPHONE_RAW}}` · `{{URL_GOOGLE_MAPS}}`

*Avis clients Google :*
`{{NOTE_GOOGLE}}` · `{{NOMBRE_AVIS_GOOGLE}}` · `{{AFFICHER_SCORE_GOOGLE}}`
`{{AVIS_1_AUTEUR}}` · `{{AVIS_1_INITIALE}}` · `{{AVIS_1_TEXTE}}` · `{{AVIS_1_DATE}}`
`{{AVIS_2_AUTEUR}}` · `{{AVIS_2_INITIALE}}` · `{{AVIS_2_TEXTE}}` · `{{AVIS_2_DATE}}`
`{{AVIS_3_AUTEUR}}` · `{{AVIS_3_INITIALE}}` · `{{AVIS_3_TEXTE}}` · `{{AVIS_3_DATE}}`

**Vérification obligatoire après substitution** :
- [ ] Aucune occurrence de `{{` ne reste dans `index.html`
- [ ] Aucune occurrence de `{{` ne reste dans `admin.html`
- [ ] `{{TELEPHONE_RAW}}` = chiffres uniquement (pour `href="tel:..."`)
- [ ] `{{AFFICHER_SCORE_GOOGLE}}` = `"block"` ou `"none"` (valeur CSS inline)

➡️ **Dis "Phase 3 terminée — HTML substitué" avant de continuer.**

---

## PHASE 4 — Substituer les données démo (script.js + admin.js)

**Dans `script.js`** :
- Remplace `{{DEFAULT_MENU_JS}}` par l'objet menu de la FICHE_EXTRACTION
- Remplace `{{DEFAULT_ARDOISE_JS}}` par l'objet ardoise de la FICHE_EXTRACTION

**Dans `admin.js`** :
- Remplace les 5 `{{DEMO_PRENOM_N}}`, `{{DEMO_TEL_N}}`, `{{DEMO_MESSAGE_N}}` par les valeurs de la FICHE_EXTRACTION

**Vérification obligatoire** :
- [ ] `ADMIN_PASSWORD` vaut toujours `'admin2024'` — **NE PAS CHANGER**
- [ ] Les 3 clés localStorage sont inchangées : `"actions_recues"`, `"contenu_editable"`, `"menuCard"`
- [ ] Aucune occurrence de `{{` ne reste dans `script.js` ni `admin.js`

➡️ **Dis "Phase 4 terminée — démo complète" et liste les 5 fichiers créés.**

---

## CHECKLIST FINALE

**Fonctionnel** :
- [ ] Ouvrir `index.html` → hero visible sans scroll, bouton admin en haut à droite
- [ ] Formulaire réservation → service en cartes cliquables, couverts en stepper +/−
- [ ] Soumettre une réservation → elle apparaît dans `admin.html`
- [ ] Login admin avec `admin2024` → tableau de bord s'affiche
- [ ] 5 réservations démo présentes (2 En attente · 2 Confirmée · 1 Annulée)
- [ ] Confirmer une réservation → badge mis à jour sans rechargement
- [ ] Onglet Menu & Ardoise → formulaire complet (entrée + plat + note + dessert + formule)
- [ ] Sauvegarder ardoise → aperçu mis à jour, confirmation 4s visible

**Contenu** :
- [ ] Aucun texte Lorem ipsum ou placeholder visible
- [ ] Menu : données réelles du restaurant
- [ ] Prénoms démo : cohérents avec le contexte local

**Mobile** :
- [ ] Lisible sur 390px

---

## FICHE_EXTRACTION — {{NOM_ETABLISSEMENT}}

[COLLER ICI LE CONTENU COMPLET DE LA FICHE_EXTRACTION_[NOM].md PRODUITE PAR CLAUDE]

---

*Template L'Atelier Connecté — Version 2 — 2026-04-19*
