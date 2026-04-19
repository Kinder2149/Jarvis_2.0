# Architecture Page Paramètres JARVIS 2.0

## Vue d'ensemble

Page d'administration complète avec système d'onglets pour gérer la configuration de JARVIS.

## Structure des fichiers

```
frontend/
├── settings.html          # Structure HTML avec 4 onglets
├── assets/
│   ├── js/
│   │   └── settings.js    # Logique complète (tabs + config)
│   └── style.css          # Styles onglets + éléments settings
```

## Onglets

### 1. 🔑 Clés API
**Fonctionnalités :**
- Affichage masqué des clés configurées (`●●●●●●●●●●`)
- Bouton révéler/masquer (👁️/🙈)
- Édition inline avec input password
- Test de connexion par provider
- Badge de statut (✅ OK / ❌ Échec)

**Providers supportés :**
- OpenRouter (principal)
- Anthropic (fallback)
- Google AI (fallback)
- Brave Search API

### 2. 🤖 Modèles
**Fonctionnalités :**
- 4 sélecteurs de modèles par type de tâche
- Descriptions détaillées du rôle de chaque type
- Chargement dynamique depuis `/api/config/models/available`
- Sauvegarde avec payload complet

**Types de tâches :**
- 🧭 Routage / Décision
- 📊 Structuration
- 💻 Code / Analyse
- 🧠 Missions complexes

### 3. 💬 Chat & Présets
**Fonctionnalités :**
- Sélection du modèle par défaut pour le chat
- Configuration du chemin METHODO
- Note de session (contexte temporaire)
- Prompt système personnalisé

**Champs :**
- `model` : Modèle par défaut
- `methodo_path` : Chemin vers fichiers méthodologie
- `session_note` : Note contextuelle
- `system_prompt_preset` : Prompt système custom

### 4. ⚙️ Avancé
**Fonctionnalités :**
- Informations système (version, stack)
- Export config en JSON
- Import config depuis JSON
- Réinitialisation complète

## API Backend

### Endpoints utilisés

```
GET  /api/config
POST /api/config
POST /api/config/test
GET  /api/config/models/available
```

### Format payload POST /api/config

```json
{
  "api_keys": {
    "openrouter_key": "sk-...",
    "anthropic_key": "sk-...",
    "google_key": "...",
    "web_search_key": "..."
  },
  "model_preferences": {
    "routing": "google/gemini-2.0-flash-001",
    "structuring": "google/gemini-2.0-flash-001",
    "code": "anthropic/claude-haiku-4.5",
    "analysis": "anthropic/claude-sonnet-4.5"
  },
  "chat": {
    "model": "anthropic/claude-sonnet-4.5",
    "methodo_path": "C:\\DEV\\METHODO",
    "session_note": "",
    "system_prompt_preset": ""
  }
}
```

**Contrainte critique :** Les champs `api_keys` et `model_preferences` sont **required**. Toujours envoyer les deux même si on ne modifie qu'un seul.

## Logique JavaScript

### Système d'onglets

```javascript
// Sauvegarde de l'onglet actif dans localStorage
localStorage.setItem('settings_active_tab', tabName);

// Restauration au chargement
const savedTab = localStorage.getItem('settings_active_tab') || 'api-keys';
switchTab(savedTab);
```

### Gestion des clés masquées

Les clés retournées par `GET /api/config` sont masquées (`...xxxx`). Le backend skip les valeurs commençant par `...` lors de la sauvegarde.

```javascript
// Exemple de clé masquée retournée
{
  "openrouter_key": "...abcd"
}

// Lors de la sauvegarde, renvoyer telle quelle si non modifiée
// Le backend ne l'écrasera pas
```

### Sauvegarde avec payload complet

```javascript
async function saveApiKey(provider) {
  const apiKeys = {
    openrouter_key: currentConfig.api_keys.openrouter_key || '',
    anthropic_key: currentConfig.api_keys.anthropic_key || '',
    google_key: currentConfig.api_keys.google_key || '',
    web_search_key: currentConfig.api_keys.web_search_key || ''
  };
  apiKeys[`${provider}_key`] = newValue;

  const payload = {
    api_keys: apiKeys,
    model_preferences: currentConfig.model_preferences || defaultPrefs
  };

  await window.API.saveConfig(payload);
}
```

## Classes CSS

### Onglets

```css
.settings-tabs              /* Container des onglets */
.settings-tab               /* Bouton onglet */
.settings-tab--active       /* Onglet actif */
.settings-tab-content       /* Contenu d'un onglet */
.settings-tab-content--active /* Contenu visible */
```

### Chat Config

```css
.chat-config-row            /* Ligne de formulaire */
.chat-config-label          /* Label du champ */
.chat-config-hint           /* Texte d'aide */
```

### Avancé

```css
.advanced-info-grid         /* Grille infos système */
.advanced-info-item         /* Item d'info */
.advanced-info-label        /* Label info */
.advanced-info-value        /* Valeur info */
.advanced-actions           /* Container boutons */
.btn-danger                 /* Bouton rouge (reset) */
```

## Fonctions principales

### settings.js

```javascript
// Onglets
initTabs()                  // Initialise le système d'onglets
switchTab(tabName)          // Change d'onglet

// Chargement
loadSettings()              // Charge config + modèles disponibles
renderApiKeys()             // Affiche les clés API
renderModelSelects()        // Remplit les sélecteurs de modèles
renderChatConfig()          // Remplit la config chat

// Sauvegarde
saveApiKey(provider)        // Sauvegarde une clé API
saveModels()                // Sauvegarde les préférences modèles
saveChatConfig()            // Sauvegarde la config chat

// Test
testConnection(provider)    // Test une connexion API

// Avancé
exportConfig()              // Export JSON
importConfig(event)         // Import JSON
resetConfig()               // Réinitialisation
```

## Flux utilisateur

### Configurer une clé API

1. Onglet "Clés API"
2. Clic sur "Configurer" ou "Modifier"
3. Input password s'affiche
4. Saisie de la clé
5. Clic "Sauvegarder"
6. Payload complet envoyé au backend
7. Toast de confirmation
8. Affichage masqué de la clé

### Tester une connexion

1. Clé configurée
2. Clic sur "Tester"
3. Spinner affiché dans le badge
4. Appel `POST /api/config/test`
5. Badge ✅ OK ou ❌ Échec

### Changer les modèles

1. Onglet "Modèles"
2. Sélection dans les 4 dropdowns
3. Clic "Sauvegarder les modèles"
4. Payload complet envoyé
5. Toast de confirmation

### Configurer le chat

1. Onglet "Chat & Présets"
2. Modification des champs
3. Clic "Sauvegarder la config chat"
4. Payload complet envoyé (avec chat)
5. Toast de confirmation

### Export/Import

**Export :**
1. Onglet "Avancé"
2. Clic "Exporter la config"
3. Téléchargement JSON `jarvis-config-YYYY-MM-DD.json`

**Import :**
1. Clic "Importer une config"
2. Sélection fichier JSON
3. Validation du format
4. Sauvegarde via API
5. Rechargement de la page

### Réinitialisation

1. Clic "Réinitialiser tout"
2. Confirmation (popup)
3. Payload par défaut envoyé
4. Rechargement de la page

## Gestion d'état

### localStorage

```javascript
settings_active_tab: 'api-keys' | 'models' | 'chat' | 'advanced'
```

### Variables globales

```javascript
let currentConfig = null;      // Config actuelle depuis API
let availableModels = null;    // Modèles disponibles depuis API
```

## Sécurité

- Clés API masquées dans l'affichage
- Input type="password" par défaut
- Bouton révéler temporaire (👁️)
- Clés stockées en SQLite côté backend
- Jamais transmises au frontend en clair (sauf lors de la saisie)

## Compatibilité

- HTML5 + CSS3
- JavaScript vanilla (ES6+)
- Aucune dépendance externe
- Compatible tous navigateurs modernes

## Points d'attention

1. **Payload complet obligatoire** : Toujours envoyer `api_keys` + `model_preferences`
2. **Clés masquées** : Renvoyer telles quelles si non modifiées
3. **Onglet actif** : Sauvegardé dans localStorage
4. **Chat config** : Optionnel dans le payload
5. **Import/Reset** : Rechargement de la page après modification

## Test manuel

1. Ouvrir `/settings.html`
2. Vérifier navigation entre onglets
3. Configurer une clé API
4. Tester la connexion
5. Modifier les modèles
6. Configurer le chat
7. Exporter la config
8. Importer la config
9. Réinitialiser (avec prudence)
