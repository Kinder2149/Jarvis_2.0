/* ═══════════════════════════════════════════════════════════════════════════
   BOARD.JS — Utilitaires JavaScript partagés pour tous les boards JARVIS
   ═══════════════════════════════════════════════════════════════════════════
   
   Fonctions disponibles globalement (pas de module)
*/

/**
 * Temps relatif en français depuis une date
 * @param {string} dateStr - Date ISO (format SQLite sans 'Z')
 * @returns {string} Temps relatif formaté
 */
function ago(dateStr) {
  if (!dateStr) return '';
  
  try {
    // Ajouter 'Z' si pas de timezone
    let isoStr = dateStr;
    if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
      isoStr = dateStr + 'Z';
    }
    
    const date = new Date(isoStr);
    if (isNaN(date.getTime())) return '';
    
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    
    if (diffSec < 60) {
      return "à l'instant";
    } else if (diffSec < 3600) {
      const min = Math.floor(diffSec / 60);
      return `il y a ${min}min`;
    } else if (diffSec < 86400) {
      const h = Math.floor(diffSec / 3600);
      return `il y a ${h}h`;
    } else if (diffSec < 172800) {
      return 'hier';
    } else {
      return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }
  } catch (e) {
    return '';
  }
}

/**
 * Génère le HTML d'un badge de statut
 * @param {string} text - Texte du badge
 * @param {string} type - Type de badge (running, waiting, completed, etc.)
 * @returns {string} HTML du badge
 */
function badge(text, type) {
  const typeNorm = String(type || '').toLowerCase().replace(/_/g, '');
  
  let variant = 'neutral';
  
  if (['running', 'encours'].includes(typeNorm)) {
    variant = 'running';
  } else if (['waiting', 'waitingvalidation', 'enfigement'].includes(typeNorm)) {
    variant = 'waiting';
  } else if (['completed', 'figee', 'done'].includes(typeNorm)) {
    variant = 'completed';
  } else if (['failed', 'error'].includes(typeNorm)) {
    variant = 'failed';
  } else if (['aborted', 'abandonnee'].includes(typeNorm)) {
    variant = 'aborted';
  } else if (['ouverte', 'created'].includes(typeNorm)) {
    variant = 'ouverte';
  }
  
  return `<span class="board-badge board-badge--${variant}">${_esc(text)}</span>`;
}

/**
 * Génère le HTML d'une carte statistique
 * @param {number|string} val - Valeur à afficher
 * @param {string} lbl - Label de la statistique
 * @param {Object} opts - Options (highlight: boolean, color: string)
 * @returns {string} HTML de la carte
 */
function statCard(val, lbl, opts = {}) {
  const highlightClass = opts.highlight ? ' board-stat-card--highlight' : '';
  const colorStyle = opts.color ? ` style="color:${opts.color}"` : '';
  
  return `
    <div class="board-stat-card${highlightClass}">
      <div class="board-stat-val"${colorStyle}>${_esc(val)}</div>
      <div class="board-stat-lbl">${_esc(lbl)}</div>
    </div>
  `;
}

/**
 * Génère le HTML d'un état vide
 * @param {string} message - Message principal
 * @param {string} hint - Texte d'aide secondaire (optionnel)
 * @returns {string} HTML de l'état vide
 */
function emptyState(message, hint = '') {
  return `
    <div class="board-empty">
      <div class="board-empty-icon">⊘</div>
      <div class="board-empty-msg">${_esc(message)}</div>
      ${hint ? `<div class="board-empty-hint">${_esc(hint)}</div>` : ''}
    </div>
  `;
}

/**
 * Génère le HTML d'une barre de progression
 * @param {number} current - Étape actuelle
 * @param {number} total - Nombre total d'étapes
 * @param {string} label - Label personnalisé (optionnel)
 * @returns {string} HTML de la barre + label
 */
function progressBar(current, total, label = '') {
  const percent = total > 0 ? Math.round((current / total) * 100) : 0;
  const defaultLabel = `${current}/${total} étapes`;
  const finalLabel = label || defaultLabel;
  
  return `
    <div class="board-progress">
      <div class="board-progress-bar" style="width:${percent}%"></div>
    </div>
    <div class="board-progress-label">${_esc(finalLabel)}</div>
  `;
}
