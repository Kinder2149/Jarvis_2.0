"""
Application FastAPI simplifiée - JARVIS 2.0
Chat simple multi-agents sans base de données
"""

import logging
from pathlib import Path

from dotenv import load_dotenv

# Charger .env AVANT tous les autres imports
load_dotenv(override=True)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.chat.api import router, initialiser_stockage_conversations
from backend.chat.stockage import StockageConversations
from backend.logging_config import setup_logging
from backend.providers.provider_factory import ProviderFactory

# Configuration du logging
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


# Initialisation du stockage de conversations
stockage_conversations = StockageConversations()
initialiser_stockage_conversations(stockage_conversations)
logger.info("StockageConversations initialisé")

# Vider le cache des providers pour forcer rechargement avec nouveau .env
ProviderFactory.clear_cache()
logger.info("Provider cache cleared - configuration rechargée depuis .env")

# Vider le cache des agents pour forcer rechargement des prompts
from backend.agents.agent_factory import clear_cache
clear_cache()
logger.info("Agent cache cleared - prompts système rechargés depuis fichiers .md")


app = FastAPI(
    title="JARVIS 2.0 - Chat Simple",
    description="Application de chat simple multi-agents",
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


@app.get("/")
async def root():
    """Servir index.html à la racine"""
    return FileResponse(frontend_path / "index.html")


@app.get("/index.html")
async def serve_index():
    """Servir index.html"""
    return FileResponse(frontend_path / "index.html")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "JARVIS 2.0 - Chat Simple"}
