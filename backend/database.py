import sqlite3
from pathlib import Path
import json
import logging
import os

DB_PATH = Path(__file__).parent / "data" / "jarvis.db"
CONFIG_PATH = Path(__file__).parent / "data" / "config.json"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
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
        api_keys = {"openrouter_key": "", "anthropic_key": "", "google_key": "", "web_search_key": ""}
    
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
        "system_prompt_preset": ""
    }
    
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_file = json.load(f)
            if "model_preferences" in config_file:
                model_preferences = config_file["model_preferences"]
                logger.info(f"📋 [DB] model_preferences chargées depuis config.json")
            if "chat" in config_file:
                chat_config.update(config_file["chat"])
                logger.info(f"💬 [DB] chat config chargée depuis config.json")
    
    logger.info(f"✅ [DB] Config chargée: {len(api_keys)} clés API, {len(model_preferences)} préférences modèles")
    return {
        "api_keys": api_keys,
        "model_preferences": model_preferences,
        "chat": chat_config
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

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            module_type TEXT DEFAULT 'dossier',
            category TEXT,
            parent_dossier_id INTEGER REFERENCES projects(id),
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Migration : ajout des 3 nouvelles colonnes si elles n'existent pas
    migrations = [
        "ALTER TABLE projects ADD COLUMN module_type TEXT DEFAULT 'dossier'",
        "ALTER TABLE projects ADD COLUMN category TEXT",
        "ALTER TABLE projects ADD COLUMN parent_dossier_id INTEGER REFERENCES projects(id)",
    ]
    for migration in migrations:
        try:
            cursor.execute(migration)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    
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
    
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN local_path TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN instructions TEXT DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
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
    _create_reflexion_tables(conn)
    _migrate_v2(conn)
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

    conn.commit()
