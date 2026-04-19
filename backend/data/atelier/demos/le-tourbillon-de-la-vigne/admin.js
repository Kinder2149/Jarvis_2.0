// ===== CONSTANTS & CONFIG =====

const PASSWORD = "admin2024";

// Calcul de la date décalée
function offsetDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

// Données démo — Réservations (cohérentes avec cuisine lyonnaise traditionnelle)
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

// Données démo — Ardoise (basée sur la vraie carte extraite)
const DEMO_ARDOISE = {
  disponible: true,
  entree: {
    nom: "Salade lyonnaise",
    prix: "12,00 €"
  },
  plat: {
    nom: "Quenelle de brochet",
    prix: "18,00 €",
    note: "Sauce Nantua maison"
  },
  dessert: {
    nom: "Tarte tatin maison",
    prix: "7,00 €"
  },
  formule: {
    active: true,
    prix: "32,00 €",
    label: "Entrée + Plat + Dessert"
  }
};

// Données démo — Carte complète
const DEMO_MENU = {
  categories: [
    {
      id: "cat-1",
      nom: "Entrées",
      ordre: 1,
      plats: [
        {
          id: "plat-1",
          nom: "Salade lyonnaise",
          prix: "12,00 €",
          description: "Frisée, lardons, œuf poché",
          disponible: true
        },
        {
          id: "plat-2",
          nom: "Terrine de foie gras maison",
          prix: "14,00 €",
          description: "Chutney de figues, brioche toastée",
          disponible: true
        },
        {
          id: "plat-3",
          nom: "Œufs en meurette",
          prix: "11,00 €",
          description: "Sauce vin rouge, lardons",
          disponible: true
        }
      ]
    },
    {
      id: "cat-2",
      nom: "Plats",
      ordre: 2,
      plats: [
        {
          id: "plat-4",
          nom: "Quenelle de brochet",
          prix: "18,00 €",
          description: "Sauce Nantua maison",
          disponible: true
        },
        {
          id: "plat-5",
          nom: "Andouillette AAAAA",
          prix: "16,00 €",
          description: "Frites maison, sauce moutarde",
          disponible: true
        },
        {
          id: "plat-6",
          nom: "Blanquette de veau",
          prix: "19,00 €",
          description: "Accompagnements de saison",
          disponible: true
        },
        {
          id: "plat-7",
          nom: "Côte de veau rôtie",
          prix: "22,00 €",
          description: "Légumes racines, jus naturel",
          disponible: true
        }
      ]
    },
    {
      id: "cat-3",
      nom: "Desserts",
      ordre: 3,
      plats: [
        {
          id: "plat-8",
          nom: "Tarte tatin maison",
          prix: "7,00 €",
          description: "Avec crème fraîche",
          disponible: true
        },
        {
          id: "plat-9",
          nom: "Fondant au chocolat",
          prix: "8,00 €",
          description: "Glace vanille",
          disponible: true
        },
        {
          id: "plat-10",
          nom: "Panna cotta",
          prix: "7,00 €",
          description: "Coulis de fruits rouges",
          disponible: true
        }
      ]
    }
  ]
};

// Données démo — Avis clients
const DEMO_REVIEWS = [
  {
    id: "avis-demo-1",
    prenom: "Claire M.",
    note: 5,
    texte: "Une adresse que l'on garde précieusement. Accueil chaleureux, carte courte mais parfaitement maîtrisée. On reviendra sans hésiter.",
    date: offsetDate(-5),
    statut: "visible",
    source: "demo"
  },
  {
    id: "avis-demo-2",
    prenom: "Pierre D.",
    note: 5,
    texte: "Excellente découverte ! Les vins sont bien choisis et les accords mets-vins parfaitement pensés. Le service est aux petits soins.",
    date: offsetDate(-12),
    statut: "visible",
    source: "demo"
  },
  {
    id: "avis-demo-3",
    prenom: "Sophie et Marc T.",
    note: 4,
    texte: "Très bonne soirée en amoureux. Cadre intime, cuisine soignée. Peut-être un peu bruyant le samedi soir, mais rien de rédhibitoire.",
    date: offsetDate(-18),
    statut: "visible",
    source: "demo"
  },
  {
    id: "avis-demo-4",
    prenom: "Isabelle R.",
    note: 5,
    texte: "J'ai organisé un repas d'anniversaire pour 8 personnes. L'équipe a été aux petits soins du début à la fin. Merci beaucoup !",
    date: offsetDate(-25),
    statut: "visible",
    source: "demo"
  },
  {
    id: "avis-demo-5",
    prenom: "Thomas B.",
    note: 4,
    texte: "Bon rapport qualité-prix pour le quartier. La formule du déjeuner est particulièrement bien pensée.",
    date: offsetDate(-30),
    statut: "visible",
    source: "demo"
  }
];

// ===== UTILITY FUNCTIONS =====

function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try {
    return JSON.parse(rawValue);
  } catch (e) {
    return fallbackValue;
  }
}

function ensureInitialData() {
  const existing = localStorage.getItem("actions_recues");
  if (!existing) {
    localStorage.setItem("actions_recues", JSON.stringify(DEMO_RESERVATIONS));
  }

  const existingArdoise = localStorage.getItem("contenu_editable");
  if (!existingArdoise) {
    localStorage.setItem("contenu_editable", JSON.stringify({ ardoise: DEMO_ARDOISE }));
  }

  const existingMenu = localStorage.getItem("menuCard");
  if (!existingMenu) {
    localStorage.setItem("menuCard", JSON.stringify(DEMO_MENU));
  }

  const existingReviews = localStorage.getItem("avis_clients");
  if (!existingReviews) {
    localStorage.setItem("avis_clients", JSON.stringify(DEMO_REVIEWS));
  }
}

function showConfirmation(message, duration = 4000) {
  const msg = document.createElement("div");
  msg.className = "confirmation-message show";
  msg.textContent = message;
  document.body.appendChild(msg);
  setTimeout(() => msg.remove(), duration);
}

// ===== LOGIN & AUTH =====

function togglePasswordVisibility() {
  const input = document.getElementById("password");
  const toggle = document.getElementById("togglePassword");
  if (input.type === "password") {
    input.type = "text";
    toggle.textContent = "🙈";
  } else {
    input.type = "password";
    toggle.textContent = "👁️";
  }
}

function handleLogin(event) {
  event.preventDefault();
  const password = document.getElementById("password").value;
  const errorDiv = document.getElementById("loginError");

  if (password === PASSWORD) {
    sessionStorage.setItem("adminLoggedIn", "true");
    document.getElementById("loginContainer").classList.add("hidden");
    document.getElementById("adminContainer").classList.add("logged-in");
    document.getElementById("adminContainer").style.display = "block";
    initDashboard();
  } else {
    errorDiv.classList.add("show");
    errorDiv.textContent = "❌ Mot de passe incorrect";
    setTimeout(() => errorDiv.classList.remove("show"), 4000);
  }
}

function handleLogout() {
  sessionStorage.removeItem("adminLoggedIn");
  document.getElementById("loginContainer").classList.remove("hidden");
  document.getElementById("adminContainer").classList.remove("logged-in");
  document.getElementById("adminContainer").style.display = "none";
  document.getElementById("password").value = "";
  document.getElementById("loginForm").reset();
}

// Vérifier si l'utilisateur est déjà connecté
function checkAuth() {
  if (sessionStorage.getItem("adminLoggedIn") === "true") {
    document.getElementById("loginContainer").classList.add("hidden");
    document.getElementById("adminContainer").classList.add("logged-in");
    document.getElementById("adminContainer").style.display = "block";
    initDashboard();
  }
}

// ===== DASHBOARD INITIALIZATION =====

function initDashboard() {
  ensureInitialData();
  updateTodayView();
  initializeCalendar();
  loadReservations();
  loadMenu();
  loadReviews();
  updateKPIs();
}

function updateTodayView() {
  const today = new Date();
  const options = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
  const dateStr = today.toLocaleDateString("fr-FR", options);
  document.getElementById("todayDate").textContent = dateStr;

  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  const todayStr = today.toISOString().split('T')[0];
  const todayReservations = reservations.filter(r => r.date === todayStr);
  const pendingToday = todayReservations.filter(r => r.statut === "En attente");

  // Section "En attente"
  const pendingListDiv = document.getElementById("todayPendingList");
  if (pendingToday.length === 0) {
    pendingListDiv.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">Aucune réservation en attente</p>';
  } else {
    pendingListDiv.innerHTML = pendingToday.map(r => createReservationCard(r, true)).join("");
  }

  // Section "Toutes les réservations"
  const allListDiv = document.getElementById("todayAllList");
  if (todayReservations.length === 0) {
    allListDiv.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">Aucune réservation aujourd\'hui</p>';
  } else {
    allListDiv.innerHTML = todayReservations.map(r => createReservationCard(r, false)).join("");
  }
}

// ===== CALENDAR & FILTERING =====

function initializeCalendar() {
  const calendarDiv = document.getElementById("calendarWeek");
  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  const today = new Date();

  calendarDiv.innerHTML = "";

  for (let i = 0; i < 7; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];
    const dayName = date.toLocaleDateString("fr-FR", { weekday: "short" });
    const dayNum = date.getDate();

    const reservationsOnDate = reservations.filter(r => r.date === dateStr);
    const couverts = reservationsOnDate.reduce((sum, r) => sum + parseInt(r.couverts || 0), 0);

    const dayDiv = document.createElement("div");
    dayDiv.className = `calendar-day ${i === 0 ? "today" : ""}`;
    dayDiv.style.cssText = `
      background-color: var(--card-bg);
      border: 2px solid ${i === 0 ? "var(--accent)" : "var(--border-soft)"};
      border-radius: 8px;
      padding: 1rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
    `;
    dayDiv.onclick = () => selectCalendarDay(dateStr, dayDiv);

    dayDiv.innerHTML = `
      <div style="font-weight: 600; font-size: 0.9rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 0.5rem;">${dayName}</div>
      <div style="font-size: 1.3rem; font-weight: 700; color: var(--accent); margin-bottom: 0.5rem;">${dayNum}</div>
      <div style="font-size: 0.8rem; color: var(--text-secondary);">${couverts} ${couverts > 1 ? "couverts" : "couvert"}</div>
    `;

    calendarDiv.appendChild(dayDiv);

    if (i === 0) {
      dayDiv.style.backgroundColor = "rgba(139, 38, 53, 0.1)";
      selectCalendarDay(dateStr, dayDiv);
    }
  }
}

let selectedCalendarDate = null;

function selectCalendarDay(dateStr, dayElement) {
  selectedCalendarDate = dateStr;
  document.querySelectorAll(".calendar-day").forEach(el => {
    el.style.backgroundColor = "var(--card-bg)";
    el.style.borderColor = "var(--border-soft)";
  });
  dayElement.style.backgroundColor = "rgba(139, 38, 53, 0.15)";
  dayElement.style.borderColor = "var(--accent)";

  loadReservations();
}

let currentServiceFilter = "tous";

function filterByService(service) {
  currentServiceFilter = service;
  document.querySelectorAll("[data-filter]").forEach(btn => btn.classList.remove("active"));
  document.querySelector(`[data-filter="${service}"]`).classList.add("active");
  loadReservations();
}

function loadReservations() {
  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  const selectedDate = selectedCalendarDate || new Date().toISOString().split('T')[0];

  let filtered = reservations.filter(r => r.date === selectedDate);
  if (currentServiceFilter !== "tous") {
    filtered = filtered.filter(r => r.service === currentServiceFilter);
  }

  const listDiv = document.getElementById("reservationsList");
  const titleDiv = document.getElementById("reservationListTitle");

  if (filtered.length === 0) {
    listDiv.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">Aucune réservation pour cette sélection</p>';
    titleDiv.textContent = "Réservations";
  } else {
    listDiv.innerHTML = filtered.map(r => createReservationCard(r, false)).join("");
    const count = filtered.length;
    titleDiv.textContent = `Réservations (${count})`;
  }
}

function createReservationCard(reservation, showButtons = true) {
  const statusColors = {
    "En attente": "var(--warning)",
    "Confirmée": "var(--success)",
    "Annulée": "var(--danger)"
  };

  return `
    <div class="reservation-card ${reservation.source === "demo" ? "demo" : ""}" data-id="${reservation.id}">
      <div class="reservation-header">
        <div class="reservation-info">
          <h3>${reservation.prenom}</h3>
          <p>📞 ${reservation.telephone}</p>
          <p>${reservation.couverts} ${reservation.couverts > 1 ? "couverts" : "couvert"} · ${reservation.service === "dejeuner" ? "🍽️ Déjeuner" : "🍷 Dîner"}</p>
          ${reservation.message ? `<p style="margin-top: 0.5rem; font-style: italic; color: var(--text-secondary);">💬 ${reservation.message}</p>` : ""}
        </div>
        <div class="reservation-badge">
          <span class="badge" style="background-color: rgba(${statusColors[reservation.statut] === "var(--warning)" ? "182, 136, 63" : statusColors[reservation.statut] === "var(--success)" ? "61, 155, 95" : "166, 72, 72"}, 0.2); color: ${statusColors[reservation.statut]};">
            ${reservation.statut}
          </span>
        </div>
      </div>
      ${showButtons ? `
        <div class="reservation-actions">
          <button class="btn btn-success" onclick="setReservationStatus('${reservation.id}', 'Confirmée')" ${reservation.statut === "Confirmée" ? "disabled" : ""}>✓ Confirmer</button>
          <button class="btn btn-danger" onclick="setReservationStatus('${reservation.id}', 'Annulée')" ${reservation.statut === "Annulée" ? "disabled" : ""}>✗ Annuler</button>
        </div>
      ` : ""}
    </div>
  `;
}

function setReservationStatus(reservationId, newStatus) {
  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  const reservation = reservations.find(r => r.id === reservationId);
  
  if (reservation) {
    reservation.statut = newStatus;
    reservation.clientConfirmationSent = false;
    localStorage.setItem("actions_recues", JSON.stringify(reservations));
    updateTodayView();
    loadReservations();
    initializeCalendar();
    updateKPIs();
    showConfirmation(`✓ Réservation marquée comme "${newStatus}"`);
  }
}

// ===== KPI UPDATES =====

function updateKPIs() {
  const reservations = safeParse(localStorage.getItem("actions_recues"), []);
  const today = new Date().toISOString().split('T')[0];
  const weekStart = new Date();
  const weekEnd = new Date();
  weekEnd.setDate(weekEnd.getDate() + 7);
  const weekStartStr = weekStart.toISOString().split('T')[0];
  const weekEndStr = weekEnd.toISOString().split('T')[0];

  // Demandes aujourd'hui
  const todayCount = reservations.filter(r => r.date === today).length;
  document.getElementById("kpiToday").textContent = todayCount;

  // En attente de confirmation
  const pendingCount = reservations.filter(r => r.statut === "En attente").length;
  document.getElementById("kpiPending").textContent = pendingCount;

  // Confirmées cette semaine
  const weekConfirmed = reservations.filter(r => 
    r.statut === "Confirmée" && 
    r.date >= weekStartStr && 
    r.date <= weekEndStr
  ).length;
  document.getElementById("kpiWeek").textContent = weekConfirmed;
}

// ===== MENU & ARDOISE =====

// Toggle affichage champs formule
document.addEventListener("DOMContentLoaded", () => {
  const formuleCheckbox = document.getElementById("formuleActive");
  if (formuleCheckbox) {
    formuleCheckbox.addEventListener("change", () => {
      document.getElementById("formuleFields").style.display = formuleCheckbox.checked ? "block" : "none";
    });
  }
});

function saveArdoise(event) {
  event.preventDefault();

  const ardoise = {
    disponible: document.getElementById("ardoiseAvailable").checked,
    plat: {
      nom: document.getElementById("ardoisePlat").value,
      prix: document.getElementById("ardoisePlatPrix").value,
      note: document.getElementById("ardoiseNote").value
    },
    entree: {
      nom: document.getElementById("ardoiseEntree").value || null,
      prix: document.getElementById("ardoiseEntreePrix").value || null
    },
    dessert: {
      nom: document.getElementById("ardoiseDessert").value || null,
      prix: document.getElementById("ardoiseDessertPrix").value || null
    },
    formule: {
      active: document.getElementById("formuleActive").checked,
      prix: document.getElementById("formulePrix").value || null,
      label: "Entrée + Plat + Dessert"
    }
  };

  // Nettoyer les valeurs nulles
  if (!ardoise.entree.nom) ardoise.entree = null;
  if (!ardoise.dessert.nom) ardoise.dessert = null;
  if (!ardoise.formule.active) ardoise.formule = null;

  const content = safeParse(localStorage.getItem("contenu_editable"), {});
  content.ardoise = ardoise;
  localStorage.setItem("contenu_editable", JSON.stringify(content));

  document.getElementById("ardoiseForm").reset();
  document.getElementById("formuleFields").style.display = "none";

  const confirmation = document.getElementById("ardoiseConfirmation");
  confirmation.style.display = "block";
  setTimeout(() => confirmation.style.display = "none", 4000);

  showConfirmation("✓ Ardoise mise à jour !");
}

function loadMenu() {
  const menu = safeParse(localStorage.getItem("menuCard"), DEMO_MENU);
  const container = document.getElementById("categoriesContainer");
  container.innerHTML = "";

  menu.categories.forEach((category, catIndex) => {
    const catDiv = document.createElement("div");
    catDiv.style.cssText = "border: 1px solid var(--border-soft); border-radius: 8px; padding: 1.5rem;";
    catDiv.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h4 style="font-size: 1.1rem; margin: 0; color: var(--text-main);">${category.nom}</h4>
        <div style="display: flex; gap: 0.5rem;">
          <button type="button" class="btn btn-secondary" onclick="deleteCategory(${catIndex})" style="padding: 0.4rem 0.8rem; font-size: 0.85rem;">✕ Supprimer</button>
        </div>
      </div>

      <div style="display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem;">
        ${category.plats.map((plat, platIndex) => `
          <div style="display: grid; grid-template-columns: 1fr 150px 80px auto; gap: 0.8rem; align-items: center; padding: 1rem; background-color: var(--bg-main); border-radius: 4px;">
            <input type="text" class="dish-name" value="${plat.nom}" onchange="updateDish(${catIndex}, ${platIndex}, 'nom', this.value)" placeholder="Nom du plat" style="padding: 0.5rem; border: 1px solid var(--border-soft); border-radius: 4px; font-size: 0.9rem;">
            <input type="text" class="dish-price" value="${plat.prix}" onchange="updateDish(${catIndex}, ${platIndex}, 'prix', this.value)" placeholder="Prix" style="padding: 0.5rem; border: 1px solid var(--border-soft); border-radius: 4px; font-size: 0.9rem;">
            <label style="display: flex; align-items: center; gap: 0.3rem; font-size: 0.9rem; cursor: pointer;">
              <input type="checkbox" ${plat.disponible ? "checked" : ""} onchange="updateDish(${catIndex}, ${platIndex}, 'disponible', this.checked)" style="width: 16px; height: 16px; cursor: pointer;">
              <span>Dispo</span>
            </label>
            <button type="button" class="btn btn-danger" onclick="deleteDish(${catIndex}, ${platIndex})" style="padding: 0.4rem 0.8rem; font-size: 0.85rem;">×</button>
          </div>
        `).join("")}
      </div>

      <button type="button" class="btn btn-secondary" onclick="addDishToCategory(${catIndex})" style="padding: 0.5rem 1rem; font-size: 0.9rem;">+ Ajouter un plat</button>
    `;
    container.appendChild(catDiv);
  });
}

function updateDish(catIndex, platIndex, field, value) {
  const menu = safeParse(localStorage.getItem("menuCard"), DEMO_MENU);
  if (menu.categories[catIndex] && menu.categories[catIndex].plats[platIndex]) {
    menu.categories[catIndex].plats[platIndex][field] = value;
    localStorage.setItem("menuCard", JSON.stringify(menu));
  }
}

function deleteDish(catIndex, platIndex) {
  const menu = safeParse(localStorage.getItem("menuCard"), DEMO_MENU);
  if (menu.categories[catIndex]) {
    menu.categories[catIndex].plats.splice(platIndex, 1);
    localStorage.setItem("menuCard", JSON.stringify(menu));
    loadMenu();
    showConfirmation("✓ Plat supprimé");
  }
}

function addDishToCategory(catIndex) {
  const menu = safeParse(localStorage.getItem("menuCard"), DEMO_MENU);
  if (menu.categories[catIndex]) {
    menu.categories[catIndex].plats.push({
      id: `plat-${Date.now()}`,
      nom: "Nouveau plat",
      prix: "0,00 €",
      description: "",
      disponible: true
    });
    localStorage.setItem("menuCard", JSON.stringify(menu));
    loadMenu();
  }
}

function deleteCategory(catIndex) {
  if (confirm("Êtes-vous sûr de vouloir supprimer cette catégorie et tous ses plats ?")) {
    const menu = safeParse(localStorage.getItem("menuCard"), DEMO_MENU);
    menu.categories.splice(catIndex, 1);
    localStorage.setItem("menuCard", JSON.stringify(menu));
    loadMenu();
    showConfirmation("✓ Catégorie supprimée");
  }
}

function addCategory() {
  const menu = safeParse(localStorage.getItem("menuCard"), DEMO_MENU);
  const newOrder = menu.categories.length + 1;
  menu.categories.push({
    id: `cat-${Date.now()}`,
    nom: "Nouvelle catégorie",
    ordre: newOrder,
    plats: []
  });
  localStorage.setItem("menuCard", JSON.stringify(menu));
  loadMenu();
}

function saveMenu(event) {
  event.preventDefault();
  showConfirmation("✓ Carte enregistrée avec succès !");
  
  const confirmation = document.getElementById("menuConfirmation");
  confirmation.style.display = "block";
  setTimeout(() => confirmation.style.display = "none", 4000);
}

// ===== AVIS CLIENTS =====

function loadReviews() {
  const reviews = safeParse(localStorage.getItem("avis_clients"), DEMO_REVIEWS);
  const listDiv = document.getElementById("reviewsList");
  const pendingBadge = document.getElementById("reviewsPendingBadge");

  const pendingCount = reviews.filter(r => r.statut === "en_attente").length;
  pendingBadge.textContent = `${pendingCount} en attente`;

  const visibleReviews = reviews.filter(r => r.statut === "visible");

  if (reviews.length === 0) {
    listDiv.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">Aucun avis pour le moment</p>';
  } else {
    // Afficher les en attente en premier
    const sorted = [
      ...reviews.filter(r => r.statut === "en_attente"),
      ...reviews.filter(r => r.statut !== "en_attente")
    ];
    listDiv.innerHTML = sorted.map(review => createReviewCard(review)).join("");
  }
}

function createReviewCard(review) {
  const stars = "★".repeat(review.note) + "☆".repeat(5 - review.note);
  const daysAgo = Math.floor((new Date() - new Date(review.date)) / (1000 * 60 * 60 * 24));
  const dateText = daysAgo === 0 ? "aujourd'hui" : daysAgo === 1 ? "hier" : `il y a ${daysAgo} jours`;

  return `
    <div class="review-card" style="${review.statut === "en_attente" ? "border-left: 4px solid var(--warning);" : ""}">
      <div class="review-header">
        <div>
          <div class="review-rating" style="font-size: 0.95rem;">${stars}</div>
          <div class="review-author">${review.prenom}</div>
          <div style="font-size: 0.85rem; color: var(--text-secondary);">${dateText}</div>
        </div>
        ${review.statut === "en_attente" ? `<span class="badge badge-attente">En attente</span>` : ""}
      </div>
      <div class="review-text">"${review.texte}"</div>
      <div class="review-actions">
        <button class="btn btn-success" onclick="setReviewStatus('${review.id}', 'visible')" ${review.statut === "visible" ? "disabled" : ""}>✓ Afficher</button>
        <button class="btn btn-danger" onclick="setReviewStatus('${review.id}', 'masque')" ${review.statut === "masque" ? "disabled" : ""}>✗ Masquer</button>
      </div>
    </div>
  `;
}

function setReviewStatus(reviewId, newStatus) {
  const reviews = safeParse(localStorage.getItem("avis_clients"), DEMO_REVIEWS);
  const review = reviews.find(r => r.id === reviewId);
  
  if (review) {
    review.statut = newStatus;
    localStorage.setItem("avis_clients", JSON.stringify(reviews));
    loadReviews();
    showConfirmation(`✓ Avis ${newStatus === "visible" ? "affiché" : newStatus === "masque" ? "masqué" : "modéré"}`);
  }
}

// ===== TAB SWITCHING =====

function switchTab(tabName) {
  document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  
  document.getElementById(`tab-${tabName}`).classList.add("active");
  document.querySelector(`[data-tab="${tabName}"]`).classList.add("active");
}

// ===== INIT ON PAGE LOAD =====

document.addEventListener("DOMContentLoaded", () => {
  ensureInitialData();
  checkAuth();
});
>>>