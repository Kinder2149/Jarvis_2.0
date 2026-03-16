import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Charger .env AVANT tous les autres imports (override=True pour forcer rechargement)
load_dotenv(override=True)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from backend.api import router
from backend.db.database import db_instance
from backend.logging_config import setup_logging
from backend.ia.providers.provider_factory import ProviderFactory

# Configuration du logging au démarrage
setup_logging(log_level=logging.DEBUG)
logger = logging.getLogger(__name__)


class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    """Désactive le cache navigateur pour les fichiers frontend (dev only)."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/frontend"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Vider le cache des providers pour forcer rechargement avec nouveau .env
    ProviderFactory.clear_cache()
    logger.info("Provider cache cleared - configuration rechargée depuis .env")
    
    # Vider le cache des agents pour forcer rechargement des prompts
    from backend.agents.agent_factory import clear_cache
    clear_cache()
    logger.info("Agent cache cleared - prompts système rechargés depuis fichiers .md")
    
    await db_instance.initialize()
    await db_instance.seed_library_if_empty()
    yield


app = FastAPI(
    title="JARVIS",
    description="Application FastAPI principale pour JARVIS 2.0 - Dernière modification: 2026-02-18 11:06",
    lifespan=lifespan
)

app.add_middleware(NoCacheStaticMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "null",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Monter le dossier frontend comme fichiers statiques
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/frontend", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

# Servir index.html à la racine
from fastapi.responses import FileResponse

@app.get("/index.html")
async def serve_index():
    """Servir index.html"""
    return FileResponse(frontend_path / "index.html")

@app.get("/health")
async def health():
    """Health check endpoint - répond immédiatement sans dépendances"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Rediriger vers index.html"""
    return FileResponse(frontend_path / "index.html")


@app.get("/health_check")
def health_check():
    return {"status": "Jarvis backend running"}
