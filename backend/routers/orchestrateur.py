from fastapi import APIRouter
from pathlib import Path
import json
import logging

from backend.database import get_connection

logger = logging.getLogger("jarvis")
router = APIRouter(prefix="/orchestrateur", tags=["orchestrateur"])

_REGISTRY_PATH = Path(__file__).parent.parent / "data" / "agents_registry.json"


@router.get("/agents")
def get_agents():
    """Retourne le registre des agents depuis la DB (source de vérité) + fichier JSON de référence."""
    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT name, display_name, description, routing_hints, page_url, color, is_active
            FROM agent_registry
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()
        agents = []
        for r in rows:
            agents.append({
                "id": r["name"].lower(),
                "nom": r["name"],
                "display_name": r["display_name"],
                "role": r["name"],
                "description": r["description"],
                "declencheurs": json.loads(r["routing_hints"]),
                "page_url": r["page_url"],
                "color": r["color"],
                "is_active": bool(r["is_active"]),
            })
        return {"agents": agents, "count": len(agents)}
    finally:
        db.close()
