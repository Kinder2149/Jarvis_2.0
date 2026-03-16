# Configuration des clés API Gemini - JARVIS 2.0

## ⚠️ Prérequis obligatoire

JARVIS 2.0 nécessite des clés API Gemini pour fonctionner. Sans clés configurées, vous obtiendrez l'erreur :

```
400 API key not valid. Please pass a valid API key.
```

---

## 📝 Étapes de configuration

### 1. Obtenir vos clés API Gemini

1. Aller sur https://aistudio.google.com/app/apikey
2. Se connecter avec un compte Google
3. Créer **5 clés API** (une par agent pour maximiser le quota RPM)
4. Copier chaque clé

### 2. Configurer le fichier `.env`

**Si le fichier `.env` n'existe pas** :
```powershell
# Copier le template
Copy-Item .env.example .env
```

**Ouvrir `.env` et remplir les clés** :

```bash
# ============================================
# 1. CLÉS API GEMINI
# ============================================

# Clé API globale (FALLBACK)
GEMINI_API_KEY=ta_clé_globale_ici

# Clés API par agent (5 clés actives)
GEMINI_API_KEY_JARVIS_MAITRE=ta_clé_jarvis_maitre_ici
GEMINI_API_KEY_ARCHITECTE=ta_clé_architecte_ici
GEMINI_API_KEY_CODEUR=ta_clé_codeur_ici
GEMINI_API_KEY_TESTEUR=ta_clé_testeur_ici
GEMINI_API_KEY_VALIDATEUR=ta_clé_validateur_ici
```

### 3. Configuration minimale

**Si tu n'as qu'une seule clé**, configure au minimum :

```bash
GEMINI_API_KEY=ta_clé_unique_ici
GEMINI_API_KEY_JARVIS_MAITRE=ta_clé_unique_ici
```

Les autres agents utiliseront la clé globale en fallback.

### 4. Redémarrer le serveur

```powershell
# Arrêter le serveur (Ctrl+C)
# Redémarrer
.\start_jarvis_complete.ps1
```

---

## 🔍 Vérification

### Logs de démarrage

Si la configuration est correcte, tu verras :
```
[OK] Fichier .env trouvé
```

### Test rapide

1. Créer un projet
2. Créer une conversation avec JARVIS_Maître
3. Envoyer un message simple : "Bonjour"
4. Si tu reçois une réponse → ✅ Configuration OK
5. Si erreur `400 API key not valid` → ❌ Clé invalide ou manquante

---

## 📊 Quotas et limites

### Quota par clé (gratuit)

- **15 RPM** (Requests Per Minute) par clé
- **1 500 RPD** (Requests Per Day) par clé
- **1 million TPM** (Tokens Per Minute) par clé

### Stratégie multi-clés

Avec **5 clés** (une par agent) :
- **75 RPM total** (15 × 5)
- **7 500 RPD total** (1 500 × 5)

Cela permet d'exécuter le workflow 5 agents sans atteindre les limites.

---

## ❌ Erreurs courantes

### Erreur : `API key not valid`

**Causes** :
- Clé copiée incorrectement (espaces, caractères manquants)
- Clé révoquée ou expirée
- Fichier `.env` non créé

**Solution** :
1. Vérifier que `.env` existe (pas `.env.example`)
2. Vérifier que la clé est complète (commence par `AIza...`)
3. Régénérer une nouvelle clé sur Google AI Studio

### Erreur : `Resource has been exhausted`

**Cause** : Quota RPM dépassé

**Solution** :
- Attendre 1 minute
- Ajouter plus de clés API (une par agent)

### Erreur : `.env` non trouvé

**Cause** : Fichier `.env` manquant

**Solution** :
```powershell
Copy-Item .env.example .env
# Puis éditer .env avec tes clés
```

---

## 🔒 Sécurité

### ⚠️ Ne jamais committer `.env`

Le fichier `.env` est dans `.gitignore` par défaut.

**Vérifier** :
```powershell
git status
# .env ne doit PAS apparaître dans les fichiers modifiés
```

### 🔐 Rotation des clés

Si une clé est compromise :
1. Révoquer la clé sur Google AI Studio
2. Générer une nouvelle clé
3. Mettre à jour `.env`
4. Redémarrer le serveur

---

## 📚 Ressources

- **Google AI Studio** : https://aistudio.google.com/app/apikey
- **Documentation Gemini** : https://ai.google.dev/gemini-api/docs
- **Limites et quotas** : https://ai.google.dev/gemini-api/docs/quota

---

## ✅ Checklist finale

Avant de tester JARVIS :

- [ ] Fichier `.env` créé (copie de `.env.example`)
- [ ] Au minimum `GEMINI_API_KEY` configurée
- [ ] Idéalement 5 clés configurées (une par agent)
- [ ] Serveur redémarré après modification `.env`
- [ ] Test simple effectué (message "Bonjour" à JARVIS_Maître)

Si tout est OK → Tu peux tester le workflow 5 agents ! 🚀
