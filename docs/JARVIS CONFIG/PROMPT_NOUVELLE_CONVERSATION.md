# PROMPT POUR NOUVELLE CONVERSATION : PARAMÉTRAGE COMPLET JARVIS 2.0

**Copie-colle ce prompt dans une nouvelle conversation avec Windsurf (ou autre IA) pour exécuter la mission complète de paramétrage JARVIS.**

---

# 🎯 MISSION : PARAMÉTRER JARVIS 2.0 POUR UTILISATION QUOTIDIENNE

## Contexte

Je suis **Keamder (Valentin Coutry)**, pilote de projet assisté par IA à 100%. Je ne code JAMAIS sans IA.

J'ai créé **JARVIS 2.0**, un assistant IA multi-agent pour génération de code, qui doit remplacer Windsurf comme mon assistant principal.

**Statut actuel JARVIS** :
- ✅ Backend fonctionnel (99% tests)
- ✅ Orchestration JARVIS_Maître → CODEUR/BASE
- ✅ Génération code sur disque
- 🔄 **Paramétrage incomplet** : JARVIS ne connaît pas encore mon profil, workflow, préférences
- 📋 Documentation utilisateur manquante

**Objectif de cette mission** : Paramétrer JARVIS complètement pour qu'il soit utilisable quotidiennement.

---

## Ta Mission Complète

Tu dois paramétrer JARVIS 2.0 en suivant la méthode détaillée dans le document de référence.

**Travail à faire** :

### 1. Paramétrer les Agents
- Créer/Modifier prompts système pour JARVIS_Maître, CODEUR, BASE
- Adapter communication pour un pilote IA (pas développeur)
- Intégrer règles absolues (Pydantic v2, Storage JSON, etc.)

### 2. Configurer la Library
- Intégrer 5 documents CONFIG dans `backend/db/library_seed.json`
- Catégorie "personal"
- Vérifier accessibilité via function `get_library_document`

### 3. Créer Documentation Utilisateur
- Guide démarrage rapide
- Exemples concrets (TODO list, site avec auth)
- Troubleshooting

### 4. Tester et Valider
- Test création projet simple (TODO list)
- Vérification génération code + documentation
- Validation workflow complet

---

## Documents de Référence (À Lire OBLIGATOIREMENT)

Ces 5 documents sont la **source de vérité** pour paramétrer JARVIS. Tu DOIS les lire intégralement avant de commencer.

### 📄 Documents CONFIG (Localisation : `docs/JARVIS CONFIG/`)

1. **KEAMDER_PROFILE.md** : Mon profil complet
   - Positionnement : Pilote de projet IA 100%
   - Compétences : Technologies pilotées via IA
   - Difficultés : Pilotage IA (prioritaire) + Techniques (secondaire)
   - Forces réelles : Vision produit, workflow structuré, persévérance
   - 9 projets réalisés dont 3 en production

2. **KEAMDER_WORKFLOW.md** : Ma méthodologie de travail
   - Workflow en 5 phases (Idée → Challenge → Plan → Génération → Tests → Amélioration)
   - Pratiques réelles (documentation systématique, tests manuels, versioning)
   - Gestion échecs et debugging (critères abandon, sources aide externe)
   - Stack normalisée préférée (Python/FastAPI, HTML/CSS/JS vanilla, SQLite/Supabase)

3. **JARVIS_ARCHITECTURE.md** : Architecture JARVIS 2.0
   - 4 agents (JARVIS_Maître, CODEUR, BASE, VALIDATEUR)
   - Stack et services (Python/FastAPI, Gemini API Tier 1, Supabase, Vercel)
   - Flux de travail (orchestration, délégation, protections anti-boucle)
   - Statut actuel et roadmap

4. **KEAMDER_DEV_RULES.md** : Règles d'orchestration pour IA
   - Principes fondamentaux (pas d'invention, structuration, validation)
   - Workflow (phases, traçabilité, validation obligatoire)
   - Règles spécifiques pour pilote IA (communication adaptée, proposer avant exécuter, guider tests)
   - Règles absolues CODEUR (Pydantic v2, Storage JSON, cohérence)

5. **JARVIS_COMPORTEMENT_GENERIQUE.md** : Comportement générique JARVIS
   - Workflow standard en 6 phases détaillées
   - Stack par défaut (ordre de préférence)
   - Gestion mémoire et contexte (rappel automatique)
   - Documentation automatique (README, plan.md, .env.example)
   - Gestion échecs (critères abandon, aide externe)
   - Exemples concrets (site avec auth, app mobile)

### 📋 Document Mission (Localisation : `docs/JARVIS CONFIG/`)

6. **MISSION_PARAMETRAGE_JARVIS_COMPLET.md** : Guide complet de la mission
   - Contexte détaillé
   - Méthode de travail (6 phases)
   - Checklist complète
   - Critères de succès
   - Fichiers à modifier/créer
   - Points d'attention

---

## Méthode de Travail (Résumé)

### Phase 1 : Analyse et Compréhension
1. Lire les 5 documents CONFIG intégralement
2. Analyser architecture actuelle (fichiers backend)
3. Créer plan de paramétrage détaillé

### Phase 2 : Paramétrage des Agents
1. Créer/Modifier prompt JARVIS_Maître (workflow 6 phases, communication adaptée)
2. Créer/Modifier prompt CODEUR (règles absolues, stack par défaut)
3. Créer/Modifier prompt BASE (format rapport validation)

### Phase 3 : Configuration Library
1. Lire contenu des 5 fichiers .md
2. Ajouter à `backend/db/library_seed.json` (catégorie "personal")
3. Vérifier format JSON valide
4. Tester accès via `get_library_document`

### Phase 4 : Documentation Utilisateur
1. Créer `docs/reference/GUIDE_DEMARRAGE_RAPIDE.md`
2. Créer `docs/reference/EXEMPLES_PROJETS.md`
3. Ajouter troubleshooting

### Phase 5 : Tests et Validation
1. Test création projet simple (TODO list)
2. Test workflow debugging
3. Test gestion mémoire

### Phase 6 : Finalisation
1. Documenter toutes modifications
2. Créer rapport final
3. Lister points d'amélioration futurs

---

## Checklist Complète (À Suivre)

### ✅ Phase 1 : Analyse
- [ ] Lire KEAMDER_PROFILE.md
- [ ] Lire KEAMDER_WORKFLOW.md
- [ ] Lire JARVIS_ARCHITECTURE.md
- [ ] Lire KEAMDER_DEV_RULES.md
- [ ] Lire JARVIS_COMPORTEMENT_GENERIQUE.md
- [ ] Lire MISSION_PARAMETRAGE_JARVIS_COMPLET.md
- [ ] Analyser fichiers backend existants
- [ ] Créer plan de paramétrage détaillé

### ✅ Phase 2 : Paramétrage Agents
- [ ] Créer/Modifier prompt JARVIS_Maître
- [ ] Créer/Modifier prompt CODEUR
- [ ] Créer/Modifier prompt BASE
- [ ] Tester prompts

### ✅ Phase 3 : Configuration Library
- [ ] Lire contenu 5 fichiers .md
- [ ] Ajouter à library_seed.json
- [ ] Vérifier JSON valide
- [ ] Tester accès documents

### ✅ Phase 4 : Documentation
- [ ] Créer GUIDE_DEMARRAGE_RAPIDE.md
- [ ] Créer EXEMPLES_PROJETS.md

### ✅ Phase 5 : Tests
- [ ] Test création projet simple
- [ ] Test workflow debugging
- [ ] Test gestion mémoire

### ✅ Phase 6 : Finalisation
- [ ] Documenter modifications
- [ ] Créer rapport final

---

## Critères de Succès (Validation Finale)

**Critères obligatoires** :
1. ✅ Agents paramétrés (JARVIS_Maître, CODEUR, BASE)
2. ✅ Library configurée (5 documents CONFIG accessibles)
3. ✅ Workflow fonctionnel (création projet simple)
4. ✅ Documentation créée (guide + exemples)
5. ✅ Tests passent (création projet, debugging, mémoire)

**Si tous ces critères sont validés, JARVIS 2.0 est prêt pour utilisation quotidienne.**

---

## Fichiers à Modifier/Créer

### À Modifier
1. `config_gemini/agents/JARVIS_MAITRE.md` (ou équivalent)
2. `config_gemini/agents/CODEUR.md` (ou équivalent)
3. `config_gemini/agents/BASE.md` (ou équivalent)
4. `backend/db/library_seed.json`

### À Créer
1. `docs/reference/GUIDE_DEMARRAGE_RAPIDE.md`
2. `docs/reference/EXEMPLES_PROJETS.md`
3. `docs/work/RAPPORT_PARAMETRAGE_JARVIS.md`

### Références (NE PAS Modifier)
1. `docs/JARVIS CONFIG/KEAMDER_PROFILE.md`
2. `docs/JARVIS CONFIG/KEAMDER_WORKFLOW.md`
3. `docs/JARVIS CONFIG/JARVIS_ARCHITECTURE.md`
4. `docs/JARVIS CONFIG/KEAMDER_DEV_RULES.md`
5. `docs/JARVIS CONFIG/JARVIS_COMPORTEMENT_GENERIQUE.md`
6. `docs/JARVIS CONFIG/MISSION_PARAMETRAGE_JARVIS_COMPLET.md`

---

## Points d'Attention

### Règles Absolues
1. **NE PAS modifier les documents CONFIG** : Ce sont les références
2. **Tester chaque modification** : Ne pas accumuler sans tests
3. **Documenter toutes modifications** : Traçabilité complète
4. **Valider avec critères de succès** : Vérifier chaque critère

### Difficultés Anticipées
1. Intégration Library : Format JSON, échappement caractères
2. Prompts agents : Équilibre détail vs concision
3. Tests workflow complet : Backend + frontend fonctionnels
4. Gestion mémoire : Implémentation rappel contexte

---

## Démarrage de la Mission

**Étape 1** : Commence par lire les 6 documents de référence dans cet ordre :
1. KEAMDER_PROFILE.md
2. KEAMDER_WORKFLOW.md
3. JARVIS_ARCHITECTURE.md
4. KEAMDER_DEV_RULES.md
5. JARVIS_COMPORTEMENT_GENERIQUE.md
6. MISSION_PARAMETRAGE_JARVIS_COMPLET.md

**Étape 2** : Analyse l'architecture actuelle (fichiers backend)

**Étape 3** : Crée un plan de paramétrage détaillé

**Étape 4** : Exécute le plan en suivant la checklist

**Étape 5** : Teste et valide avec les critères de succès

**Étape 6** : Crée le rapport final

---

## Livrables Attendus

1. **Prompts agents paramétrés** (JARVIS_Maître, CODEUR, BASE)
2. **Library configurée** (library_seed.json avec 5 documents)
3. **Documentation utilisateur** (guide + exemples)
4. **Rapport final** (toutes modifications documentées)

---

## 🚀 COMMENCE LA MISSION

Lis d'abord les 6 documents de référence, puis crée ton plan de paramétrage détaillé.

**Bonne chance !** 🎯
