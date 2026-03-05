"""Module de migrations pour JARVIS 2.0.

Contient les fonctions de migration pour la base de données.
"""

import os

from backend.db.database import Database


async def migrate_sessions_to_conversations(sessions_dict: dict):
    """
    Migre les sessions in-memory existantes vers des conversations persistantes.
    À exécuter une seule fois lors du déploiement.

    Args:
        sessions_dict: Le dictionnaire SESSIONS de api.py
    """
    if not sessions_dict:
        return

    db = Database()
    await db.initialize()

    legacy_project = await db.create_project(
        name="Conversations Historiques",
        path=os.getcwd(),
        description="Projet créé automatiquement pour migrer les anciennes sessions",
    )

    for session_id, session_data in sessions_dict.items():
        conversation = await db.create_conversation(
            project_id=legacy_project["id"],
            agent_id=session_data.get("agent_id", "BASE"),
            title=f"Session {session_id[:8]}",
        )

        for msg in session_data.get("history", []):
            await db.add_message(
                conversation_id=conversation["id"], role=msg["role"], content=msg["content"]
            )

    sessions_dict.clear()


# NOTE: migrate_library_data() a été supprimée (doublon avec library_seed.json)
# Les données de la librairie sont maintenant gérées via :
# - backend/db/library_seed.json : source de vérité pour les données initiales
# - backend/db/database.py::seed_library_if_empty() : chargement automatique au démarrage
