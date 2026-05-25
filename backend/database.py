import sqlite3
from pathlib import Path
import json
import logging
import os

DB_PATH = Path(__file__).parent / "data" / "jarvis.db"
CONFIG_PATH = Path(__file__).parent / "data" / "config.json"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def load_config():
    """
    Charge la configuration complète depuis SQLite et config.json.
    Retourne un dict avec api_keys, model_preferences et optionnellement chat.
    """
    logger = logging.getLogger("uvicorn")
    
    logger.info("🔑 [DB] Chargement des clés API depuis SQLite...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM app_config WHERE category = 'api_keys'")
    rows = cursor.fetchall()
    conn.close()
    
    logger.info(f"🔍 [DB] Nombre de clés trouvées en DB: {len(rows)}")
    for row in rows:
        key_name = row["key"]
        value = row["value"]
        masked = "..." + value[-4:] if value and len(value) > 4 else "(vide)"
        logger.info(f"   - {key_name}: {masked}")
    
    api_keys = {row["key"]: row["value"] or "" for row in rows}
    if not api_keys:
        logger.warning("⚠️ [DB] Aucune clé API en DB, utilisation des valeurs par défaut vides")
        api_keys = {"openrouter_key": "", "anthropic_key": "", "google_key": "", "web_search_key": "", "twelve_data_key": ""}
    
    # Fallback .env : si une clé est vide en DB, chercher dans les variables d'environnement
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            env_key, env_val = line.split("=", 1)
            env_val = env_val.strip()
            env_map = {
                "OPENROUTER_KEY": "openrouter_key",
                "ANTHROPIC_KEY": "anthropic_key",
                "GOOGLE_KEY": "google_key",
                "WEB_SEARCH_KEY": "web_search_key",
                "TWELVE_DATA_KEY": "twelve_data_key",
            }
            db_key = env_map.get(env_key.strip())
            if db_key and not api_keys.get(db_key):
                api_keys[db_key] = env_val
    
    # Lire les vraies variables d'environnement système (pour Docker/desktop)
    for env_var, db_key in [
        ("OPENROUTER_KEY", "openrouter_key"),
        ("ANTHROPIC_KEY", "anthropic_key"),
        ("GOOGLE_KEY", "google_key"),
        ("WEB_SEARCH_KEY", "web_search_key"),
        ("TWELVE_DATA_KEY", "twelve_data_key"),
    ]:
        if not api_keys.get(db_key) and os.environ.get(env_var):
            api_keys[db_key] = os.environ[env_var]
    
    # Lire model_preferences depuis config.json
    model_preferences = {
        "routing": "google/gemini-2.5-flash",
        "structuring": "google/gemini-2.5-flash",
        "code": "anthropic/claude-haiku-4.5",
        "analysis": "anthropic/claude-sonnet-4.5"
    }
    
    chat_config = {
        "model": "anthropic/claude-sonnet-4.5",
        "methodo_path": "C:\\DEV\\METHODO",
        "session_note": "",
        "system_prompt_preset": "",
        "vision_model": "anthropic/claude-sonnet-4-6"
    }
    
    cascade_mode = True
    
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_file = json.load(f)
            if "model_preferences" in config_file:
                model_preferences = config_file["model_preferences"]
                logger.info(f"📋 [DB] model_preferences chargées depuis config.json")
            if "chat" in config_file:
                chat_config.update(config_file["chat"])
                logger.info(f"💬 [DB] chat config chargée depuis config.json")
            cascade_mode = config_file.get("cascade_mode", True)
    
    # Charger les contextes utilisateur depuis les fichiers .md (backend/data/contexts/)
    contexts_dir = Path(__file__).parent / "data" / "contexts"
    context = {}
    for key in ("profil_utilisateur", "global_context", "regles_globales"):
        f = contexts_dir / f"{key}.md"
        context[key] = f.read_text(encoding="utf-8").strip() if f.exists() else ""

    logger.info(f"✅ [DB] Config chargée: {len(api_keys)} clés API, {len(model_preferences)} préférences modèles, contexte: {[k for k, v in context.items() if v]}")
    return {
        "api_keys": api_keys,
        "model_preferences": model_preferences,
        "chat": chat_config,
        "context": context,
        "cascade_mode": cascade_mode
    }

def _seed_api_keys_from_env(conn):
    """Copie les clés API depuis .env vers SQLite si elles sont absentes en DB."""
    from pathlib import Path as _Path
    import os

    env_to_db = {
        "OPENROUTER_KEY": "openrouter_key",
        "ANTHROPIC_KEY": "anthropic_key",
        "GOOGLE_KEY": "google_key",
        "WEB_SEARCH_KEY": "web_search_key",
        "TWELVE_DATA_KEY": "twelve_data_key",
    }

    # Lire les valeurs candidates : .env d'abord, puis variables OS
    candidates = {}

    env_file = _Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() in env_to_db and v.strip():
                candidates[k.strip()] = v.strip()

    for env_key in env_to_db:
        if env_key not in candidates and os.environ.get(env_key):
            candidates[env_key] = os.environ[env_key]

    if not candidates:
        return

    cursor = conn.cursor()
    for env_key, db_key in env_to_db.items():
        if env_key not in candidates:
            continue
        # Lire valeur actuelle en DB
        cursor.execute("SELECT value FROM app_config WHERE key = ?", (db_key,))
        row = cursor.fetchone()
        current_value = row["value"] if row else None
        if not current_value or len(current_value.strip()) < 20:
            cursor.execute(
                "INSERT OR REPLACE INTO app_config (key, value, category) VALUES (?, ?, 'api_keys')",
                (db_key, candidates[env_key])
            )
    conn.commit()

def _migrate_v3(conn):
    """Migration v3 : ajoute prix_moyen et prix_revient pour Sentinelle (idempotent)."""
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE sentinelle_positions ADD COLUMN prix_moyen REAL DEFAULT 0.0")
    except Exception:
        pass
    
    try:
        cursor.execute("ALTER TABLE sentinelle_positions ADD COLUMN prix_revient REAL DEFAULT 0.0")
    except Exception:
        pass
    
    conn.commit()

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            instructions TEXT DEFAULT '',
            module_type TEXT NOT NULL CHECK(module_type IN ('dossier', 'code')),
            category TEXT,
            parent_dossier_id INTEGER REFERENCES projects(id),
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            workflow_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'CREATED',
            current_step_index INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            step_index INTEGER NOT NULL,
            step_name TEXT NOT NULL,
            step_display_name TEXT NOT NULL,
            model_type TEXT NOT NULL,
            model_used TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING',
            input_data TEXT,
            output_data TEXT,
            requires_validation INTEGER DEFAULT 0,
            validated_at TEXT,
            error_message TEXT,
            output_type TEXT DEFAULT 'text',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE pipeline_steps ADD COLUMN output_type TEXT DEFAULT 'text'")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE conversations ADD COLUMN folder_path TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    # Migrations Chat : internet_access, context_summary, model
    migrations_chat = [
        "ALTER TABLE conversations ADD COLUMN internet_access INTEGER DEFAULT 0",
        "ALTER TABLE conversations ADD COLUMN context_summary TEXT DEFAULT ''",
        "ALTER TABLE conversations ADD COLUMN model TEXT DEFAULT ''",
    ]
    for migration in migrations_chat:
        try:
            cursor.execute(migration)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    
    # Migrations Messages : attachment_base64, attachment_filename
    migrations_messages = [
        "ALTER TABLE messages ADD COLUMN attachment_base64 TEXT",
        "ALTER TABLE messages ADD COLUMN attachment_filename TEXT",
    ]
    for migration in migrations_messages:
        try:
            cursor.execute(migration)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_decision_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            step_name TEXT,
            model_type TEXT,
            model_id_chosen TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            title TEXT NOT NULL DEFAULT 'Nouvelle conversation',
            folder_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT,
            category TEXT DEFAULT 'api_keys',
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Initialiser global_context si absent
    cursor.execute("""
        INSERT OR IGNORE INTO app_config (key, value, category) 
        VALUES ('global_context', '', 'context')
    """)
    
    # Initialiser profil_utilisateur si absent
    cursor.execute("""
        INSERT OR IGNORE INTO app_config (key, value, category) 
        VALUES ('profil_utilisateur', '', 'context')
    """)
    
    # Initialiser regles_globales si absent
    cursor.execute("""
        INSERT OR IGNORE INTO app_config (key, value, category) 
        VALUES ('regles_globales', '', 'context')
    """)
    
    # Initialiser clients_export_path si absent
    cursor.execute("""
        INSERT OR IGNORE INTO app_config (key, value, category) 
        VALUES ('clients_export_path', 'C:/DEV/PROJETS/Clients', 'paths')
    """)
    conn.commit()
    
    # Cycle de vie prospects : identifié → en_analyse → proposition_ok → démo_générée → contacté → relancé → signé / perdu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
            nom         TEXT NOT NULL,
            categorie   TEXT NOT NULL DEFAULT 'restauration',
            url         TEXT,
            statut      TEXT NOT NULL DEFAULT 'identifié',
            score       TEXT,
            form_data   TEXT,
            fiche       TEXT,
            proposition TEXT,
            demo_path   TEXT,
            demo_url    TEXT,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    
    conn.commit()
    
    # Tables Sentinelle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentinelle_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            quantite REAL NOT NULL,
            enveloppe TEXT NOT NULL CHECK(enveloppe IN ('PEA','CTO','liquidites')),
            date_entree TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentinelle_watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL UNIQUE,
            niveau_risque TEXT NOT NULL CHECK(niveau_risque IN ('faible','modere','eleve','speculatif')),
            note TEXT,
            date_ajout TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentinelle_theses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actif TEXT NOT NULL,
            texte TEXT NOT NULL,
            statut TEXT NOT NULL DEFAULT 'active' CHECK(statut IN ('active','revisee')),
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentinelle_cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            etat TEXT NOT NULL DEFAULT 'PHASE_1' CHECK(etat IN ('PHASE_1','PHASE_2','PHASE_3','PHASE_4','PHASE_5','PHASE_6','CLOTURE')),
            mode TEXT NOT NULL DEFAULT 'normal' CHECK(mode IN ('normal','accumulation','opportunite')),
            budget_mensuel REAL NOT NULL DEFAULT 20.0,
            budget_utilise REAL NOT NULL DEFAULT 0.0,
            mois TEXT NOT NULL,
            donnees_veille TEXT,
            donnees_analyse TEXT,
            donnees_propositions TEXT,
            decision TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentinelle_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id INTEGER REFERENCES sentinelle_cycles(id),
            ticker TEXT NOT NULL,
            quantite REAL NOT NULL,
            prix_reel REAL NOT NULL,
            frais REAL NOT NULL DEFAULT 0.0,
            date_transaction TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentinelle_alertes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            variation_pct REAL NOT NULL,
            cours_actuel REAL,
            cours_reference REAL,
            lu INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jarvis_plans (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            home_conversation_id INTEGER NOT NULL,
            title                TEXT NOT NULL,
            status               TEXT NOT NULL DEFAULT 'EN_ATTENTE_CONFIRM'
                CHECK(status IN ('EN_ATTENTE_CONFIRM','CONFIRMED','EN_COURS',
                                 'TERMINE','ECHEC','ANNULE')),
            created_at           TEXT DEFAULT (datetime('now')),
            updated_at           TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (home_conversation_id) REFERENCES conversations(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jarvis_plan_steps (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id             INTEGER NOT NULL,
            step_order          INTEGER NOT NULL,
            agent               TEXT NOT NULL
                CHECK(agent IN ('MENTOR','FORGE','SENTINELLE','ATELIER','MEDIA','JARVIS')),
            title               TEXT NOT NULL,
            input_message       TEXT NOT NULL,
            output_text         TEXT,
            error_message       TEXT,
            sub_conversation_id INTEGER,
            status              TEXT NOT NULL DEFAULT 'EN_ATTENTE'
                CHECK(status IN ('EN_ATTENTE','EN_COURS','EN_ATTENTE_UTILISATEUR',
                                 'TERMINEE','ECHEC','ANNULEE')),
            depends_on          INTEGER,
            created_at          TEXT DEFAULT (datetime('now')),
            updated_at          TEXT DEFAULT (datetime('now')),
            completed_at        TEXT,
            FOREIGN KEY (plan_id)    REFERENCES jarvis_plans(id),
            FOREIGN KEY (depends_on) REFERENCES jarvis_plan_steps(id)
        )
    """)
    
    conn.commit()
    _create_reflexion_tables(conn)
    _migrate_v2(conn)
    _migrate_v3(conn)
    _migrate_prospects_v2(conn)
    _migrate_reflexion_attachments(conn)
    _migrate_v4_jarvis(conn)
    _migrate_v5_media(conn)
    _migrate_v6_consultation_state(conn)
    _migrate_v7_disc(conn)
    _seed_api_keys_from_env(conn)
    conn.close()


def _create_reflexion_tables(conn):
    """Crée les tables du Module Réflexion (idempotent)."""
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reflexion_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            livrable_type TEXT NOT NULL CHECK(livrable_type IN ('mission_code','decision_figee','plan_multi_missions')),
            titre TEXT,
            statut TEXT NOT NULL DEFAULT 'OUVERTE' CHECK(statut IN ('OUVERTE','EN_FIGEMENT','FIGEE','ABANDONNEE')),
            modele_utilise TEXT NOT NULL DEFAULT 'anthropic/claude-sonnet-4.5',
            input_tokens_total INTEGER NOT NULL DEFAULT 0,
            output_tokens_total INTEGER NOT NULL DEFAULT 0,
            livrable_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            frozen_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reflexion_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','assistant','system','sante_cadrage')),
            content TEXT NOT NULL,
            attachments TEXT,
            compacted INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES reflexion_sessions(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mission_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reflexion_session_id INTEGER NOT NULL,
            livrable_type TEXT NOT NULL,
            content TEXT NOT NULL,
            recommandation_modele TEXT,
            files_targeted TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            consumed_at TEXT,
            FOREIGN KEY (reflexion_session_id) REFERENCES reflexion_sessions(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexion_sessions_project ON reflexion_sessions(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexion_messages_session ON reflexion_messages(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mission_prompts_session ON mission_prompts(reflexion_session_id)")
    
    conn.commit()


def _migrate_prospects_v2(conn):
    """Migration : détecte l'ancien schéma prospects (nom_entreprise) et recrée la table avec le nouveau schéma."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(prospects)")
    columns = [row[1] for row in cursor.fetchall()]
    if "nom" in columns:
        return  # déjà le bon schéma
    # Ancien schéma détecté — renommer et recréer
    cursor.execute("ALTER TABLE prospects RENAME TO prospects_old")
    cursor.execute("""
        CREATE TABLE prospects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
            nom         TEXT NOT NULL,
            categorie   TEXT NOT NULL DEFAULT 'restauration',
            url         TEXT,
            statut      TEXT NOT NULL DEFAULT 'identifié',
            score       TEXT,
            form_data   TEXT,
            fiche       TEXT,
            proposition TEXT,
            demo_path   TEXT,
            demo_url    TEXT,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    # Migrer ce qui peut l'être depuis l'ancien schéma
    cursor.execute("""
        INSERT INTO prospects (nom, statut, notes, created_at, updated_at)
        SELECT
            COALESCE(nom_entreprise, 'Prospect migré'),
            COALESCE(statut, 'identifié'),
            COALESCE(notes, ''),
            COALESCE(created_at, datetime('now')),
            COALESCE(updated_at, datetime('now'))
        FROM prospects_old
    """)
    cursor.execute("DROP TABLE prospects_old")
    conn.commit()


def _migrate_reflexion_attachments(conn):
    """Migration : ajoute attachment_base64 et attachment_filename à reflexion_messages."""
    cursor = conn.cursor()
    
    migrations_reflexion = [
        "ALTER TABLE reflexion_messages ADD COLUMN attachment_base64 TEXT",
        "ALTER TABLE reflexion_messages ADD COLUMN attachment_filename TEXT",
    ]
    for migration in migrations_reflexion:
        try:
            cursor.execute(migration)
        except Exception:
            pass
    conn.commit()


def _migrate_v4_jarvis(conn):
    """Migration v4 : fondation architecture multi-agents (idempotent)."""
    cursor = conn.cursor()
    
    # Table agent_registry : registre des agents disponibles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_registry (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL UNIQUE,
            display_name  TEXT NOT NULL,
            description   TEXT NOT NULL,
            routing_hints TEXT NOT NULL,
            page_url      TEXT,
            color         TEXT DEFAULT '#6b7280',
            is_active     INTEGER DEFAULT 1,
            created_at    TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Seed des 5 agents (INSERT OR IGNORE — idempotent grâce à UNIQUE sur name)
    agents = [
        (
            "JARVIS",
            "JARVIS",
            "Orchestrateur central et conversation directe. Répond directement si aucun agent spécialiste n'est pertinent. Analyse l'intention et route vers le bon agent.",
            '["bonjour", "aide-moi", "explique", "comment", "pourquoi", "qu\'est-ce que", "question", "information"]',
            None,
            "#6b7280"
        ),
        (
            "MENTOR",
            "MENTOR",
            "Analyse structurée et production de livrables actionnables. Conduit des sessions de réflexion pour produire des missions code, des décisions figées ou des plans multi-missions.",
            '["analyser", "réfléchir", "décider", "planifier", "aide-moi à", "qu\'est-ce que tu penses", "mission code", "livrable", "stratégie", "comment aborder", "réflexion", "réfléchissons"]',
            "/app/mission.html",
            "#3b82f6"
        ),
        (
            "FORGE",
            "FORGE",
            "Exécution pure de missions code. Reçoit un livrable MENTOR et l'applique via le pipeline d'exécution. N'analyse pas, n'improvise pas.",
            '["exécute", "applique", "lance le pipeline", "démarre forge", "implémente", "forge", "fichier à modifier", "lance la mission"]',
            "/app/mission.html",
            "#f97316"
        ),
        (
            "SENTINELLE",
            "SENTINELLE",
            "Surveillance et gestion du portefeuille d'investissement personnel selon la règle 70/20/10. Consulte positions, budget, alertes, et met à jour thèses et watchlist.",
            '["portefeuille", "investissement", "position", "budget", "70/20/10", "pea", "cto", "watchlist", "thèse", "dividende", "cours", "alerte", "acheter", "vendre", "action", "ticker", "sentinelle"]',
            "/app/sentinelle.html",
            "#22c55e"
        ),
        (
            "ATELIER",
            "ATELIER",
            "Pipeline commercial prospects pour la restauration. Crée des prospects, génère des fiches et des démonstrations HTML personnalisées.",
            '["prospect", "restaurant", "restauration", "client", "démo", "kanban", "atelier", "fiche prospect", "pipeline prospect", "nouveau prospect"]',
            "/app/atelier.html",
            "#a855f7"
        ),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO agent_registry
            (name, display_name, description, routing_hints, page_url, color)
        VALUES (?, ?, ?, ?, ?, ?)
    """, agents)
    
    # C5+C6 — Corriger description et couleur ATELIER (INSERT OR IGNORE ne met pas à jour les lignes existantes)
    cursor.execute("""
        UPDATE agent_registry SET
            description = 'Crée un prospect restauration via une conversation rapide (3 questions). Le kanban, le pipeline démo et l''export restent dans l''Atelier.',
            color = '#e879f9'
        WHERE name = 'ATELIER'
    """)
    
    # C4 — Corriger description MENTOR
    cursor.execute("""
        UPDATE agent_registry SET
            description = 'Réflexion structurée pour cadrer une mission code (V1). Conduit une session de conversation puis génère un livrable que FORGE peut exécuter.'
        WHERE name = 'MENTOR'
    """)
    
    # mission_prompts : enveloppe structurée FORGE + reverse pointer
    for sql in [
        "ALTER TABLE mission_prompts ADD COLUMN livrable_forge TEXT",
        "ALTER TABLE mission_prompts ADD COLUMN forge_session_id INTEGER REFERENCES sessions(id)",
        "ALTER TABLE mission_prompts ADD COLUMN consumed_at TEXT",
    ]:
        try:
            cursor.execute(sql)
        except Exception:
            pass
    
    # messages : tracking agent + lien instance
    for sql in [
        "ALTER TABLE messages ADD COLUMN agent TEXT DEFAULT 'JARVIS'",
        "ALTER TABLE messages ADD COLUMN instance_ref TEXT",
    ]:
        try:
            cursor.execute(sql)
        except Exception:
            pass
    
    # pipeline_steps : résumé fonctionnel en français
    try:
        cursor.execute("ALTER TABLE pipeline_steps ADD COLUMN summary_fr TEXT")
    except Exception:
        pass
    
    conn.commit()


def _migrate_v5_media(conn):
    """Migration v5 : agent MEDIA — table jobs + seed agent_registry (idempotent)."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS media_jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL,
            media_type      TEXT NOT NULL CHECK(media_type IN ('image', 'video')),
            prompt          TEXT NOT NULL,
            result_url      TEXT,
            status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'done', 'error')),
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO agent_registry
            (name, display_name, description, routing_hints, page_url, color)
        VALUES (
            'MEDIA',
            'MEDIA',
            'Génération d''images (Flux 1.1 Pro) et vidéos (Kling 1.6) via fal.ai. Crée du contenu visuel à partir d''une description en langage naturel.',
            '["image", "photo", "illustration", "vidéo", "video", "clip", "animation", "génère", "génère une image", "crée une image", "dessine", "visualise", "flux", "kling"]',
            NULL,
            '#ef4444'
        )
    """)

    # Migration app_config : ajout colonne updated_at si absente
    try:
        cursor.execute("ALTER TABLE app_config ADD COLUMN updated_at TEXT")
    except Exception:
        pass  # Colonne déjà présente — idempotent

    conn.commit()


def _migrate_v6_consultation_state(conn):
    """Migration v6 : consultation_state machine (conversations directes uniquement).
    
    Les plans utilisent jarvis_plans.status + jarvis_plan_steps.status.
    
    Valeurs autorisées pour consultation_state :
    - NULL : conversation normale sans machine d'état
    - 'parsing' : parsing initial de la demande utilisateur
    - 'mentor_analysis' : MENTOR analyse et produit un livrable
    - 'user_questioning' : JARVIS pose des questions de clarification à l'utilisateur
    - 'mentor_validation' : MENTOR valide/ajuste le livrable après réponses utilisateur
    - 'forge_running' : FORGE exécute le code
    - 'jarvis_step_audit' : JARVIS audite le résultat d'une étape
    - 'completed' : consultation terminée avec succès
    
    consultation_data : JSON libre (TEXT) pour stocker métadonnées, ex: {"forge_retries": {"step_0": 1}}
    """
    cursor = conn.cursor()
    
    # Guard idempotent : vérifier si colonnes existent déjà
    cursor.execute("PRAGMA table_info(conversations)")
    conv_cols = {row["name"] for row in cursor.fetchall()}
    
    if "consultation_state" not in conv_cols:
        conn.execute("ALTER TABLE conversations ADD COLUMN consultation_state TEXT DEFAULT NULL")
    
    if "consultation_data" not in conv_cols:
        conn.execute("ALTER TABLE conversations ADD COLUMN consultation_data TEXT DEFAULT NULL")
    
    conn.commit()


def _migrate_v2(conn):
    """Migration v2 : ajoute les colonnes pour le Module Code refactorisé (idempotent)."""
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN modele_override TEXT NULL")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN source_mission_prompt_id INTEGER NULL")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE pipeline_steps ADD COLUMN sub_step_index INTEGER NULL")
    except Exception:
        pass

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_pipeline_steps_session_sub "
        "ON pipeline_steps(session_id, step_index, sub_step_index)"
    )

    try:
        cursor.execute("ALTER TABLE model_decision_log ADD COLUMN module_name TEXT DEFAULT 'unknown'")
    except Exception:
        pass

    conn.commit()


def _migrate_v7_disc(conn):
    """Migration v7 : agent DISC — tables disc_rules + disc_sessions + seed (idempotent)."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disc_rules (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            article        TEXT NOT NULL UNIQUE,
            parent_article TEXT,
            titre          TEXT NOT NULL,
            contenu        TEXT NOT NULL,
            categorie      TEXT NOT NULL CHECK(categorie IN (
                               'definitions','field','possession','stall','fouls',
                               'violations','scoring','out_of_bounds','restart',
                               'timeouts','spirit','officiating')),
            mots_cles      TEXT DEFAULT '[]',
            cross_refs     TEXT DEFAULT '[]',
            created_at     TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disc_sessions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id  INTEGER,
            question         TEXT NOT NULL,
            articles_utilises TEXT DEFAULT '[]',
            created_at       TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_disc_rules_article ON disc_rules(article)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_disc_rules_categorie ON disc_rules(categorie)")

    # Seed agent dans le registry
    cursor.execute("""
        INSERT OR IGNORE INTO agent_registry
            (name, display_name, description, routing_hints, page_url, color)
        VALUES (
            'DISC',
            'DISC',
            'Expert des règles officielles WFDF d''Ultimate Frisbee 2025-2028. Répond aux questions de règles, situations de jeu, self-officiating et Spirit of the Game (SOTG).',
            '["ultimate", "frisbee", "disc", "règle", "foul", "faute", "stall", "turnover", "SOTG", "spirit", "WFDF", "violation", "out of bounds", "end zone", "self-officiating", "disque", "lancer", "réception", "hors-jeu"]',
            NULL,
            '#22c55e'
        )
    """)

    # Seed règles fondamentales WFDF 2025-2028 — numéros approx., seront corrigés par PDF
    # Format : (article, parent_article, titre, contenu, categorie, mots_cles, cross_refs)
    seed_rules = [
        # ── Spirit of the Game ────────────────────────────────────────────────
        (
            "1", None,
            "Spirit of the Game (SOTG)",
            "Ultimate repose sur le Spirit of the Game, qui place la responsabilité du fair-play "
            "sur chaque joueur. Un jeu compétitif peut et doit se dérouler dans un esprit de respect "
            "mutuel entre joueurs. Les règles du jeu sont conçues de sorte qu'il soit possible de "
            "résoudre toutes les situations sans arbitre officiel. Les joueurs doivent toujours tenter "
            "de jouer dans les limites de l'esprit du jeu, même lorsque l'adversaire ne le fait pas. "
            "Les actes de triche délibérée, d'intimidation ou de comportement agressif sont contraires "
            "au Spirit of the Game et ne sont pas tolérés.",
            "spirit",
            '["spirit","SOTG","fair play","respect","self-officiating","esprit","fair-play","comportement","intimidation","triche"]',
            '["1.1","1.2","1.3","16"]'
        ),
        (
            "1.1", "1",
            "Connaissance des règles",
            "Les joueurs sont responsables de connaître et d'appliquer les règles. Un joueur qui "
            "commet une violation involontaire doit l'accepter sans contester. La règle d'or : "
            "si un joueur n'est pas certain qu'une violation a eu lieu, il ne doit pas appeler. "
            "Le doute profite à l'adversaire.",
            "spirit",
            '["connaissance règles","violation involontaire","doute","bonne foi","responsabilité"]',
            '["1","14","15"]'
        ),
        # ── Terrain & définitions ──────────────────────────────────────────────
        (
            "2", None,
            "Terrain — Dimensions officielles",
            "Le terrain de jeu est un rectangle de 100 mètres de long sur 37 mètres de large. "
            "Deux zones d'en-but (end zones) de 18 mètres chacune se situent aux deux extrémités. "
            "La zone centrale de jeu mesure donc 64 mètres. Les lignes de périmètre appartiennent "
            "à la zone hors-limites (out of bounds). Les lignes de but font partie de la zone d'en-but.",
            "field",
            '["terrain","dimensions","100 mètres","37 mètres","18 mètres","end zone","en-but","ligne","périmètre"]',
            '["10","12"]'
        ),
        (
            "2.A", "2",
            "Définitions — Disque vivant (live) et mort (dead)",
            "Le disque est VIVANT (live) dès que le lanceur établit son point de pivot après une "
            "reprise de jeu. Le disque est MORT (dead) dans les cas suivants : a) il touche le sol ; "
            "b) il sort hors-limites ; c) un appel (call) est formulé et reconnu ; d) le stall count "
            "atteint 10. Quand le disque est mort, le jeu s'arrête immédiatement — aucun déplacement "
            "ni lancer n'est valide.",
            "definitions",
            '["disque vivant","disque mort","live","dead","pivot","arrêt de jeu","call"]',
            '["8","9","10","15"]'
        ),
        (
            "2.B", "2",
            "Définitions — Possession et réception valide",
            "La possession est établie lorsqu'un joueur tient fermement le disque avec une ou deux "
            "mains. Une réception est valide (catch) lorsque le joueur : a) contrôle le disque avec "
            "au moins une main sans que le disque ne rebondisse ; b) maintient ce contrôle jusqu'à "
            "ce qu'il établisse son point de pivot. Si le disque touche le sol lors de la réception, "
            "c'est un turnover (possession perdue). La réception est aussi invalide si le joueur perd "
            "le contrôle en entrant en contact avec le sol (sauf s'il avait établi le contrôle avant).",
            "definitions",
            '["possession","réception","catch","contrôle","saisie","tenir","rebond"]',
            '["9","10","12","14"]'
        ),
        (
            "2.C", "2",
            "Définitions — Turnover (changement de possession)",
            "Un turnover se produit quand la possession change d'équipe. Causes de turnover : "
            "a) le disque touche le sol non contrôlé (drop) ; b) le disque est intercepté par un "
            "défenseur (interception) ; c) le disque sort hors-limites (OOB) ; d) le stall count "
            "atteint 10 (stall-out) ; e) le lanceur commet un travel ou une autre violation de lancer. "
            "Après un turnover, l'ancienne défense devient attaque et doit jouer depuis le point où "
            "s'est produit le turnover.",
            "definitions",
            '["turnover","changement possession","stall-out","interception","drop","sol","OOB","hors-limites"]',
            '["9","10","11","15"]'
        ),
        (
            "2.D", "2",
            "Définitions — Appel, Contest, Accept, Retract",
            "APPEL (call) : annonce verbale d'une infraction par un joueur concerné. "
            "CONTEST (contestation) : l'adversaire ne reconnaît pas la faute/violation appelée — "
            "le jeu revient alors à la dernière position incontestée. "
            "ACCEPT (acceptation) : l'adversaire reconnaît la faute/violation — la correction "
            "s'applique immédiatement. "
            "RETRACT (retrait) : le joueur qui a appelé retire son appel — le jeu reprend comme "
            "si la faute n'avait pas eu lieu. "
            "Règle fondamentale : en cas de désaccord non résolu, le disque revient au dernier "
            "lanceur avec un stall count de 'stall 1'.",
            "definitions",
            '["appel","call","contest","contestation","accept","accepter","retract","retirer","désaccord","procédure"]',
            '["1","14","15","9"]'
        ),
        # ── Pull — Engagement ─────────────────────────────────────────────────
        (
            "7", None,
            "Le Pull — Engagement initial",
            "Chaque point commence par un pull (engagement). L'équipe défendant l'en-but "
            "d'un côté lance le disque vers l'équipe attaquante positionnée à l'extrémité opposée. "
            "Le pull est valide si : a) le lanceur reste dans sa zone d'en-but au moment du lancer ; "
            "b) tous les joueurs restent dans leur propre zone d'en-but jusqu'au lancer. "
            "Si le pull sort OOB avant d'être touché par l'équipe attaquante, cette équipe peut : "
            "i) reprendre le jeu depuis son propre en-but, ou ii) depuis le point brick (20 mètres "
            "de son en-but). Si le pull est attrapé dans l'en-but de l'attaque, le porteur peut "
            "soit jouer depuis là, soit reculer au point brick.",
            "restart",
            '["pull","engagement","lancer initial","départ","brick","début de point","zone départ"]',
            '["7.1","7.2","8","10","11"]'
        ),
        (
            "7.1", "7",
            "Pull — Faux-départ (offside)",
            "Si un joueur quitte sa zone d'en-but avant que le pull soit lancé, l'équipe adverse "
            "peut appeler 'Offside'. Si l'appel est accepté : l'équipe attaquante peut ignorer le "
            "résultat du pull et recommencer depuis son en-but. "
            "Esprit du jeu : prévenir verbalement avant d'appeler offside.",
            "restart",
            '["offside","faux départ","pull","avant lancer","zone"]',
            '["7","1"]'
        ),
        # ── Reprise de jeu ────────────────────────────────────────────────────
        (
            "8", None,
            "Reprise du jeu — Check",
            "Le jeu ne reprend que lorsque le porteur du disque crie 'Disc in' après avoir "
            "obtenu l'accord de l'adversaire le plus proche. Procédure après un appel : "
            "1) Les deux équipes se positionnent comme au moment de l'appel ; "
            "2) Le défenseur désigné touche le disque ou dit 'OK' (check disc) ; "
            "3) Le porteur dit 'Disc in' — le jeu reprend. "
            "Si le porteur lance avant le check, le lancer est nul et le disque revient.",
            "restart",
            '["check","disc in","reprise","jeu","check disc","après appel","positionner"]',
            '["9","14","15"]'
        ),
        (
            "8.1", "8",
            "Reprise après turnover OOB",
            "Si le disque sort hors-limites, l'équipe qui récupère la possession reprend depuis "
            "le point brick le plus proche de l'endroit où le disque est sorti. "
            "Point brick : marquage au sol à 20 mètres de chaque zone d'en-but. "
            "Le jeu reprend avec la procédure de check standard.",
            "out_of_bounds",
            '["brick","OOB","hors-limites","reprise turnover","point brick","20 mètres","sortie terrain"]',
            '["7","8","10"]'
        ),
        # ── Stall Count ───────────────────────────────────────────────────────
        (
            "9", None,
            "Stall Count — Règle principale",
            "Le stall count est le décompte verbal de 1 à 10 effectué par le défenseur qui marque "
            "(garde) le porteur du disque. Règles du stall count : "
            "a) Le décompte doit être audible et clairement énoncé ('stall 1, stall 2...' ou '1,2...'). "
            "b) Une seconde minimum doit s'écouler entre chaque nombre. "
            "c) Si le stall count atteint 10 avant le lancer (stall-out), c'est un turnover. "
            "d) Le défenseur qui compte doit être le seul à marquer le porteur. "
            "e) Si le marqueur change pendant le décompte, le nouveau marqueur reprend à 'stall 1'.",
            "stall",
            '["stall","décompte","compte","10","stall-out","marqueur","audible","marquer porteur"]',
            '["9.1","9.2","9.3","9.4","9.5","15.2"]'
        ),
        (
            "9.1", "9",
            "Stall Count — Interruptions légales",
            "Le stall count est légalement interrompu (reprend à 1) dans les cas suivants : "
            "a) Le marqueur s'éloigne à plus de 3 mètres du porteur ; "
            "b) Un appel (call) est formulé et reconnu ; "
            "c) Un time-out est accordé ; "
            "d) Le porteur reçoit le disque après un check. "
            "Après résolution d'un appel ACCEPTÉ par le marqueur : le décompte reprend à 'stall 1'. "
            "Après résolution d'un appel CONTESTÉ : le décompte reprend au nombre où il était "
            "au moment de l'appel, plus 1 (ex : si l'appel était à 'stall 6', reprise à 'stall 7').",
            "stall",
            '["interruption stall","reprend à 1","appel","3 mètres","time-out","after call","stall après appel"]',
            '["9","8","13","15"]'
        ),
        (
            "9.2", "9",
            "Fast Count — Décompte trop rapide",
            "Si le marqueur compte plus vite qu'une seconde par nombre (fast count), le porteur peut "
            "appeler 'Fast count'. "
            "Si la faute est acceptée : le décompte reprend à 'stall [nombre actuel - 2]' (minimum 1). "
            "Si contestée : le jeu revient à la position précédente avec 'stall 1'. "
            "Exemple : si fast count est appelé à 'stall 7', reprise à 'stall 5'.",
            "stall",
            '["fast count","décompte rapide","trop vite","compte rapide","stalling","rythme"]',
            '["9","9.1"]'
        ),
        (
            "9.3", "9",
            "Stalling — Décompte sans être le marqueur",
            "Seul le défenseur qui marque directement le porteur peut effectuer le stall count. "
            "Si un autre défenseur commence à compter, c'est une violation 'Stalling'. "
            "Le porteur appelle 'Stalling' et le décompte reprend à 'stall 1'.",
            "stall",
            '["stalling","marqueur","seul défenseur","compter","qui peut compter"]',
            '["9","15.2"]'
        ),
        # ── Hors-limites (Out of Bounds) ───────────────────────────────────────
        (
            "10", None,
            "Hors-limites (Out of Bounds) — Règle principale",
            "Le terrain est délimité par des lignes. Ces lignes appartiennent à la zone hors-limites "
            "(OOB) — elles ne font PAS partie du terrain de jeu. "
            "Le disque est OOB si : a) il touche le sol, un objet ou une personne situés OOB ; "
            "b) il est en contact avec la ligne de périmètre. "
            "Un joueur est OOB si une partie de son corps touche la ligne ou l'extérieur du terrain, "
            "SAUF s'il est en l'air et que ses pieds sont in-bounds au moment de la réception.",
            "out_of_bounds",
            '["out of bounds","hors-limites","OOB","ligne","terrain","périmètre","touche la ligne"]',
            '["10.1","10.2","10.3","2","8"]'
        ),
        (
            "10.1", "10",
            "Réception in-bounds par un joueur en l'air",
            "Un joueur en l'air peut réceptionner in-bounds même si son élan le porte hors du terrain, "
            "à condition que : a) aucune partie de son corps ne touche OOB au moment où il contrôle "
            "le disque ; b) le premier contact avec le sol après la réception doit être in-bounds. "
            "Si le joueur atterrit OOB après avoir contrôlé le disque in-bounds : "
            "— la réception EST valide si les deux conditions ci-dessus sont remplies. "
            "— la réception N'EST PAS valide si son pied touche OOB pendant la réception.",
            "out_of_bounds",
            '["saut","en l air","réception en l air","atterrissage","pied in-bounds","momentum","joueur volant"]',
            '["10","12"]'
        ),
        (
            "10.2", "10",
            "Réception OOB — Procédure après sortie",
            "Si le disque sort OOB, le jeu s'arrête. La possession revient à l'équipe qui n'a PAS "
            "lancé le disque OOB (l'adversaire du dernier lanceur). "
            "Reprise : depuis le point de la ligne le plus proche de là où le disque est sorti, "
            "ou depuis le point brick le plus proche si cela est plus avantageux. "
            "Si le disque sort après avoir été touché en dernier par l'attaque : turnover. "
            "Si par la défense : retour au lanceur.",
            "out_of_bounds",
            '["disque sort","reprise OOB","qui reprend","après sortie","possession","brick","ligne"]',
            '["8","8.1","7","10"]'
        ),
        (
            "10.3", "10",
            "Disque ou joueur touchant la ligne de fond (end zone)",
            "La ligne de fond (end zone line) fait partie de la zone d'en-but, PAS de la zone OOB. "
            "Si le disque est réceptionné sur ou derrière la ligne de fond de l'adversaire : "
            "c'est un point marqué, SAUF si le récepteur est OOB. "
            "Si le récepteur saute depuis in-bounds et attrape dans la zone d'en-but : point valide "
            "si ses pieds restent in-bounds ou s'il n'a pas encore touché le sol OOB.",
            "out_of_bounds",
            '["ligne fond","end zone line","en-but","ligne derrière","réception end zone","point ligne"]',
            '["10","12","12.1"]'
        ),
        # ── Marquer un point ──────────────────────────────────────────────────
        (
            "12", None,
            "Marquer un point — Règle principale",
            "Un point est marqué lorsqu'un joueur de l'équipe attaquante réceptionne légalement "
            "le disque dans la zone d'en-but adverse. Conditions obligatoires : "
            "a) Le joueur doit avoir les deux pieds dans la zone d'en-but au moment de la réception ; "
            "b) La réception doit être complète (contrôle total du disque) ; "
            "c) Le joueur ne doit pas être OOB. "
            "Si un appel est formulé PENDANT la réception du point : le point n'est valide que si "
            "toutes les parties reconnaissent que la réception était complète et in-bounds.",
            "scoring",
            '["point","but","marquer","scoring","end zone","en-but","réception zone","gagner point"]',
            '["12.1","12.2","10","14.3"]'
        ),
        (
            "12.1", "12",
            "Point contesté",
            "Si une faute ou une violation est appelée pendant la réception qui marque un point, "
            "et que cet appel est contesté par l'adversaire : "
            "— La possession revient au porteur avant le lancer (pas de point). "
            "— Le stall count reprend à 'stall 1'. "
            "Si la faute est acceptée et aurait empêché la réception : le point est accordé. "
            "Si la faute est acceptée mais n'aurait pas changé l'issue : le point est accordé si "
            "le récepteur était clairement in-bounds.",
            "scoring",
            '["point contesté","appel pendant réception","faute point","scoring contest","but refusé"]',
            '["12","14","14.3","2.D"]'
        ),
        # ── Procédure d'appel ─────────────────────────────────────────────────
        (
            "13", None,
            "Procédure d'appel — Règle universelle",
            "Tout appel (call) doit être : a) formulé clairement et audiblement ; "
            "b) formulé IMMÉDIATEMENT (pas après plusieurs échanges) ; "
            "c) formulé par le joueur directement concerné (sauf en cas d'OOB visible). "
            "Quand un appel est formulé : 1) le jeu s'arrête immédiatement ; "
            "2) les deux parties discutent calmement ; 3) si accord → correction et reprise ; "
            "4) si désaccord (contest) → retour à la dernière position incontestée avec stall 1. "
            "Un appel tardif ou formulé par un mauvais joueur peut être refusé.",
            "restart",
            '["appel","call","procédure","formuler appel","accord","désaccord","contest","accept","retract"]',
            '["2.D","14","15","9.1"]'
        ),
        (
            "13.1", "13",
            "Time-out d'équipe",
            "Chaque équipe dispose d'un nombre limité de time-outs par mi-temps (généralement 2). "
            "Un time-out peut être demandé uniquement par le porteur du disque (attaque) ou "
            "par n'importe quel défenseur (défense) lorsque le disque est mort. "
            "Durée : 70 secondes maximum. "
            "Après le time-out : reprise avec check depuis la position où le disque se trouvait.",
            "timeouts",
            '["time-out","timeout","équipe","pause","70 secondes","reprise après time-out"]',
            '["8","9.1","16"]'
        ),
        # ── Fautes ────────────────────────────────────────────────────────────
        (
            "14", None,
            "Fautes (Fouls) — Règle principale",
            "Une faute est un contact physique illégal entre adversaires qui affecte le jeu. "
            "Seul le joueur fauté peut appeler 'Foul'. Procédure : "
            "1) Le joueur fauté appelle 'Foul' ; 2) le jeu s'arrête immédiatement ; "
            "3) si la faute est ACCEPTÉE (non contestée) → correction selon le type de faute ; "
            "4) si la faute est CONTESTÉE → retour à la dernière position avant la faute, stall 1. "
            "Important : un contact minimal et involontaire (non significatif) ne constitue PAS une faute.",
            "fouls",
            '["faute","foul","contact","illégal","physique","appel foul","correction faute"]',
            '["14.1","14.2","14.3","14.4","15","2.D"]'
        ),
        (
            "14.1", "14",
            "Strip — Faute sur le porteur (disque arraché)",
            "Un strip se produit lorsqu'un défenseur frappe ou touche le disque alors que le porteur "
            "en a déjà le contrôle, lui faisant perdre la possession. "
            "Si la faute est ACCEPTÉE : le porteur récupère la possession au point du strip, "
            "stall count reprend à 'stall 1'. "
            "Si CONTESTÉE : retour au lanceur avant le strip.",
            "fouls",
            '["strip","arraché","disque arraché","porteur","contrôle","défenseur frappe","perte possession"]',
            '["14","2.B"]'
        ),
        (
            "14.2", "14",
            "Faute sur le lancer (Throwing Foul)",
            "Une faute sur le lancer se produit quand un défenseur entre en contact physique avec "
            "le bras ou le corps du lanceur pendant ou juste avant le lancer. "
            "Si la faute est ACCEPTÉE : le porteur relance depuis le même endroit, stall 1. "
            "Si CONTESTÉE : si le lancer aboutit à une réception valide, la réception est maintenue. "
            "Si le lancer aboutit à un turnover, retour au lanceur, stall 1.",
            "fouls",
            '["throwing foul","faute lancer","bras","contact bras","lanceur","pendant lancer"]',
            '["14","9.1"]'
        ),
        (
            "14.3", "14",
            "Faute sur réception (Receiving Foul)",
            "Une faute sur réception se produit quand un défenseur entre en contact avec un joueur "
            "attaquant qui tente de réceptionner le disque, affectant la réception. "
            "Si la faute est ACCEPTÉE : l'attaquant obtient la possession à l'endroit de la faute. "
            "Si la réception était dans la zone d'en-but : le point est accordé. "
            "Si CONTESTÉE : retour au lanceur, stall 1.",
            "fouls",
            '["receiving foul","faute réception","contact récepteur","réception perturbée","défenseur attaquant"]',
            '["14","12","12.1"]'
        ),
        (
            "14.4", "14",
            "Faute défensive sur coupé (Guarding Foul)",
            "Un défenseur ne peut pas entrer en contact physique significatif avec un attaquant "
            "qui court (coupe), même si le disque n'est pas encore lancé dans sa direction. "
            "Le joueur fauté appelle 'Foul'. Si acceptée : l'attaquant reprend sa course depuis "
            "le point de la faute. Si contestée : retour à la dernière position.",
            "fouls",
            '["guarding foul","faute marquage","couper","coupé","attaquant qui court","défenseur"]',
            '["14","15.4"]'
        ),
        # ── Violations ────────────────────────────────────────────────────────
        (
            "15", None,
            "Violations — Règle principale",
            "Une violation est une infraction non physique aux règles du jeu. "
            "Elle est appelée par l'équipe non-fautive. Procédure identique aux fautes : "
            "appel, arrêt du jeu, discussion, accept ou contest. "
            "Différence clé avec les fautes : les violations impliquent rarement un contact physique. "
            "Types principaux : travel, double team, disc space, pick, stalling, fast count.",
            "violations",
            '["violation","infraction","règle","non physique","double team","disc space","pick","travel","stalling"]',
            '["15.1","15.2","15.3","15.4","15.5","9"]'
        ),
        (
            "15.1", "15",
            "Travel (marcher)",
            "Un travel se produit quand : a) le porteur déplace son pied de pivot avant de lâcher "
            "le disque ; b) le porteur avance avec le disque sans établir de pivot ; "
            "c) le porteur récupère le disque en courant et ne s'arrête pas correctement. "
            "L'adversaire (ou tout joueur) peut appeler 'Travel'. "
            "Si accepté : le porteur retourne à sa position de pivot légale, stall 1. "
            "Si contesté : stall 1, jeu reprend depuis la position actuelle.",
            "violations",
            '["travel","marcher","pivot","pied pivot","déplacer pivot","avancer disque","établir pivot"]',
            '["15","9.1","2.B"]'
        ),
        (
            "15.2", "15",
            "Double Team",
            "Double team : deux défenseurs ou plus à moins de 3 mètres du porteur simultanément, "
            "sans qu'un attaquant ne se trouve dans cette même zone. "
            "L'un des défenseurs doit s'éloigner. Si l'appel 'Double team' est formulé : "
            "Si accepté : stall count réduit de 2 ('stall [N-2]', minimum 1). "
            "Si contesté : stall count reprend à 'stall [N-1]'.",
            "violations",
            '["double team","deux défenseurs","3 mètres","zone porteur","plusieurs marqueurs"]',
            '["15","9","9.1"]'
        ),
        (
            "15.3", "15",
            "Disc Space",
            "Le marqueur doit maintenir une distance d'au moins un disque de diamètre entre lui "
            "et le porteur (disc space). Si le marqueur est trop proche (moins d'un disque), "
            "le porteur appelle 'Disc space'. "
            "Si accepté : le marqueur recule immédiatement. "
            "Si l'appel survient pendant le stall count : stall réduit de 2 (minimum 1). "
            "Disc space s'applique aussi si le marqueur bloque activement le mouvement du bras du lanceur.",
            "violations",
            '["disc space","espace","trop proche","marqueur","distance","un disque","diamètre","bloquer bras"]',
            '["15","9","14.2"]'
        ),
        (
            "15.4", "15",
            "Pick",
            "Un pick se produit quand un joueur attaquant bloque involontairement ou volontairement "
            "le chemin d'un défenseur qui marque un autre attaquant, l'empêchant de suivre sa cible. "
            "Le défenseur gêné appelle 'Pick'. "
            "Si accepté : le défenseur reprend sa position relative par rapport à sa cible (comme si "
            "le pick n'avait pas eu lieu). Le jeu reprend depuis la position au moment du pick.",
            "violations",
            '["pick","bloquer défenseur","chemin","écran","gêner marquage","bloquer route"]',
            '["15","14.4"]'
        ),
        # ── Blessure & Spirit timeout ─────────────────────────────────────────
        (
            "16", None,
            "Blessure — Arrêt de jeu",
            "Si un joueur est blessé pendant le jeu, le jeu s'arrête IMMÉDIATEMENT. "
            "Tous les joueurs maintiennent leur position. Procédure : "
            "1) Le jeu s'arrête ; 2) le joueur blessé est soigné ; "
            "3) Si le joueur peut reprendre rapidement : reprise avec check depuis la position au moment "
            "de la blessure ; "
            "4) Si remplacement nécessaire : l'équipe adverse peut aussi effectuer un remplacement. "
            "Exception : si la blessure résulte d'un contact illégal, l'adversaire ne peut pas substituer.",
            "timeouts",
            '["blessure","injury","joueur blessé","arrêt de jeu","soins","remplacement","substitution"]',
            '["16.1","13.1","1"]'
        ),
        (
            "16.1", "16",
            "Spirit Timeout (Time-out Esprit)",
            "N'importe quel joueur peut demander un spirit timeout pour résoudre un conflit ou "
            "améliorer l'atmosphère du jeu. Le spirit timeout dure au maximum 5 minutes. "
            "Il ne compte pas dans les time-outs d'équipe réglementaires. "
            "Les capitaines des deux équipes doivent être présents pour la discussion. "
            "Objectif : résoudre un problème de comportement ou d'interprétation des règles "
            "avant que la situation ne s'aggrave.",
            "timeouts",
            '["spirit timeout","time-out esprit","conflit","capitaine","5 minutes","comportement","résoudre"]',
            '["1","16","13.1"]'
        ),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO disc_rules
            (article, parent_article, titre, contenu, categorie, mots_cles, cross_refs)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, seed_rules)

    conn.commit()
