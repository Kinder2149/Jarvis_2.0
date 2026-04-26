/**
 * ============================================================================
 * ADMIN.JS — Espace Gérant Pointe de Rêve
 * ============================================================================
 * Gestion complète : Login | Dashboard | Réservations | Ardoise | Événements
 * ============================================================================
 */

// ============================================================================
// CONFIGURATION & CONSTANTES
// ============================================================================

const MOT_DE_PASSE_ADMIN = 'admin';

const DEMO_RESERVATIONS = [
  {
    id: 'demo-1',
    prenom: 'Marie D.',
    telephone: '06 12 34 56 78',
    date: offsetDate(1),
    service: 'diner',
    couverts: '2',
    message: 'Anniversaire de mariage, si possible une table en retrait',
    statut: 'En attente',
    source: 'demo'
  },
  {
    id: 'demo-2',
    prenom: 'Thomas B.',
    telephone: '07 65 43 21 09',
    date: offsetDate(1),
    service: 'dejeuner',
    couverts: '4',
    message: '',
    statut: 'Confirmée',
    source: 'demo'
  },
  {
    id: 'demo-3',
    prenom: 'Sophie M.',
    telephone: '06 98 76 54 32',
    date: offsetDate(2),
    service: 'diner',
    couverts: '6',
    message: 'Une personne allergique aux crustacés',
    statut: 'En attente',
    source: 'demo'
  },
  {
    id: 'demo-4',
    prenom: 'Laurent F.',
    telephone: '07 11 22 33 44',
    date: offsetDate(3),
    service: 'dejeuner',
    couverts: '2',
    message: 'Menu dégustation si disponible',
    statut: 'Confirmée',
    source: 'demo'
  },
  {
    id: 'demo-5',
    prenom: 'Isabelle R.',
    telephone: '06 55 44 33 22',
    date: offsetDate(4),
    service: 'diner',
    couverts: '8',
    message: 'Repas d\'entreprise',
    statut: 'Annulée',
    source: 'demo'
  }
];

const DEMO_ARDOISE = {
  disponible: true,
  entree: {
    nom: 'Velouté de butternut, crème fraîche',
    prix: '8,00 €'
  },
  plat: {
    nom: 'Magret de canard, jus de cerise',
    prix: '21,00 €',
    note: 'Cuisson selon votre goût'
  },
  dessert: {
    nom: 'Fondant au chocolat, glace vanille',
    prix: '7,00 €'
  },
  formule: {
    active: true,
    prix: '31,00 €',
    label: 'Entrée + Plat + Dessert'
  }
};

const DEMO_EVENTS = [
  {
    id: 'event-1',
    titre: 'Soirée Jazz',
    date: offsetDate(7),
    description: 'Ambiance jazz live avec le trio Laurent Delbecque. Réservation obligatoire.',
    visible: true
  },
  {
    id: 'event-2',
    titre: 'Menu dégustation spécial',
    date: offsetDate(14),
    description: 'Menu 5 services avec vins d\'accompagnement. Sur réservation.',
    visible: true
  }
];

const DEMO_MENU = {
  categories: [
    {
      id: 'cat-1',
      nom: 'Entrées',
      ordre: 1,
      plats: [
        { id: 'plat-1', nom: 'Terrine de foie gras maison', prix: '14,00 €', description: 'Chutney de figues, brioche toastée', disponible: true },
        { id: 'plat-2', nom: 'Carpaccio de saumon', prix: '13,00 €', description: 'Citron, câpres, pain toasté', disponible: true },
        { id: 'plat-3', nom: 'Salade périgourdine', prix: '11,00 €', description: 'Gésiers, foie gras, noix', disponible: true }
      ]
    },
    {
      id: 'cat-2',
      nom: 'Plats',
      ordre: 2,
      plats: [
        { id: 'plat-4', nom: 'Filet de bœuf, sauce poivre', prix: '28,00 €', description: 'Avec frites maison', disponible: true },
        { id: 'plat-5', nom: 'Sole meunière', prix: '26,00 €', description: 'Beurre noisette, citron', disponible: true },
        { id: 'plat-6', nom: 'Coq au vin', prix: '24,00 €', description: 'Champignons, oignons, lardons', disponible: true },
        { id: 'plat-7', nom: 'Magret de canard', prix: '25,00 €', description: 'Sauce aux cerises, légumes de saison', disponible: true }
      ]
    },
    {
      id: 'cat-3',
      nom: 'Desserts',
      ordre: 3,
      plats: [
        { id: 'plat-8', nom: 'Tarte tatin', prix: '7,00 €', description: 'Glace vanille', disponible: true },
        { id: 'plat-9', nom: 'Fondant au chocolat', prix: '8,00 €', description: 'Glace vanille', disponible: true },
        { id: 'plat-10', nom: 'Panna cotta', prix: '7,00 €', description: 'Coulis de fraise', disponible: true }
      ]
    }
  ]
};

// ============================================================================
// UTILITAIRES
// ============================================================================

/**
 * Calcule une date future/passée par rapport à aujourd'hui
 * @param {number} offset - Nombre de jours (0 = aujourd'hui, 1 = demain)
 * @returns {string} Date au format ISO (YYYY-MM-DD)
 */
function offsetDate(offset) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return date.toISOString().split('T')[0];
}

/**
 * Formate une date ISO en français
 * @param {string} dateStr - Date ISO (YYYY-MM-DD)
 * @returns {string} Date formatée
 */
function formatDate(dateStr) {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('fr-FR', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });
}

/**
 * Formate une date ISO en jour court + numéro
 * @param {string} dateStr - Date ISO
 * @returns {object} { day, date }
 */
function getShortDate(dateStr) {
  const date = new Date(dateStr + 'T00:00:00');
  const dayName = date.toLocaleDateString('fr-FR', { weekday: 'short' }).toUpperCase();
  return {
    day: dayName,
    date: date.getDate()
  };
}

/**
 * Parse JSON en toute sécurité
 * @param {string} rawValue - Valeur JSON
 * @param {*} fallbackValue - Valeur par défaut
 * @returns {*} Valeur parsée ou fallback
 */
function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try {
    return JSON.parse(rawValue);
  } catch (e) {
    console.error('Parse error:', e);
    return fallbackValue;
  }
}

/**
 * Affiche une notification temporaire
 * @param {string} message - Message à afficher
 * @param {string} type - Type de notification (success, error, warning, info)
 * @param {HTMLElement} container - Conteneur cible
 * @param {number} duration - Durée en ms
 */
function showNotification(message, type = 'success', container = document.body, duration = 4000) {
  const notification = document.createElement('div');
  notification.className = `feedback-message visible feedback-${type}`;
  notification.textContent = message;
  
  if (container.classList && container.classList.contains('feedback-message')) {
    container.className = `feedback-message visible feedback-${type}`;
    container.textContent = message;
  } else {
    container.appendChild(notification);
  }

  if (duration > 0) {
    setTimeout(() => {
      notification.remove?.() || (container.innerHTML = '');
    }, duration);
  }
}

/**
 * Initialise les données démo si absent du localStorage
 */
function ensureInitialData() {
  const existing = localStorage.getItem('DEMO_reservations');
  if (!existing) {
    localStorage.setItem('DEMO_reservations', JSON.stringify(DEMO_RESERVATIONS));
    localStorage.setItem('DEMO_ardoise', JSON.stringify(DEMO_ARDOISE));
    localStorage.setItem('DEMO_events', JSON.stringify(DEMO_EVENTS));
    localStorage.setItem('DEMO_menu', JSON.stringify(DEMO_MENU));
  }
}

// ============================================================================
// GESTION LOGIN
// ============================================================================

function initLogin() {
  const loginScreen = document.getElementById('loginScreen');
  const passwordInput = document.getElementById('passwordInput');
  const passwordToggle = document.getElementById('passwordToggle');
  const loginBtn = document.getElementById('loginBtn');
  const loginError = document.getElementById('loginError');

  // Toggle affichage mot de passe
  passwordToggle.addEventListener('click', (e) => {
    e.preventDefault();
    const isPassword = passwordInput.type === 'password';
    passwordInput.type = isPassword ? 'text' : 'password';
    passwordToggle.textContent = isPassword ? '🙈' : '👁';
  });

  // Soumettre
  loginBtn.addEventListener('click', () => {
    const password = passwordInput.value.trim();
    
    if (password === MOT_DE_PASSE_ADMIN) {
      // Succès
      sessionStorage.setItem('admin_logged', 'true');
      loginScreen.classList.remove('login-visible');
      loginScreen.classList.add('dashboard-hidden');
      document.getElementById('dashboard').classList.remove('dashboard-hidden');
      passwordInput.value = '';
      loginError.classList.remove('visible');
      initDashboard();
    } else {
      // Erreur
      loginError.textContent = '❌ Mot de passe incorrect';
      loginError.classList.add('visible');
      passwordInput.value = '';
      passwordInput.focus();
    }
  });

  // Entrée = soumettre
  passwordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') loginBtn.click();
  });
}

// ============================================================================
// GESTION LOGOUT
// ============================================================================

function initLogout() {
  document.getElementById('logoutBtn').addEventListener('click', () => {
    sessionStorage.removeItem('admin_logged');
    document.getElementById('dashboard').classList.add('dashboard-hidden');
    document.getElementById('loginScreen').classList.remove('dashboard-hidden');
    document.getElementById('loginScreen').classList.add('login-visible');
    document.getElementById('passwordInput').value = '';
    document.getElementById('passwordInput').type = 'password';
    document.getElementById('passwordToggle').textContent = '👁';
    document.getElementById('loginError').classList.remove('visible');
  });
}

// ============================================================================
// DASHBOARD INITIALIZATION
// ============================================================================

function initDashboard() {
  ensureInitialData();
  updateTodaySection();
  updateKPIs();
  renderReservationsList();
  renderArdoise();
  renderMenu();
  renderEvents();
  initTabs();
  initServiceFilters();
  initStatusFilters();
  initCalendar();
  initArdoiseEditor();
  initEventForm();
}

// ============================================================================
// VUE AUJOURD'HUI — À TRAITER
// ============================================================================

function updateTodaySection() {
  const today = offsetDate(0);
  const todayDate = document.getElementById('todayDate');
  const todayCount = document.getElementById('todayCount');
  const todayList = document.getElementById('todayList');

  todayDate.textContent = formatDate(today);

  const reservations = safeParse(localStorage.getItem('DEMO_reservations'), []);
  const todayReservations = reservations.filter(r => r.date === today && r.statut === 'En attente');

  todayCount.textContent = `${todayReservations.length}`;

  if (todayReservations.length === 0) {
    todayList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">✓</div><p>Aucune réservation en attente pour aujourd\'hui</p></div>';
    return;
  }

  todayList.innerHTML = todayReservations.map(r => {
    const serviceLabel = r.service === 'dejeuner' ? '🌅 Déjeuner' : '🌙 Dîner';
    return `
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">${r.prenom}</div>
            <div class="card-subtitle">${r.couverts} couverts • ${serviceLabel}</div>
          </div>
          <span class="badge badge-warning">En attente</span>
        </div>
        <div class="card-body">
          <div style="display: grid; gap: 0.75rem; font-size: 0.9rem;">
            <div>📞 <strong>${r.telephone}</strong></div>
            ${r.message ? `<div>💬 ${r.message}</div>` : ''}
          </div>
        </div>
        <div class="card-footer">
          <button class="btn-primary" data-id="${r.id}" data-action="confirm">✓ Confirmer</button>
          <button class="btn-secondary" data-id="${r.id}" data-action="cancel">✗ Annuler</button>
        </div>
      </div>
    `;
  }).join('');

  // Attach event listeners
  todayList.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', handleReservationAction);
  });
}

function handleReservationAction(e) {
  const action = e.currentTarget.dataset.action;
  const id = e.currentTarget.dataset.id;
  const reservations = safeParse(localStorage.getItem('DEMO_reservations'), []);
  const index = reservations.findIndex(r => r.id === id);

  if (index === -1) return;

  if (action === 'confirm') {
    reservations[index].statut = 'Confirmée';
    showNotification('✓ Réservation confirmée', 'success', document.body, 3000);
  } else if (action === 'cancel') {
    reservations[index].statut = 'Annulée';
    showNotification('✗ Réservation annulée', 'warning', document.body, 3000);
  }

  localStorage.setItem('DEMO_reservations', JSON.stringify(reservations));
  updateTodaySection();
  updateKPIs();
  renderReservationsList();
}

// ============================================================================
// KPIs
// ============================================================================

function updateKPIs() {
  const reservations = safeParse(localStorage.getItem('DEMO_reservations'), []);
  const today = offsetDate(0);
  
  // KPI 1: Demandes aujourd'hui (toutes les réservations d'aujourd'hui)
  const todayCount = reservations.filter(r => r.date === today).length;
  document.getElementById('kpiDemandesToday').textContent = todayCount;

  // KPI 2: En attente de confirmation
  const pendingCount = reservations.filter(r => r.statut === 'En attente').length;
  document.getElementById('kpiPending').textContent = pendingCount;

  // KPI 3: Confirmées cette semaine
  const weekConfirmed = reservations.filter(r => {
    const rDate = new Date(r.date);
    const todayDate = new Date(today);
    const daysUntilSunday = (7 - todayDate.getDay()) % 7 || 7;
    const weekEnd = new Date(todayDate);
    weekEnd.setDate(weekEnd.getDate() + daysUntilSunday);
    return rDate >= todayDate && rDate <= weekEnd && r.statut === 'Confirmée';
  }).length;
  document.getElementById('kpiConfirmedWeek').textContent = weekConfirmed;
}

// ============================================================================
// RÉSERVATIONS — ONGLET
// ============================================================================

function initCalendar() {
  const calendar = document.getElementById('calendarWeek');
  const today = offsetDate(0);
  
  calendar.innerHTML = '';

  for (let i = 0; i < 7; i++) {
    const date = offsetDate(i);
    const { day, date: dateNum } = getShortDate(date);
    const dayBtn = document.createElement('button');
    dayBtn.className = 'calendar-day' + (i === 0 ? ' active' : '');
    dayBtn.dataset.date = date;
    
    const reservations = safeParse(localStorage.getItem('DEMO_reservations'), []);
    const count = reservations.filter(r => r.date === date).length;
    
    dayBtn.innerHTML = `
      <div class="calendar-day-name">${day}</div>
      <div class="calendar-day-date">${dateNum}</div>
      <div class="calendar-day-indicator">${count > 0 ? '●' : ''}</div>
    `;
    
    dayBtn.addEventListener('click', () => {
      document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('active'));
      dayBtn.classList.add('active');
      renderReservationsList(date);
    });
    
    calendar.appendChild(dayBtn);
  }
}

function initServiceFilters() {
  document.querySelectorAll('[data-service]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('[data-service]').forEach(b => b.classList.remove('active'));
      e.currentTarget.classList.add('active');
      const selectedDate = document.querySelector('.calendar-day.active')?.dataset.date || offsetDate(0);
      renderReservationsList(selectedDate);
    });
  });
}

function initStatusFilters() {
  document.querySelectorAll('.status-filter button').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.status-filter button').forEach(b => b.classList.remove('active'));
      e.currentTarget.classList.add('active');
      const selectedDate = document.querySelector('.calendar-day.active')?.dataset.date || offsetDate(0);
      renderReservationsList(selectedDate);
    });
  });
}

function renderReservationsList(date = null) {
  if (!date) date = offsetDate(0);
  
  const reservations = safeParse(localStorage.getItem('DEMO_reservations'), []);
  const selectedService = document.querySelector('[data-service].active')?.dataset.service || 'all';
  const selectedStatus = document.querySelector('.status-filter button.active')?.dataset.status || 'all';

  let filtered = reservations.filter(r => r.date === date);
  
  if (selectedService !== 'all') {
    filtered = filtered.filter(r => r.service === selectedService);
  }
  
  if (selectedStatus !== 'all') {
    filtered = filtered.filter(r => r.statut === selectedStatus);
  }

  const container = document.getElementById('reservationsList');

  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>Aucune réservation pour cette sélection.</p></div>';
    return;
  }

  container.innerHTML = filtered.map(r => {
    const serviceLabel = r.service === 'dejeuner' ? '🌅 Déjeuner' : '🌙 Dîner';
    const statusClass = `status-${r.statut.toLowerCase().replace(' ', '-')}`;
    const statusBadgeClass = r.statut === 'En attente' ? 'badge-warning' : r.statut === 'Confirmée' ? 'badge-success' : 'badge-danger';
    
    return `
      <div class="reservation-card">
        <div class="reservation-header">
          <div>
            <div class="reservation-name">${r.prenom}</div>
            <div class="reservation-meta" style="grid-template-columns: repeat(2, 1fr); gap: 0.75rem;">
              <div class="reservation-detail">
                <span class="reservation-detail-label">Service</span>
                <span class="reservation-detail-value">${serviceLabel}</span>
              </div>
              <div class="reservation-detail">
                <span class="reservation-detail-label">Couverts</span>
                <span class="reservation-detail-value">${r.couverts}</span>
              </div>
              <div class="reservation-detail">
                <span class="reservation-detail-label">Date</span>
                <span class="reservation-detail-value">${formatDate(r.date)}</span>
              </div>
              <div class="reservation-detail">
                <span class="reservation-detail-label">Téléphone</span>
                <span class="reservation-detail-value">${r.telephone}</span>
              </div>
            </div>
          </div>
          <span class="badge ${statusBadgeClass}">${r.statut}</span>
        </div>
        
        ${r.message ? `<div class="card-body"><p style="margin: 0;"><strong>💬 Note :</strong> ${r.message}</p></div>` : ''}
        
        <div class="card-footer">
          <button class="btn-primary" data-id="${r.id}" data-action="confirm" ${r.statut === 'Confirmée' ? 'disabled' : ''}>✓ Confirmer</button>
          <button class="btn-secondary" data-id="${r.id}" data-action="cancel" ${r.statut === 'Annulée' ? 'disabled' : ''}>✗ Annuler</button>
        </div>
      </div>
    `;
  }).join('');

  container.querySelectorAll('button[data-action]').forEach(btn => {
    btn.addEventListener('click', handleReservationAction);
  });
}

// ============================================================================
// ARDOISE — ONGLET
// ============================================================================

function initArdoiseEditor() {
  const availableToggle = document.getElementById('ardoiseAvailable');
  const formuleCheckbox = document.getElementById('ardoiseFormuleActive');
  const formuleFields = document.getElementById('ardoiseFormuleFields');
  const saveBtn = document.getElementById('saveArdoiseBtn');

  // Charger données existantes
  const ardoise = safeParse(localStorage.getItem('DEMO_ardoise'), DEMO_ARDOISE);
  
  availableToggle.checked = ardoise.disponible;
  document.getElementById('ardoisePlat').value = ardoise.plat?.nom || '';
  document.getElementById('ardoisePrix').value = ardoise.plat?.prix || '';
  document.getElementById('ardoiseNote').value = ardoise.plat?.note || '';
  document.getElementById('ardoiseEntree').value = ardoise.entree?.nom || '';
  document.getElementById('ardoiseEntreePrix').value = ardoise.entree?.prix || '';
  document.getElementById('ardoiseDessert').value = ardoise.dessert?.nom || '';
  document.getElementById('ardoiseDessertPrix').value = ardoise.dessert?.prix || '';
  formuleCheckbox.checked = ardoise.formule?.active || false;
  document.getElementById('ardoiseFormuleLabel').value = ardoise.formule?.label || '';
  document.getElementById('ardoiseFormulePrix').value = ardoise.formule?.prix || '';

  if (formuleCheckbox.checked) {
    formuleFields.style.display = 'block';
  }

  formuleCheckbox.addEventListener('change', () => {
    formuleFields.style.display = formuleCheckbox.checked ? 'block' : 'none';
  });

  availableToggle.addEventListener('change', updateArdoisePreview);
  document.getElementById('ardoisePlat').addEventListener('input', updateArdoisePreview);
  document.getElementById('ardoisePrix').addEventListener('input', updateArdoisePreview);
  document.getElementById('ardoiseNote').addEventListener('input', updateArdoisePreview);
  document.getElementById('ardoiseEntree').addEventListener('input', updateArdoisePreview);
  document.getElementById('ardoiseEntreePrix').addEventListener('input', updateArdoisePreview);
  document.getElementById('ardoiseDessert').addEventListener('input', updateArdoisePreview);
  document.getElementById('ardoiseDessertPrix').addEventListener('input', updateArdoisePreview);
  document.getElementById('ardoiseFormuleLabel').addEventListener('input', updateArdoisePreview);
  document.getElementById('ardoiseFormulePrix').addEventListener('input', updateArdoisePreview);

  saveBtn.addEventListener('click', saveArdoise);

  updateArdoisePreview();
}

function updateArdoisePreview() {
  const available = document.getElementById('ardoiseAvailable').checked;
  const preview = document.getElementById('ardoisePreview');

  if (!available) {
    preview.innerHTML = '<p style="color: var(--text-secondary); font-style: italic;">Ardoise masquée sur le site</p>';
    return;
  }

  const plat = document.getElementById('ardoisePlat').value;
  const prix = document.getElementById('ardoisePrix').value;
  const note = document.getElementById('ardoiseNote').value;
  const entree = document.getElementById('ardoiseEntree').value;
  const entreePrix = document.getElementById('ardoiseEntreePrix').value;
  const dessert = document.getElementById('ardoiseDessert').value;
  const dessertPrix = document.getElementById('ardoiseDessertPrix').value;
  const formuleActive = document.getElementById('ardoiseFormuleActive').checked;
  const formuleLabel = document.getElementById('ardoiseFormuleLabel').value;
  const formulePrix = document.getElementById('ardoiseFormulePrix').value;

  let html = '<div style="background-color: white; padding: var(--spacing-md); border-radius: 4px;">';

  if (entree) {
    html += `<div style="margin-bottom: var(--spacing-sm);"><strong style="color: var(--accent);">Entrée</strong> : ${entree} <span style="float: right; color: var(--accent); font-weight: 700;">${entreePrix}</span></div>`;
  }

  html += `<div style="margin-bottom: var(--spacing-sm);"><strong style="color: var(--accent); font-size: 1.1rem;">Plat du jour</strong> : ${plat} <span style="float: right; color: var(--accent); font-weight: 700; font-size: 1.1rem;">${prix}</span></div>`;
  
  if (note) {
    html += `<div style="margin-bottom: var(--spacing-sm); color: var(--text-secondary); font-size: 0.9rem; font-style: italic;">💡 ${note}</div>`;
  }

  if (dessert) {
    html += `<div style="margin-bottom: var(--spacing-sm);"><strong style="color: var(--accent);">Dessert</strong> : ${dessert} <span style="float: right; color: var(--accent); font-weight: 700;">${dessertPrix}</span></div>`;
  }

  if (formuleActive && formuleLabel && formulePrix) {
    html += `<div style="margin-top: var(--spacing-lg); background-color: rgba(83, 135, 94, 0.1); padding: var(--spacing-md); border-radius: 4px; text-align: center; border: 2px solid var(--accent);"><strong style="color: var(--accent);">📦 Formule : ${formuleLabel}</strong><br><span style="font-size: 1.5rem; color: var(--accent); font-weight: 700;">${formulePrix}</span></div>`;
  }

  html += '</div>';
  preview.innerHTML = html;
}

function saveArdoise() {
  const ardoise = {
    disponible: document.getElementById('ardoiseAvailable').checked,
    plat: {
      nom: document.getElementById('ardoisePlat').value,
      prix: document.getElementById('ardoisePrix').value,
      note: document.getElementById('ardoiseNote').value
    },
    entree: {
      nom: document.getElementById('ardoiseEntree').value,
      prix: document.getElementById('ardoiseEntreePrix').value
    },
    dessert: {
      nom: document.getElementById('ardoiseDessert').value,
      prix: document.getElementById('ardoiseDessertPrix').value
    },
    formule: {
      active: document.getElementById('ardoiseFormuleActive').checked,
      label: document.getElementById('ardoiseFormuleLabel').value,
      prix: document.getElementById('ardoiseFormulePrix').value
    }
  };

  localStorage.setItem('DEMO_ardoise', JSON.stringify(ardoise));
  
  const feedback = document.getElementById('ardoiseFeedback');
  showNotification('✓ Ardoise mise à jour !', 'success', feedback, 4000);
}

function renderArdoise() {
  // Affichage lecture seule si nécessaire
  // Cette fonction peut afficher l'ardoise sur le dashboard
}

// ============================================================================
// MENU — ONGLET
// ============================================================================

function renderMenu() {
  const menu = safeParse(localStorage.getItem('DEMO_menu'), DEMO_MENU);
  const container = document.getElementById('menuDisplay');

  container.innerHTML = menu.categories.map(cat => `
    <div style="margin-bottom: var(--spacing-lg);">
      <h4 style="margin-bottom: var(--spacing-md); color: var(--accent);">${cat.nom}</h4>
      <div style="display: grid; gap: var(--spacing-md);">
        ${cat.plats.map(plat => `
          <div style="padding-bottom: var(--spacing-md); border-bottom: 1px solid var(--border-soft);">
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: var(--spacing-xs);">
              <strong style="${!plat.disponible ? 'text-decoration: line-through;' : ''}">${plat.nom}</strong>
              <span style="color: var(--accent); font-weight: 700;">${plat.prix}</span>
            </div>
            ${plat.description ? `<p style="margin: 0; font-size: 0.9rem; color: var(--text-secondary);">${plat.description}</p>` : ''}
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

// ============================================================================
// ÉVÉNEMENTS — ONGLET
// ============================================================================

function initEventForm() {
  const addBtn = document.getElementById('addEventBtn');
  const titleInput = document.getElementById('eventTitle');
  const dateInput = document.getElementById('eventDate');
  const descInput = document.getElementById('eventDescription');
  const feedback = document.getElementById('eventFeedback');

  // Set minimum date to today
  dateInput.min = offsetDate(0);

  addBtn.addEventListener('click', () => {
    const title = titleInput.value.trim();
    const date = dateInput.value;
    const description = descInput.value.trim();

    if (!title || !date) {
      showNotification('⚠️ Titre et date obligatoires', 'warning', feedback, 3000);
      return;
    }

    const events = safeParse(localStorage.getItem('DEMO_events'), []);
    const newEvent = {
      id: 'event-' + Date.now(),
      titre: title,
      date: date,
      description: description,
      visible: true
    };

    events.push(newEvent);
    localStorage.setItem('DEMO_events', JSON.stringify(events));

    titleInput.value = '';
    dateInput.value = '';
    descInput.value = '';

    showNotification('✓ Événement créé !', 'success', feedback, 3000);
    renderEvents();
  });
}

function renderEvents() {
  const events = safeParse(localStorage.getItem('DEMO_events'), []);
  const container = document.getElementById('eventsList');

  if (events.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>Aucun événement créé pour le moment.</p></div>';
    return;
  }

  container.innerHTML = events.map(evt => {
    const isUpcoming = new Date(evt.date) >= new Date(offsetDate(0));
    return `
      <div class="event-card">
        <div class="event-info">
          <h4>${evt.titre}</h4>
          <div class="event-date">📅 ${formatDate(evt.date)}</div>
          <div class="event-description">${evt.description}</div>
        </div>
        <div class="event-actions">
          <label class="toggle-switch">
            <input type="checkbox" class="toggle-input" ${evt.visible ? 'checked' : ''} data-id="${evt.id}" data-action="toggle-visible">
            <span style="font-size: 0.85rem;">Visible</span>
          </label>
          <button class="btn-secondary" style="padding: 0.5rem var(--spacing-md); font-size: 0.85rem;" data-id="${evt.id}" data-action="delete">🗑️ Supprimer</button>
        </div>
      </div>
    `;
  }).join('');

  container.querySelectorAll('[data-action="toggle-visible"]').forEach(input => {
    input.addEventListener('change', (e) => {
      const id = e.currentTarget.dataset.id;
      const events = safeParse(localStorage.getItem('DEMO_events'), []);
      const evt = events.find(e => e.id === id);
      if (evt) {
        evt.visible = e.currentTarget.checked;
        localStorage.setItem('DEMO_events', JSON.stringify(events));
      }
    });
  });

  container.querySelectorAll('[data-action="delete"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = e.currentTarget.dataset.id;
      const events = safeParse(localStorage.getItem('DEMO_events'), []);
      const filtered = events.filter(e => e.id !== id);
      localStorage.setItem('DEMO_events', JSON.stringify(filtered));
      renderEvents();
    });
  });
}

// ============================================================================
// GESTION DES ONGLETS
// ============================================================================

function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabContents = document.querySelectorAll('.tab-content');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabName = btn.dataset.tab;

      tabButtons.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(`tab-${tabName}`).classList.add('active');
    });
  });
}

// ============================================================================
// INITIALISATION AU CHARGEMENT
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Vérifier si déjà connecté
  const isLogged = sessionStorage.getItem('admin_logged');
  
  if (isLogged) {
    document.getElementById('loginScreen').classList.add('dashboard-hidden');
    document.getElementById('loginScreen').classList.remove('login-visible');
    document.getElementById('dashboard').classList.remove('dashboard-hidden');
    initDashboard();
  } else {
    document.getElementById('dashboard').classList.add('dashboard-hidden');
  }

  // Init login/logout
  initLogin();
  initLogout();
});