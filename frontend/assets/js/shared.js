window.EventBus = {
  emit(name, data) { 
    document.dispatchEvent(new CustomEvent(`jarvis:${name}`, { detail: data })); 
  },
  on(name, cb) { 
    document.addEventListener(`jarvis:${name}`, e => cb(e.detail)); 
  }
};

window.getURLParam = (name) => new URLSearchParams(window.location.search).get(name);

window.escapeHtml = function(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
};
window._esc = window.escapeHtml;

window.formatDate = (isoString) => {
  if (!isoString) return '';
  const d = new Date(isoString);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today); 
  yesterday.setDate(today.getDate() - 1);
  const itemDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const hhmm = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  if (itemDay.getTime() === today.getTime()) return `Aujourd'hui ${hhmm}`;
  if (itemDay.getTime() === yesterday.getTime()) return 'Hier';
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
};

window.formatCost = (usd) => usd != null ? `$${Number(usd).toFixed(3)}` : '';

window.renderMarkdown = (text) => {
  if (!text) return '';
  
  let result = text
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>');
  
  const lines = result.split('\n');
  const output = [];
  let inList = false;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const isListItem = /^- (.+)$/.test(line);
    
    if (isListItem) {
      if (!inList) {
        output.push('<ul>');
        inList = true;
      }
      output.push(line.replace(/^- (.+)$/, '<li>$1</li>'));
    } else {
      if (inList) {
        output.push('</ul>');
        inList = false;
      }
      output.push(line);
    }
  }
  
  if (inList) {
    output.push('</ul>');
  }
  
  return output.join('<br>');
};

window.renderDiff = (diffText) => {
  if (!diffText) return '';
  const lines = diffText.split('\n');
  let html = '<div class="diff-viewer">';
  lines.forEach(line => {
    const escaped = line.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
      html += `<div class="diff-line-header">${escaped}</div>`;
    } else if (line.startsWith('+')) {
      html += `<div class="diff-line-add">${escaped}</div>`;
    } else if (line.startsWith('-')) {
      html += `<div class="diff-line-remove">${escaped}</div>`;
    } else {
      html += `<div style="color:var(--text-muted)">${escaped}</div>`;
    }
  });
  html += '</div>';
  return html;
};

window.initLayout = async () => {
  if (typeof window.initSidebar === 'function') await window.initSidebar();
  const pid = window.getURLParam('project_id') || window.getURLParam('id');
  if (pid) window.currentProjectId = parseInt(pid);
};

document.addEventListener('DOMContentLoaded', () => window.initLayout());
