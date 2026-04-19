---
# DEMO_TEMPLATE — L'Atelier Connecté
> Dossier de référence contenant les 5 fichiers génériques de toute démo client restauration.
> Source de vérité absolue pour la structure, la logique et les conventions.
> NE JAMAIS modifier ces fichiers directement — ils servent de base pour chaque nouveau client.

---

## PRINCIPE

Pour chaque nouveau prospect, Cascade reçoit :
1. La FICHE_EXTRACTION du client (variables remplies par Claude)
2. Ce dossier DEMO_TEMPLATE/ (structure prête à l'emploi)

Sa seule tâche : copier les 5 fichiers dans le dossier client et substituer les {{VARIABLES}}.
Il ne construit pas, il ne réinvente pas — il complète.

---

## LES 5 FICHIERS

| Fichier | Rôle |
|---|---|
| styles.css | Variables CSS + tous les styles — couleurs et polices en {{VARIABLES}} |
| index.html | Site public — données client en {{VARIABLES}} |
| script.js | Logique site public — menu et ardoise démo en {{VARIABLES}} |
| admin.html | Espace gérant — nom et logo en {{VARIABLES}} |
| admin.js | Logique admin — données démo en {{VARIABLES}}, règles figées en dur |

---

## LISTE DES {{VARIABLES}}

### Identité visuelle (styles.css + index.html + admin.html)
- {{BG_MAIN}} — couleur de fond principal (ex: #ffffff)
- {{BG_ALT}} — couleur de fond alterné (ex: #fffaf3)
- {{ACCENT}} — couleur accent : boutons, titres, prix (ex: #53875e)
- {{ACCENT_DARK}} — accent hover, légèrement plus foncé (ex: #467650)
- {{ACCENT_RGB}} — accent en valeurs R,G,B sans # (ex: 83, 135, 94)
- {{TEXT_MAIN}} — texte principal (ex: #444444)
- {{TEXT_SECONDARY}} — texte secondaire (ex: #848484)
- {{CARD_BG}} — fond des cartes (ex: #fffef9)
- {{BORDER_SOFT}} — bordure douce (ex: rgba(83, 135, 94, 0.08))
- {{FONT_TITRES}} — nom Google Font titres (ex: Satisfy)
- {{FONT_CORPS}} — nom Google Font corps (ex: Poppins)
- {{GOOGLE_FONTS_URL}} — URL complète Google Fonts pour le <link>

### Données client (index.html + admin.html)
- {{NOM_ETABLISSEMENT}} — nom exact (ex: Pointe de Rêve)
- {{VILLE}} — ville (ex: Villeurbanne)
- {{URL_LOGO}} — URL directe du logo
- {{URL_HERO}} — URL de l'image hero (placée dans styles.css .hero)
- {{URL_PRESENTATION}} — URL image section présentation
- {{BADGE_HERO}} — pill au-dessus du titre hero (ex: "Cuisine maison · Vue mer")
- {{SOUS_TITRE_HERO}} — accroche sous le nom (ex: Cuisine traditionnelle · Villeurbanne)
- {{TEXTE_PRESENTATION_1}} — premier paragraphe de présentation
- {{TEXTE_PRESENTATION_2}} — deuxième paragraphe
- {{HORAIRES_DEJEUNER}} — ex: 12h00 – 14h30 (affiché dans les cartes service)
- {{HORAIRES_DINER}} — ex: 19h30 – 22h00 (affiché dans les cartes service)
- {{HORAIRES_TEXTE_FOOTER}} — ex: "Mar–Sam midi et soir" (footer + infos pratiques)
- {{ADRESSE}} — adresse complète
- {{TELEPHONE}} — téléphone affiché (ex: 06 12 34 56 78)
- {{TELEPHONE_RAW}} — téléphone pour href tel: (chiffres seuls, ex: 0612345678)
- {{URL_GOOGLE_MAPS}} — lien Google Maps direct

### Avis clients Google (index.html)
- {{NOTE_GOOGLE}} — note globale (ex: "4,7")
- {{NOMBRE_AVIS_GOOGLE}} — nombre d'avis (ex: "142")
- {{AFFICHER_SCORE_GOOGLE}} — "block" si note disponible, "none" sinon
- {{AVIS_1_AUTEUR}}, {{AVIS_1_INITIALE}}, {{AVIS_1_TEXTE}}, {{AVIS_1_DATE}}
- {{AVIS_2_AUTEUR}}, {{AVIS_2_INITIALE}}, {{AVIS_2_TEXTE}}, {{AVIS_2_DATE}}
- {{AVIS_3_AUTEUR}}, {{AVIS_3_INITIALE}}, {{AVIS_3_TEXTE}}, {{AVIS_3_DATE}}

### Données démo (script.js + admin.js)
- {{DEFAULT_MENU_JS}} — objet JS du menu (catégories + plats réels)
- {{DEFAULT_ARDOISE_JS}} — objet JS de l'ardoise démo
- {{DEMO_PRENOM_1}} à {{DEMO_PRENOM_5}} — prénoms cohérents avec le contexte local
- {{DEMO_TEL_1}} à {{DEMO_TEL_5}} — téléphones format français (ex: 06 12 34 56 78)
- {{DEMO_MESSAGE_1}}, {{DEMO_MESSAGE_3}}, {{DEMO_MESSAGE_5}} — messages démo (2 et 4 = vides)

---

## RÈGLES ABSOLUES — JAMAIS NÉGOCIABLES

| Règle | Valeur figée |
|---|---|
| Mot de passe admin | admin2024 — codé en dur dans admin.js, JAMAIS une {{VARIABLE}} |
| Clé localStorage réservations | "actions_recues" — ne jamais utiliser une autre clé |
| Clé localStorage contenu | "contenu_editable" — ne jamais utiliser une autre clé |
| Clé localStorage menu | "menuCard" — ne jamais utiliser une autre clé |
| Champs JS réservation | prenom, telephone, service, couverts, message, statut, source — toujours en français |
| Valeurs service | "dejeuner" ou "diner" (minuscules, sans accent) — jamais autre chose |
| Statuts réservation | "En attente", "Confirmée", "Annulée" — exactement ces chaînes |
| Répartition démo | 2 En attente · 2 Confirmée · 1 Annulée — toujours |
| Titre admin | "Espace Gérant — {{NOM_ETABLISSEMENT}}" — jamais générique seul |
| Polices max | 2 Google Fonts — jamais 3 |
| Alerts | Interdits — toutes les confirmations sont inline avec setTimeout 4s |

---

## UTILISATION POUR UN NOUVEAU CLIENT

1. Claude reçoit le PROMPT_LANCEMENT (URL + observations terrain)
2. Claude fait web_fetch → produit FICHE_EXTRACTION_[NOM].md (toutes variables résolues)
3. [VALIDATION] — confirmer avant de continuer
4. Claude produit PROMPT_CASCADE_[NOM].md (court : FICHE + instructions de substitution)
5. Cascade : copie DEMO_TEMPLATE/ dans le dossier client → substitue les {{VARIABLES}}
6. [VÉRIFICATION] comparaison visuelle → corrections si besoin
7. Déploiement GitHub Pages → mail Template C

---

*Créé le 2026-04-19 — Version 2 — L'Atelier Connecté*
