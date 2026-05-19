/**
 * script.js — Restaurant Pointe de Rêve
 * Gestion client : réservations, ardoise, menu
 * Contrat localStorage : DEMO_RESERVATIONS, DEMO_ARDOISE, DEMO_ARDOISE_DISPONIBLE
 */

// ====================================================================
// UTILITAIRES
// ====================================================================

/**
 * Parse sécurisé localStorage
 */
function safeParse(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key));
    return value || fallback;
  } catch (e) {
    return fallback;
  }
}

/**
 * Scroll lisse vers un élément
 */
function smoothScroll(selector) {
  const element = document.querySelector(selector);
  if (element) {
    element.scrollIntoView({ behavior: "smooth" });
  }
}

// ====================================================================
// MENU TABS
// ====================================================================

/**
 * Initialise les onglets du menu (Entrées/Plats/Desserts)
 */
function initMenuTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn[data-tab]");
  const tabContents = document.querySelectorAll(".menu-tab-content");

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabName = btn.getAttribute("data-tab");

      // Retirer active de tous les boutons et contenus
      tabButtons.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      // Ajouter active au bouton cliqué et au contenu correspondant
      btn.classList.add("active");
      const activeContent = document.querySelector(
        `.menu-tab-content[data-tab-content="${tabName}"]`
      );
      if (activeContent) {
        activeContent.classList.add("active");
      }
    });
  });
}

// ====================================================================
// ARDOISE DU JOUR
// ====================================================================

/**
 * Met à jour l'affichage de l'ardoise du jour
 */
function updateArdoiseDisplay() {
  const ardoise = safeParse("DEMO_ARDOISE", {});
  const disponible = localStorage.getItem("DEMO_ARDOISE_DISPONIBLE");

  const ardoiseSection = document.getElementById("ardoise");
  const ardoiseEmpty = document.getElementById("ardoise-empty");

  // Si l'ardoise n'est pas disponible
  if (disponible === "false") {
    if (ardoiseSection) ardoiseSection.classList.add("hidden");
    if (ardoiseEmpty) ardoiseEmpty.classList.remove("hidden");
    return;
  }

  // L'ardoise est disponible
  if (ardoiseSection) ardoiseSection.classList.remove("hidden");
  if (ardoiseEmpty) ardoiseEmpty.classList.add("hidden");

  // Structure PLATE : ardoise.plat EST la string, jamais ardoise.plat.nom
  if (ardoise.plat) {
    const platNom = document.getElementById("ardoise-plat-nom");
    if (platNom) platNom.textContent = ardoise.plat;
  }
  if (ardoise.plat_prix) {
    const platPrix = document.getElementById("ardoise-plat-prix");
    if (platPrix) platPrix.textContent = ardoise.plat_prix;
  }
  if (ardoise.plat_note) {
    const platNote = document.getElementById("ardoise-plat-note");
    if (platNote) platNote.textContent = ardoise.plat_note;
  }
  if (ardoise.entree) {
    const entreNom = document.getElementById("ardoise-entree-nom");
    if (entreNom) entreNom.textContent = ardoise.entree;
  }
  if (ardoise.entree_prix) {
    const entrePrix = document.getElementById("ardoise-entree-prix");
    if (entrePrix) entrePrix.textContent = ardoise.entree_prix;
  }
  if (ardoise.dessert) {
    const dessertNom = document.getElementById("ardoise-dessert-nom");
    if (dessertNom) dessertNom.textContent = ardoise.dessert;
  }
  if (ardoise.dessert_prix) {
    const dessertPrix = document.getElementById("ardoise-dessert-prix");
    if (dessertPrix) dessertPrix.textContent = ardoise.dessert_prix;
  }
}

// ====================================================================
// FORMULAIRE RÉSERVATION
// ====================================================================

/**
 * Initialise le formulaire de réservation
 */
function initReservationForm() {
  const dateInput = document.getElementById("res-date");
  const stepperMinus = document.getElementById("stepper-minus");
  const stepperPlus = document.getElementById("stepper-plus");
  const personnesInput = document.getElementById("res-personnes");
  const messageInput = document.getElementById("res-message");
  const charCounter = document.getElementById("char-current");

  // === Dates min/max ===
  if (dateInput) {
    const today = new Date();
    const minDate = today.toISOString().split("T")[0];
    const maxDate = new Date(today.getTime() + 90 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0];
    dateInput.setAttribute("min", minDate);
    dateInput.setAttribute("max", maxDate);
  }

  // === Stepper ===
  if (stepperMinus && personnesInput) {
    stepperMinus.addEventListener("click", (e) => {
      e.preventDefault();
      let val = parseInt(personnesInput.value) || 2;
      if (val > 1) {
        val--;
        personnesInput.value = val;
      }
    });
  }

  if (stepperPlus && personnesInput) {
    stepperPlus.addEventListener("click", (e) => {
      e.preventDefault();
      let val = parseInt(personnesInput.value) || 2;
      if (val < 12) {
        val++;
        personnesInput.value = val;
      }
    });
  }

  // === Compteur caractères ===
  if (messageInput && charCounter) {
    messageInput.addEventListener("input", () => {
      charCounter.textContent = messageInput.value.length;
    });
  }
}

/**
 * Gère la soumission du formulaire de réservation
 */
function handleFormSubmit(e) {
  e.preventDefault();

  const form = e.target;
  const nom = document.getElementById("res-nom");
  const email = document.getElementById("res-email");
  const tel = document.getElementById("res-tel");
  const date = document.getElementById("res-date");
  const heure = document.getElementById("res-heure");
  const personnes = document.getElementById("res-personnes");
  const message = document.getElementById("res-message");

  // Construire l'objet réservation avec le contrat exact
  const formData = {
    id: Date.now().toString(),
    nom: nom?.value || "",
    email: email?.value || "",
    tel: tel?.value || "",
    date: date?.value || "",
    heure: heure?.value || "",
    personnes: parseInt(personnes?.value) || 2,
    message: message?.value || "",
    statut: "En attente",
    source: "client",
    createdAt: new Date().toISOString(),
  };

  // Récupérer les réservations existantes
  const reservations = safeParse("DEMO_RESERVATIONS", []);
  reservations.push(formData);
  localStorage.setItem("DEMO_RESERVATIONS", JSON.stringify(reservations));

  // Réinitialiser le formulaire
  form.reset();
  if (personnes) personnes.value = "2";
  const charCounter = document.getElementById("char-current");
  if (charCounter) charCounter.textContent = "0";

  // Afficher message de confirmation
  const confirmationMessage = document.getElementById("confirmationMessage");
  if (confirmationMessage) {
    confirmationMessage.classList.remove("hidden");
    // Masquer après 5 secondes
    setTimeout(() => {
      confirmationMessage.classList.add("hidden");
    }, 5000);
  }

  // Scroll vers le message
  smoothScroll("#confirmationMessage");
}

// ====================================================================
// LISTENERS GLOBAUX
// ====================================================================

/**
 * Écoute les changements localStorage depuis d'autres onglets/fenêtres
 */
window.addEventListener("storage", (e) => {
  if (e.key === "DEMO_ARDOISE" || e.key === "DEMO_ARDOISE_DISPONIBLE") {
    updateArdoiseDisplay();
  }
});

// ====================================================================
// INITIALISATION
// ====================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Initialiser les onglets du menu
  initMenuTabs();

  // Initialiser et afficher l'ardoise
  updateArdoiseDisplay();

  // Initialiser le formulaire de réservation
  initReservationForm();

  // Attacher le listener de soumission
  const reservationForm = document.getElementById("reservationForm");
  if (reservationForm) {
    reservationForm.addEventListener("submit", handleFormSubmit);
  }

  // Mettre à jour l'année du footer
  const yearSpan = document.getElementById("year");
  if (yearSpan) {
    yearSpan.textContent = new Date().getFullYear().toString();
  }
});