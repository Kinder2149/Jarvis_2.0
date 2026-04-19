// ========== CONFIGURATIONS & CONSTANTS ==========

const PASSWORD = "admin2024";

// Fonction utilitaire pour parser JSON en toute sécurité
function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try {
    return JSON.parse(rawValue);
  } catch (e) {
    return fallbackValue;
  }
}

// Fonction pour calculer la date offset depuis aujourd'hui
function offsetDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

// Données démo - 5 réservations
const DEMO_RESERVATIONS = [
  {
    id: "demo-1",
    prenom: "Marie D.",
    telephone: "06 12 34 56 78",
    date: offsetDate(1),
    service: "diner",
    couverts: "2",
    message: "Anniversaire de mariage, si possible une table en retrait",
    statut: "En attente",
    source: "demo"
  },
  {
    id: "demo-2",
    prenom: "Thomas B.",
    telephone: "07 65 43 21 09",
    date: offsetDate(1),
    service: "dejeuner",
    couverts: "4",
    message: "",
    statut: "Confirmée",
    source: "demo"
  },
  {
    id: "demo-3",
    prenom: "Sophie M.",
    telephone: "06 98 76 54 32",
    date: offsetDate(2),
    service: "diner",
    couverts: "6",
    message: "Une personne allergique aux crustacés",
    statut: "En attente",
    source: "demo"
  },
  {
    id: "demo-4",
    prenom: "Laurent F.",
    telephone: "07 11 22 33 44",
    date: offsetDate(3),
    service: "dejeuner",
    couverts: "2",
    message: "Menu dégustation si disponible",
    statut: "Confirmée",
    source: "demo"
  },
  {
    id: "demo-5",
    prenom: "Isabelle R.",
    telephone: "06 55 44 33 22",
    date: offsetDate(4),
    service: "diner",
    couverts: "8",
    message: "Repas d'entreprise",
    statut: "Annulée",
    source: "demo"
  }
];

// Ardoise démo
const DEMO_ARDOISE = {
  disponible: true,
  entree: { nom: "Velouté de butternut, crème fraîche", prix: "8,00 €" },
  plat: { nom: "Magret de canard, jus de cerise", prix: "21,00 €", note: "Cuisson selon votre goût" },
  dessert: { nom: "Fondant au chocolat, glace vanille", prix: "7,00 €" },
  formule: { active: true, prix: "31,00 €", label: "Entrée + Plat + Dessert" }
};

// Carte démo
const DEMO_MENU_CARD = {
  categories: [
    {
      id: "cat-1",
      nom: "Entrées",
      ordre: 1,
      plats: [
        { id: "plat-1", nom: "Salade samossa chèvre, pommes, noix, miel", prix: "8,00 €", description: "", disponible: true },
        { id: "plat-2", nom: "Pâté de campagne au camembert", prix: "8,50 €", description: "", disponible: true },
        { id: "plat-3", nom: "Terrine de légumes, coulis de tomates", prix: "8,00 €", description: "", disponible: true }
      ]
    },
    {
      id: "cat-2",
      nom: "Plats",
      ordre: 2,
      plats: [
        { id: "plat-4", nom: "Onglet de veau croûte aux herbes", prix: "18,00 €", description: "gnocchi à la romaine, légumes", disponible: true },
        { id: "plat-5", nom: "Risotto au pesto vert, burratina, roquette", prix: "16,00 €", description: "", disponible: true },
        { id: "plat-6", nom: "Filet de poisson beurre thym citron, écrasé patates douces", prix: "18,00 €", description: "", disponible: true },
        { id: "plat-7", nom: "Gratin de Ravioles du Royans, tomme de Savoie, tomates confites", prix: "16,00 €", description: "", disponible: true }
      ]
    },
    {
      id: "cat-3",
      nom: "Desserts",
      ordre: 3,
      plats: [
        { id: "plat-8", nom: "Moelleux aux amandes, caramel beurre demi-sel, chantilly", prix: "7,00 €", description: "", disponible: true },
        { id: "plat-9", nom: "Coulant au chocolat", prix: "7,50 €", description: "coeur spéculos, glace vanille", disponible: true },
        { id: "plat-10", nom: "Crème brûlée", prix: "7,00 €", description: "parfum selon l'humeur du chef", disponible: true },
        { id: "plat-11", nom: "Salade de fruits frais", prix: "6,50 €", description: "", disponible: true },
        { id: "plat-12", nom: "Café gourmand", prix: "8,00 €", description: "Thé : supplément 0,50€", disponible: true },
        { id: "plat-13", nom: "Vacherin glacé", prix: "7,00 €", description: "", disponible: true },
        { id: "plat-14", nom: "Fromage blanc, crème ou coulis de fruits maison", prix: "5,50 €", description: "", disponible: true }
      ]
    }
  ]
};

// ========== INITIALISATION ==========

function ensureInitialData() {
  const existingReservations = localStorage.getItem("actions_recues");
  if (!existingReservations) {
    localStorage.setItem("actions_recues", JSON.stringify(DEMO_RESERVATIONS));
  }

  const existingArdoise = localStorage.getItem("contenu_editable");
  if (!existingArdoise) {
    localStorage.setItem("contenu_editable", JSON.stringify({ ardoise: DEMO_ARDOISE }));
  }

  const existingMenu = localStorage.getItem("menuCard");
  if (!existingMenu) {
    localStorage.setItem("menuCard", JSON.stringify(DEMO_MENU_CARD));
  }
}

// ========== LOGIN SYSTEM ==========

const loginScreen = document.getElementById("loginScreen");
const adminDashboard = document.getElementById("adminDashboard");
const passwordInput = document.getElementById("passwordInput");
const togglePasswordBtn = document.getElementById("togglePassword");
const loginBtn = document.getElementById("loginBtn");
const loginError = document.getElementById("loginError");
const logoutBtn = document.getElementById("logoutBtn");

togglePasswordBtn.addEventListener("click", (e) => {
  e.preventDefault();
  const type = passwordInput.type === "password" ? "text" : "password";
  passwordInput.type = type;
  togglePasswordBtn.textContent = type === "password" ? "👁️" : "👁️‍🗨️";
});

loginBtn.addEventListener("click", () => {
  if (passwordInput.value === PASSWORD) {
    loginScreen.classList.add("hidden");
    adminDashboard.classList.add("visible");
    loginError.classList.remove("show");
  } else {
    loginError.classList.add("show");
    passwordInput.value = "";
  }
});

passwordInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    loginBtn.click();
  }
});

logoutBtn.addEventListener("click", () => {
  adminDashboard.classList.remove("visible");
  loginScreen.classList.remove("hidden");
  passwordInput.value = "";
  loginError.classList.remove("show");
});

// ========== UTILS ==========

function getToday() {
  return new Date().toISOString().split('T')[0];
}

function formatDate(dateStr) {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'numeric' });
}

function getDayName(dateStr) {
  const date = new Date(dateStr + "T00:00:00");
  const days = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];
  return days[date.getDay()];
}

function getServiceLabel(service) {
  return service === "dejeuner" ? "Déjeuner" : "Dîner";
}

function showConfirmation(elementId, duration = 4000) {
  const elem = document.getElementById(elementId);
  if (!elem) return;
  elem.classList.remove("hidden");
  setTimeout(() => {
    elem.classList.add("hidden");
  }, duration);
}

// ========== DISPLAY FUNCTIONS ==========

function displayTodayDate() {
  const today = getToday();
  const formatted = new Date(today + "T00:00:00").toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });
  document.getElementById("todayDate").textContent = formatted;
}

function updateKPIs() {
  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  const today = getToday();

  // Demandes aujourd'hui
  const todayReservations = reservations.filter(r => r.date === today);
  document.getElementById("kpiToday").textContent = todayReservations.length;

  // En attente de confirmation
  const pendingReservations = reservations.filter(r => r.statut === "En attente");
  document.getElementById("kpiPending").textContent = pendingReservations.length;

  // Confirmées cette semaine
  const weekStart = getToday();
  const weekEnd = offsetDate(7);
  const confirmedWeek = reservations.filter(r =>
    r.statut === "Confirmée" && r.date >= weekStart && r.date <= weekEnd
  );
  document.getElementById("kpiWeek").textContent = confirmedWeek.length;
}

function renderPendingReservations() {
  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  const pending = reservations.filter(r => r.statut === "En attente");
  const container = document.getElementById("pendingReservations");

  if (pending.length === 0) {
    container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; margin: 0;">Aucune demande en attente</p>';
    return;
  }

  container.innerHTML = pending.map(res => `
    <div class="admin-reservation-card">
      <div class="reservation-info">
        <p><strong>${res.prenom}</strong></p>
        <p>📞 ${res.telephone}</p>
        <p>📅 ${formatDate(res.date)} · ${getServiceLabel(res.service)} · ${res.couverts} pers.</p>
        ${res.message ? `<p style="font-style: italic; color: var(--text-secondary);">"${res.message}"</p>` : ''}
      </div>
      <div class="reservation-meta" style="flex-direction: column; align-items: flex-end; gap: 1rem;">
        <span class="badge badge-attente">En attente</span>
        <div style="display: flex; gap: 0.75rem;">
          <button type="button" class="btn-success btn-confirm" data-id="${res.id}" style="padding: 0.5rem 1rem; font-size: 0.9rem;">
            ✓ Confirmer
          </button>
          <button type="button" class="btn-danger btn-cancel" data-id="${res.id}" style="padding: 0.5rem 1rem; font-size: 0.9rem;">
            ✗ Annuler
          </button>
        </div>
      </div>
    </div>
  `).join('');

  container.querySelectorAll(".btn-confirm").forEach(btn => {
    btn.addEventListener("click", () => setReservationStatus(btn.dataset.id, "Confirmée"));
  });

  container.querySelectorAll(".btn-cancel").forEach(btn => {
    btn.addEventListener("click", () => setReservationStatus(btn.dataset.id, "Annulée"));
  });
}

function setReservationStatus(id, newStatus) {
  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  const reservation = reservations.find(r => r.id === id);
  if (reservation) {
    reservation.statut = newStatus;
    localStorage.setItem("actions_recues", JSON.stringify(reservations));
    updateKPIs();
    renderPendingReservations();
    renderReservations();
  }
}

// ========== CALENDAR ==========

function initCalendar() {
  const today = getToday();
  for (let i = 0; i < 7; i++) {
    const date = offsetDate(i);
    const dateElem = document.getElementById(`cal-${i}`);
    const labelElem = document.getElementById(`cal-${i}-label`);
    
    if (dateElem) dateElem.textContent = formatDate(date);
    if (labelElem && i > 0) labelElem.textContent = getDayName(date);
  }

  updateCalendarIndicators();

  document.querySelectorAll(".calendar-day").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".calendar-day").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const dayOffset = parseInt(btn.dataset.day);
      renderReservations(dayOffset);
    });
  });

  document.querySelector("[data-day='0']").classList.add("active");
}

function updateCalendarIndicators() {
  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  for (let i = 0; i < 7; i++) {
    const date = offsetDate(i);
    const count = reservations.filter(r => r.date === date).length;
    const indicator = document.getElementById(`cal-dot-${i}`);
    if (indicator) {
      indicator.style.display = count > 0 ? "block" : "none";
    }
  }
}

// ========== RESERVATIONS TAB ==========

let selectedDate = getToday();
let selectedService = "tous";

document.querySelectorAll(".service-filter").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".service-filter").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    selectedService = btn.dataset.service;
    renderReservations();
  });
});

function renderReservations(dayOffset = 0) {
  selectedDate = offsetDate(dayOffset);
  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  let filtered = reservations.filter(r => r.date === selectedDate);

  if (selectedService !== "tous") {
    filtered = filtered.filter(r => r.service === selectedService);
  }

  const container = document.getElementById("reservationsList");

  if (filtered.length === 0) {
    container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; grid-column: 1/-1;">Aucune réservation pour cette sélection</p>';
    return;
  }

  container.innerHTML = filtered.map(res => `
    <div class="admin-reservation-card">
      <div class="reservation-info">
        <p><strong>${res.prenom}</strong></p>
        <p>📞 ${res.telephone}</p>
        <p>📅 ${getServiceLabel(res.service)} · ${res.couverts} pers.</p>
        ${res.message ? `<p style="font-style: italic; color: var(--text-secondary);">"${res.message}"</p>` : ''}
      </div>
      <div class="reservation-meta" style="flex-direction: column; align-items: flex-end; gap: 1rem;">
        <span class="badge ${
          res.statut === "En attente" ? "badge-attente" :
          res.statut === "Confirmée" ? "badge-confirme" :
          "badge-annule"
        }">${res.statut}</span>
        <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; justify-content: flex-end;">
          <button type="button" class="btn-success btn-confirm ${res.statut === "Confirmée" ? "disabled" : ""}" data-id="${res.id}" ${res.statut === "Confirmée" ? "disabled" : ""} style="padding: 0.5rem 1rem; font-size: 0.9rem;">
            ✓ Confirmer
          </button>
          <button type="button" class="btn-danger btn-cancel ${res.statut === "Annulée" ? "disabled" : ""}" data-id="${res.id}" ${res.statut === "Annulée" ? "disabled" : ""} style="padding: 0.5rem 1rem; font-size: 0.9rem;">
            ✗ Annuler
          </button>
        </div>
      </div>
    </div>
  `).join('');

  container.querySelectorAll(".btn-confirm:not(.disabled)").forEach(btn => {
    btn.addEventListener("click", () => setReservationStatus(btn.dataset.id, "Confirmée"));
  });

  container.querySelectorAll(".btn-cancel:not(.disabled)").forEach(btn => {
    btn.addEventListener("click", () => setReservationStatus(btn.dataset.id, "Annulée"));
  });
}

// ========== MENU & ARDOISE TAB ==========

document.getElementById("ardoiseSaveBtn").addEventListener("click", () => {
  const ardoise = {
    disponible: document.getElementById("ardoiseToggle").checked,
    entree: {
      nom: document.getElementById("ardoiseEntreeNom").value,
      prix: document.getElementById("ardoiseEntreePrix").value
    },
    plat: {
      nom: document.getElementById("ardoisePlatNom").value,
      prix: document.getElementById("ardoisePlatPrix").value,
      note: document.getElementById("ardoisePlatNote").value
    },
    dessert: {
      nom: document.getElementById("ardoiseDessertNom").value,
      prix: document.getElementById("ardoiseDessertPrix").value
    },
    formule: {
      active: document.getElementById("formuleActive").checked,
      prix: document.getElementById("formulePrix").value,
      label: document.getElementById("formuleLabel").value
    }
  };

  const contentEditable = safeParse(localStorage.getItem("contenu_editable"), {});
  contentEditable.ardoise = ardoise;
  localStorage.setItem("contenu_editable", JSON.stringify(contentEditable));

  showConfirmation("ardoiseConfirmation");
});

function loadArdoiseData() {
  const contentEditable = safeParse(localStorage.getItem("contenu_editable"), { ardoise: DEMO_ARDOISE });
  const ardoise = contentEditable.ardoise || DEMO_ARDOISE;

  document.getElementById("ardoiseToggle").checked = ardoise.disponible !== false;
  document.getElementById("ardoiseEntreeNom").value = ardoise.entree?.nom || "";
  document.getElementById("ardoiseEntreePrix").value = ardoise.entree?.prix || "";
  document.getElementById("ardoisePlatNom").value = ardoise.plat?.nom || "";
  document.getElementById("ardoisePlatNote").value = ardoise.plat?.note || "";
  document.getElementById("ardoisePlatPrix").value = ardoise.plat?.prix || "";
  document.getElementById("ardoiseDessertNom").value = ardoise.dessert?.nom || "";
  document.getElementById("ardoiseDessertPrix").value = ardoise.dessert?.prix || "";
  document.getElementById("formuleActive").checked = ardoise.formule?.active || false;
  document.getElementById("formuleLabel").value = ardoise.formule?.label || "Entrée + Plat + Dessert";
  document.getElementById("formulePrix").value = ardoise.formule?.prix || "";
}

document.getElementById("menuSaveBtn").addEventListener("click", () => {
  const categories = [];
  document.querySelectorAll(".menu-category-editor").forEach((catElem, idx) => {
    const catName = catElem.querySelector(".category-name-editor").value;
    const platsContainer = catElem.querySelector(".menu-plats-editor");
    const plats = [];

    platsContainer.querySelectorAll(".menu-plat-editor").forEach(platElem => {
      plats.push({
        id: platElem.dataset.id,
        nom: platElem.querySelector(".plat-nom-editor").value,
        prix: platElem.querySelector(".plat-prix-editor").value,
        description: platElem.querySelector(".plat-desc-editor").value,
        disponible: platElem.querySelector(".plat-disponible-editor").checked
      });
    });

    categories.push({
      id: catElem.dataset.id,
      nom: catName,
      ordre: idx + 1,
      plats: plats
    });
  });

  localStorage.setItem("menuCard", JSON.stringify({ categories }));
  showConfirmation("menuConfirmation");
});

function renderMenuEditor() {
  const menuCard = safeParse(localStorage.getItem("menuCard"), DEMO_MENU_CARD);
  const container = document.getElementById("menuCategoriesEditor");

  container.innerHTML = menuCard.categories.map(cat => `
    <div class="menu-category-editor" data-id="${cat.id}">
      <div style="display: grid; grid-template-columns: 1fr auto; gap: 1rem; margin-bottom: 1rem; align-items: center;">
        <input type="text" class="category-name-editor" value="${cat.nom}" style="padding: 0.75rem; border: 1px solid var(--border-soft); border-radius: 4px;">
        <button type="button" class="btn-danger btn-delete-category" data-id="${cat.id}" style="padding: 0.5rem 1rem; font-size: 0.9rem;">
          Supprimer
        </button>
      </div>
      <div class="menu-plats-editor" style="display: grid; gap: 1rem; margin-left: 1rem;">
        ${cat.plats.map(plat => `
          <div class="menu-plat-editor" data-id="${plat.id}" style="background-color: var(--bg-alt); padding: 1rem; border-radius: 4px; display: grid; gap: 0.75rem;">
            <div style="display: grid; grid-template-columns: 1fr auto 20px; gap: 0.75rem; align-items: center;">
              <input type="text" class="plat-nom-editor" value="${plat.nom}" placeholder="Nom du plat" style="padding: 0.5rem; border: 1px solid var(--border-soft); border-radius: 4px;">
              <input type="text" class="plat-prix-editor" value="${plat.prix}" placeholder="Prix" style="padding: 0.5rem; border: 1px solid var(--border-soft); border-radius: 4px; width: 100px;">
              <label style="display: flex; align-items: center; cursor: pointer; margin: 0;">
                <input type="checkbox" class="plat-disponible-editor" ${plat.disponible ? "checked" : ""} style="width: 18px; height: 18px;">
              </label>
            </div>
            <input type="text" class="plat-desc-editor" value="${plat.description || ""}" placeholder="Description (optionnel)" style="padding: 0.5rem; border: 1px solid var(--border-soft); border-radius: 4px; font-size: 0.9rem;">
          </div>
        `).join('')}
        <button type="button" class="btn-secondary btn-add-plat" data-cat-id="${cat.id}" style="padding: 0.75rem; font-size: 0.9rem;">
          + Ajouter un plat
        </button>
      </div>
    </div>
  `).join('');

  // Event listeners
  container.querySelectorAll(".btn-delete-category").forEach(btn => {
    btn.addEventListener("click", () => {
      if (confirm("Supprimer cette catégorie et tous ses plats ?")) {
        deleteCategoryEditor(btn.dataset.id);
      }
    });
  });

  container.querySelectorAll(".btn-add-plat").forEach(btn => {
    btn.addEventListener("click", () => {
      addPlatEditor(btn.dataset.catId);
    });
  });
}

function addPlatEditor(catId) {
  const menuCard = safeParse(localStorage.getItem("menuCard"), DEMO_MENU_CARD);
  const cat = menuCard.categories.find(c => c.id === catId);
  if (cat) {
    const newPlat = {
      id: `plat-${Date.now()}`,
      nom: "",
      prix: "",
      description: "",
      disponible: true
    };
    cat.plats.push(newPlat);
    localStorage.setItem("menuCard", JSON.stringify(menuCard));
    renderMenuEditor();
  }
}

function deleteCategoryEditor(catId) {
  const menuCard = safeParse(localStorage.getItem("menuCard"), DEMO_MENU_CARD);
  menuCard.categories = menuCard.categories.filter(c => c.id !== catId);
  localStorage.setItem("menuCard", JSON.stringify(menuCard));
  renderMenuEditor();
}

// ========== ONGLETS ADMIN ==========

document.querySelectorAll(".admin-tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const tabName = btn.dataset.tab;
    document.querySelectorAll(".admin-tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".admin-tab-content").forEach(c => c.classList.remove("visible"));
    btn.classList.add("active");
    document.getElementById(`tab-${tabName}`).classList.add("visible");
  });
});

// ========== INIT ==========

document.addEventListener("DOMContentLoaded", () => {
  ensureInitialData();
  displayTodayDate();
  updateKPIs();
  renderPendingReservations();
  initCalendar();
  renderReservations();
  loadArdoiseData();
  renderMenuEditor();
});

// ========== STYLES DYNAMIQUES ==========

const style = document.createElement('style');
style.textContent = `
  .calendar-day {
    background-color: var(--card-bg);
    border: 1px solid var(--border-soft);
    border-radius: 4px;
    padding: 1rem 0.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    text-align: center;
    font-weight: 500;
  }

  .calendar-day:hover {
    border-color: var(--accent);
  }

  .calendar-day.active {
    background-color: var(--accent);
    border-color: var(--accent);
    color: white;
  }

  .calendar-day__label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.75;
  }

  .calendar-day__date {
    font-size: 1rem;
    font-weight: 700;
  }

  .calendar-day__indicator {
    width: 8px;
    height: 8px;
    background-color: var(--accent);
    border-radius: 50%;
  }

  .calendar-day.active .calendar-day__indicator {
    background-color: white;
  }

  .service-filter {
    background-color: var(--card-bg);
    border: 1px solid var(--border-soft);
    color: var(--text-main);
    padding: 0.75rem 1.5rem;
  }

  .service-filter.active {
    background-color: var(--accent);
    border-color: var(--accent);
    color: white;
  }

  .admin-reservation-card {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 2rem;
    align-items: start;
  }

  @media (max-width: 768px) {
    .admin-reservation-card {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .reservation-meta {
      justify-content: flex-start !important;
    }

    .reservation-actions {
      justify-content: flex-start !important;
      flex-direction: row;
    }
  }

  .editor-confirmation {
    background-color: var(--success);
    color: white;
    padding: 1rem;
    border-radius: 4px;
    text-align: center;
    font-weight: 600;
    margin-top: 1rem;
    animation: slideInRight 0.3s ease;
  }

  .editor-confirmation.hidden {
    display: none;
  }

  @keyframes slideInRight {
    from {
      transform: translateX(-400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  .kpi-card__number {
    font-size: 2.5rem;
    color: var(--accent);
    font-weight: 700;
    margin: 0;
  }

  button.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  button.disabled:hover {
    opacity: 0.5;
  }
`;
document.head.appendChild(style);