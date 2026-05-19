# Scénarios de test manuel — JARVIS Orchestrateur

Tests à réaliser dans le navigateur sur `http://localhost:8000/jarvis.html`.
Serveur requis : `uvicorn backend.main:app --reload --port 8000` 

---

## Prérequis

- [ ] Serveur démarré, pas d'erreur dans la console uvicorn
- [ ] Page jarvis.html chargée sans erreur JS (F12 → Console)
- [ ] Les 5 cartes agents visibles à gauche (JARVIS, MENTOR, FORGE, SENTINELLE, ATELIER)
- [ ] Badge "5 actifs · 24/7" visible en haut à droite

---

## Scénario 1 — JARVIS Orchestrateur direct

**Objectif** : JARVIS répond seul aux questions générales, sans déléguer.

| # | Action | Résultat attendu | ✓ |
|---|--------|-----------------|---|
| 1 | Cliquer sur la carte JARVIS (gauche) | Carte JARVIS active (bordure bleue), badge chat = "⚡ JARVIS", indicateur = "auto-routing" (vert) | ☐ |
| 2 | Taper : "Bonjour, comment tu fonctionnes ?" → Envoyer | Réponse de JARVIS, badge dans le message = JARVIS (bleu), aucune délégation | ☐ |
| 3 | Taper : "Qu'est-ce que tu peux faire ?" → Envoyer | Réponse JARVIS décrivant les 4 agents | ☐ |
| 4 | Cliquer "+ Nouvelle" → Confirmer | Thread vidé, titre conversation remis à "JARVIS Orchestrateur", indicateur = "auto-routing" | ☐ |

---

## Scénario 2 — Routing automatique vers MENTOR

**Objectif** : JARVIS détecte l'intention "mission" et route vers MENTOR.

| # | Action | Résultat attendu | ✓ |
|---|--------|-----------------|---|
| 1 | Vérifier que JARVIS est sélectionné (auto-routing) | Indicateur vert "auto-routing" visible | ☐ |
| 2 | Taper : "Je veux définir une mission pour développer une fonctionnalité." → Envoyer | Badge réponse = MENTOR (ambre), lien "Voir la réflexion →" visible sous le badge | ☐ |
| 3 | La carte MENTOR s'active visuellement (bordure ambre) | Carte MENTOR marquée active | ☐ |
| 4 | Taper un second message de suivi (ex : "Les fichiers concernés sont api.py et utils.py") → Envoyer | MENTOR répond en continuant la réflexion, même session | ☐ |
| 5 | Cliquer "Voir la réflexion →" | Redirige vers mission.html avec la bonne session | ☐ |

---

## Scénario 3 — Mode direct ATELIER (clic carte)

**Objectif** : Cliquer sur ATELIER bypass le routing, ATELIER reçoit les messages directement.

| # | Action | Résultat attendu | ✓ |
|---|--------|-----------------|---|
| 1 | Cliquer sur la carte ATELIER | Carte ATELIER active (bordure violette), indicateur = "direct" (orange), placeholder = "Message direct à ATELIER…" | ☐ |
| 2 | Taper : "Je veux créer un nouveau prospect." → Envoyer | Badge réponse = ATELIER (violet), demande le nom du restaurant | ☐ |
| 3 | Taper : "La Bella Vista" → Envoyer | ATELIER demande l'URL | ☐ |
| 4 | Taper : "pas de site" → Envoyer | ATELIER demande une note (optionnel) | ☐ |
| 5 | Taper : "-" → Envoyer | ATELIER confirme la création, lien "Ouvrir dans l'Atelier →" cliquable | ☐ |
| 6 | Cliquer le lien → vérifier dans atelier.html | Prospect "La Bella Vista" visible dans la liste | ☐ |

---

## Scénario 4 — SENTINELLE : consultation + watchlist

**Objectif** : SENTINELLE consulte les données et gère la watchlist.

| # | Action | Résultat attendu | ✓ |
|---|--------|-----------------|---|
| 1 | Cliquer sur la carte SENTINELLE | Indicateur = "direct" (orange) | ☐ |
| 2 | Taper : "Quel est mon budget ce mois-ci ?" → Envoyer | SENTINELLE répond avec les données budget (0€ si vide, cohérent) | ☐ |
| 3 | Taper : "Ajoute LVMH à ma watchlist." → Envoyer | Confirmation "✅ LVMH ajouté à ta watchlist." | ☐ |
| 4 | Taper : "Je veux acheter 5 actions LVMH." → Envoyer | SENTINELLE refuse et redirige vers sentinelle.html | ☐ |
| 5 | Cliquer → sentinelle.html | Page SENTINELLE s'ouvre, LVMH visible dans la watchlist | ☐ |

---

## Scénario 5 — Retour à JARVIS / switch d'agent

**Objectif** : Basculer entre agents sans perdre le contexte.

| # | Action | Résultat attendu | ✓ |
|---|--------|-----------------|---|
| 1 | Depuis mode direct ATELIER, cliquer sur la carte JARVIS | Indicateur repasse en "auto-routing" (vert), placeholder = "Message à JARVIS (route automatiquement)…" | ☐ |
| 2 | Taper : "Bonjour" → Envoyer | JARVIS répond (pas ATELIER), badge = JARVIS | ☐ |
| 3 | Cliquer "+ Nouvelle" | Nouvelle conversation, tout réinitialisé, JARVIS auto-routing actif | ☐ |

---

## Scénario 6 — Vérifications visuelles et navigation

| # | Vérification | Attendu | ✓ |
|---|-------------|---------|---|
| 1 | Menu ☰ en haut à droite | Dropdown avec : Conversations, Dashboard, Paramètres | ☐ |
| 2 | Pas de liens directs dans la nav (Projets, Sentinelle, Atelier…) | Seuls Brand + Status + ☰ visibles dans la nav | ☐ |
| 3 | Stats hero (sessions, livrables) | Chiffres chargés après ~2s (pas "—" indéfiniment) | ☐ |
| 4 | Stat ATELIER dans la carte | "N prospects actifs" avec point vert si N > 0 | ☐ |
| 5 | Console JS (F12) | Aucune erreur rouge | ☐ |

---

## Comment lancer les tests automatiques

```bash
# Étape 1 : démarrer le serveur
uvicorn backend.main:app --reload --port 8000

# Étape 2 : lancer les tests live API (autre terminal)
pytest tests/live/test_jarvis_orchestrator.py -m live -v --timeout=120
pytest tests/live/test_jarvis_atelier.py      -m live -v --timeout=120
pytest tests/live/test_jarvis_sentinelle.py   -m live -v --timeout=120

# Ou tout en une commande :
pytest tests/live/test_jarvis_orchestrator.py tests/live/test_jarvis_atelier.py tests/live/test_jarvis_sentinelle.py -m live -v --timeout=120
```
