// ========================================
// SCRIPT PUBLIC — L'ATELIER CONNECTÉ
// Site client : index.html
// ========================================

// ===== UTILITAIRES =====

function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try { return JSON.parse(rawValue); }
  catch (e) { return fallbackValue; }
}

// ===== DONNÉES PAR DÉFAUT =====

const DEFAULT_MENU = {{DEFAULT_MENU_JS}};

const DEFAULT_ARDOISE = {{DEFAULT_ARDOISE_JS}};

// ===== INITIALISATION DONNÉES =====

function ensureInitialData() {
  if (!localStorage.getItem("menuCard")) {
    localStorage.setItem("menuCard", JSON.stringify(DEFAULT_MENU));
  }
  if (!localStorage.getItem("contenu_editable")) {
    localStorage.setItem("contenu_editable", JSON.stringify({ ardoise: DEFAULT_ARDOISE }));
  }
}

// ===== AFFICHAGE MENU (DYNAMIQUE) =====

function renderMenu() {
  const container = document.getElementById("menu-container");
  if (!container) return;

  const menuData = safeParse(localStorage.getItem("menuCard"), DEFAULT_MENU);
  if (!menuData || !menuData.categories || menuData.categories.length === 0) return;

  container.innerHTML = "";

  // Tabs navigation
  const tabsNav = document.createElement("div");
  tabsNav.className = "menu-tabs";

  const panelsWrapper = document.createDocumentFragment();

  menuData.categories.forEach((category, index) => {
    // Tab button
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "menu-category-btn" + (index === 0 ? " active" : "");
    btn.textContent = category.nom;
    btn.addEventListener("click", () => {
      container.querySelectorAll(".menu-category-btn").forEach(b => b.classList.remove("active"));
      container.querySelectorAll(".menu-category").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("panel-" + category.id).classList.add("active");
    });
    tabsNav.appendChild(btn);

    // Content panel
    const panel = document.createElement("div");
    panel.className = "menu-category" + (index === 0 ? " active" : "");
    panel.id = "panel-" + category.id;

    const grid = document.createElement("div");
    grid.className = "menu-items";

    category.plats.forEach(plat => {
      const item = document.createElement("div");
      item.className = "menu-item" + (!plat.disponible ? " unavailable" : "");

      let html = `<div class="menu-item-header">
        <h4>${plat.nom}</h4>
        <span class="menu-item-price">${plat.prix}</span>
      </div>`;

      if (plat.description) {
        html += `<p class="menu-item-description">${plat.description}</p>`;
      }
      if (plat.signature) {
        html += `<span class="menu-item-signature">★ Signature</span>`;
      }

      item.innerHTML = html;
      grid.appendChild(item);
    });

    panel.appendChild(grid);
    panelsWrapper.appendChild(panel);
  });

  container.appendChild(tabsNav);
  container.appendChild(panelsWrapper);
}

// ===== AFFICHAGE ARDOISE =====

function renderArdoise() {
  const contenueEditable = safeParse(localStorage.getItem("contenu_editable"), { ardoise: DEFAULT_ARDOISE });
  const ardoise = contenueEditable.ardoise || DEFAULT_ARDOISE;

  const container = document.getElementById("ardoise-container");
  if (!container) return;

  if (!ardoise.disponible) {
    container.style.display = "none";
    return;
  }

  container.style.display = "block";

  const cardsDiv = document.getElementById("ardoise-cards");
  if (cardsDiv) {
    cardsDiv.innerHTML = "";

    if (ardoise.entree) {
      cardsDiv.appendChild(buildArdoiseCard("Entrée", ardoise.entree.nom, ardoise.entree.prix, null));
    }
    if (ardoise.plat) {
      cardsDiv.appendChild(buildArdoiseCard("Plat du jour", ardoise.plat.nom, ardoise.plat.prix, ardoise.plat.note || null));
    }
    if (ardoise.dessert) {
      cardsDiv.appendChild(buildArdoiseCard("Dessert", ardoise.dessert.nom, ardoise.dessert.prix, null));
    }
  }

  const formuleDiv = document.getElementById("ardoise-formule");
  const formuleLabelEl = document.getElementById("ardoise-formule-label");
  const formulePrixEl = document.getElementById("ardoise-formule-prix");

  if (formuleDiv && ardoise.formule && ardoise.formule.active) {
    if (formuleLabelEl) formuleLabelEl.textContent = ardoise.formule.label || "";
    if (formulePrixEl) formulePrixEl.textContent = ardoise.formule.prix || "";
    formuleDiv.style.display = "flex";
  } else if (formuleDiv) {
    formuleDiv.style.display = "none";
  }
}

function buildArdoiseCard(label, nom, prix, note) {
  const card = document.createElement("div");
  card.className = "ardoise-card";
  card.innerHTML = `
    <div class="ardoise-card-label">${label}</div>
    <div class="ardoise-card-nom">${nom}</div>
    ${note ? `<div class="ardoise-card-note">${note}</div>` : ""}
    <div class="ardoise-card-prix">${prix}</div>
  `;
  return card;
}

// ===== ANIMATIONS SCROLL =====

function initScrollAnimations() {
  const elements = document.querySelectorAll(".fade-in");
  if (!elements.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  elements.forEach(el => observer.observe(el));
}

// ===== FORMULAIRE RÉSERVATION =====

function initReservationForm() {
  const form = document.getElementById("reservation-form");
  if (!form) return;

  // Date minimum = aujourd'hui
  const dateInput = document.getElementById("date");
  if (dateInput) {
    dateInput.setAttribute("min", new Date().toISOString().split("T")[0]);
  }

  // Service cards
  const serviceCards = document.querySelectorAll(".service-card");
  serviceCards.forEach(card => {
    card.addEventListener("click", () => {
      serviceCards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      const radio = card.querySelector("input[type='radio']");
      if (radio) radio.checked = true;
    });
  });

  // Stepper couverts
  const stepperMinus = document.getElementById("stepper-minus");
  const stepperPlus = document.getElementById("stepper-plus");
  const stepperValue = document.getElementById("stepper-value");
  const couvertsInput = document.getElementById("couverts");

  if (stepperMinus && stepperPlus) {
    stepperMinus.addEventListener("click", (e) => {
      e.preventDefault();
      let val = parseInt(couvertsInput.value);
      if (val > 1) {
        val--;
        couvertsInput.value = val;
        stepperValue.textContent = val;
      }
    });
    stepperPlus.addEventListener("click", (e) => {
      e.preventDefault();
      let val = parseInt(couvertsInput.value);
      if (val < 12) {
        val++;
        couvertsInput.value = val;
        stepperValue.textContent = val;
      }
    });
  }

  // Submit
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const prenom = document.getElementById("prenom").value.trim();
    const telephone = document.getElementById("telephone").value.trim();
    const date = document.getElementById("date").value;
    const serviceChecked = document.querySelector("input[name='service']:checked");
    const service = serviceChecked ? serviceChecked.value : "dejeuner";
    const couvCount = couvertsInput ? couvertsInput.value : "2";
    const message = document.getElementById("message").value.trim();

    const newReservation = {
      id: Date.now(),
      prenom,
      telephone,
      date,
      service,
      couverts: couvCount,
      message,
      statut: "En attente",
      source: "public"
    };

    const existing = safeParse(localStorage.getItem("actions_recues"), []);
    existing.push(newReservation);
    localStorage.setItem("actions_recues", JSON.stringify(existing));

    showConfirmationInline();
    showToast("✓ Demande envoyée — confirmation par téléphone sous 24h");

    // Reset
    form.reset();
    couvertsInput.value = "2";
    stepperValue.textContent = "2";
    serviceCards.forEach((c, i) => {
      c.classList.toggle("active", i === 0);
      const r = c.querySelector("input[type='radio']");
      if (r) r.checked = (i === 0);
    });
  });
}

// ===== CONFIRMATION INLINE =====

function showConfirmationInline() {
  const el = document.getElementById("confirmation-inline");
  if (!el) return;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 5000);
}

// ===== TOAST =====

function showToast(text) {
  const toast = document.getElementById("confirmation-toast");
  if (!toast) return;
  toast.textContent = text;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 4000);
}

// ===== INITIALISATION =====

document.addEventListener("DOMContentLoaded", () => {
  ensureInitialData();
  renderMenu();
  renderArdoise();
  initScrollAnimations();
  initReservationForm();

  window.addEventListener("storage", () => {
    renderMenu();
    renderArdoise();
  });
});
