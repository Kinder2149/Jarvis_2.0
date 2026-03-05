import uuid
from datetime import datetime
from pathlib import Path

import aiosqlite


class _ForeignKeyConnection:
    """Context manager qui ouvre une connexion aiosqlite avec PRAGMA foreign_keys = ON."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    async def __aenter__(self):
        self._conn = await aiosqlite.connect(self.db_path)
        await self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            await self._conn.close()
        return False


class Database:
    def __init__(self, db_path: str = "jarvis_data.db"):
        self.db_path = db_path
        self._initialized = False

    def _connect(self):
        """Ouvre une connexion SQLite avec foreign_keys activé."""
        return _ForeignKeyConnection(self.db_path)

    async def initialize(self):
        if self._initialized:
            return

        schema_path = Path(__file__).parent / "schema.sql"
        schema_sql = schema_path.read_text(encoding="utf-8")

        async with self._connect() as db:
            await db.executescript(schema_sql)
            await db.commit()

        self._initialized = True

    async def create_project(self, name: str, path: str, description: str | None = None) -> dict:
        project_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        async with self._connect() as db:
            await db.execute(
                "INSERT INTO projects (id, name, path, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (project_id, name, path, description, created_at),
            )
            await db.commit()

        return {
            "id": project_id,
            "name": name,
            "path": path,
            "description": description,
            "created_at": created_at,
        }

    async def get_project(self, project_id: str) -> dict | None:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    async with db.execute(
                        "SELECT COUNT(*) as count FROM conversations WHERE project_id = ?",
                        (project_id,),
                    ) as count_cursor:
                        count_row = await count_cursor.fetchone()
                        conversation_count = count_row[0] if count_row else 0

                    return {
                        "id": row["id"],
                        "name": row["name"],
                        "path": row["path"],
                        "description": row["description"],
                        "created_at": row["created_at"],
                        "conversation_count": conversation_count,
                    }
                return None

    async def list_projects(self) -> list[dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM projects ORDER BY created_at DESC") as cursor:
                rows = await cursor.fetchall()
                projects = []
                for row in rows:
                    async with db.execute(
                        "SELECT COUNT(*) as count FROM conversations WHERE project_id = ?",
                        (row["id"],),
                    ) as count_cursor:
                        count_row = await count_cursor.fetchone()
                        conversation_count = count_row[0] if count_row else 0

                    projects.append(
                        {
                            "id": row["id"],
                            "name": row["name"],
                            "path": row["path"],
                            "description": row["description"],
                            "created_at": row["created_at"],
                            "conversation_count": conversation_count,
                        }
                    )
                return projects

    async def update_project(
        self, project_id: str, name: str | None = None, description: str | None = None
    ) -> bool:
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return False

        params.append(project_id)
        sql = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"

        async with self._connect() as db:
            cursor = await db.execute(sql, params)
            await db.commit()
            return cursor.rowcount > 0

    async def delete_project(self, project_id: str) -> bool:
        async with self._connect() as db:
            cursor = await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def create_conversation(
        self, agent_id: str, project_id: str | None = None, title: str | None = None
    ) -> dict:
        conversation_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        if title is None:
            if project_id:
                title = f"Conversation {datetime.now().strftime('%d/%m %H:%M')}"
            else:
                title = f"Chat {datetime.now().strftime('%d/%m %H:%M')}"

        async with self._connect() as db:
            await db.execute(
                "INSERT INTO conversations (id, project_id, agent_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (conversation_id, project_id, agent_id, title, created_at, created_at),
            )
            await db.commit()

        return {
            "id": conversation_id,
            "project_id": project_id,
            "agent_id": agent_id,
            "title": title,
            "created_at": created_at,
            "updated_at": created_at,
            "message_count": 0,
        }

    async def get_conversation(self, conversation_id: str) -> dict | None:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    async with db.execute(
                        "SELECT COUNT(*) as count FROM messages WHERE conversation_id = ?",
                        (conversation_id,),
                    ) as count_cursor:
                        count_row = await count_cursor.fetchone()
                        message_count = count_row[0] if count_row else 0

                    return {
                        "id": row["id"],
                        "project_id": row["project_id"],
                        "agent_id": row["agent_id"],
                        "title": row["title"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "message_count": message_count,
                    }
                return None

    async def list_conversations(self, project_id: str | None = None) -> list[dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            if project_id is None:
                sql = (
                    "SELECT * FROM conversations WHERE project_id IS NULL ORDER BY updated_at DESC"
                )
                params = ()
            else:
                sql = "SELECT * FROM conversations WHERE project_id = ? ORDER BY updated_at DESC"
                params = (project_id,)

            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                conversations = []
                for row in rows:
                    async with db.execute(
                        "SELECT COUNT(*) as count FROM messages WHERE conversation_id = ?",
                        (row["id"],),
                    ) as count_cursor:
                        count_row = await count_cursor.fetchone()
                        message_count = count_row[0] if count_row else 0

                    conversations.append(
                        {
                            "id": row["id"],
                            "project_id": row["project_id"],
                            "agent_id": row["agent_id"],
                            "title": row["title"],
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                            "message_count": message_count,
                        }
                    )
                return conversations

    async def delete_conversation(self, conversation_id: str) -> bool:
        async with self._connect() as db:
            cursor = await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def update_conversation_timestamp(self, conversation_id: str):
        updated_at = datetime.now().isoformat()
        async with self._connect() as db:
            await db.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (updated_at, conversation_id),
            )
            await db.commit()

    async def update_conversation_title(self, conversation_id: str, title: str):
        async with self._connect() as db:
            await db.execute(
                "UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id)
            )
            await db.commit()

    async def add_message(self, conversation_id: str, role: str, content: str) -> dict:
        timestamp = datetime.now().isoformat()

        async with self._connect() as db:
            cursor = await db.execute(
                "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, timestamp),
            )
            await db.commit()
            message_id = cursor.lastrowid

        await self.update_conversation_timestamp(conversation_id)

        return {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
        }

    async def get_messages(self, conversation_id: str, limit: int = 100) -> list[dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC LIMIT ?",
                (conversation_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "conversation_id": row["conversation_id"],
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                    }
                    for row in rows
                ]

    async def get_conversation_history(self, conversation_id: str) -> list[dict]:
        messages = await self.get_messages(conversation_id)
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    async def create_library_document(
        self,
        category: str,
        name: str,
        description: str,
        content: str,
        tags: list[str],
        agents: list[str],
        icon: str | None = None,
    ) -> dict:
        import json

        doc_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        async with self._connect() as db:
            await db.execute(
                """INSERT INTO library_documents 
                (id, category, name, icon, description, content, tags, agents, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc_id,
                    category,
                    name,
                    icon,
                    description,
                    content,
                    json.dumps(tags),
                    json.dumps(agents),
                    created_at,
                    created_at,
                ),
            )
            await db.commit()

        return {
            "id": doc_id,
            "category": category,
            "name": name,
            "icon": icon,
            "description": description,
            "content": content,
            "tags": tags,
            "agents": agents,
            "created_at": created_at,
            "updated_at": created_at,
        }

    async def get_library_document(self, doc_id: str) -> dict | None:
        import json

        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM library_documents WHERE id = ?", (doc_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "category": row["category"],
                        "name": row["name"],
                        "icon": row["icon"],
                        "description": row["description"],
                        "content": row["content"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "agents": json.loads(row["agents"]) if row["agents"] else [],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                return None

    async def list_library_documents(
        self,
        category: str | None = None,
        agent: str | None = None,
        tag: str | None = None,
        search: str | None = None,
    ) -> list[dict]:
        import json

        query = "SELECT * FROM library_documents WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if agent:
            query += " AND agents LIKE ?"
            params.append(f'%"{agent}"%')

        if tag:
            query += " AND tags LIKE ?"
            params.append(f'%"{tag}"%')

        if search:
            query += " AND (name LIKE ? OR description LIKE ? OR content LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        query += " ORDER BY updated_at DESC"

        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "category": row["category"],
                        "name": row["name"],
                        "icon": row["icon"],
                        "description": row["description"],
                        "content": row["content"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "agents": json.loads(row["agents"]) if row["agents"] else [],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                    for row in rows
                ]

    async def update_library_document(
        self,
        doc_id: str,
        name: str | None = None,
        description: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
        agents: list[str] | None = None,
        icon: str | None = None,
    ) -> bool:
        import json

        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))
        if agents is not None:
            updates.append("agents = ?")
            params.append(json.dumps(agents))
        if icon is not None:
            updates.append("icon = ?")
            params.append(icon)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(doc_id)

        sql = f"UPDATE library_documents SET {', '.join(updates)} WHERE id = ?"

        async with self._connect() as db:
            cursor = await db.execute(sql, params)
            await db.commit()
            return cursor.rowcount > 0

    async def delete_library_document(self, doc_id: str) -> bool:
        async with self._connect() as db:
            cursor = await db.execute(
                "DELETE FROM library_documents WHERE id = ?", (doc_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def create_document_version(
        self, document_id: str, change_summary: str | None = None, created_by: str = "system"
    ) -> dict:
        """Crée une version d'un document avant modification"""
        import json

        # Récupérer le document actuel
        doc = await self.get_library_document(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        version_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        async with self._connect() as db:
            # Récupérer la version actuelle
            async with db.execute(
                "SELECT version FROM library_documents WHERE id = ?", (document_id,)
            ) as cursor:
                row = await cursor.fetchone()
                current_version = row[0] if row else 1

            # Créer l'entrée de version
            await db.execute(
                """INSERT INTO library_document_versions 
                (id, document_id, version, category, name, icon, description, content, tags, agents, created_at, created_by, change_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    version_id,
                    document_id,
                    current_version,
                    doc["category"],
                    doc["name"],
                    doc["icon"],
                    doc["description"],
                    doc["content"],
                    json.dumps(doc["tags"]),
                    json.dumps(doc["agents"]),
                    created_at,
                    created_by,
                    change_summary,
                ),
            )
            await db.commit()

        return {"id": version_id, "version": current_version, "created_at": created_at}

    async def get_document_versions(self, document_id: str) -> list[dict]:
        """Récupère l'historique des versions d'un document"""
        import json

        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM library_document_versions WHERE document_id = ? ORDER BY version DESC",
                (document_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "document_id": row["document_id"],
                        "version": row["version"],
                        "category": row["category"],
                        "name": row["name"],
                        "icon": row["icon"],
                        "description": row["description"],
                        "content": row["content"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "agents": json.loads(row["agents"]) if row["agents"] else [],
                        "created_at": row["created_at"],
                        "created_by": row["created_by"],
                        "change_summary": row["change_summary"],
                    }
                    for row in rows
                ]

    async def log_document_access(
        self, document_id: str, agent_id: str, access_type: str = "read", context: str | None = None
    ) -> None:
        """Enregistre un accès à un document"""
        log_id = str(uuid.uuid4())
        accessed_at = datetime.now().isoformat()

        async with self._connect() as db:
            # Créer le log d'accès
            await db.execute(
                """INSERT INTO library_access_logs 
                (id, document_id, agent_id, accessed_at, access_type, context)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (log_id, document_id, agent_id, accessed_at, access_type, context),
            )

            # Mettre à jour ou créer les métriques
            async with db.execute(
                "SELECT id, access_count FROM library_document_metrics WHERE document_id = ? AND agent_id = ?",
                (document_id, agent_id),
            ) as cursor:
                row = await cursor.fetchone()

            if row:
                # Incrémenter le compteur existant
                await db.execute(
                    """UPDATE library_document_metrics 
                    SET access_count = access_count + 1, last_accessed_at = ?, updated_at = ?
                    WHERE document_id = ? AND agent_id = ?""",
                    (accessed_at, accessed_at, document_id, agent_id),
                )
            else:
                # Créer nouvelle métrique
                metric_id = str(uuid.uuid4())
                await db.execute(
                    """INSERT INTO library_document_metrics 
                    (id, document_id, agent_id, access_count, last_accessed_at, created_at, updated_at)
                    VALUES (?, ?, ?, 1, ?, ?, ?)""",
                    (metric_id, document_id, agent_id, accessed_at, accessed_at, accessed_at),
                )

            await db.commit()

    async def get_document_metrics(self, document_id: str) -> list[dict]:
        """Récupère les métriques d'utilisation d'un document"""
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM library_document_metrics WHERE document_id = ? ORDER BY access_count DESC",
                (document_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "document_id": row["document_id"],
                        "agent_id": row["agent_id"],
                        "access_count": row["access_count"],
                        "last_accessed_at": row["last_accessed_at"],
                        "total_read_time_seconds": row["total_read_time_seconds"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                    for row in rows
                ]

    async def get_top_documents(self, limit: int = 10) -> list[dict]:
        """Récupère les documents les plus consultés"""
        import json

        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT ld.*, SUM(ldm.access_count) as total_accesses
                FROM library_documents ld
                LEFT JOIN library_document_metrics ldm ON ld.id = ldm.document_id
                GROUP BY ld.id
                ORDER BY total_accesses DESC
                LIMIT ?""",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "category": row["category"],
                        "name": row["name"],
                        "icon": row["icon"],
                        "description": row["description"],
                        "content": row["content"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "agents": json.loads(row["agents"]) if row["agents"] else [],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "total_accesses": row["total_accesses"] or 0,
                    }
                    for row in rows
                ]

    async def seed_library_if_empty(self):
        """
        Peuple la Library si elle est vide (premier démarrage).
        Lit les documents depuis library_seed.json et les insère dans la BDD.
        """
        import json
        import logging
        from pathlib import Path

        logger = logging.getLogger(__name__)

        async with self._connect() as db:
            async with db.execute("SELECT COUNT(*) FROM library_documents") as cursor:
                row = await cursor.fetchone()
                count = row[0] if row else 0

            if count > 0:
                logger.debug(f"Library déjà peuplée ({count} documents)")
                return

            seed_file = Path(__file__).parent / "library_seed.json"

            if not seed_file.exists():
                logger.warning("library_seed.json introuvable, skip seed")
                return

            with open(seed_file, "r", encoding="utf-8") as f:
                library_items = json.load(f)

            for item in library_items:
                await self.create_library_document(
                    category=item["category"],
                    name=item["name"],
                    icon=item.get("icon", ""),
                    description=item["description"],
                    content=item["content"],
                    tags=item.get("tags", []),
                    agents=item.get("agents", []),
                )

            logger.info(f"✅ Library initialisée avec {len(library_items)} documents")


db_instance = Database()
