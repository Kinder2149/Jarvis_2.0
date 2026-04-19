# MISSION AC_02 — Pipeline workflow + injection de contexte

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/RAPPORT_AC_01.md — vérifier que AC_01 est marqué ✅ avant de continuer
3. backend/data/pipelines.json (structure et format des workflows existants)
4. backend/data/prompts.json (structure et format des prompts existants)
5. backend/services/context_manager.py (lire entièrement — tu vas le modifier)

Confirme en 1 phrase que AC_01 est bien marqué terminé dans le rapport.
Si ce n'est pas le cas : STOP — ne pas continuer cette mission.

---

MISSION : AC_02 — Pipeline workflow + injection de contexte

OBJECTIF :
Connecter le workflow atelier_restauration à l'infrastructure JARVIS :
ajouter la définition du workflow dans pipelines.json,
les 6 prompts dans prompts.json,
et la branche de contexte atelier dans context_manager.py.

PÉRIMÈTRE :
Fichiers à modifier uniquement :
- backend/data/pipelines.json
- backend/data/prompts.json
- backend/services/context_manager.py

Aucun autre fichier n'est touché dans cette mission.

---

INSTRUCTIONS DÉTAILLÉES :

### ÉTAPE 1 — backend/data/pipelines.json : ajouter le workflow atelier_restauration

Ajouter la clé "atelier_restauration" au JSON existant.
NE PAS modifier les 6 workflows existants.

Bloc JSON à ajouter (copier exactement) :

"atelier_restauration": {
  "workflow_type": "atelier_restauration",
  "display_name": "Atelier — Nouveau prospect (Restauration)",
  "phases": ["Saisie", "Analyse", "Proposition", "Génération", "Export"],
  "steps": [
    {
      "index": 0,
      "name": "saisie",
      "display_name": "Saisie prospect",
      "model_type": "none",
      "prompt_key": null,
      "requires_validation": true,
      "output_type": "form",
      "phase": "Saisie",
      "context_envelope": {
        "atelier_resources": [],
        "fetch_url": false,
        "inject_activated_tools": false,
        "previous_steps_output": [],
        "user_input": true,
        "include_file_list": false
      }
    },
    {
      "index": 1,
      "name": "qualification",
      "display_name": "Qualification prospect",
      "model_type": "routing",
      "prompt_key": "atelier_qualification",
      "requires_validation": false,
      "output_type": "qualification",
      "phase": "Analyse",
      "context_envelope": {
        "atelier_resources": ["CADRAGE_STRATEGIQUE"],
        "fetch_url": false,
        "inject_activated_tools": false,
        "previous_steps_output": ["saisie"],
        "user_input": false,
        "include_file_list": false
      }
    },
    {
      "index": 2,
      "name": "analyse_site",
      "display_name": "Analyse du site client",
      "model_type": "analysis",
      "prompt_key": "atelier_analyse_site",
      "requires_validation": false,
      "output_type": "extraction",
      "phase": "Analyse",
      "context_envelope": {
        "atelier_resources": ["CADRAGE_STRATEGIQUE", "CATEGORIES_CLIENT_RESTAURATION"],
        "fetch_url": true,
        "inject_activated_tools": false,
        "previous_steps_output": ["saisie"],
        "user_input": false,
        "include_file_list": false
      }
    },
    {
      "index": 3,
      "name": "proposition",
      "display_name": "Proposition d'impact",
      "model_type": "analysis",
      "prompt_key": "atelier_proposition",
      "requires_validation": false,
      "output_type": "proposition",
      "phase": "Analyse",
      "context_envelope": {
        "atelier_resources": ["CADRAGE_STRATEGIQUE", "CATEGORIES_CLIENT_RESTAURATION"],
        "fetch_url": false,
        "inject_activated_tools": false,
        "previous_steps_output": ["saisie", "analyse_site"],
        "user_input": false,
        "include_file_list": false
      }
    },
    {
      "index": 4,
      "name": "checkpoint",
      "display_name": "Validation de la proposition",
      "model_type": "none",
      "prompt_key": null,
      "requires_validation": true,
      "output_type": "checkpoint",
      "phase": "Proposition",
      "context_envelope": {
        "atelier_resources": [],
        "fetch_url": false,
        "inject_activated_tools": false,
        "previous_steps_output": ["proposition"],
        "user_input": false,
        "include_file_list": false
      }
    },
    {
      "index": 5,
      "name": "generation_css",
      "display_name": "Génération CSS",
      "model_type": "code",
      "prompt_key": "atelier_generation_css",
      "requires_validation": false,
      "output_type": "file",
      "phase": "Génération",
      "context_envelope": {
        "atelier_resources": ["STACK_STANDARD"],
        "fetch_url": false,
        "inject_activated_tools": false,
        "previous_steps_output": ["saisie", "analyse_site"],
        "user_input": false,
        "include_file_list": false
      }
    },
    {
      "index": 6,
      "name": "generation_index",
      "display_name": "Génération site public",
      "model_type": "code",
      "prompt_key": "atelier_generation_index",
      "requires_validation": false,
      "output_type": "file",
      "phase": "Génération",
      "context_envelope": {
        "atelier_resources": ["STACK_STANDARD", "CATEGORIES_CLIENT_RESTAURATION"],
        "fetch_url": false,
        "inject_activated_tools": true,
        "previous_steps_output": ["saisie", "analyse_site", "proposition", "generation_css"],
        "user_input": false,
        "include_file_list": false
      }
    },
    {
      "index": 7,
      "name": "generation_admin",
      "display_name": "Génération espace gérant",
      "model_type": "code",
      "prompt_key": "atelier_generation_admin",
      "requires_validation": false,
      "output_type": "file",
      "phase": "Génération",
      "context_envelope": {
        "atelier_resources": ["STACK_STANDARD", "CATEGORIES_CLIENT_RESTAURATION"],
        "fetch_url": false,
        "inject_activated_tools": true,
        "previous_steps_output": ["saisie", "analyse_site", "proposition", "generation_css"],
        "user_input": false,
        "include_file_list": false
      }
    },
    {
      "index": 8,
      "name": "export",
      "display_name": "Export fichiers démo",
      "model_type": "none",
      "prompt_key": null,
      "requires_validation": false,
      "output_type": "export",
      "phase": "Export",
      "context_envelope": {
        "atelier_resources": [],
        "fetch_url": false,
        "inject_activated_tools": false,
        "previous_steps_output": ["generation_css", "generation_index", "generation_admin"],
        "user_input": false,
        "include_file_list": false
      }
    }
  ]
}

Après modification : valider le JSON en terminal :
python -c "import json; json.load(open('backend/data/pipelines.json', encoding='utf-8')); print('JSON valide')"


### ÉTAPE 2 — backend/data/prompts.json : ajouter les 6 prompts atelier

Ajouter ces 6 clés au JSON existant. NE PAS toucher aux prompts existants.
Pour chaque prompt : copier le texte tel quel, en respecter les sauts de ligne (\n).

---

PROMPT 1 — clé : "atelier_qualification"

Contenu :
Tu es l'assistant de L'Atelier Connecté, micro-entreprise de services numériques de proximité basée à Villeurbanne (Lyon).

CADRAGE STRATÉGIQUE :
{{CADRAGE_STRATEGIQUE}}

---

DONNÉES DU PROSPECT :
{{saisie_output}}

---

MISSION : Qualifier ce prospect selon les critères de qualification (signaux et seuils) du CADRAGE_STRATÉGIQUE.

Produis uniquement un JSON valide avec cette structure :

{
  "score": "★★★",
  "label": "Chaud",
  "decision": "GO",
  "signaux_detectes": ["description courte signal 1", "description courte signal 2"],
  "douleur_principale": "formulée en conséquence métier — jamais en manque technique",
  "raison_stop": null
}

Valeurs autorisées :
- score : "★★★" ou "★★" ou "★"
- label : "Chaud" ou "Tiède" ou "Froid"
- decision : "GO" ou "STOP"
- raison_stop : string si decision=STOP, null sinon

RÈGLES :
- 1 signal fort (★★★) OU 2 signaux moyens (★★) minimum → decision GO
- Douleur formulée côté client : "vous perdez des réservations" jamais "vous n'avez pas de formulaire"
- Si STOP : dire la vérité franchement, pas de compromis
- JSON pur uniquement — aucun texte avant ou après les accolades

---

PROMPT 2 — clé : "atelier_analyse_site"

Contenu :
Tu es l'assistant de L'Atelier Connecté.

CATÉGORIES CLIENT — RESTAURATION :
{{CATEGORIES_CLIENT_RESTAURATION}}

---

DONNÉES SAISIE PROSPECT :
{{saisie_output}}

---

CONTENU DU SITE WEB (extrait via fetch) :
{{site_html}}

---

MISSION : Extraire toutes les informations utiles à la construction d'une démo personnalisée pour ce prospect restaurateur.

Produis uniquement un JSON valide avec cette structure exacte :

{
  "identite": {
    "nom": "nom exact de l'établissement",
    "slogan": "accroche principale mot pour mot ou null",
    "presentation": "texte de présentation mot pour mot, 2-4 phrases ou null",
    "gerants": "prénom(s) et nom(s) ou null",
    "adresse": "adresse complète ou null",
    "telephone": "numéro formaté ou null",
    "email": "adresse email ou null",
    "horaires": "horaires complets jour par jour ou null"
  },
  "palette": {
    "bg_main": "#xxxxxx",
    "bg_alt": "#xxxxxx",
    "accent": "#xxxxxx",
    "text_main": "#xxxxxx",
    "text_secondary": "#xxxxxx"
  },
  "polices": {
    "titres": "nom exact Google Font ou null",
    "corps": "nom exact Google Font ou null"
  },
  "images": {
    "logo": "URL directe ou null",
    "hero": "URL directe ou null",
    "equipe": "URL directe ou null",
    "ambiance": ["URL1 ou null"]
  },
  "carte": {
    "categories": [
      {
        "nom": "Entrées",
        "plats": [{"nom": "...", "prix": "X,XX €", "description": "..."}]
      }
    ]
  },
  "outils_existants": ["Planity", "LaFourchette"],
  "slug": "nom-en-minuscules-sans-accents-avec-tirets"
}

RÈGLES ABSOLUES :
- Couleurs HEX : extraire du CSS/style réel du site — si non identifiable : #f5f5f5 pour fonds clairs, #1a1a1a pour textes sombres
- Textes : 100% réels, mot pour mot depuis le site — jamais inventer ni paraphraser
- Informations absentes du site : null — jamais inventer
- Slug : uniquement minuscules, tirets, pas d'espaces ni accents ni caractères spéciaux
- JSON pur uniquement — aucun texte avant ou après

---

PROMPT 3 — clé : "atelier_proposition"

Contenu :
Tu es l'assistant de L'Atelier Connecté.

CADRAGE STRATÉGIQUE :
{{CADRAGE_STRATEGIQUE}}

CATÉGORIES CLIENT — RESTAURATION :
{{CATEGORIES_CLIENT_RESTAURATION}}

---

DONNÉES SAISIE :
{{saisie_output}}

ANALYSE DU SITE :
{{analyse_site_output}}

---

MISSION : Produire la proposition d'impact qui sera soumise à validation avant toute construction de démo.

Respecte exactement ce format de sortie (en-têtes et tirets compris) :

---
PROSPECT : [NOM] — Restauration
SCORE : [★★★/★★/★] [label]

DOULEUR PRINCIPALE :
[formulée en conséquence métier — ex : "Vous manquez des réservations le soir quand le téléphone n'est plus décroché" pas "Vous n'avez pas de formulaire en ligne"]

OUTILS PROPOSÉS :
✅ Réservations — [raison courte justifiant l'activation]
✅ Menu & Ardoise — [raison courte]
[✅ ou ❌] Événements — [raison : activer si soirées/privatisations observées, sinon expliquer pourquoi non]
[✅ ou ❌] Avis clients — [raison : activer si peu d'avis Google ou avis positifs non valorisés]
[✅ ou ❌] Vente à emporter — [raison : activer si mention emporter/traiteur observée]

CE QUE LE PROSPECT VERRA EN 10 SECONDES :
[promesse visuelle immédiate — ce qui s'affiche au premier regard sur la démo]

BÉNÉFICES DÉMONTRÉS :
— [BÉNÉFICE 1 en langage métier]
— [BÉNÉFICE 2]
— [BÉNÉFICE 3]
— [BÉNÉFICE 4]

[SIGNAL D'ALERTE : uniquement si un risque ou une limite doit être signalé — supprimer cette ligne si rien à signaler]
---

RÈGLES :
- Activer un outil uniquement si le signal terrain le justifie ET si coché dans les données saisie
- Bénéfices : toujours en langage métier, jamais techniques
- Honnêteté totale sur les signaux d'alerte — mieux vaut signaler avant de construire
- Respecter l'exacte syntaxe des en-têtes et tirets

---

PROMPT 4 — clé : "atelier_generation_css"

Contenu :
Tu es un développeur web expert HTML/CSS/JS vanilla.

STACK STANDARD — RÈGLES TECHNIQUES (appliquer sans exception) :
{{STACK_STANDARD}}

---

DONNÉES SAISIE :
{{saisie_output}}

ANALYSE DU SITE CLIENT :
{{analyse_site_output}}

---

MISSION : Générer le fichier styles.css complet pour la démo de ce prospect restaurateur.

INSTRUCTIONS :

1. Variables CSS dans :root — utiliser EXACTEMENT les valeurs de la palette extraite :
   --bg-main       (bg_main de l'extraction)
   --bg-alt        (bg_alt de l'extraction)
   --accent        (accent de l'extraction)
   --text-main     (text_main de l'extraction)
   --text-secondary(text_secondary de l'extraction)
   --card-bg       (légèrement plus clair que --bg-main, calculé)
   --border-soft   (très discret, rgba faible opacité)
   --success: #3d9b5f
   --warning: #b6883f
   --danger:  #a64848

2. @import Google Fonts en tête :
   - Police titres : polices.titres de l'extraction (si null : "Georgia, serif")
   - Police corps : polices.corps de l'extraction (si null : "system-ui, sans-serif")

3. Sections CSS obligatoires :
   - Reset + base (box-sizing border-box, margin 0, font-family)
   - Header sticky (logo gauche, btn-admin droite)
   - Hero (min-height 90vh, background-image, overlay rgba)
   - Sections corps (padding 4rem 0 desktop, 2.5rem 0 mobile)
   - Navigation carte (onglets ou sections)
   - Service cards (2 cartes cliquables Déjeuner/Dîner)
   - Stepper couverts (boutons − et +)
   - Confirmation inline (message 4s, fond --accent)
   - Badges statut (.badge-attente, .badge-confirme, .badge-annule)
   - Admin login screen (plein écran)
   - Admin dashboard (header + KPIs + onglets)
   - Responsive 390px minimum

4. Règles STACK_STANDARD obligatoires :
   - Alternance bg-main / bg-alt (jamais 2 sections identiques adjacentes)
   - Accent : max 3 usages visuellement distincts
   - border-radius: 8px cartes, 4px boutons
   - box-shadow: 0 2px 8px rgba(0,0,0,0.08) maximum
   - Bouton admin : toujours en haut à droite du header

SORTIE : code CSS complet entre balises ```css et ```. Aucun texte explicatif en dehors du code.

---

PROMPT 5 — clé : "atelier_generation_index"

Contenu :
Tu es un développeur web expert HTML/CSS/JS vanilla.

STACK STANDARD :
{{STACK_STANDARD}}

SPÉCIFICATIONS UX DES OUTILS ACTIVÉS :
{{TOOL_SPECS}}

CATÉGORIES CLIENT — RESTAURATION :
{{CATEGORIES_CLIENT_RESTAURATION}}

---

DONNÉES SAISIE :
{{saisie_output}}

ANALYSE DU SITE CLIENT :
{{analyse_site_output}}

PROPOSITION VALIDÉE :
{{proposition_output}}

CSS GÉNÉRÉ (variables disponibles) :
{{generation_css_output}}

---

MISSION : Générer index.html ET script.js pour le site public de la démo restaurateur.

STRUCTURE index.html OBLIGATOIRE (ordre exact) :
1. <head> avec <link rel="stylesheet" href="styles.css"> + Google Fonts + favicon (logo URL de l'extraction)
2. <header> sticky — logo gauche + <nav> + bouton "🔒 Espace Gérant" EN HAUT À DROITE lié à admin.html
3. Hero (min-height 90vh) — background-image URL hero réelle + overlay rgba(0,0,0,0.45) + H1 (nom) + sous-titre (slogan) + CTA "Réserver une table" → #reservation
4. Section Présentation — textes réels (présentation, gérants) + photo équipe si disponible
5. Section Notre carte — onglets par catégorie + plats avec vrais noms et prix depuis l'extraction
6. Section Ardoise du jour (id="ardoise") — badge "Aujourd'hui" + plat du jour (masquée si disponible=false en localStorage)
7. Section Réservation (id="reservation") — formulaire complet
8. [Si Événements activé dans proposition] Section Événements
9. [Si Avis activé dans proposition] Section Avis clients (carousel 3 cartes démo)
10. [Si Emporter activé dans proposition] Section Commander à emporter
11. Footer — adresse + horaires + téléphone + lien discret "Espace gérant" → admin.html

FORMULAIRE RÉSERVATION — règles non négociables :
- Service : 2 cartes cliquables stylisées avec classe .service-card — JAMAIS <select> ni radio brut visible
- Couverts : stepper avec boutons − et + — JAMAIS <input type="number"> visible
- Confirmation : message inline visible 4 secondes — JAMAIS alert()

SCRIPT.JS :
- DOMContentLoaded : lire localStorage "contenu_editable" → mettre à jour ardoise du jour
- DOMContentLoaded : lire localStorage "menuCard" → mettre à jour la carte si présent
- Submit formulaire réservation → stocker dans localStorage "actions_recues" (tableau JSON)
- Fonction safeParse(raw, fallback) pour tout JSON.parse()
- Aucun console.log dans le code livré

Tous les textes : 100% réels depuis l'extraction JSON — zéro Lorem ipsum, zéro placeholder.

SORTIE — deux fichiers séparés par ce délimiteur exact (respecter l'orthographe) :
<<<FILE: index.html>>>
[contenu complet de index.html]
<<<FILE: script.js>>>
[contenu complet de script.js]

---

PROMPT 6 — clé : "atelier_generation_admin"

Contenu :
Tu es un développeur web expert HTML/CSS/JS vanilla.

STACK STANDARD :
{{STACK_STANDARD}}

SPÉCIFICATIONS UX DES OUTILS ACTIVÉS :
{{TOOL_SPECS}}

CATÉGORIES CLIENT — RESTAURATION :
{{CATEGORIES_CLIENT_RESTAURATION}}

---

DONNÉES SAISIE :
{{saisie_output}}

ANALYSE DU SITE CLIENT :
{{analyse_site_output}}

PROPOSITION VALIDÉE :
{{proposition_output}}

CSS GÉNÉRÉ (variables disponibles) :
{{generation_css_output}}

---

MISSION : Générer admin.html ET admin.js pour l'espace gérant de la démo restaurateur.

STRUCTURE admin.html OBLIGATOIRE :

1. ÉCRAN LOGIN (visible au premier chargement, plein écran, z-index élevé) :
   - Logo + titre "Espace Gérant — [NOM_ETABLISSEMENT exact de l'extraction]"
   - Champ mot de passe type="password" + bouton œil toggle show/hide
   - Bouton "Accéder à mon espace"
   - Message erreur inline sous le bouton — JAMAIS alert()

2. DASHBOARD (display:none jusqu'au login réussi) :
   - Header : logo + "Espace Gérant — [NOM]" + bouton "Se déconnecter"
   - VUE AUJOURD'HUI en premier plan :
     - Date du jour affichée dynamiquement
     - 3 KPIs : "Demandes aujourd'hui" / "En attente de confirmation" / "Confirmées cette semaine"
     - Section "En attente" avec les réservations à traiter en premier — visible sans scroll
     - Boutons [Confirmer ✓] [Annuler ✗] sur chaque carte en attente
   - Onglets selon outils activés dans la proposition :
     ✅ Onglet "Réservations" (toujours présent) :
        - Calendrier 7 jours avec nombre de couverts par jour
        - Filtres Déjeuner / Dîner / Tous
        - Cartes réservation avec badge statut coloré
        - Boutons Confirmer / Annuler → badge mis à jour SANS rechargement
     ✅ Onglet "Menu & Ardoise" (toujours présent) :
        - Ardoise du jour : champs plat / prix / note + toggle disponible / non disponible
        - Éditeur carte : catégories + plats + prix + bouton "Sauvegarder"
        - Sauvegarde → localStorage "contenu_editable" et "menuCard"
     [Si Événements activé] Onglet "Événements"
     [Si Avis activé] Onglet "Avis clients" — modération + toggle visible/masqué
     [Si Emporter activé] Onglet "Commandes à emporter"

ADMIN.JS :
- Mot de passe : "admin2024" codé en dur (comparaison directe)
- DEMO_RESERVATIONS constant avec 5 entrées codées en dur :
  - 2 statut "En attente", 2 "Confirmée", 1 "Annulée"
  - Dates calculées via offsetDate(N) depuis aujourd'hui (offsetDate(0)=today, offsetDate(1)=demain, etc.)
  - Prénoms et messages réalistes (ex: "Anniversaire de mariage", "Allergie aux crustacés")
  - IDs : "demo-1" à "demo-5"
- ensureInitialData() : si localStorage "actions_recues" absent → injecter DEMO_RESERVATIONS
- document.addEventListener("DOMContentLoaded", ensureInitialData)
- Clés localStorage : "actions_recues" / "contenu_editable" / "menuCard"
- Fonction safeParse(raw, fallback) pour tout JSON.parse()
- Flag confirmationSent sur chaque réservation pour éviter double envoi
- Aucun console.log dans le code livré

NOM DE LA PAGE : <title>Espace Gérant — [NOM_ETABLISSEMENT]</title>
En-tête dashboard : "[NOM_ETABLISSEMENT]" en toutes lettres — JAMAIS "Admin" ou "Dashboard" seul.

SORTIE — deux fichiers séparés par ce délimiteur exact (respecter l'orthographe) :
<<<FILE: admin.html>>>
[contenu complet de admin.html]
<<<FILE: admin.js>>>
[contenu complet de admin.js]

---

Après ajout des 6 prompts, valider le JSON :
python -c "import json; json.load(open('backend/data/prompts.json', encoding='utf-8')); print('JSON valide')"


### ÉTAPE 3 — backend/services/context_manager.py : ajouter la branche atelier

Lire entièrement context_manager.py avant de modifier.

MODIFICATION 1 : dans la signature de build_context_envelope(), ajouter le paramètre workflow_type.
Avant (approximatif, adapter au code réel) :
  def build_context_envelope(step, session_id, db):
Après :
  def build_context_envelope(step, session_id, workflow_type, db):

MODIFICATION 2 : en début de fonction build_context_envelope(), ajouter :
  if workflow_type and workflow_type.startswith("atelier_"):
      return await _build_atelier_context(step, session_id, db)

Si build_context_envelope n'est pas async : la rendre async ou créer une version sync
selon ce que le reste du code attend. Ne pas casser les appels existants.

MODIFICATION 3 : ajouter la fonction _build_atelier_context() dans le même fichier :

async def _build_atelier_context(step: dict, session_id: int, db) -> dict:
    from backend.services.atelier_service import load_resource, load_tool_spec, get_activated_tools, fetch_url
    import json

    envelope = step.get("context_envelope", {})
    context = {}

    # 1. Charger les fichiers ressources demandés
    for resource_name in envelope.get("atelier_resources", []):
        content = load_resource(f"{resource_name}.md")
        context[resource_name] = content

    # 2. Charger les outputs des steps précédents
    cursor = db.cursor()
    for step_name_ref in envelope.get("previous_steps_output", []):
        row = cursor.execute(
            """SELECT output_data FROM pipeline_steps
               WHERE session_id=? AND step_name=? AND status='COMPLETED'
               ORDER BY step_index ASC LIMIT 1""",
            (session_id, step_name_ref)
        ).fetchone()
        if row and row["output_data"]:
            context[f"{step_name_ref}_output"] = row["output_data"]

    # 3. Fetch URL si demandé (step analyse_site uniquement)
    if envelope.get("fetch_url", False):
        saisie_raw = context.get("saisie_output", "{}")
        try:
            saisie_data = json.loads(saisie_raw) if isinstance(saisie_raw, str) else saisie_raw
            url = saisie_data.get("url", "")
            if url and url.strip() not in ("aucun site", "", "null"):
                site_data = await fetch_url(url)
                context["site_html"] = site_data.get("text", "")
            else:
                context["site_html"] = "[Aucun site fourni — analyser uniquement les observations terrain]"
        except Exception:
            context["site_html"] = "[Erreur lors de l'extraction du site]"

    # 4. Injecter les specs des outils activés (steps génération uniquement)
    if envelope.get("inject_activated_tools", False):
        saisie_raw = context.get("saisie_output", "{}")
        try:
            saisie_data = json.loads(saisie_raw) if isinstance(saisie_raw, str) else saisie_raw
            activated = get_activated_tools(saisie_data)
            tool_specs = []
            for tool in activated:
                spec = load_tool_spec(tool)
                if spec:
                    tool_specs.append(f"=== OUTIL : {tool.upper().replace('_', ' ')} ===\n{spec}")
            context["TOOL_SPECS"] = "\n\n".join(tool_specs)
        except Exception:
            context["TOOL_SPECS"] = ""

    return context

MODIFICATION 4 : dans execute_step() (pipeline_engine.py), trouver l'appel à
build_context_envelope() et passer le workflow_type en paramètre.
Le workflow_type est disponible depuis la session — récupérer avec :
  session_row = cursor.execute("SELECT workflow_type FROM sessions WHERE id=?", (session_id,)).fetchone()
  workflow_type = session_row["workflow_type"] if session_row else ""

MODIFICATION 5 : vérifier inject_into_template().
Si une clé {{var}} est dans le prompt mais absente du context, ne pas crasher.
Ajouter un fallback : si key non présente → remplacer par chaîne vide.
Exemple de sécurisation (adapter au code réel) :
  for key, value in context.items():
      template = template.replace("{{" + key + "}}", str(value) if value else "")
  # Supprimer les {{vars}} restantes non résolues
  import re
  template = re.sub(r'\{\{[^}]+\}\}', '', template)


---

TESTS À EFFECTUER (dans l'ordre) :

Test 1 — JSON valide
  python -c "import json; json.load(open('backend/data/pipelines.json', encoding='utf-8')); print('pipelines.json OK')"
  python -c "import json; json.load(open('backend/data/prompts.json', encoding='utf-8')); print('prompts.json OK')"
  Les deux doivent afficher OK.

Test 2 — Démarrage JARVIS
  Redémarrer JARVIS. Aucune erreur au démarrage.

Test 3 — Workflow listé
  GET http://localhost:8000/api/pipelines/workflows (ou équivalent selon l'API)
  → "atelier_restauration" doit apparaître dans la liste.

Test 4 — Pipeline créée avec 9 steps
  Utiliser un prospect existant créé en AC_01 (ou en créer un nouveau).
  POST http://localhost:8000/api/atelier/prospects/{id}/start
  GET http://localhost:8000/api/pipelines/{session_id}
  → 9 steps présents, step 0 (saisie) en WAITING_VALIDATION.

Test 5 — Step 0 validé → step 1 lancé
  POST http://localhost:8000/api/pipelines/{session_id}/validate/{step0_id}
  Body: {"output": "{\"nom\":\"Test\",\"url\":\"aucun site\",\"observations\":\"test\",\"outils\":{\"evenements\":false,\"avis\":false,\"emporter\":false}}"}
  → step 1 (qualification) passe en RUNNING puis COMPLETED dans les logs.

Test 6 — Contexte atelier injecté
  Dans jarvis.log, vérifier que les appels LLM du workflow atelier contiennent
  le contenu de CADRAGE_STRATEGIQUE (chercher "L'Atelier Connecté" dans les logs).

Test 7 — Workflows existants non impactés
  Sur un projet JARVIS existant, lancer un workflow bug_simple.
  → Fonctionne normalement. Aucune régression.

---

RAPPORT DE FIN DE MISSION :

Créer le fichier temp/RAPPORT_AC_02.md avec :

# RAPPORT AC_02 — Pipeline workflow + injection de contexte

## Statut global : ✅ Terminé / ❌ Bloqué

## Fichiers modifiés
- [ ] backend/data/pipelines.json (+1 workflow atelier_restauration, 9 steps)
- [ ] backend/data/prompts.json (+6 prompts atelier_*)
- [ ] backend/services/context_manager.py (branche atelier + _build_atelier_context)
- [ ] backend/services/pipeline_engine.py (passage workflow_type à build_context_envelope)

## Validation JSON
- [ ] pipelines.json : JSON valide ✅
- [ ] prompts.json : JSON valide ✅

## Résultats des tests
- [ ] Test 1 — JSON valide
- [ ] Test 2 — Démarrage sans erreur
- [ ] Test 3 — Workflow listé
- [ ] Test 4 — Pipeline créée avec 9 steps
- [ ] Test 5 — Step 0 validé → step 1 lancé
- [ ] Test 6 — Contexte atelier injecté dans les appels LLM
- [ ] Test 7 — Workflows existants non impactés

## Lignes modifiées dans context_manager.py
[Indiquer les numéros de lignes ajoutées/modifiées]

## Problèmes rencontrés
[Décrire si applicable]
```
