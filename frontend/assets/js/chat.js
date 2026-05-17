(function() {
  let conversationId = null;
  let projectId = null;
  let conversation = null;
  let isSending = false;
  let attachedImage = null;

  document.addEventListener('DOMContentLoaded', async () => {
    conversationId = window.getURLParam ? window.getURLParam('id') : new URLSearchParams(location.search).get('id');
    projectId = window.getURLParam ? window.getURLParam('project_id') : new URLSearchParams(location.search).get('project_id');

    if (!conversationId) {
      document.getElementById('page-chat').innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center">Conversation non trouvée</p>';
      return;
    }

    await loadConversation();
    await loadAvailableModels();
    attachEventListeners();
  });

  async function loadAvailableModels() {
    try {
      const models = await window.API.getAvailableModels();
      const select = document.getElementById('chat-model-select');
      if (!select || !models) return;
      
      let modelList = [];
      if (Array.isArray(models)) {
        modelList = models;
      } else {
        const seen = new Set();
        Object.values(models).forEach(list => {
          if (Array.isArray(list)) {
            list.forEach(m => {
              const id = typeof m === 'string' ? m : m.id || m.model_id;
              if (id && !seen.has(id)) { seen.add(id); modelList.push(id); }
            });
          }
        });
      }
      
      const savedModel = localStorage.getItem(`chat_model_${conversationId}`) || '';
      
      modelList.forEach(model => {
        const id = typeof model === 'string' ? model : model.id || model.model_id;
        const label = id.split('/').pop();
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = label;
        if (id === savedModel) opt.selected = true;
        select.appendChild(opt);
      });
      
      select.addEventListener('change', () => {
        localStorage.setItem(`chat_model_${conversationId}`, select.value);
      });
      
    } catch (e) {
      console.warn('Modèles non disponibles:', e);
    }
  }

  async function loadConversation() {
    try {
      conversation = await window.API.getConversation(conversationId);
      
      document.getElementById('chat-title').textContent = conversation.title || 'Conversation sans titre';

      // Charger internet_access
      const toggleInternet = document.getElementById('toggle-internet');
      if (toggleInternet) {
        toggleInternet.checked = conversation.internet_access || false;
      }

      // Charger context_summary
      const summaryTextarea = document.getElementById('summary-textarea');
      if (summaryTextarea) {
        summaryTextarea.value = conversation.context_summary || '';
        // Auto-affichage si résumé non vide
        if (conversation.context_summary && conversation.context_summary.trim()) {
          document.getElementById('panel-summary').style.display = 'block';
        }
      }

      // Charger model
      const modelSelect = document.getElementById('chat-model-select');
      if (modelSelect && conversation.model) {
        modelSelect.value = conversation.model;
      }

      // Charger folder_path
      const folderInput = document.getElementById('folder-path-input');
      if (folderInput) {
        folderInput.value = conversation.folder_path || '';
      }

      // Badge dossier si project_id défini
      if (conversation.project_id || projectId) {
        const pid = conversation.project_id || projectId;
        try {
          const project = await window.API.getProject(pid);
          const badge = document.getElementById('chat-dossier-badge');
          badge.innerHTML = `<a class="project-badge" href="dossier.html?id=${project.id}">📁 ${project.name}</a>`;
        } catch (e) {
          console.warn('Dossier non trouvé:', e);
        }
      }

      renderMessages();
      scrollToBottom();

    } catch (error) {
      console.error('Erreur chargement conversation:', error);
      if (window.showToast) window.showToast('Erreur de chargement', 'error');
    }
  }

  function renderMessages() {
    const container = document.getElementById('chat-messages');
    
    if (!conversation.messages || conversation.messages.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem">Aucun message</p>';
      return;
    }

    container.innerHTML = conversation.messages.map(msg => renderMessage(msg)).join('');
  }

  function renderMessage(msg) {
    const formatDate = window.formatDate || ((d) => new Date(d).toLocaleString('fr-FR'));
    const renderMarkdown = window.renderMarkdown || ((text) => text);

    if (msg.role === 'user') {
      const attachmentBadge = msg.attachment_filename ? `<span class="msg-attachment-badge">📎 ${escapeHtml(msg.attachment_filename)}</span>` : '';
      return `
        <div class="message message--user">
          <div class="message-content">${escapeHtml(msg.content)}</div>
          ${attachmentBadge}
          <div class="message-time">${formatDate(msg.created_at)}</div>
        </div>
      `;
    } else {
      const modelBadge = msg.model ? `<span class="msg-model">via ${msg.model}</span>` : '';
      return `
        <div class="message message--assistant">
          <div class="message-avatar">⚡</div>
          <div class="message-body">
            <div class="message-content">${renderMarkdown(msg.content)}</div>
            <div class="message-footer">
              <div class="message-time">${formatDate(msg.created_at)}</div>
              ${modelBadge}
            </div>
          </div>
        </div>
      `;
    }
  }

  const escapeHtml = window.escapeHtml;

  function attachEventListeners() {
    const textarea = document.getElementById('chat-input');
    const btnSend = document.getElementById('btn-send');
    const btnDelete = document.getElementById('btn-delete-conversation');

    // Créer les éléments d'attachement
    const inputWrapper = document.querySelector('.chat-input-wrapper');
    const attachBtn = document.createElement('button');
    attachBtn.id = 'attach-btn';
    attachBtn.className = 'attach-btn';
    attachBtn.title = 'Joindre une image';
    attachBtn.textContent = '📎';
    attachBtn.type = 'button';

    const attachInput = document.createElement('input');
    attachInput.type = 'file';
    attachInput.id = 'attach-input';
    attachInput.accept = 'image/png,image/jpeg,image/webp';
    attachInput.style.display = 'none';

    const attachPreview = document.createElement('div');
    attachPreview.id = 'attach-preview';
    attachPreview.className = 'attach-preview';
    attachPreview.style.display = 'none';
    attachPreview.innerHTML = `
      <span id="attach-filename" class="attach-filename"></span>
      <button id="attach-clear" class="attach-clear" type="button">✕</button>
    `;

    inputWrapper.insertBefore(attachBtn, btnSend);
    inputWrapper.appendChild(attachInput);
    inputWrapper.parentElement.insertBefore(attachPreview, inputWrapper.nextSibling);

    btnSend.addEventListener('click', handleSendMessage);

    // Gestion attachement image
    attachBtn.addEventListener('click', () => {
      attachInput.click();
    });

    attachInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        const dataUrl = event.target.result;
        const base64 = dataUrl.split(',')[1];
        attachedImage = {
          base64: base64,
          filename: file.name
        };
        document.getElementById('attach-filename').textContent = file.name;
        document.getElementById('attach-preview').style.display = 'flex';
      };
      reader.readAsDataURL(file);
    });

    document.addEventListener('click', (e) => {
      if (e.target && e.target.id === 'attach-clear') {
        attachedImage = null;
        document.getElementById('attach-preview').style.display = 'none';
        document.getElementById('attach-input').value = '';
      }
    });

    textarea.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        handleSendMessage();
      }
    });

    textarea.addEventListener('input', () => {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    });

    btnDelete.addEventListener('click', handleDeleteConversation);

    // Toggle Internet
    document.getElementById('toggle-internet').addEventListener('change', async (e) => {
      try {
        await window.API.patch(`/api/chat/conversations/${conversationId}`, {
          internet_access: e.target.checked
        });
        if (window.showToast) window.showToast(e.target.checked ? 'Accès internet activé' : 'Accès internet désactivé', 'info');
      } catch (error) {
        console.error('Erreur sauvegarde internet_access:', error);
        if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
      }
    });

    // Sauvegarde résumé
    document.getElementById('btn-save-summary').addEventListener('click', async () => {
      try {
        const summary = document.getElementById('summary-textarea').value;
        await window.API.patch(`/api/chat/conversations/${conversationId}`, { context_summary: summary });
        if (window.showToast) window.showToast('Résumé sauvegardé', 'success');
      } catch (error) {
        console.error('Erreur sauvegarde résumé:', error);
        if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
      }
    });

    // Régénérer résumé
    document.getElementById('btn-regenerate-summary').addEventListener('click', async () => {
      const btn = document.getElementById('btn-regenerate-summary');
      btn.textContent = '⏳';
      btn.disabled = true;
      try {
        const result = await window.API.updateConvSummary(conversationId);
        document.getElementById('summary-textarea').value = result.summary || '';
        if (window.showToast) window.showToast('Résumé mis à jour', 'success');
      } catch (error) {
        console.error('Erreur génération résumé:', error);
        if (window.showToast) window.showToast('Erreur lors de la génération', 'error');
      } finally {
        btn.textContent = '♻️ Régénérer';
        btn.disabled = false;
      }
    });

    // Panneaux collapsibles (fermer l'un si l'autre s'ouvre)
    document.getElementById('btn-toggle-summary').addEventListener('click', () => {
      const panelSummary = document.getElementById('panel-summary');
      const panelFolder = document.getElementById('panel-folder');
      if (panelSummary.style.display === 'none') {
        panelSummary.style.display = 'block';
        panelFolder.style.display = 'none';
      } else {
        panelSummary.style.display = 'none';
      }
    });

    document.getElementById('btn-toggle-folder').addEventListener('click', () => {
      const panelSummary = document.getElementById('panel-summary');
      const panelFolder = document.getElementById('panel-folder');
      if (panelFolder.style.display === 'none') {
        panelFolder.style.display = 'block';
        panelSummary.style.display = 'none';
        loadFolderFiles();
      } else {
        panelFolder.style.display = 'none';
      }
    });

    // Dossier Windows
    document.getElementById('btn-save-folder').addEventListener('click', async () => {
      try {
        const path = document.getElementById('folder-path-input').value.trim();
        await window.API.patch(`/api/chat/conversations/${conversationId}`, { folder_path: path });
        if (window.showToast) window.showToast('Dossier lié', 'success');
        loadFolderFiles();
      } catch (error) {
        console.error('Erreur sauvegarde dossier:', error);
        if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
      }
    });

    // Modèle — sauvegarder au changement
    document.getElementById('chat-model-select').addEventListener('change', async (e) => {
      try {
        await window.API.patch(`/api/chat/conversations/${conversationId}`, { model: e.target.value });
      } catch (error) {
        console.error('Erreur sauvegarde modèle:', error);
      }
    });
  }

  async function loadFolderFiles() {
    const path = document.getElementById('folder-path-input').value.trim();
    if (!path) return;
    try {
      const result = await window.API.get(`/api/files/list?path=${encodeURIComponent(path)}`);
      const container = document.getElementById('folder-files-list');
      if (result.files && result.files.length > 0) {
        container.innerHTML = result.files.slice(0, 30).map(f => 
          `<span class="file-chip">📄 ${f.path}</span>` 
        ).join('');
      } else {
        container.innerHTML = '<span class="text-muted">Dossier vide ou inaccessible</span>';
      }
    } catch (error) {
      console.error('Erreur lecture dossier:', error);
      document.getElementById('folder-files-list').innerHTML = '<span class="text-muted">Impossible de lire le dossier</span>';
    }
  }

  async function handleSendMessage() {
    if (isSending) return;

    const textarea = document.getElementById('chat-input');
    const content = textarea.value.trim();

    if (!content) return;

    isSending = true;
    const btnSend = document.getElementById('btn-send');
    const btnSendText = document.getElementById('btn-send-text');
    const btnSendSpinner = document.getElementById('btn-send-spinner');

    textarea.disabled = true;
    btnSend.disabled = true;
    btnSendText.style.display = 'none';
    btnSendSpinner.style.display = 'block';

    const userMessage = {
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    };
    conversation.messages.push(userMessage);

    const container = document.getElementById('chat-messages');
    container.innerHTML += renderMessage(userMessage);
    scrollToBottom();

    const loadingMessage = `
      <div class="message message--assistant message--loading" id="loading-message">
        <div class="message-avatar">⚡</div>
        <div class="message-body"><div class="spinner"></div></div>
      </div>
    `;
    container.innerHTML += loadingMessage;
    scrollToBottom();

    textarea.value = '';
    textarea.style.height = 'auto';

    try {
      const modelSelect = document.getElementById('chat-model-select');
      const selectedModel = modelSelect ? modelSelect.value : null;
      
      const body = { content: content, model: selectedModel || null };
      if (attachedImage) {
        body.attachment_base64 = attachedImage.base64;
        body.attachment_filename = attachedImage.filename;
      }
      
      const response = await window.API.post(`/api/chat/conversations/${conversationId}/messages`, body);

      const loadingEl = document.getElementById('loading-message');
      if (loadingEl) loadingEl.remove();

      const assistantContent = response.assistant_message?.content || response.response;
      if (assistantContent) {
        const assistantMessage = {
          role: 'assistant',
          content: assistantContent,
          created_at: new Date().toISOString(),
          model: selectedModel || response.assistant_message?.model || null
        };
        conversation.messages.push(assistantMessage);
        container.innerHTML += renderMessage(assistantMessage);
        scrollToBottom();
      }
      
      // Reset attachement après envoi réussi
      if (attachedImage) {
        attachedImage = null;
        document.getElementById('attach-preview').style.display = 'none';
        document.getElementById('attach-input').value = '';
      }

    } catch (error) {
      console.error('Erreur envoi message:', error);
      const loadingEl = document.getElementById('loading-message');
      if (loadingEl) loadingEl.remove();
      if (window.showToast) window.showToast('Erreur envoi message', 'error');
    } finally {
      isSending = false;
      textarea.disabled = false;
      btnSend.disabled = false;
      btnSendText.style.display = 'block';
      btnSendSpinner.style.display = 'none';
      textarea.focus();
    }
  }

  async function handleDeleteConversation() {
    if (!window.showModal) {
      if (!confirm('Supprimer cette conversation ?')) return;
      await deleteConversation();
      return;
    }

    window.showModal(
      'Supprimer cette conversation ?',
      'Cette conversation sera supprimée définitivement.',
      [
        {
          label: 'Supprimer',
          type: 'danger',
          onClick: async () => {
            await deleteConversation();
          }
        },
        {
          label: 'Annuler',
          type: 'secondary',
          onClick: () => {
            if (window.closeModal) window.closeModal();
          }
        }
      ]
    );
  }

  async function deleteConversation() {
    try {
      await window.API.deleteConversation(conversationId);
      if (window.showToast) window.showToast('Conversation supprimée');
      location.href = 'index.html';
    } catch (error) {
      console.error('Erreur suppression:', error);
      if (window.showToast) window.showToast('Erreur suppression', 'error');
    }
  }

  function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
  }
})();
