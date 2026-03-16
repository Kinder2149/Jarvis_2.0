# Configuration .env - Guide rapide

## ⚠️ Problème actuel

Erreur : `400 API key not valid`

## ✅ Solution

### 1. Ajouter GEMINI_API_KEY global

**Même si chaque agent a sa clé**, tu DOIS ajouter une clé globale pour l'agent BASE.

**Dans ton fichier `.env`**, ajoute cette ligne :

```bash
# Clé API globale (OBLIGATOIRE pour agent BASE)
GEMINI_API_KEY=ta_clé_jarvis_maitre_ici

# Clés par agent (déjà configurées)
GEMINI_API_KEY_JARVIS_MAITRE=ta_clé_jarvis_maitre_ici
GEMINI_API_KEY_ARCHITECTE=ta_clé_architecte_ici
GEMINI_API_KEY_CODEUR=ta_clé_codeur_ici
GEMINI_API_KEY_TESTEUR=ta_clé_testeur_ici
GEMINI_API_KEY_VALIDATEUR=ta_clé_validateur_ici
```

**Astuce** : Utilise la même clé que JARVIS_Maître pour `GEMINI_API_KEY`.

### 2. Redémarrer le serveur

```powershell
# Arrêter (Ctrl+C)
# Redémarrer
.\start_jarvis_complete.ps1
```

### 3. Vérifier

Si tu vois cette erreur disparaître → ✅ Configuration OK

---

## 📋 Checklist

- [ ] Fichier `.env` existe (pas `.env.example`)
- [ ] `GEMINI_API_KEY=...` configurée (ligne ajoutée)
- [ ] Les 5 clés agents configurées
- [ ] Serveur redémarré
- [ ] Test simple effectué

---

## 🎯 Nouvelle interface

Après redémarrage, tu verras :

```
┌─────────────┬──────────┬─────────────┐
│Conversations│   Chat   │  Fichiers   │
│             │          │             │
├─────────────┤          │             │
│  ⚙️ Workflow│          │             │
│             │          │             │
└─────────────┴──────────┴─────────────┘
```

Le workflow apparaîtra **sous les conversations** quand JARVIS_Maître délèguera une tâche.
