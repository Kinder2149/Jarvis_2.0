import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "jarvis.db"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

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

    env_file = _Path(__file__).parent / ".env"
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
        if not current_value:
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
    _seed_api_keys_from_env(conn)
    conn.close()
