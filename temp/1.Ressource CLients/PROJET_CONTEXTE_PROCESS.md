# PROJET_CONTEXTE — PROCESS URL→DEMO — L'ATELIER CONNECTÉ

> Source de vérité absolue du process de production de démos.
> Lire EN ENTIER avant toute action sur les ressources.
> Toute décision qui contredit ce fichier est interdite.
> Si une demande sort de ce cadre : poser UNE question avant d'agir.

---

## 1. IDENTITÉ

| Champ | Valeur |
|---|---|
| Nom | Process URL→Demo — L'Atelier Connecté |
| Type | Workflow IA (non-code) |
| Objectif | Produire une démo client personnalisée et demo-ready à partir d'une URL, prête à envoyer sans retouche au premier passage Cascade |
| Catégorie active | Restauration (V1 complète) |
| Catégories prévues | Commerce · Praticien libéral · Association · Artisan |
| Statut | En développement — restauration en cours de finalisation |
| Dernière mise à jour | 2026-04-15 |

---

## 2. OUTILS DU PROCESS

| Outil | Rôle dans le process |
|---|---|
| Claude (ce projet) | Analyse prospect, proposition d'impact, production du PROMPT_CASCADE, vérification post-Cascade, mail final |
| Cascade (Windsurf) | Construction du code HTML/CSS/JS à partir du PROMPT_CASCADE |
| GitHub Pages | Déploiement et génération du lien public à envoyer |
| EmailJS | Confirmation emails client (restauration uniquement, si activé) |
| localStorage | Simulation base de données pour la démo |

---

## 3. ARCHITECTURE DOCUMENTAIRE

> Cette structure ne change pas sans validation écrite dans ce fichier.

```
1.Ressource CLients/
├── PROJET_CONTEXTE_PROCESS.md      ← ce fichier — source de vérité du process
├── PROJET_CONTEXTE_DEMO.md         ← boilerplate copié dans chaque dossier client
├── PROMPT_LANCEMENT.md             ← seul point d'entrée du process (1 prospect = 1 utilisation)
├── FICHE_CLIENT_TEMPLATE.md        ← template de fiche client
├── STACK_STANDARD.md               ← règles techniques + charte visuelle
├── CADRAGE_STRATEGIQUE.md          ← identité L'Atelier Connecté, tarifs, douleurs cibles
├── CATEGORIES_CLIENT.md            ← specs UX par catégorie de prospect
├── EMAILS_TEMPLATES.md             ← 5 templates de messages (A→E)
└── BASE/
    ├── PROCESS_AMORCAGE_CLIENT.md      ← phases 1→7 du process détaillées
    ├── INSTRUCTIONS_PROJET.md          ← instructions Claude pour chaque étape
    ├── ADMIN_TEMPLATE_RESTAURATION.md  ← template HTML/JS admin pour Cascade
    ├── TOOL_RESERVATIONS_SPEC.md       ← spec UX outil réservations (obligatoire)
    ├── TOOL_MENU_ARDOISE_SPEC.md       ← spec UX outil menu + ardoise du jour (obligatoire)
    ├── TOOL_EVENEMENTS_SPEC.md         ← spec UX outil événements (optionnel)
    ├── TOOL_AVIS_SPEC.md               ← spec UX outil avis clients (optionnel)
    └── TOOL_EMPORTER_SPEC.md           ← spec UX outil vente à emporter (optionnel)

[nom-client]/                           ← dossier par démo client
├── PROJET_CONTEXTE_DEMO.md         ← copié depuis ressources
├── STACK_STANDARD.md               ← copié depuis ressources
├── PROMPT_CASCADE_[NOM].md         ← produit par Claude, consommé par Cascade
├── FICHE_CLIENT.md                 ← produit par Claude à l'analyse
├── index.html                      ← construit par Cascade
├── admin.html                      ← construit par Cascade
├── styles.css                      ← construit par Cascade
├── script.js                       ← construit par Cascade
├── admin.js                        ← construit par Cascade
└── assets/                         ← images réelles extraites du site original
```

---

## 4. CAPACITÉS DU PROCESS

**✅ Stables — catégorie Restauration**
- Phase 1 : Qualification prospect (signaux + seuils)
- Phase 2 : Analyse site via web_fetch (hex, polices, textes, images, outils existants)
- Phase 3 : Proposition d'impact (douleur + outil + bénéfices)
- Phase 4 : Production PROMPT_CASCADE (Cascade construit le code)
- Phase 5 : Déploiement GitHub Pages
- Phase 6 : Vérification fidélité (comparaison + correction si besoin)
- Phase 7 : Mail premier contact (Template C) + relance (D) + proposition (E)
- Outils disponibles : Réservations, Menu & Ardoise, Événements, Avis, Emporter

**🚧 En cours**
- Finalisation des TOOL_*_SPEC.md (specs UX complètes + données démo type)
- Intégration des 4 outils optionnels dans ADMIN_TEMPLATE_RESTAURATION.md

**❌ Bugs connus**
- Bouton admin parfois placé en haut à gauche au lieu du haut à droite (corrigé dans STACK_STANDARD.md + checklist Phase 6)

**🔒 Hors scope**
- Backend, base de données réelle, paiement en ligne
- Développement des 4 autres catégories (Commerce, Praticien, Association, Artisan) — placeholders uniquement
- Personnalisation du process par client (le process est générique, seules les données changent)

---

## 5. RÈGLES SPÉCIFIQUES AU PROCESS

- **Spec avant transposition** : les TOOL_*_SPEC.md définissent le standard UX. Cascade applique, ne réinvente pas.
- **Démo avant contact** : la démo est construite et déployée AVANT l'envoi du premier mail. Jamais l'inverse.
- **Un seul passage Cascade** : la démo doit être demo-ready au premier passage. Si une V2 est nécessaire, c'est un bug de spec.
- **Charte visuelle toujours respectée** : Cascade applique les couleurs et polices du client selon les règles de STACK_STANDARD.md — il ne choisit pas.
- **Tout dans une seule conversation** : toute la production d'une démo (analyse → mail) se fait dans une seule conversation Claude. Pas de double flux.
- **Outils obligatoires Restauration** : Réservations + Menu & Ardoise — toujours présents.
- **Outils optionnels Restauration** : Événements, Avis, Emporter — activés sur signal observé.

---

## 6. DÉCISIONS FIGÉES

| Date | Décision | Raison |
|---|---|---|
| 2026-04-15 | 4 types d'outils restauration : Réservations, Menu & Ardoise, Événements, Avis, Emporter | Couvre les douleurs quotidiennes réelles d'un restaurateur |
| 2026-04-15 | Ardoise du jour fusionnée avec Carte des menus (onglet "Menu & Ardoise") | Évite la redondance dans l'admin, un seul endroit pour tout ce qui est contenu |
| 2026-04-15 | localStorage uniquement — zéro backend | Site statique déployable sur GitHub Pages, démo rapide sans infrastructure |
| 2026-04-15 | PROJET_CONTEXTE.md renommé PROJET_CONTEXTE_DEMO.md | Distinguer le boilerplate client de la source de vérité du process |
| 2026-04-14 | Démo avant 1er contact | On montre une preuve, on ne promet pas |
| 2026-04-14 | Validation proposition avant construction | Évite de construire pour un mauvais prospect |

---

## 7. FICHIERS AUTORISÉS

**Dans `1.Ressource CLients/` :**

| Fichier | Statut |
|---|---|
| PROJET_CONTEXTE_PROCESS.md | ✅ Obligatoire |
| PROJET_CONTEXTE_DEMO.md | ✅ Boilerplate client |
| PROMPT_LANCEMENT.md | ✅ |
| FICHE_CLIENT_TEMPLATE.md | ✅ |
| STACK_STANDARD.md | ✅ |
| CADRAGE_STRATEGIQUE.md | ✅ |
| CATEGORIES_CLIENT.md | ✅ |
| EMAILS_TEMPLATES.md | ✅ |

**Dans `BASE/` :**

| Fichier | Statut |
|---|---|
| PROCESS_AMORCAGE_CLIENT.md | ✅ |
| INSTRUCTIONS_PROJET.md | ✅ |
| ADMIN_TEMPLATE_RESTAURATION.md | ✅ |
| TOOL_RESERVATIONS_SPEC.md | ✅ |
| TOOL_MENU_ARDOISE_SPEC.md | ✅ |
| TOOL_EVENEMENTS_SPEC.md | ✅ |
| TOOL_AVIS_SPEC.md | ✅ |
| TOOL_EMPORTER_SPEC.md | ✅ |

Tout autre fichier dans ces dossiers → `_archives/`.

---

## 8. SESSION EN COURS

**Objectif de la session :** Finalisation complète des ressources restauration — création TOOL_SPEC, CADRAGE_STRATEGIQUE, CATEGORIES_CLIENT, EMAILS_TEMPLATES + mise à jour des fichiers existants.

**Fichiers concernés :** Tous les fichiers listés en section 7.

**Hors scope cette session :** Développement des 4 autres catégories, code des démos existantes.

**Résultat fin de session :** Process url→demo complet, cohérent, prêt pour le premier usage sur catégorie restauration sans retouche.

---

## 9. BACKLOG

> Ordonné par priorité. Ne jamais commencer le suivant sans que le précédent soit terminé et testé.

1. ✅ Finaliser ressources restauration (session courante)
2. Tester le process complet sur Pointe de Rêve (url → démo → vérification)
3. Documenter les retours du premier test terrain (Tourbillon / Pointe de Rêve)
4. Développer catégorie Commerce (adapter outils : catalogue, commande, stock)
5. Développer catégorie Praticien libéral (adapter outils : RDV, agenda, prestations)
6. Développer catégorie Association (adapter outils : adhésions, événements, bénévoles)
7. Développer catégorie Artisan (adapter outils : devis, galerie, contact projet)

---

*Créé le 2026-04-15 — Process L'Atelier Connecté V2*
