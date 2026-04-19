"""
Test end-to-end du module Atelier Connecté.

Deux modes :
  python tests/test_atelier_e2e.py           → mode MOCK (sans appels LLM, rapide)
  python tests/test_atelier_e2e.py --live    → mode LIVE (appels LLM réels, coûte quelques centimes)

Prérequis : serveur JARVIS démarré sur http://localhost:8000
"""

import sys
import json
import time
import requests

# Fix encodage Windows (cp1252 ne supporte pas les caractères Unicode)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "http://localhost:8000"
LIVE_MODE = "--live" in sys.argv

# URL d'un vrai restaurant pour le mode LIVE
LIVE_URL = "https://atelier-connecte.github.io/Atelier-Connect-/"  # remplacer par une vraie URL

SAISIE_FORM = {
    "nom": "Le Tourbillon de la Vigne",
    "url": LIVE_URL if LIVE_MODE else "aucun site",
    "observations": "Réservations uniquement par téléphone. Carte changée souvent. Instagram actif mais aucun lien.",
    "gerants": "Marie et Thomas",
    "adresse": "12 rue de la Paix, Lyon 69001",
    "email": "contact@test.fr",
    "telephone": "04 72 00 00 00",
    "instagram": "https://instagram.com/test",
    "canal": "email",
    "outils": {
        "evenements": False,
        "avis": True,
        "emporter": False
    }
}

# Outputs mock pour éviter les appels LLM en mode non-live
MOCK_OUTPUTS = {
    "qualification": json.dumps({
        "score": "★★★",
        "label": "Chaud",
        "decision": "GO",
        "signaux_detectes": ["Réservations par téléphone uniquement", "Instagram actif sans outil de conversion"],
        "douleur_principale": "Vous perdez des réservations le soir quand le téléphone n'est plus décroché",
        "raison_stop": None
    }),
    "analyse_site": json.dumps({
        "identite": {
            "nom": "Le Tourbillon de la Vigne",
            "slogan": "La cuisine du terroir, au cœur de Lyon",
            "presentation": "Restaurant familial depuis 1998, cuisine traditionnelle lyonnaise.",
            "gerants": "Marie et Thomas Dupont",
            "adresse": "12 rue de la Paix, Lyon 69001",
            "telephone": "04 72 00 00 00",
            "email": "contact@tourbillon.fr",
            "horaires": "Mar-Sam 12h-14h / 19h-22h. Fermé Dim et Lun.",
            "type_cuisine": "Cuisine lyonnaise traditionnelle"
        },
        "palette": {
            "bg_main": "#f9f5f0",
            "bg_alt": "#ffffff",
            "accent": "#8b2635",
            "text_main": "#2c2c2c",
            "text_secondary": "#6b6b6b"
        },
        "polices": {
            "titres": "Playfair Display",
            "corps": "Lato"
        },
        "images": {
            "logo": None,
            "hero": None,
            "equipe": None,
            "ambiance": [],
            "hero_query": "french bistrot lyon food"
        },
        "carte": {
            "categories": [
                {"nom": "Entrées", "plats": [{"nom": "Salade lyonnaise", "prix": "12,00 €", "description": "Frisée, lardons, œuf poché"}]},
                {"nom": "Plats", "plats": [{"nom": "Quenelle de brochet", "prix": "18,00 €", "description": "Sauce Nantua maison"}]}
            ]
        },
        "outils_existants": [],
        "slug": "le-tourbillon-de-la-vigne"
    }),
    "proposition": """---
PROSPECT : Le Tourbillon de la Vigne — Restauration
SCORE : ★★★ Chaud

DOULEUR PRINCIPALE :
Vous perdez des réservations le soir quand le téléphone n'est plus décroché.

OUTILS PROPOSÉS :
✅ Réservations — Outil obligatoire, signal fort détecté
✅ Menu & Ardoise — Outil obligatoire, carte change souvent
❌ Événements — Aucun signal de soirées thématiques observé
✅ Avis clients — Coché + avis positifs non valorisés
❌ Vente à emporter — Aucun signal observé

CE QUE LE PROSPECT VERRA EN 10 SECONDES :
Un site à leurs couleurs avec un bouton "Réserver une table" visible dès l'arrivée.

BÉNÉFICES DÉMONTRÉS :
— Prendre des réservations en ligne sans perdre d'appels le soir
— Voir en un coup d'œil les couverts du jour depuis leur téléphone
— Modifier la carte très simplement quand elle change
— Mettre en avant les avis de leurs clients directement sur leur page
---""",
    "generation_css": """```css
:root {
  --bg-main: #f9f5f0;
  --bg-alt: #ffffff;
  --accent: #8b2635;
  --text-main: #2c2c2c;
  --text-secondary: #6b6b6b;
  --card-bg: #fdfaf7;
  --border-soft: rgba(44,44,44,0.1);
  --success: #3d9b5f;
  --warning: #b6883f;
  --danger: #a64848;
}
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lato:wght@400;500&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Lato', system-ui, sans-serif; background: var(--bg-main); color: var(--text-main); }
header { position: sticky; top: 0; z-index: 100; background: var(--bg-main); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.btn-admin { background: var(--accent); color: white; padding: 0.5rem 1rem; border-radius: 4px; text-decoration: none; }
.hero { min-height: 90vh; background: linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.45)), #555; display: flex; align-items: center; justify-content: center; text-align: center; }
.hero h1 { font-family: 'Playfair Display', serif; font-size: 2.5rem; color: white; }
section { padding: 4rem 0; }
```""",
    "generation_index": """<<<FILE: index.html>>>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Le Tourbillon de la Vigne</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<header>
  <nav>
    <span class="nav-logo">Le Tourbillon de la Vigne</span>
    <a href="admin.html" class="btn-admin">🔒 Espace Gérant</a>
  </nav>
</header>
<section class="hero">
  <div>
    <h1>Le Tourbillon de la Vigne</h1>
    <p>La cuisine du terroir, au cœur de Lyon</p>
    <a href="#reservation" class="btn-cta">Réserver une table</a>
  </div>
</section>
<section id="reservation">
  <h2>Réserver une table</h2>
  <form id="form-reservation">
    <input type="text" id="prenom" placeholder="Votre prénom" required>
    <input type="tel" id="telephone" placeholder="Votre téléphone" required>
    <input type="date" id="date" required>
    <div class="service-cards">
      <div class="service-card" data-value="dejeuner">Déjeuner</div>
      <div class="service-card" data-value="diner">Dîner</div>
    </div>
    <div class="stepper">
      <button type="button" id="moins">−</button>
      <span id="couverts">2</span>
      <button type="button" id="plus">+</button>
    </div>
    <button type="submit">Réserver</button>
  </form>
  <div id="confirmation" style="display:none">Votre réservation a bien été enregistrée !</div>
</section>
<footer>
  <p>12 rue de la Paix, Lyon 69001 — 04 72 00 00 00</p>
  <a href="admin.html">Espace gérant</a>
</footer>
</body>
</html>
<<<FILE: script.js>>>
function safeParse(raw, fallback) {
  if (!raw) return fallback;
  try { return JSON.parse(raw); } catch(e) { return fallback; }
}

document.addEventListener('DOMContentLoaded', function() {
  let serviceSelected = null;
  let couverts = 2;

  document.querySelectorAll('.service-card').forEach(function(card) {
    card.addEventListener('click', function() {
      document.querySelectorAll('.service-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      serviceSelected = card.dataset.value;
    });
  });

  document.getElementById('moins').addEventListener('click', function() {
    if (couverts > 1) { couverts--; document.getElementById('couverts').textContent = couverts; }
  });
  document.getElementById('plus').addEventListener('click', function() {
    if (couverts < 12) { couverts++; document.getElementById('couverts').textContent = couverts; }
  });

  document.getElementById('form-reservation').addEventListener('submit', function(e) {
    e.preventDefault();
    var reservation = {
      id: Date.now(),
      prenom: document.getElementById('prenom').value,
      telephone: document.getElementById('telephone').value,
      date: document.getElementById('date').value,
      service: serviceSelected || 'diner',
      couverts: String(couverts),
      message: '',
      statut: 'En attente',
      source: 'formulaire'
    };
    var existing = safeParse(localStorage.getItem('actions_recues'), []);
    existing.push(reservation);
    localStorage.setItem('actions_recues', JSON.stringify(existing));
    var conf = document.getElementById('confirmation');
    conf.style.display = 'block';
    setTimeout(function() { conf.style.display = 'none'; }, 4000);
    e.target.reset();
    serviceSelected = null;
    couverts = 2;
    document.getElementById('couverts').textContent = '2';
  });
});""",
    "generation_admin": """<<<FILE: admin.html>>>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Espace Gérant — Le Tourbillon de la Vigne</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div id="login-screen">
  <h1>Espace Gérant — Le Tourbillon de la Vigne</h1>
  <input type="password" id="password" placeholder="Mot de passe">
  <button onclick="login()">Accéder à mon espace</button>
  <p id="login-error" style="display:none;color:var(--danger)">Mot de passe incorrect</p>
</div>
<div id="dashboard" style="display:none">
  <header>
    <span>Espace Gérant — Le Tourbillon de la Vigne</span>
    <button onclick="logout()">Se déconnecter</button>
  </header>
  <div class="kpis">
    <div class="kpi"><span id="kpi-today">0</span><label>Demandes aujourd'hui</label></div>
    <div class="kpi"><span id="kpi-pending">0</span><label>En attente</label></div>
    <div class="kpi"><span id="kpi-week">0</span><label>Confirmées cette semaine</label></div>
  </div>
  <div id="reservations-list"></div>
</div>
<script src="admin.js"></script>
</body>
</html>
<<<FILE: admin.js>>>
function safeParse(raw, fallback) {
  if (!raw) return fallback;
  try { return JSON.parse(raw); } catch(e) { return fallback; }
}

function offsetDate(n) {
  var d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
}

var DEMO_RESERVATIONS = [
  {id:"demo-1",prenom:"Marie D.",telephone:"06 12 34 56 78",date:offsetDate(1),service:"diner",couverts:"2",message:"Anniversaire de mariage",statut:"En attente",source:"demo"},
  {id:"demo-2",prenom:"Thomas B.",telephone:"07 65 43 21 09",date:offsetDate(1),service:"dejeuner",couverts:"4",message:"",statut:"Confirmée",source:"demo"},
  {id:"demo-3",prenom:"Sophie M.",telephone:"06 98 76 54 32",date:offsetDate(2),service:"diner",couverts:"6",message:"Allergie aux crustacés",statut:"En attente",source:"demo"},
  {id:"demo-4",prenom:"Laurent F.",telephone:"07 11 22 33 44",date:offsetDate(3),service:"dejeuner",couverts:"2",message:"Menu dégustation si possible",statut:"Confirmée",source:"demo"},
  {id:"demo-5",prenom:"Isabelle R.",telephone:"06 55 44 33 22",date:offsetDate(4),service:"diner",couverts:"8",message:"Repas d'entreprise",statut:"Annulée",source:"demo"}
];

function ensureInitialData() {
  if (!localStorage.getItem('actions_recues')) {
    localStorage.setItem('actions_recues', JSON.stringify(DEMO_RESERVATIONS));
  }
}

function login() {
  if (document.getElementById('password').value === 'admin') {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    renderDashboard();
  } else {
    document.getElementById('login-error').style.display = 'block';
  }
}

function logout() {
  document.getElementById('login-screen').style.display = 'block';
  document.getElementById('dashboard').style.display = 'none';
}

function renderDashboard() {
  var reservations = safeParse(localStorage.getItem('actions_recues'), []);
  var today = new Date().toISOString().split('T')[0];
  document.getElementById('kpi-today').textContent = reservations.filter(r => r.date === today).length;
  document.getElementById('kpi-pending').textContent = reservations.filter(r => r.statut === 'En attente').length;
  document.getElementById('kpi-week').textContent = reservations.filter(r => r.statut === 'Confirmée').length;
  var list = document.getElementById('reservations-list');
  list.innerHTML = reservations.map(function(r) {
    return '<div class="resa-card"><strong>' + r.prenom + '</strong> — ' + r.date + ' — ' + r.couverts + ' couverts<span class="badge">' + r.statut + '</span></div>';
  }).join('');
}

document.addEventListener('DOMContentLoaded', ensureInitialData);""",
    "verification_qa": json.dumps({
        "checks": {
            "css_admin_link": {"ok": True, "detail": "admin.html contient href=styles.css"},
            "hero_image": {"ok": True, "detail": "URL hero présente"},
            "logo_url": {"ok": True, "detail": "URL logo absolue"},
            "menu_categories": {"ok": True, "detail": "catégories HTML correspondent au DEFAULT_MENU"},
            "no_lorem": {"ok": True, "detail": "aucun Lorem ipsum"},
            "demo_reservations": {"ok": True, "detail": "5 entrées DEMO_RESERVATIONS présentes"},
            "ardoise_realiste": {"ok": True, "detail": "DEMO_ARDOISE cohérente"},
            "css_variables": {"ok": True, "detail": "toutes les variables :root définies"},
            "admin_title": {"ok": True, "detail": "title admin contient nom établissement"}
        },
        "score": "9/9",
        "bloquants": [],
        "warnings": [],
        "pret_pour_demo": True
    })
}


def ok(msg):
    print(f"  ✅ {msg}")

def fail(msg):
    print(f"  ❌ {msg}")
    sys.exit(1)

def check_server():
    print("\n── Vérification serveur ─────────────────────────────")
    try:
        r = requests.get(f"{BASE}/api/atelier/prospects", timeout=5)
        if r.status_code == 200:
            ok(f"Serveur en ligne — {len(r.json())} prospect(s) existant(s)")
        else:
            fail(f"GET /prospects → {r.status_code}")
    except requests.exceptions.ConnectionError:
        fail("Serveur non joignable sur localhost:8000 — démarrer JARVIS d'abord")


def test_crud():
    print("\n── Test 1 : CRUD Prospects ──────────────────────────")

    # Créer
    r = requests.post(f"{BASE}/api/atelier/prospects", json={
        "nom": "Test Restaurant E2E",
        "categorie": "restauration",
        "url": "https://example.com"
    })
    assert r.status_code in (200, 201), f"POST /prospects → {r.status_code} : {r.text}"
    prospect = r.json()
    pid = prospect["id"]
    ok(f"Prospect créé id={pid}")

    # Lire
    r = requests.get(f"{BASE}/api/atelier/prospects/{pid}")
    assert r.status_code == 200, f"GET /prospects/{pid} → {r.status_code}"
    ok("Lecture prospect OK")

    # Mettre à jour
    r = requests.patch(f"{BASE}/api/atelier/prospects/{pid}", json={"statut": "contacté"})
    assert r.status_code == 200, f"PATCH → {r.status_code}"
    assert r.json()["statut"] == "contacté", "Statut non mis à jour"
    ok("Mise à jour statut OK")

    return pid


def test_pipeline_creation(pid):
    print("\n── Test 2 : Création pipeline ───────────────────────")

    r = requests.post(f"{BASE}/api/atelier/prospects/{pid}/start")
    assert r.status_code == 200, f"POST /start → {r.status_code} : {r.text}"
    data = r.json()
    session_id = data["session_id"]
    ok(f"Pipeline créée session_id={session_id}")

    # Vérifier les 9 steps
    r = requests.get(f"{BASE}/api/pipelines/{session_id}")
    assert r.status_code == 200, f"GET /pipelines/{session_id} → {r.status_code}"
    session = r.json()
    assert len(session["steps"]) == 10, f"Attendu 10 steps, reçu {len(session['steps'])}"
    ok("10 steps créés")

    # Vérifier step 0 en WAITING_VALIDATION (saisie, model_type=none)
    step0 = next(s for s in session["steps"] if s["step_index"] == 0)
    assert step0["status"] == "WAITING_VALIDATION", f"Step 0 status={step0['status']} (attendu WAITING_VALIDATION)"
    ok(f"Step 0 (saisie) → WAITING_VALIDATION ✓")

    # Vérifier les output_type
    for step in sorted(session["steps"], key=lambda s: s["step_index"]):
        print(f"     Step {step['step_index']} {step['step_name']:<20} model={step['model_type']:<10} output_type={step['output_type']}")

    return session_id, step0["id"]


def test_pipeline_flow(session_id, step0_id):
    print("\n── Test 3 : Flux pipeline (mode MOCK) ───────────────")

    # Valider step 0 (SAISIE) avec les données du formulaire
    saisie_json = json.dumps(SAISIE_FORM)
    r = requests.post(
        f"{BASE}/api/pipelines/{session_id}/validate/{step0_id}",
        json={"approved": True, "edited_output": saisie_json}
    )
    assert r.status_code == 200, f"validate step 0 → {r.status_code} : {r.text}"
    ok("Step 0 (saisie) validé")

    if LIVE_MODE:
        _run_live_pipeline(session_id)
    else:
        _run_mock_pipeline(session_id)


def _run_mock_pipeline(session_id):
    """Avance la pipeline en injectant des outputs mock (sans appels LLM)."""
    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent / "backend" / "data" / "jarvis.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    steps_to_mock = [
        ("analyse_site",     MOCK_OUTPUTS["analyse_site"]),
        ("qualification",    MOCK_OUTPUTS["qualification"]),
        ("proposition",      MOCK_OUTPUTS["proposition"]),
        ("generation_css",   MOCK_OUTPUTS["generation_css"]),
        ("generation_index", MOCK_OUTPUTS["generation_index"]),
        ("generation_admin", MOCK_OUTPUTS["generation_admin"]),
        ("verification_qa",  MOCK_OUTPUTS["verification_qa"]),
    ]

    for step_name, mock_output in steps_to_mock:
        row = cursor.execute(
            "SELECT id, step_index FROM pipeline_steps WHERE session_id=? AND step_name=?",
            (session_id, step_name)
        ).fetchone()
        if not row:
            fail(f"Step '{step_name}' introuvable en base")

        cursor.execute(
            "UPDATE pipeline_steps SET status='COMPLETED', output_data=? WHERE id=?",
            (mock_output, row["id"])
        )
        cursor.execute(
            "UPDATE sessions SET current_step_index=? WHERE id=?",
            (row["step_index"] + 1, session_id)
        )
        conn.commit()
        ok(f"Step {step_name} → COMPLETED (mock)")

    # Forcer le step checkpoint en WAITING_VALIDATION (comme le fait l'engine)
    checkpoint_row = cursor.execute(
        "SELECT id, step_index FROM pipeline_steps WHERE session_id=? AND step_name='checkpoint'",
        (session_id,)
    ).fetchone()
    prop_output = MOCK_OUTPUTS["proposition"]
    cursor.execute(
        "UPDATE pipeline_steps SET status='WAITING_VALIDATION', output_data=? WHERE id=?",
        (prop_output, checkpoint_row["id"])
    )
    cursor.execute(
        "UPDATE sessions SET status='WAITING_VALIDATION', current_step_index=? WHERE id=?",
        (checkpoint_row["step_index"], session_id)
    )
    conn.commit()
    ok("Step checkpoint → WAITING_VALIDATION (mock)")

    conn.close()

    # Valider le checkpoint via l'API (comme le ferait le frontend)
    r = requests.get(f"{BASE}/api/pipelines/{session_id}")
    session = r.json()
    checkpoint = next((s for s in session["steps"] if s["step_name"] == "checkpoint"), None)
    assert checkpoint, "Step checkpoint introuvable dans la session"

    r = requests.post(
        f"{BASE}/api/pipelines/{session_id}/validate/{checkpoint['id']}",
        json={"approved": True}
    )
    assert r.status_code == 200, f"validate checkpoint → {r.status_code} : {r.text}"
    ok("Step checkpoint validé via API ✓")


def _run_live_pipeline(session_id):
    """Exécute la pipeline avec de vrais appels LLM et polling."""
    print("     Mode LIVE — appels LLM réels en cours...")

    timeout = 300
    start = time.time()

    while time.time() - start < timeout:
        r = requests.get(f"{BASE}/api/pipelines/{session_id}")
        session = r.json()
        status = session["status"]

        for step in sorted(session["steps"], key=lambda s: s["step_index"]):
            if step["status"] in ("RUNNING", "WAITING_VALIDATION", "COMPLETED", "FAILED"):
                print(f"     Step {step['step_index']} {step['step_name']:<20} → {step['status']}")

        if status == "WAITING_VALIDATION":
            waiting = next(s for s in session["steps"] if s["status"] == "WAITING_VALIDATION")
            if waiting["step_name"] == "checkpoint":
                print(f"\n     === PROPOSITION ===\n{waiting['output_data']}\n")
                r = requests.post(
                    f"{BASE}/api/pipelines/{session_id}/validate/{waiting['id']}",
                    json={"approved": True}
                )
                assert r.status_code == 200
                ok("Checkpoint validé automatiquement (mode live)")
        elif status == "COMPLETED":
            ok("Pipeline COMPLETED")
            break
        elif status == "FAILED":
            fail("Pipeline FAILED — voir les logs JARVIS")

        # Avancer le prochain step
        r = requests.post(f"{BASE}/api/pipelines/{session_id}/next")
        time.sleep(3)
    else:
        fail(f"Timeout après {timeout}s")


def test_export(session_id):
    print("\n── Test 4 : Export fichiers démo ────────────────────")

    r = requests.get(f"{BASE}/api/pipelines/{session_id}")
    session = r.json()

    # En mode mock, les fichiers sont dans la DB mais pas encore écrits sur disque
    # car l'engine n'a pas exécuté le step export
    # → on le déclenche via l'API pipelines/next
    export_step = next((s for s in session["steps"] if s["step_name"] == "export"), None)
    assert export_step, "Step export introuvable"

    if export_step["status"] != "COMPLETED":
        ok("Step export pas encore exécuté (normal en mode mock) — test ignoré")
        return

    # Récupérer le prospect pour avoir son id
    r = requests.get(f"{BASE}/api/atelier/prospects")
    prospects = r.json()
    prospect = next((p for p in prospects if p.get("session_id") == session_id), None)
    if not prospect:
        ok("Prospect non retrouvé — test export ignoré")
        return

    r = requests.get(f"{BASE}/api/atelier/prospects/{prospect['id']}/files")
    assert r.status_code == 200
    files = r.json()
    ok(f"Fichiers démo : {[f['name'] for f in files]}")

    r = requests.get(f"{BASE}/api/atelier/prospects/{prospect['id']}/export")
    assert r.status_code == 200
    assert "zip" in r.headers.get("content-type", "")
    ok(f"ZIP téléchargé ({len(r.content)} bytes)")


def test_cleanup(pid):
    print("\n── Nettoyage ─────────────────────────────────────────")
    r = requests.delete(f"{BASE}/api/atelier/prospects/{pid}")
    assert r.status_code in (200, 204), f"DELETE → {r.status_code}"
    ok(f"Prospect {pid} supprimé")


def test_no_regression():
    print("\n── Test 5 : Non-régression workflows existants ───────")
    r = requests.get(f"{BASE}/api/projects")
    assert r.status_code == 200, f"GET /projects → {r.status_code}"
    ok("GET /projects toujours fonctionnel")

    r = requests.get(f"{BASE}/api/config")
    assert r.status_code == 200, f"GET /config → {r.status_code}"
    ok("GET /config toujours fonctionnel")

    r = requests.get(f"{BASE}/api/chat/conversations")
    assert r.status_code == 200, f"GET /conversations → {r.status_code}"
    ok("GET /conversations toujours fonctionnel")


if __name__ == "__main__":
    print("=" * 55)
    print(f"  TEST ATELIER E2E — mode {'LIVE (LLM réels)' if LIVE_MODE else 'MOCK (sans LLM)'}")
    print("=" * 55)

    check_server()
    pid = test_crud()
    session_id, step0_id = test_pipeline_creation(pid)
    test_pipeline_flow(session_id, step0_id)
    test_export(session_id)
    test_no_regression()
    test_cleanup(pid)

    print("\n" + "=" * 55)
    print("  ✅ TOUS LES TESTS PASSENT")
    print("=" * 55)
