(function() {
  let currentConfig = null;
  let availableModels = null;

  document.addEventListener('DOMContentLoaded', async () => {
    initTabs();
    await loadSettings();
  });

  // ── Système d'onglets ──────────────────────────────────────────
  function initTabs() {
    const tabs = document.querySelectorAll('.settings-tab');
    const savedTab = localStorage.getItem('settings_active_tab') || 'api-keys';
    
    // Activer l'onglet sauvegardé
    switchTab(savedTab);
    
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        switchTab(tabName);
        localStorage.setItem('settings_active_tab', tabName);
      });
    });
  }

  function switchTab(tabName) {
    // Désactiver tous les onglets
    document.querySelectorAll('.settings-tab').forEach(t => {
      t.classList.remove('settings-tab--active');
    });
    document.querySelectorAll('.settings-tab-content').forEach(c => {
      c.classList.remove('settings-tab-content--active');
    });
    
    // Activer l'onglet sélectionné
    const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
    const activeContent = document.getElementById(`tab-${tabName}`);
    
    if (activeTab) activeTab.classList.add('settings-tab--active');
    if (activeContent) activeContent.classList.add('settings-tab-content--active');
  }

  // ── Chargement config ──────────────────────────────────────────
  async function loadSettings() {
    try {
      [currentConfig, availableModels] = await Promise.all([
        window.API.getConfig(),
        window.API.getAvailableModels()
      ]);

      renderApiKeys();
      renderModelSelects();
      setupTabSwitching();
      loadConfig();
      loadGlobalContext();
      setupProfilsModulesHandlers();
      await loadExportPaths();
      attachEventListeners();
      
      // Initialiser les badges à "Non testé"
      initializeTestBadges();

    } catch (error) {
      console.error('Erreur chargement paramètres:', error);
      if (window.showToast) window.showToast('Erreur de chargement', 'error');
    }
  }

  function renderApiKeys() {
    const providers = ['openrouter', 'anthropic', 'google', 'web_search', 'twelve_data'];
    providers.forEach(provider => {
      const maskedValue = currentConfig.api_keys?.[`${provider}_key`] || '';
      renderApiKey(provider, maskedValue);
    });
  }

  function renderApiKey(provider, maskedValue) {
    const container = document.getElementById(`key-display-${provider}`);
    if (!container) return;

    if (maskedValue && maskedValue.trim()) {
      container.innerHTML = `
        <div class="key-defined-state">
          <span class="key-masked" id="key-val-${provider}">●●●●●●●●●●</span>
          <button class="btn-icon btn-reveal" data-provider="${provider}" title="Révéler">👁️</button>
          <button class="btn-secondary btn-sm btn-edit-key" data-provider="${provider}">✏️ Modifier</button>
          <span class="key-status-ok">✅ Configurée</span>
        </div>
      `;

      const btnReveal = container.querySelector('.btn-reveal');
      const btnEdit = container.querySelector('.btn-edit-key');

      if (btnReveal) {
        btnReveal.addEventListener('click', () => toggleRevealKey(provider, maskedValue));
      }

      if (btnEdit) {
        btnEdit.addEventListener('click', () => showEditForm(provider, maskedValue));
      }

    } else {
      container.innerHTML = `
        <div class="key-undefined-state">
          <span class="key-status-missing">⚠️ Non configurée</span>
          <button class="btn-primary btn-sm btn-set-key" data-provider="${provider}">+ Configurer</button>
        </div>
      `;

      const btnSet = container.querySelector('.btn-set-key');
      if (btnSet) {
        btnSet.addEventListener('click', () => showEditForm(provider, null));
      }
    }
  }

  function toggleRevealKey(provider, maskedValue) {
    const keySpan = document.getElementById(`key-val-${provider}`);
    const btnReveal = document.querySelector(`[data-provider="${provider}"].btn-reveal`);

    if (!keySpan || !btnReveal) return;

    if (keySpan.textContent === '●●●●●●●●●●') {
      keySpan.textContent = maskedValue;
      btnReveal.textContent = '🙈';
      btnReveal.title = 'Masquer';
    } else {
      keySpan.textContent = '●●●●●●●●●●';
      btnReveal.textContent = '👁️';
      btnReveal.title = 'Révéler';
    }
  }

  function showEditForm(provider, currentValue) {
    const container = document.getElementById(`key-display-${provider}`);
    if (!container) return;

    const previousState = container.innerHTML;

    container.innerHTML = `
      <div class="key-edit-state">
        <input type="password" class="input-field key-input" id="key-input-${provider}"
          placeholder="Coller la clé API ici..." value="${currentValue || ''}">
        <button class="btn-icon btn-reveal-input" data-provider="${provider}" title="Révéler">👁️</button>
        <button class="btn-primary btn-sm btn-save-key" data-provider="${provider}">💾 Sauvegarder</button>
        <button class="btn-secondary btn-sm btn-cancel-key" data-provider="${provider}">Annuler</button>
      </div>
    `;

    const input = document.getElementById(`key-input-${provider}`);
    const btnRevealInput = container.querySelector('.btn-reveal-input');
    const btnSave = container.querySelector('.btn-save-key');
    const btnCancel = container.querySelector('.btn-cancel-key');

    if (input) input.focus();

    if (btnRevealInput) {
      btnRevealInput.addEventListener('click', () => {
        if (input.type === 'password') {
          input.type = 'text';
          btnRevealInput.textContent = '🙈';
        } else {
          input.type = 'password';
          btnRevealInput.textContent = '👁️';
        }
      });
    }

    if (btnSave) {
      btnSave.addEventListener('click', async () => {
        await saveApiKey(provider);
      });
    }

    if (btnCancel) {
      btnCancel.addEventListener('click', () => {
        container.innerHTML = previousState;
        renderApiKey(provider, currentConfig.api_keys?.[`${provider}_key`] || '');
      });
    }
  }

  async function saveApiKey(provider) {
    const input = document.getElementById(`key-input-${provider}`);
    if (!input) return;

    const keyValue = input.value.trim();
    if (!keyValue) {
      if (window.showToast) window.showToast('Clé vide', 'warning');
      return;
    }

    try {
      const currentApiKeys = currentConfig.api_keys || {};
      const apiKeys = {
        openrouter_key: currentApiKeys.openrouter_key || '',
        anthropic_key: currentApiKeys.anthropic_key || '',
        google_key: currentApiKeys.google_key || '',
        web_search_key: currentApiKeys.web_search_key || '',
        twelve_data_key: currentApiKeys.twelve_data_key || ''
      };
      apiKeys[`${provider}_key`] = keyValue;

      const defaultPrefs = {
        routing: 'google/gemini-2.5-flash',
        structuring: 'google/gemini-2.5-flash',
        code: 'anthropic/claude-haiku-4.5',
        analysis: 'anthropic/claude-sonnet-4.5'
      };

      const payload = {
        api_keys: apiKeys,
        model_preferences: currentConfig.model_preferences || defaultPrefs
      };

      console.log('📤 [SAVE_API_KEY] Config sauvegardée (clés masquées)');
      await window.API.saveConfig(payload);

      if (!currentConfig.api_keys) currentConfig.api_keys = {};
      currentConfig.api_keys[`${provider}_key`] = keyValue;

      if (window.showToast) window.showToast('Clé sauvegardée', 'success');
      renderApiKey(provider, keyValue);

    } catch (error) {
      console.error('Erreur sauvegarde clé:', error);
      if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
    }
  }

  function attachEventListeners() {
    const testButtons = document.querySelectorAll('.btn-test-connection');
    testButtons.forEach(btn => {
      btn.addEventListener('click', async () => {
        const provider = btn.dataset.provider;
        await testConnection(provider);
      });
    });

    const btnSaveModels = document.getElementById('btn-save-models');
    if (btnSaveModels) {
      btnSaveModels.addEventListener('click', saveModels);
    }

    const btnSaveChat = document.getElementById('btn-save-chat');
    if (btnSaveChat) {
      btnSaveChat.addEventListener('click', saveChatConfig);
    }

    const btnSaveGlobalContext = document.getElementById('btn-save-global-context');
    if (btnSaveGlobalContext) {
      btnSaveGlobalContext.addEventListener('click', saveGlobalContext);
    }

    const btnExportConfig = document.getElementById('btn-export-config');
    if (btnExportConfig) {
      btnExportConfig.addEventListener('click', exportConfig);
    }

    const btnImportConfig = document.getElementById('btn-import-config');
    if (btnImportConfig) {
      btnImportConfig.addEventListener('click', () => {
        document.getElementById('input-import-config').click();
      });
    }

    const inputImportConfig = document.getElementById('input-import-config');
    if (inputImportConfig) {
      inputImportConfig.addEventListener('change', importConfig);
    }

    const btnResetConfig = document.getElementById('btn-reset-config');
    if (btnResetConfig) {
      btnResetConfig.addEventListener('click', resetConfig);
    }

    const btnBackupDatabase = document.getElementById('btn-backup-database');
    if (btnBackupDatabase) {
      btnBackupDatabase.addEventListener('click', backupDatabase);
    }

    const btnSaveExportPaths = document.getElementById('btn-save-export-paths');
    if (btnSaveExportPaths) {
      btnSaveExportPaths.addEventListener('click', saveExportPaths);
    }
  }

  async function testConnection(provider) {
    const badge = document.getElementById(`badge-${provider}`);
    if (!badge) return;

    badge.innerHTML = '<div class="spinner spinner--sm"></div>';

    try {
      await window.API.testConnection({ provider });
      badge.innerHTML = '<span class="badge badge--success">✅ OK</span>';
      return true;
    } catch (error) {
      console.error(`Erreur test ${provider}:`, error);
      badge.innerHTML = '<span class="badge badge--error">❌ Échec</span>';
      if (window.showToast) window.showToast(`Erreur test ${provider}: ${error.message}`, 'error');
      return false;
    }
  }

  function initializeTestBadges() {
    const providers = ['openrouter', 'anthropic', 'google', 'web_search', 'twelve_data'];
    providers.forEach(provider => {
      const badge = document.getElementById(`badge-${provider}`);
      if (badge) {
        const key = currentConfig.api_keys?.[`${provider}_key`];
        if (!key || key.length < 10) {
          badge.innerHTML = '<span class="badge badge--muted">— Non configuré</span>';
        } else {
          badge.innerHTML = '<span class="badge badge--muted">— Non testé</span>';
        }
      }
    });
  }

  async function testAllProviders() {
    const providers = ['openrouter', 'anthropic', 'google', 'web_search', 'twelve_data'];
    const alert = document.getElementById('openrouter-alert');
    
    // Tester chaque provider qui a une clé configurée
    const results = {};
    for (const provider of providers) {
      const key = currentConfig.api_keys?.[`${provider}_key`];
      const badge = document.getElementById(`badge-${provider}`);
      
      if (!key || key.length < 10) {
        // Clé non configurée
        if (badge) badge.innerHTML = '<span class="badge badge--muted">— Non configuré</span>';
        results[provider] = null;
      } else {
        // Tester la clé
        results[provider] = await testConnection(provider);
      }
    }
    
    // Afficher l'alerte si OpenRouter est KO
    if (alert) {
      if (results.openrouter === false) {
        alert.style.display = 'block';
      } else {
        alert.style.display = 'none';
      }
    }
  }

  function renderModelSelects() {
    const modelTypes = ['routing', 'structuring', 'code', 'analysis'];

    modelTypes.forEach(type => {
      const select = document.getElementById(`model-${type}`);
      if (!select) return;

      select.innerHTML = '';

      let models = [];
      if (availableModels && availableModels[type]) {
        models = availableModels[type];
      }

      if (models.length === 0) {
        select.innerHTML = '<option value="">Aucun modèle disponible</option>';
        return;
      }

      models.forEach(model => {
        const option = document.createElement('option');
        option.value = typeof model === 'string' ? model : model.id || model.name;
        option.textContent = typeof model === 'string' ? model : model.name || model.id;
        select.appendChild(option);
      });

      const currentValue = currentConfig.model_preferences?.[type];
      if (currentValue) {
        select.value = currentValue;
      }
    });
  }

  async function saveModels() {
    const model_preferences = {
      routing: document.getElementById('model-routing')?.value,
      structuring: document.getElementById('model-structuring')?.value,
      code: document.getElementById('model-code')?.value,
      analysis: document.getElementById('model-analysis')?.value
    };

    if (!model_preferences.routing || !model_preferences.structuring || !model_preferences.code || !model_preferences.analysis) {
      if (window.showToast) window.showToast('Veuillez sélectionner tous les modèles', 'warning');
      return;
    }

    try {
      const defaultApiKeys = {
        openrouter_key: '',
        anthropic_key: '',
        google_key: '',
        web_search_key: ''
      };

      const payload = {
        api_keys: currentConfig.api_keys || defaultApiKeys,
        model_preferences: model_preferences
      };

      await window.API.saveConfig(payload);

      currentConfig.model_preferences = model_preferences;

      if (window.showToast) window.showToast('Modèles sauvegardés', 'success');

    } catch (error) {
      console.error('Erreur sauvegarde modèles:', error);
      if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
    }
  }

  // ── Onglet Chat & Présets ──────────────────────────────────────────
  function renderChatConfig() {
    const chatConfig = currentConfig.chat || {};
    
    // Remplir le sélecteur de modèle chat avec tous les modèles disponibles
    const chatModelSelect = document.getElementById('chat-default-model');
    if (chatModelSelect && availableModels) {
      chatModelSelect.innerHTML = '';
      
      // Combiner tous les modèles disponibles
      const allModels = new Set();
      Object.values(availableModels).forEach(models => {
        models.forEach(m => {
          const modelId = typeof m === 'string' ? m : (m.id || m.name);
          allModels.add(modelId);
        });
      });
      
      Array.from(allModels).sort().forEach(modelId => {
        const option = document.createElement('option');
        option.value = modelId;
        option.textContent = modelId;
        chatModelSelect.appendChild(option);
      });
      
      if (chatConfig.model) {
        chatModelSelect.value = chatConfig.model;
      }
    }
    
    // Remplir les autres champs
    const methodoPath = document.getElementById('chat-methodo-path');
    if (methodoPath) {
      methodoPath.value = chatConfig.methodo_path || 'C:\\DEV\\METHODO';
    }
    
    const sessionNote = document.getElementById('chat-session-note');
    if (sessionNote) {
      sessionNote.value = chatConfig.session_note || '';
    }
    
    const systemPrompt = document.getElementById('chat-system-prompt');
    if (systemPrompt) {
      systemPrompt.value = chatConfig.system_prompt_preset || '';
    }
    
    // Charger le contenu du profil utilisateur
    fetch('/api/config/profil_utilisateur')
      .then(r => r.json())
      .then(data => {
        const ta = document.getElementById('chat-profil-utilisateur');
        if (ta) ta.value = data.content || '';
      })
      .catch(() => {});
    
    // Charger le contenu des règles globales
    window.API.getReglesGlobales()
      .then(data => {
        const ta = document.getElementById('chat-regles-globales');
        if (ta) ta.value = data.value || '';
      })
      .catch(() => {});
    
    // Charger les profils modules (Couche 1)
    const modulesMap = {
      'sentinelle_profil': 'profil-sentinelle',
      'atelier_profil': 'profil-atelier',
      'code_profil': 'profil-code',
      'reflexion_profil': 'profil-reflexion',
      'chat_profil': 'profil-chat'
    };
    
    Object.entries(modulesMap).forEach(([moduleKey, textareaId]) => {
      window.API.getCouche1(moduleKey)
        .then(data => {
          const ta = document.getElementById(textareaId);
          if (ta) ta.value = data.value || '';
        })
        .catch(() => {});
    });
  }

  async function saveChatConfig() {
    const chatConfig = {
      model: document.getElementById('chat-default-model')?.value || 'anthropic/claude-sonnet-4.5',
      methodo_path: document.getElementById('chat-methodo-path')?.value || 'C:\\DEV\\METHODO',
      session_note: document.getElementById('chat-session-note')?.value || '',
      system_prompt_preset: document.getElementById('chat-system-prompt')?.value || ''
    };

    try {
      const defaultApiKeys = {
        openrouter_key: '',
        anthropic_key: '',
        google_key: '',
        web_search_key: ''
      };

      const defaultPrefs = {
        routing: 'google/gemini-2.5-flash',
        structuring: 'google/gemini-2.5-flash',
        code: 'anthropic/claude-haiku-4.5',
        analysis: 'anthropic/claude-sonnet-4.5'
      };

      const payload = {
        api_keys: currentConfig.api_keys || defaultApiKeys,
        model_preferences: currentConfig.model_preferences || defaultPrefs,
        chat: chatConfig
      };

      await window.API.saveConfig(payload);

      if (!currentConfig.chat) currentConfig.chat = {};
      currentConfig.chat = chatConfig;
      
      // Sauvegarder le profil utilisateur
      const profilContent = document.getElementById('chat-profil-utilisateur')?.value || '';
      fetch('/api/config/profil_utilisateur', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({value: profilContent})
      })
      .then(r => r.json())
      .then(() => {
        // Silencieux — la confirmation globale de sauvegarde suffit
      })
      .catch(err => console.warn('Erreur sauvegarde profil:', err));
      
      // Sauvegarder les règles globales
      const reglesContent = document.getElementById('chat-regles-globales')?.value || '';
      window.API.saveReglesGlobales(reglesContent)
        .then(() => {
          // Silencieux — la confirmation globale de sauvegarde suffit
        })
        .catch(err => console.warn('Erreur sauvegarde règles:', err));

      if (window.showToast) window.showToast('Config chat sauvegardée', 'success');

    } catch (error) {
      console.error('Erreur sauvegarde chat config:', error);
      if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
    }
  }

  // ── Handlers Profils Modules ──────────────────────────────────────────
  function setupProfilsModulesHandlers() {
    const buttons = document.querySelectorAll('[data-module]');
    buttons.forEach(btn => {
      btn.addEventListener('click', async () => {
        const moduleKey = btn.getAttribute('data-module');
        const textareaId = {
          'sentinelle_profil': 'profil-sentinelle',
          'atelier_profil': 'profil-atelier',
          'code_profil': 'profil-code',
          'reflexion_profil': 'profil-reflexion',
          'chat_profil': 'profil-chat'
        }[moduleKey];
        
        const textarea = document.getElementById(textareaId);
        if (!textarea) return;
        
        try {
          await window.API.saveCouche1(moduleKey, textarea.value);
          if (window.showToast) window.showToast('Profil sauvegardé', 'success');
        } catch (error) {
          console.error('Erreur sauvegarde profil module:', error);
          if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
        }
      });
    });
  }

  // ── Onglet Contexte Global ──────────────────────────────────────────
  async function loadGlobalContext() {
    try {
      const response = await window.API.getGlobalContext();
      const input = document.getElementById('global-context-input');
      if (input && response && response.value !== undefined) {
        input.value = response.value;
      }
    } catch (error) {
      console.error('Erreur chargement global_context:', error);
    }
  }

  async function saveGlobalContext() {
    const input = document.getElementById('global-context-input');
    const statusSpan = document.getElementById('global-context-status');
    
    if (!input) return;

    const value = input.value.trim();

    try {
      await window.API.saveGlobalContext(value);
      
      if (statusSpan) {
        statusSpan.textContent = '✅ Sauvegardé';
        statusSpan.style.color = '#4caf50';
        setTimeout(() => {
          statusSpan.textContent = '';
        }, 3000);
      }
      
      if (window.showToast) window.showToast('Contexte global sauvegardé', 'success');

    } catch (error) {
      console.error('Erreur sauvegarde global_context:', error);
      
      if (statusSpan) {
        statusSpan.textContent = '❌ Erreur';
        statusSpan.style.color = '#f44336';
      }
      
      if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
    }
  }

  // ── Onglet Avancé ──────────────────────────────────────────
  function exportConfig() {
    const exportData = {
      api_keys: currentConfig.api_keys || {},
      model_preferences: currentConfig.model_preferences || {},
      chat: currentConfig.chat || {},
      exported_at: new Date().toISOString(),
      version: '2.0.0'
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `jarvis-config-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);

    if (window.showToast) window.showToast('Configuration exportée', 'success');
  }

  async function importConfig(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const importedData = JSON.parse(text);

      if (!importedData.api_keys || !importedData.model_preferences) {
        throw new Error('Fichier de configuration invalide');
      }

      const payload = {
        api_keys: importedData.api_keys,
        model_preferences: importedData.model_preferences,
        chat: importedData.chat || {}
      };

      await window.API.saveConfig(payload);

      if (window.showToast) window.showToast('Configuration importée, rechargement...', 'success');
      
      setTimeout(() => {
        window.location.reload();
      }, 1000);

    } catch (error) {
      console.error('Erreur import config:', error);
      if (window.showToast) window.showToast('Erreur d\'import: ' + error.message, 'error');
    }

    // Réinitialiser l'input file
    event.target.value = '';
  }

  async function resetConfig() {
    if (!confirm('⚠️ Réinitialiser toute la configuration ?\n\nCette action est irréversible. Toutes les clés API et préférences seront supprimées.')) {
      return;
    }

    try {
      const defaultPayload = {
        api_keys: {
          openrouter_key: '',
          anthropic_key: '',
          google_key: '',
          web_search_key: ''
        },
        model_preferences: {
          routing: 'google/gemini-2.5-flash',
          structuring: 'google/gemini-2.5-flash',
          code: 'anthropic/claude-haiku-4.5',
          analysis: 'anthropic/claude-sonnet-4.5'
        },
        chat: {
          model: 'anthropic/claude-sonnet-4.5',
          methodo_path: 'C:\\DEV\\METHODO',
          session_note: '',
          system_prompt_preset: ''
        }
      };

      await window.API.saveConfig(defaultPayload);

      if (window.showToast) window.showToast('Configuration réinitialisée, rechargement...', 'success');
      
      setTimeout(() => {
        window.location.reload();
      }, 1000);

    } catch (error) {
      console.error('Erreur reset config:', error);
      if (window.showToast) window.showToast('Erreur de réinitialisation', 'error');
    }
  }

  async function backupDatabase() {
    const btn = document.getElementById('btn-backup-database');
    if (!btn) return;

    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ Sauvegarde en cours...';

    try {
      const response = await window.API.backupDatabase();
      
      if (response.success && response.filename) {
        if (window.showToast) {
          window.showToast(`✅ Base de données sauvegardée : ${response.filename}`, 'success');
        }
      } else {
        throw new Error('Réponse invalide du serveur');
      }

    } catch (error) {
      console.error('Erreur backup database:', error);
      if (window.showToast) window.showToast('Erreur lors de la sauvegarde', 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }

  async function loadExportPaths() {
    try {
      const response = await window.API.getClientsExportPath();
      const input = document.getElementById('clients-export-path');
      if (input && response && response.value !== undefined) {
        input.value = response.value;
      }
    } catch (error) {
      console.error('Erreur chargement clients_export_path:', error);
    }
  }

  async function saveExportPaths() {
    const input = document.getElementById('clients-export-path');
    const statusSpan = document.getElementById('export-paths-status');
    
    if (!input) return;

    const value = input.value.trim();

    try {
      await window.API.saveClientsExportPath(value);
      
      if (statusSpan) {
        statusSpan.textContent = '✅ Sauvegardé';
        statusSpan.style.color = '#4caf50';
        setTimeout(() => {
          statusSpan.textContent = '';
        }, 3000);
      }
      
      if (window.showToast) window.showToast('Chemin d\'export sauvegardé', 'success');

    } catch (error) {
      console.error('Erreur sauvegarde clients_export_path:', error);
      
      if (statusSpan) {
        statusSpan.textContent = '❌ Erreur';
        statusSpan.style.color = '#f44336';
      }
      
      if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
    }
  }
})();
