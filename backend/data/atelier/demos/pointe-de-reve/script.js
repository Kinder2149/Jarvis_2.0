// ===== UTILITY FUNCTIONS =====

function safeParse(key, fallback) {
  if (!key) return fallback;
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch (e) {
    return fallback;
  }
}

function smoothScroll(selector) {
  const element = document.querySelector(selector);
  if (element) {
    element.scrollIntoView({ behavior: "smooth" });
  }
}

// ===== MENU TABS =====

function initMenuTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".menu-tab-content");

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const targetTab = button.getAttribute("data-tab");

      // Remove active class from all buttons and contents
      tabButtons.forEach((btn) => btn.classList.remove("active"));
      tabContents.forEach((content) => content.classList.remove("active"));

      // Add active class to clicked button and corresponding content
      button.classList.add("active");
      const targetContent = document.getElementById(targetTab);
      if (targetContent) {
        targetContent.classList.add("active");
      }
    });
  });
}

// ===== ARDOISE (BLACKBOARD) =====

function updateArdoiseDisplay() {
  const ardoise = safeParse("DEMO_ARDOISE", {});
  const disponible = localStorage.getItem("DEMO_ARDOISE_DISPONIBLE");

  // If ardoise is not available, hide the section
  if (disponible === "false") {
    const ardoiseSection = document.getElementById("ardoise");
    if (ardoiseSection) {
      ardoiseSection.style.display = "none";
    }
    return;
  }

  // Show ardoise section if it was hidden
  const ardoiseSection = document.getElementById("ardoise");
  if (ardoiseSection) {
    ardoiseSection.style.display = "";
  }

  // Update plat (main dish)
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

  // Update entree (starter)
  if (ardoise.entree) {
    const entreeNom = document.getElementById("ardoise-entree-nom");
    if (entreeNom) entreeNom.textContent = ardoise.entree;
  }

  if (ardoise.entree_prix) {
    const entreePrix = document.getElementById("ardoise-entree-prix");
    if (entreePrix) entreePrix.textContent = ardoise.entree_prix;
  }

  // Update dessert
  if (ardoise.dessert) {
    const dessertNom = document.getElementById("ardoise-dessert-nom");
    if (dessertNom) dessertNom.textContent = ardoise.dessert;
  }

  if (ardoise.dessert_prix) {
    const dessertPrix = document.getElementById("ardoise-dessert-prix");
    if (dessertPrix) dessertPrix.textContent = ardoise.dessert_prix;
  }
}

// ===== RESERVATION FORM =====

function initReservationForm() {
  const dateInput = document.getElementById("res-date");
  const messageTextarea = document.getElementById("res-message");
  const stepperMinus = document.getElementById("stepper-minus");
  const stepperPlus = document.getElementById("stepper-plus");
  const personnesInput = document.getElementById("res-personnes");

  // Set date input constraints: min = today, max = today + 90 days
  if (dateInput) {
    const today = new Date();
    const todayISO = today.toISOString().split("T")[0];
    const maxDate = new Date(today);
    maxDate.setDate(maxDate.getDate() + 90);
    const maxDateISO = maxDate.toISOString().split("T")[0];

    dateInput.setAttribute("min", todayISO);
    dateInput.setAttribute("max", maxDateISO);
  }

  // Stepper functionality
  if (stepperMinus) {
    stepperMinus.addEventListener("click", (e) => {
      e.preventDefault();
      const currentValue = parseInt(personnesInput.value) || 2;
      if (currentValue > 1) {
        personnesInput.value = currentValue - 1;
      }
    });
  }

  if (stepperPlus) {
    stepperPlus.addEventListener("click", (e) => {
      e.preventDefault();
      const currentValue = parseInt(personnesInput.value) || 2;
      if (currentValue < 12) {
        personnesInput.value = currentValue + 1;
      }
    });
  }

  // Character counter for message textarea
  if (messageTextarea) {
    messageTextarea.addEventListener("input", () => {
      const charCurrent = document.getElementById("char-current");
      if (charCurrent) {
        charCurrent.textContent = messageTextarea.value.length;
      }
    });
  }
}

// ===== FORM SUBMISSION =====

function handleFormSubmit(e) {
  e.preventDefault();

  // Retrieve form values from DOM
  const nom = document.getElementById("res-nom")?.value?.trim();
  const email = document.getElementById("res-email")?.value?.trim();
  const tel = document.getElementById("res-tel")?.value?.trim();
  const date = document.getElementById("res-date")?.value;
  const heure = document.getElementById("res-heure")?.value;
  const personnes = parseInt(document.getElementById("res-personnes")?.value) || 2;
  const message = document.getElementById("res-message")?.value?.trim();

  // Validate required fields
  if (!nom || !email || !tel || !date || !heure) {
    alert("Veuillez remplir tous les champs obligatoires.");
    return;
  }

  // Create reservation object (exact contract from brief)
  const reservation = {
    id: Date.now().toString(),
    nom: nom,
    email: email,
    tel: tel,
    date: date,
    heure: heure,
    personnes: personnes,
    message: message || "",
    statut: "En attente",
    source: "client",
    createdAt: new Date().toISOString()
  };

  // Get existing reservations from localStorage
  const reservations = safeParse("DEMO_RESERVATIONS", []);

  // Add new reservation
  reservations.push(reservation);

  // Save to localStorage
  localStorage.setItem("DEMO_RESERVATIONS", JSON.stringify(reservations));

  // Reset form
  const form = document.getElementById("reservationForm");
  if (form) {
    form.reset();
  }

  // Reset personnes to 2
  const personnesInput = document.getElementById("res-personnes");
  if (personnesInput) {
    personnesInput.value = 2;
  }

  // Reset character counter
  const charCurrent = document.getElementById("char-current");
  if (charCurrent) {
    charCurrent.textContent = 0;
  }

  // Show confirmation message
  const confirmationMessage = document.getElementById("confirmationMessage");
  if (confirmationMessage) {
    confirmationMessage.classList.remove("hidden");

    // Hide message after 4 seconds
    setTimeout(() => {
      confirmationMessage.classList.add("hidden");
    }, 4000);
  }

  // Smooth scroll to confirmation
  smoothScroll("#reservation");
}

// ===== STORAGE LISTENER (real-time sync) =====

window.addEventListener("storage", (e) => {
  if (e.key === "DEMO_ARDOISE" || e.key === "DEMO_ARDOISE_DISPONIBLE") {
    updateArdoiseDisplay();
  }
});

// ===== INITIALIZATION =====

document.addEventListener("DOMContentLoaded", () => {
  // Initialize menu tabs
  initMenuTabs();

  // Initialize ardoise display
  updateArdoiseDisplay();

  // Initialize reservation form
  initReservationForm();

  // Attach form submission handler
  const reservationForm = document.getElementById("reservationForm");
  if (reservationForm) {
    reservationForm.addEventListener("submit", handleFormSubmit);
  }

  // Set footer year
  const footerYear = document.getElementById("footer-year");
  if (footerYear) {
    footerYear.textContent = new Date().getFullYear();
  }
});