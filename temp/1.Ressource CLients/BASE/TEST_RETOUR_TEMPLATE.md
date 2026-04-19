# RAPPORT TEST — [NOM_ETABLISSEMENT]
> À remplir après chaque build Cascade, avant l'envoi client.
> Statuts : ✅ OK · ⚠️ Dégradé (acceptable) · ❌ Bloquant (à corriger avant envoi)

---

## MÉTADONNÉES

| Champ | Valeur |
|---|---|
| Client | |
| URL déployée | |
| Date du test | |
| Testeur | |
| Version Cascade | |

---

## 1. IDENTITÉ VISUELLE

| Point | Statut | Observation |
|---|---|---|
| Couleur de fond principale conforme | | |
| Couleur accent conforme (hex exact) | | |
| Police titres conforme | | |
| Police corps conforme | | |
| Logo visible et correct | | |
| Image hero visible (pas de fond uni) | | |
| Image présentation visible | | |

---

## 2. CONTENU CLIENT

| Point | Statut | Observation |
|---|---|---|
| Aucun `{{` visible sur la page | | |
| Aucun Lorem ipsum visible | | |
| Nom établissement correct partout | | |
| Adresse et téléphone corrects | | |
| Horaires corrects (déjeuner + dîner) | | |
| Badge hero pertinent | | |
| Sous-titre hero pertinent | | |
| Textes présentation non génériques | | |

---

## 3. MENU PUBLIC

| Point | Statut | Observation |
|---|---|---|
| Onglets de catégories visibles | | |
| Premier onglet actif au chargement | | |
| Changement d'onglet fonctionnel | | |
| Plats avec noms et prix réels | | |
| Aucun plat "indisponible" affiché par défaut | | |

---

## 4. ARDOISE DU JOUR

| Point | Statut | Observation |
|---|---|---|
| Section ardoise visible (fond sombre) | | |
| Plat du jour affiché avec prix | | |
| Prix en couleur accent | | |
| Entrée affichée (si renseignée) | | |
| Dessert affiché (si renseigné) | | |
| Formule affichée (si active) | | |

---

## 5. AVIS CLIENTS

| Point | Statut | Observation |
|---|---|---|
| 3 cartes avis visibles | | |
| Avatars colorés avec initiales | | |
| Textes avis non génériques | | |
| Score Google visible (si AFFICHER_SCORE_GOOGLE = block) | | |

---

## 6. FORMULAIRE RÉSERVATION

| Point | Statut | Observation |
|---|---|---|
| Horaires affichés dans les cartes service | | |
| Service = cartes cliquables (pas select) | | |
| Couverts = stepper +/− (pas input texte) | | |
| Date minimum = aujourd'hui | | |
| Soumettre → confirmation inline 4s | | |
| Réservation enregistrée dans localStorage | | |
| Aucun `alert()` à la soumission | | |

---

## 7. ESPACE GÉRANT (admin.html)

| Point | Statut | Observation |
|---|---|---|
| Login avec `admin2024` fonctionne | | |
| Mauvais mot de passe → erreur inline (pas alert) | | |
| 5 réservations démo présentes au premier login | | |
| Répartition correcte : 2 En attente · 2 Confirmée · 1 Annulée | | |
| KPIs calculés correctement | | |
| Confirmer réservation → badge mis à jour sans rechargement | | |
| Annuler réservation → badge mis à jour sans rechargement | | |
| Calendrier semaine : 7 jours cliquables | | |
| Onglet Menu & Ardoise accessible | | |
| Ardoise : sauvegarder → confirmation 4s (pas alert) | | |
| Ardoise : aperçu mis à jour en temps réel | | |
| Menu : ajouter catégorie via modal (pas prompt) | | |
| Menu : ajouter plat via modal (pas prompt) | | |
| Menu : supprimer catégorie via modal (pas confirm) | | |
| Menu : enregistrer → confirmation 4s | | |
| Déconnexion → retour écran login | | |

---

## 8. INFOS PRATIQUES

| Point | Statut | Observation |
|---|---|---|
| 3 cartes visibles (adresse, téléphone, horaires) | | |
| Lien Google Maps fonctionnel | | |
| Lien téléphone `tel:` fonctionnel | | |

---

## 9. ANIMATIONS & RESPONSIVE

| Point | Statut | Observation |
|---|---|---|
| Sections s'animent au scroll (fade-in) | | |
| Pas de contenu invisible (animations bloquées) | | |
| Lisible sur 390px (mobile) | | |
| Navigation sticky fonctionne | | |
| Footer : un seul lien "Espace gérant" (petit, discret) | | |

---

## 10. DÉPLOIEMENT

| Point | Statut | Observation |
|---|---|---|
| URL GitHub Pages accessible publiquement | | |
| index.html accessible sans erreur 404 | | |
| admin.html accessible sans erreur 404 | | |
| Tous les assets chargés (CSS, JS, images) | | |

---

## SCORE GLOBAL

| Dimension | Score |
|---|---|
| Fonctionnel | /10 |
| Contenu | /10 |
| Visuel | /10 |
| Impact "prospect" (10s test) | /10 |

**Décision** : ✅ PRÊT À ENVOYER · ⚠️ ENVOYER AVEC RÉSERVE · ❌ CORRIGER D'ABORD

---

## CORRECTIONS REQUISES

| # | Problème | Fichier | Priorité |
|---|---|---|---|
| 1 | | | Bloquant / Mineur |

---

## PROMPT DE CORRECTION CASCADE

> Si des corrections sont nécessaires, copier-coller ce bloc dans Cascade :

```
Corrections sur le site [NOM_ETABLISSEMENT] :

1. [description précise du problème]
   Fichier : [fichier] — ligne/section : [repère]
   Correction attendue : [ce qui doit changer]

2. [...]
```

---

*Template version 1.0 — L'Atelier Connecté — 2026-04-19*
