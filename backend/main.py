from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import json
import shutil

from backend.database import init_db, get_connection
from backend.routers import projects, pipelines, files, chat, atelier, config, reflexions

LOG_PATH = Path(__file__).parent / "data" / "jarvis.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

handler = RotatingFileHandler(
    LOG_PATH,
    maxBytes=1_000_000,
    backupCount=3,
    encoding="utf-8"
)
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="JARVIS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api")
app.include_router(pipelines.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(atelier.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(reflexions.router, prefix="/api")

frontend_path = Path(__file__).parent.parent / "frontend"
logger.info(f"Frontend path: {frontend_path}")
logger.info(f"Frontend path exists: {frontend_path.exists()}")
if frontend_path.exists():
    logger.info(f"Mounting static files from: {frontend_path}")
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
else:
    logger.error(f"Frontend directory not found at: {frontend_path}")

@app.get("/")
def root():
    return RedirectResponse(url="/app/index.html")

def migrate_config_to_sqlite():
    """Migre les clés API de config.json vers SQLite (une seule fois)."""
    config_path = Path(__file__).parent / "data" / "config.json"
    
    if not config_path.exists():
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Vérifier si migration déjà faite
    cursor.execute("SELECT COUNT(*) as count FROM app_config WHERE category = 'api_keys'")
    count = cursor.fetchone()["count"]
    
    if count > 0:
        conn.close()
        return  # Migration déjà effectuée
    
    # Lire config.json
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    api_keys = config.get("api_keys", {})
    
    # Migrer api_keys vers SQLite
    for key_name, value in api_keys.items():
        if value:  # Seulement si clé non vide
            cursor.execute("""
                INSERT INTO app_config (key, value, category, updated_at)
                VALUES (?, ?, 'api_keys', datetime('now'))
            """, (key_name, value))
    
    conn.commit()
    conn.close()
    
    # Backup config.json
    backup_path = config_path.with_suffix(".json.backup")
    shutil.copy(config_path, backup_path)
    logger.info(f"Backup config.json → {backup_path}")
    
    # Réécrire config.json sans api_keys (garder seulement model_preferences)
    new_config = {"model_preferences": config.get("model_preferences", {})}
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2)
    
    logger.info("Migration config.json → SQLite terminée")

def seed_context_from_methodo():
    """Seed profil_utilisateur et regles_globales depuis fichiers METHODO si vides."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lire le chemin METHODO depuis config (ou fallback)
    try:
        cursor.execute("SELECT value FROM app_config WHERE key = 'chat_methodo_path'")
        row = cursor.fetchone()
        methodo_path = Path(row["value"]) if row and row["value"] else Path("C:\\DEV\\METHODO")
    except Exception:
        methodo_path = Path("C:\\DEV\\METHODO")
    
    # Mapping clé SQLite → nom fichier
    context_files = {
        "profil_utilisateur": "PROFIL_UTILISATEUR.md",
        "regles_globales": "REGLES_GLOBALES.md"
    }
    
    for key, filename in context_files.items():
        try:
            # Lire valeur actuelle en SQLite
            cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            current_value = row["value"] if row else ""
            
            # Si déjà rempli, ne rien faire
            if current_value and current_value.strip():
                continue
            
            # Construire chemin fichier source
            source_file = methodo_path / "COMMUN" / filename
            
            if not source_file.exists():
                logger.warning(f"Seeding {key}: fichier source absent → {source_file}")
                continue
            
            # Lire contenu et écrire en SQLite
            content = source_file.read_text(encoding="utf-8")
            cursor.execute(
                "INSERT OR REPLACE INTO app_config (key, value, category, updated_at) VALUES (?, ?, 'context', datetime('now'))",
                (key, content)
            )
            logger.info(f"✅ Seeded {key} depuis {source_file}")
        
        except Exception as e:
            logger.warning(f"Erreur seeding {key}: {e}")
    
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()
    
    # Reset sessions RUNNING → FAILED (arrêt brutal serveur)
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE sessions SET status = 'FAILED', updated_at = datetime('now') WHERE status = 'RUNNING'"
    )
    affected_sessions = cursor.rowcount
    
    cursor.execute(
        "UPDATE pipeline_steps SET status = 'FAILED', error_message = 'Interrompu par redémarrage serveur' WHERE status = 'RUNNING'"
    )
    affected_steps = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    if affected_sessions > 0:
        logger.warning(f"Startup recovery: {affected_sessions} sessions RUNNING → FAILED, {affected_steps} steps réinitialisés")
    
    migrate_config_to_sqlite()
    seed_context_from_methodo()
    logger.info("JARVIS démarré")
