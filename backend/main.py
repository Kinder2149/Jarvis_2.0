from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

from backend.database import init_db
from backend.routers import projects, pipelines, models, files, chat

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
app.include_router(models.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

@app.get("/")
def root():
    return RedirectResponse(url="/app/index.html")

@app.on_event("startup")
def startup():
    init_db()
    logger.info("JARVIS démarré")
