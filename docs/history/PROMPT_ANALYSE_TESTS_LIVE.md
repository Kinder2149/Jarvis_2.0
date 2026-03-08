# PROMPT — Analyse Résultats Tests Live JARVIS 2.0

**Date** : 7 mars 2026  
**Contexte** : Après corrections prompts JARVIS_Maître v5.1 et CODEUR v3.2  
**Objectif** : Analyser résultats tests live et corriger les problèmes restants

---

## 📋 PROMPT À COPIER-COLLER

```
# CONTEXTE

Je viens de lancer les tests live de JARVIS 2.0 après avoir appliqué des corrections aux prompts des agents.

**Corrections appliquées** :
1. JARVIS_Maître v5.0 → v5.1 : Ajout exception validation pour projets vides/TEST
2. CODEUR v3.1 → v3.2 : Renforcement RÈGLE 3 (cohérence, imports, structure)

**Fichiers modifiés** :
- `config_agents/JARVIS_MAITRE.md` (v5.1)
- `config_agents/CODEUR.md` (v3.2)

---

# RÉSULTATS TESTS LIVE

[COLLER ICI LES RÉSULTATS COMPLETS DU TERMINAL]

---

# MISSION

Analyse ces résultats et :

## 1. DIAGNOSTIC
- Identifier les succès et échecs
- Comparer avec résultats précédents (avant corrections)
- Déterminer si les corrections ont fonctionné

## 2. ANALYSE DES ÉCHECS
Pour chaque test qui échoue :
- Identifier la cause exacte (prompt agent, code généré, timeout, etc.)
- Localiser le fichier/ligne problématique
- Déterminer quel agent est responsable

## 3. CORRECTIONS NÉCESSAIRES
Pour chaque problème identifié :
- Proposer correction précise (quel fichier, quelle ligne, quel changement)
- Expliquer pourquoi cette correction résoudra le problème
- Prioriser les corrections (critique, important, mineur)

## 4. PLAN D'ACTION
- Lister les fichiers à modifier dans l'ordre
- Pour chaque modification : fichier, section, changement exact
- Estimer impact (résoudra quel(s) test(s))

---

# RÈGLES IMPORTANTES

1. **Analyse factuelle** : Base-toi uniquement sur les résultats fournis
2. **Pas d'invention** : Ne suppose pas, vérifie dans les fichiers si besoin
3. **Corrections ciblées** : Modifications minimales et précises
4. **Validation** : Explique comment vérifier que la correction fonctionne

---

# FORMAT ATTENDU

## ✅ SUCCÈS
- Liste des tests qui passent
- Confirmation que les corrections appliquées ont fonctionné

## ❌ ÉCHECS
- Liste des tests qui échouent
- Pour chaque échec : cause + fichier responsable

## 🔧 CORRECTIONS PROPOSÉES

### Correction 1 : [Titre]
**Fichier** : `chemin/fichier.ext`  
**Problème** : [Description]  
**Solution** : [Modification exacte]  
**Impact** : Résoudra test [nom]

### Correction 2 : [Titre]
...

## 📋 PLAN D'EXÉCUTION
1. Modifier `fichier1` (ligne X-Y)
2. Modifier `fichier2` (ligne Z)
3. Relancer tests live
4. Vérifier résultats

---

# COMMENCE L'ANALYSE
```

---

## 📝 NOTES D'UTILISATION

### Étape 1 : Copier le prompt
Copie tout le texte entre les triple backticks ci-dessus.

### Étape 2 : Nouvelle conversation
Ouvre une nouvelle conversation dans Windsurf/Cascade.

### Étape 3 : Coller et compléter
1. Colle le prompt
2. Remplace `[COLLER ICI LES RÉSULTATS COMPLETS DU TERMINAL]` par la sortie complète de `python tests/live/test_live_projects.py`

### Étape 4 : Envoyer
Envoie le message et laisse l'IA analyser.

---

## 🎯 RÉSULTATS ATTENDUS

L'IA devrait produire :
- ✅ Diagnostic clair des succès/échecs
- ✅ Analyse détaillée de chaque problème
- ✅ Corrections précises (fichier + ligne + changement)
- ✅ Plan d'action ordonné

---

## 📊 EXEMPLE DE RÉSULTATS PRÉCÉDENTS

**Avant corrections (6 mars 2026)** :
- ✅ Calculatrice : 13 tests passent
- ❌ TODO : Erreurs import
- ❌ MiniBlog : AttributeError

**Problèmes identifiés** :
1. JARVIS_Maître demande validation sur projets vides
2. CODEUR génère code avec erreurs cohérence

**Corrections appliquées** :
- JARVIS_Maître v5.1 : Exception validation projets vides
- CODEUR v3.2 : Cohérence renforcée

**Score attendu après corrections** : 3/3 (100%)

---

**Document créé le** : 7 mars 2026  
**Usage** : Nouvelle conversation Windsurf/Cascade  
**Objectif** : Analyse automatisée résultats tests live
