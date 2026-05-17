(function() {
  let conversations = [];

  document.addEventListener('DOMContentLoaded', async () => {
    await loadConversations();
    attachEventListeners();
  });

  async function loadConversations() {
    try {
      conversations = await window.API.getConversations();
      renderConversations();
    } catch (error) {
      console.error('Erreur chargement conversations:', error);
      const container = document.getElementById('conversations-list');
      container.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center">Erreur de chargement</p>';
    }
  }

  function renderConversations() {
    const container = document.getElementById('conversations-list');
    const emptyState = document.getElementById('empty-state');

    if (!conversations || conversations.length === 0) {
      container.style.display = 'none';
      emptyState.style.display = 'flex';
      return;
    }

    container.style.display = 'grid';
    emptyState.style.display = 'none';

    const formatDate = window.formatDate || ((d) => new Date(d).toLocaleString('fr-FR'));
    
    conversations.sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at));

    const html = conversations.map(conv => {
      const messageCount = conv.message_count || 0;
      const lastUpdate = formatDate(conv.updated_at || conv.created_at);
      const projectBadge = conv.project_id ? `<span class="conv-badge">📁 Projet</span>` : '';
      const folderBadge = conv.folder_path ? `<span class="conv-badge">📂 Dossier lié</span>` : '';
      const internetBadge = conv.internet_access ? `<span class="conv-badge">🌐 Internet</span>` : '';

      return `
        <div class="conversation-card" data-id="${conv.id}">
          <div class="conversation-card-header">
            <h3 class="conversation-card-title">${escapeHtml(conv.title || 'Conversation sans titre')}</h3>
            <button class="btn-icon btn-danger-icon btn-delete-conv" data-id="${conv.id}" title="Supprimer">🗑️</button>
          </div>
          <div class="conversation-card-meta">
            <span class="conv-meta-item">💬 ${messageCount} message${messageCount > 1 ? 's' : ''}</span>
            <span class="conv-meta-item">🕒 ${lastUpdate}</span>
          </div>
          <div class="conversation-card-badges">
            ${projectBadge}
            ${folderBadge}
            ${internetBadge}
          </div>
        </div>
      `;
    }).join('');

    container.innerHTML = html;

    document.querySelectorAll('.conversation-card').forEach(card => {
      card.addEventListener('click', (e) => {
        if (!e.target.closest('.btn-delete-conv')) {
          const id = card.dataset.id;
          window.location.href = `chat.html?id=${id}`;
        }
      });
    });

    document.querySelectorAll('.btn-delete-conv').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        await handleDeleteConversation(id);
      });
    });
  }

  const escapeHtml = window.escapeHtml;

  function attachEventListeners() {
    document.getElementById('btn-new-conversation').addEventListener('click', handleNewConversation);
    document.getElementById('btn-new-conversation-empty')?.addEventListener('click', handleNewConversation);
  }

  async function handleNewConversation() {
    try {
      const conv = await window.API.createConversation({
        title: 'Nouvelle conversation',
        project_id: null
      });
      
      if (window.showToast) window.showToast('Conversation créée', 'success');
      window.location.href = `chat.html?id=${conv.id}`;
    } catch (error) {
      console.error('Erreur création conversation:', error);
      if (window.showToast) window.showToast('Erreur de création', 'error');
    }
  }

  async function handleDeleteConversation(id) {
    if (!window.showModal) {
      if (!confirm('Supprimer cette conversation ?')) return;
      await deleteConversation(id);
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
            await deleteConversation(id);
            if (window.closeModal) window.closeModal();
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

  async function deleteConversation(id) {
    try {
      await window.API.deleteConversation(id);
      if (window.showToast) window.showToast('Conversation supprimée', 'success');
      conversations = conversations.filter(c => c.id !== parseInt(id));
      renderConversations();
    } catch (error) {
      console.error('Erreur suppression:', error);
      if (window.showToast) window.showToast('Erreur suppression', 'error');
    }
  }
})();
