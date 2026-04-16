async function fetchAPI(endpoint, method = 'GET', body = null) {
  const options = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) options.body = JSON.stringify(body);
  
  try {
    const response = await fetch(`/api${endpoint}`, options);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    showToast(`Erreur: ${error.message}`, 'error');
    throw error;
  }
}

function renderMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>');
}

function renderDiff(diffText) {
  if (!diffText) return '';
  const lines = diffText.split('\n');
  let html = '<pre style="background: var(--bg-input); padding: 1rem; border-radius: 6px; overflow-x: auto;">';
  
  lines.forEach(line => {
    if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
      html += `<div class="diff-line-header">${line}</div>`;
    } else if (line.startsWith('+')) {
      html += `<div class="diff-line-add">${line}</div>`;
    } else if (line.startsWith('-')) {
      html += `<div class="diff-line-remove">${line}</div>`;
    } else {
      html += `<div style="color: var(--text-muted);">${line}</div>`;
    }
  });
  
  html += '</pre>';
  return html;
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.style.background = type === 'error' ? 'var(--danger)' : 'var(--success)';
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => toast.remove(), 3000);
}

function showModal(title, content, onConfirm) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal">
      <h2 style="margin-bottom: 1rem;">${title}</h2>
      <div style="margin-bottom: 1.5rem;">${content}</div>
      <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
        <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">Annuler</button>
        <button class="btn btn-success" id="modal-confirm">Confirmer</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  document.getElementById('modal-confirm').onclick = () => {
    onConfirm();
    overlay.remove();
  };
}
