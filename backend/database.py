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

    # Seed 15+ règles fondamentales WFDF 2025-2028 (numéros approximatifs)
    seed_rules = [
        ("1", None, "Spirit of the Game", "Ultimate repose sur le Spirit of the Game, qui place la responsabilité du fair-play sur chaque joueur. Un jeu compétitif peut et doit se dérouler dans un esprit de respect mutuel entre joueurs. Les règles du jeu sont conçues de sorte qu'il soit possible de résoudre toutes les situations sans un arbitre officiel. Les joueurs doivent toujours tenter de jouer dans les limites de l'esprit du jeu, même lorsque l'adversaire ne le fait pas.", "spirit", '["spirit","SOTG","fair play","respect","self-officiating","esprit"]', '["1.1","1.2"]'),
        ("2.1", "2", "Terrain", "Le terrain est un rectangle de 100 mètres de long sur 37 mètres de large, avec deux zones d'en-but aux deux extrémités de 18 mètres chacune. Les lignes délimitant le terrain ne font pas partie du terrain de jeu (in-bounds). Un joueur dont les deux pieds sont à l'intérieur des lignes est considéré comme in-bounds.", "field", '["terrain","field","dimensions","ligne","end zone","zone en-but"]', '["11","12"]'),
        ("2.2", "2", "Définitions — Disque vivant et mort", "Le disque est vivant (live) dès que le lanceur établit son point de pivot. Le disque est mort (dead) dans les cas suivants : a) il touche le sol ; b) il est intercepté ou capturé par la défense ; c) il sort des limites du terrain ; d) un appel (call) est formulé et accepté.", "definitions", '["disque vivant","disque mort","live","dead","pivot","point de pivot"]', '["9","10","11"]'),
        ("2.3", "2", "Définitions — Possession et réception", "La possession du disque signifie qu'un joueur tient fermement le disque. Une réception (catch) est établie lorsqu'un joueur attrapant saisit le disque et maintient cette saisie suffisamment longtemps pour établir le contrôle sur le disque. Un joueur ne contrôle pas le disque s'il rebondit sur sa main ou si le premier contact avec le sol (sol ou obstacle) modifie sa trajectoire.", "definitions", '["possession","réception","catch","attraper","contrôle","saisie"]', '["9","10","14"]'),
        ("2.4", "2", "Définitions — Turnover", "Un turnover se produit lorsque la possession du disque change d'équipe. Cela survient dans les cas suivants : a) le disque touche le sol sans être contrôlé ; b) le disque est intercepté par un défenseur ; c) le disque sort des limites du terrain ; d) le stall count atteint 10 (stall-out) ; e) une violation de lancer est commise.", "definitions", '["turnover","changement possession","stall-out","interception","sol"]', '["9","10","11","12"]'),
        ("9", None, "Stall Count", "Le stall count est le décompte de 1 à 10 effectué par le défenseur marquant le porteur du disque. Le décompte doit être audible. Si le stall count atteint 10 avant que le disque soit lancé (stall-out), c'est un turnover. Le décompte recommence à 1 : a) après un appel ; b) si le marqueur s'éloigne de plus de 3 mètres du porteur ; c) sur reprise de jeu après time-out. Le décompte reprend à 'stall [nombre+1]' dans certaines situations de contestation.", "stall", '["stall","décompte","marqueur","10","stall-out","stalling","compte"]', '["9.1","9.2","9.3","9.4","9.5"]'),
        ("9.3", "9", "Décompte rapide (Fast Count)", "Si le décompte est trop rapide (moins d'une seconde entre chaque nombre), le porteur peut appeler 'Fast count'. Le décompte reprend à 'stall [nombre actuel - 1]' si le compte était à 2 ou plus, ou à 'stall 1' si en début de compte.", "stall", '["fast count","décompte rapide","stalling","compte trop rapide"]', '["9","17"]'),
        ("10", None, "Hors-limites — Out of Bounds", "Le disque est hors-limites (out of bounds, OOB) lorsqu'il touche le sol, un objet ou une personne hors des lignes. La ligne elle-même n'est pas in-bounds. Pour une réception OOB, ce qui compte est le premier point de contact avec le sol ou un objet fixe. Un joueur dans les airs peut réceptionner in-bounds tant qu'aucune partie de son corps ne touche OOB pendant la réception.", "out_of_bounds", '["out of bounds","hors-limites","OOB","ligne","réception","sol","limites"]', '["10.1","10.2","10.3","11"]'),
        ("10.2", "10", "Réception en limite de terrain", "Si un joueur réceptionne le disque avec un pied in-bounds et l'autre OOB, la réception est OOB. Si le premier contact au sol est in-bounds mais glisse hors des limites, le jeu s'arrête à la ligne. Le lanceur suivant reprend depuis le point brick le plus proche ou le point d'interception.", "out_of_bounds", '["réception ligne","pied hors-limites","sortie","border","limite terrain"]', '["10","11","8"]'),
        ("11", None, "Reprise du jeu", "La reprise du jeu suit des procédures spécifiques selon la cause de l'arrêt. Après un turnover OOB, le jeu reprend au point brick le plus proche de l'endroit où le disque est sorti. Après un appel accepté, l'équipe non-fautive reprend avec le disque à l'endroit où il était au moment de l'appel.", "restart", '["reprise","brick","restart","reprise du jeu","after call"]', '["10","12","14","15"]'),
        ("12", None, "Marquer un point", "Un point est marqué lorsqu'un joueur de l'équipe attaquante réceptionne légalement le disque dans la zone d'en-but adverse. La réception doit être complète avant que le joueur touche le sol dans la zone d'en-but. Si un appel est formulé pendant une réception dans la zone d'en-but, le point n'est accordé que si toutes les parties sont d'accord.", "scoring", '["point","but","scoring","en-but","end zone","réception zone","marquer"]', '["12.1","12.2","2.1"]'),
        ("12.2", "12", "Contestation de point", "Si un appel est formulé pendant la réception d'un point et que les parties ne sont pas d'accord, la possession revient au dernier lanceur incontesté. Si une faute est appelée pendant la réception et non contestée, le point est accordé.", "scoring", '["contestation","point contesté","appel en-but","faute réception"]', '["12","14","16"]'),
        ("14", None, "Fautes (Fouls)", "Une faute est un contact physique illégal entre adversaires. Le porteur du disque appelle 'Foul'. Si la faute est acceptée (non contestée), le disque revient au porteur. Si la faute est contestée, le disque revient au dernier lanceur incontesté. Types principaux : strip (disque arraché), faute sur réception, faute sur lancer.", "fouls", '["faute","foul","contact","strip","arraché","foul offensif","foul défensif"]', '["14.1","14.2","14.3","15","16"]'),
        ("14.3", "14", "Faute sur réception (Receiving Foul)", "Si un défenseur commet une faute sur un joueur attaquant pendant la réception et que la faute n'est pas contestée, l'attaquant obtient la possession à l'endroit de la faute. Si la réception était dans la zone d'en-but, le point est accordé.", "fouls", '["faute réception","receiving foul","contact récepteur","défenseur","attaquant"]', '["12","14","16"]'),
        ("15", None, "Violations", "Une violation est une infraction aux règles autre qu'une faute ou un appel. Les violations courantes incluent : travel (marcher/déplacer le pivot), double-team (deux défenseurs à moins de 3m du porteur), disc space (défenseur trop proche du porteur en line), pick (bloquer un défenseur). L'équipe non-fautive appelle la violation.", "violations", '["violation","travel","double team","disc space","pick","marcher","pivot"]', '["15.1","15.2","15.3","15.4","9"]'),
        ("15.1", "15", "Travel", "Un travel se produit lorsque le porteur du disque déplace son pied de pivot avant de lâcher le disque, ou avance avec le disque sans avoir établi de point de pivot. L'adversaire peut appeler 'Travel'. Le compte reprend à 'stall 1'. Correction : retour à la position de pivot légale.", "violations", '["travel","marcher","pivot","pied pivot","déplacement"]', '["9","15"]'),
        ("15.2", "15", "Double Team", "Une situation de double-team se produit lorsque deux défenseurs ou plus se trouvent simultanément à moins de 3 mètres du porteur du disque. Exception : si un autre attaquant se trouve dans cette zone. L'appel 'Double team' réinitialise le compte à 'stall [nombre - 1]'.", "violations", '["double team","deux défenseurs","3 mètres","marqueur","zone porteur"]', '["9","15"]'),
        ("16", None, "Blessure et Time-out Spirit", "Si un joueur est blessé, le jeu s'arrête immédiatement. L'équipe blessée peut traiter la blessure. L'équipe peut substituer le joueur blessé uniquement si l'équipe adverse substitue aussi (sauf si la blessure est le résultat d'un contact illégal). Un time-out Spirit peut être demandé par n'importe quel joueur pour résoudre un problème d'esprit du jeu.", "timeouts", '["blessure","injury","time-out spirit","spirit timeout","substitution"]', '["1","13"]'),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO disc_rules
            (article, parent_article, titre, contenu, categorie, mots_cles, cross_refs)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, seed_rules)

    conn.commit()
