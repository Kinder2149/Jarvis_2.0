# PROMPT DE LANCEMENT — L'ATELIER CONNECTÉ
> Le seul geste de départ. À copier-coller dans ce projet Claude, variables remplies.
> Tout se déroule ensuite dans la même conversation.

---

## LE PROMPT (copier-coller ici dans ce projet, remplir les [VARIABLES])

```
[NOUVEAU PROSPECT]

URL du site : [URL_DU_SITE ou "aucun site"]

Catégorie : [Restaurateur / Commerce / Praticien libéral / Association / Artisan]

Ce que j'ai observé sur le terrain :
[2-4 lignes concrètes sur leur fonctionnement réel.
Pas "beau lieu". Exemple :
- Réservations uniquement par téléphone, coupé le soir
- Carte changée toutes les 2 semaines, mise à jour manuelle
- Instagram actif mais aucun lien vers un formulaire]

Informations connues :
- Nom de la structure : [NOM EXACT]
- Gérant(s) : [PRÉNOMS ou "inconnus"]
- Adresse : [ADRESSE ou "à confirmer"]
- Email : [EMAIL ou "inconnu"]
- Téléphone : [TEL ou "inconnu"]
- Instagram : [URL ou "aucun"]
- Canal de contact prévu : [Email / Instagram / Terrain]

Outils à inclure dans la démo :
- [x] Réservations (toujours pour restauration)
- [x] Menu & Ardoise (toujours pour restauration)
- [ ] Événements (cocher si : soirées thématiques, privatisations, repas événementiels observés)
- [ ] Avis clients (cocher si : peu d'avis Google, avis positifs non valorisés sur le site)
- [ ] Vente à emporter (cocher si : mention "à emporter", traiteur, plats du jour à récupérer)
```

---

## CE QUE CLAUDE FAIT EN RÉPONSE

**Phase 1 — Analyse et proposition (Claude répond à ce message)**

Claude utilise `web_fetch` sur l'URL fournie et extrait :
- Palette hex complète
- Typographies réelles
- Textes réels (slogan, histoire, noms, horaires)
- URLs d'images exploitables
- Outils existants et fonctionnement numérique actuel

Puis croise avec `CADRAGE_STRATEGIQUE.md` et `CATEGORIES_CLIENT.md` pour produire :

**→ FICHE CLIENT** (contenu prêt pour le dossier ressources)
**→ ANALYSE D'IMPACT** : douleur principale identifiée + outil proposé + pourquoi
**→ SIGNAL D'ALERTE** si le prospect n'est pas assez qualifié (douleur trop faible, pas de signal numérique, cycle trop long) — Claude le dit franchement avant de continuer

La réponse se termine par :
> "Est-ce que cette analyse et cet impact te semblent pertinents ? Je peux ajuster avant de produire le prompt Cascade."

---

## CE QUE TU FAIS APRÈS LA RÉPONSE

**Si la proposition est validée :**
Répondre simplement : `[VALIDE]` ou `[VALIDE — ajuste : ...]`

**Si le prospect est écarté :**
Répondre : `[ABANDON — raison]`

→ Claude produit alors le fichier `PROMPT_CASCADE_[NOM].md`

---

## APRÈS AVOIR REÇU LES 3 FICHIERS

Claude produit 3 fichiers : `CLAUDE.md` + `PROJET_CONTEXTE.md` + `PROMPT_CASCADE_[NOM].md`

**Étape manuelle :**
1. Créer un dossier vide `[nom-client]/`
2. Copier le contenu de `1.Ressource_Clients/` dans ce dossier (templates de référence)
3. Y ajouter les 3 fichiers livrés par Claude : `CLAUDE.md` + `PROJET_CONTEXTE.md` + `PROMPT_CASCADE_[NOM].md`
4. Ouvrir Windsurf dans ce dossier → nouvelle session Cascade
5. Coller `PROMPT_CASCADE_[NOM].md` dans Cascade

Cascade construit la démo (4 phases, confirme chaque étape), puis déployer sur GitHub Pages.

---

## RETOUR APRÈS DÉPLOIEMENT

Revenir dans **cette même conversation** avec :

```
[VÉRIFICATION]

Client : [NOM]
URL démo : https://atelier-connecte.github.io/[nom-repo]/
Fichiers joints : index.html + admin.html + styles.css
```

Claude compare avec le site original, valide la fidélité visuelle, et produit si besoin un prompt de correction Cascade.

---

## RETOUR FINAL POUR LE MAIL

Une fois la démo validée et corrigée, dans la même conversation :

```
[DÉMO PRÊTE]

Client : [NOM]
URL finale : https://atelier-connecte.github.io/[nom-repo]/
```

Claude produit le mail final prêt à copier dans Gmail.

---

*Mis à jour le : 2026-04-15 — Ajout sélection outils*
