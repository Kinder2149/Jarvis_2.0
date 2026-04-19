window.showToast = (message, type = 'success') => {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toasts = container.querySelectorAll('.toast');
  if (toasts.length >= 3) {
    toasts[0].remove();
  }

  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px">
      <span>${message}</span>
      <button onclick="this.parentElement.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1.2rem;line-height:1">×</button>
    </div>
  `;
  
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 200);
  }, 4000);
};

window.showModal = (title, bodyHTML, actions) => {
  const existing = document.querySelector('.modal-overlay');
  if (existing) existing.remove();

  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  
  let actionsHTML = '';
  actions.forEach(action => {
    const btnClass = action.type === 'primary' ? 'btn-primary' : 
                     action.type === 'danger' ? 'btn-danger' : 'btn-secondary';
    actionsHTML += `<button class="${btnClass}" data-action-id="${actions.indexOf(action)}">${action.label}</button>`;
  });

  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h3 style="margin:0;color:var(--text-primary)">${title}</h3>
        <button class="btn-icon" onclick="window.closeModal()">×</button>
      </div>
      <div class="modal-body">${bodyHTML}</div>
      <div class="modal-actions">${actionsHTML}</div>
    </div>
  `;

  document.body.appendChild(overlay);

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) window.closeModal();
  });

  overlay.querySelectorAll('[data-action-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      const actionId = parseInt(btn.dataset.actionId);
      actions[actionId].onClick();
    });
  });
};

window.closeModal = () => {
  const overlay = document.querySelector('.modal-overlay');
  if (overlay) overlay.remove();
};

window.statusBadge = (status) => {
  const badges = {
    'PENDING': '<span class="badge badge--pending">En attente</span>',
    'RUNNING': '<span class="badge badge--running">⏳ En cours</span>',
    'COMPLETED': '<span class="badge badge--success">✅ Terminé</span>',
    'ERROR': '<span class="badge badge--error">❌ Erreur</span>',
    'ABORTED': '<span class="badge badge--pending">Abandonné</span>',
    'WAITING_VALIDATION': '<span class="badge badge--waiting">⏸️ Validation</span>'
  };
  return badges[status] || `<span class="badge">${status}</span>`;
};

window.costBadge = (usd) => {
  if (usd == null) return '';
  return `<span class="badge badge--cost">${window.formatCost(usd)}</span>`;
};
