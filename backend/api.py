import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from backend.agents.agent_config import list_agents_detailed, list_available_agents
from backend.agents.agent_factory import get_agent
from backend.agents.base_agent import InvalidRuntimeMessageError
from backend.db.database import db_instance
from backend.models import (
    ChatMessage,
    Conversation,
    ConversationCreate,
    DirectoryListing,
    FileContent,
    FileInfo,
    LibraryDocument,
    LibraryDocumentCreate,
    LibraryDocumentUpdate,
    Message,
    Mission,
    MissionStatus,
    MissionPhase,
    Project,
    ProjectCreate,
    ProjectUpdate,
)
from backend.models.mission_api import (
    MissionStartRequest,
    MissionStartResponse,
    MissionValidateRequest,
    MissionValidateResponse,
    MissionContinueResponse,
    MissionStatusResponse,
)
from backend.models.session_state import ProjectState, SessionState
from backend.services import (
    FileService,
    FunctionExecutor,
    SimpleOrchestrator,
    build_chat_simple_context,
    file_tree_cache,
)
from backend.services.project_service import ProjectService
from backend.services.mission_manager import MissionManager

logger = logging.getLogger(__name__)
mission_manager = MissionManager()
orchestrator = SimpleOrchestrator()
# Partager la même instance de MissionManager
orchestrator.mission_manager = mission_manager
from backend.services.file_service import (
    EncodingError,
    FileServiceError,
    FileTooLargeError,
    PathTraversalError,
    PermissionDeniedError,
    UnsupportedFileTypeError,
)

router = APIRouter()


@router.post("/api/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    try:
        project_path = Path(project.path).resolve()
        if not project_path.exists():
            raise HTTPException(status_code=400, detail="Project path does not exist")
        if not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Project path is not a directory")

        result = await db_instance.create_project(
            name=project.name, path=str(project_path), description=project.description
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects", response_model=list[Project])
async def list_projects():
    try:
        projects = await db_instance.list_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    try:
        project = await db_instance.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, update: ProjectUpdate):
    try:
        success = await db_instance.update_project(
            project_id=project_id, name=update.name, description=update.description
        )
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")

        project = await db_instance.get_project(project_id)
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    try:
        success = await db_instance.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")

        file_tree_cache.invalidate(project_id)
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/conversations", response_model=Conversation)
async def create_standalone_conversation(conv: ConversationCreate):
    """
    Crée une conversation standalone (chat simple, sans projet).
    """
    try:
        conversation = await db_instance.create_conversation(
            agent_id=conv.agent_id, project_id=None, title=conv.title
        )
        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/conversations", response_model=list[Conversation])
async def list_standalone_conversations():
    """
    Liste toutes les conversations standalone (sans projet).
    """
    try:
        conversations = await db_instance.list_conversations(project_id=None)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/projects/{project_id}/conversations", response_model=Conversation)
async def create_conversation(project_id: str, conv: ConversationCreate):
    try:
        project = await db_instance.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        conversation = await db_instance.create_conversation(
            agent_id=conv.agent_id, project_id=project_id, title=conv.title
        )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects/{project_id}/conversations", response_model=list[Conversation])
async def list_conversations(project_id: str):
    try:
        conversations = await db_instance.list_conversations(project_id)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    try:
        conversation = await db_instance.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    try:
        success = await db_instance.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/conversations/{conversation_id}/messages", response_model=list[Message])
async def get_messages(conversation_id: str, limit: int = 100):
    try:
        messages = await db_instance.get_messages(conversation_id, limit)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, msg: ChatMessage):
    try:
        conversation = await db_instance.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Créer SessionState depuis conversation
        session_state = SessionState.from_conversation(conversation)

        messages = await db_instance.get_conversation_history(conversation_id)

        # Injecter contexte selon le mode (projet ou chat simple) au 1er message
        context_injected = False
        original_content = msg.content

        if len(messages) == 0:
            if conversation["project_id"]:
                project = await db_instance.get_project(conversation["project_id"])
                # Si projet supprimé, utiliser contexte minimal
                if not project:
                    logger.warning(f"Project {conversation['project_id']} not found, using minimal context")
                    msg.content = f"MODE PROJET: Méthodologie obligatoire\nÉTAT: Projet non trouvé\n\n---\n\n{msg.content}"
                    context_injected = True
                else:
                    file_tree = file_tree_cache.get(project["id"])
                    if not file_tree:
                        try:
                            file_tree = FileService.get_file_tree(project["path"], max_depth=2)
                            file_tree_cache.set(project["id"], file_tree)
                        except Exception:
                            file_tree = {"name": "project", "type": "directory", "items": []}

                    # Analyser état projet et dette technique
                    project_state = ProjectService.analyze_project_state(project["path"])
                    session_state.set_project_state(project_state)

                    debt_report = None
                    if project_state == ProjectState.DEBT:
                        debt_report = ProjectService.analyze_debt(project["path"])

                    # Contexte enrichi avec état projet et dette
                    context_content = ProjectService.build_enriched_context(
                        project, file_tree, project_state, debt_report
                    )
                    msg.content = f"{context_content}\n\n---\n\n{msg.content}"
                    context_injected = True
            else:
                # Mode chat simple — contexte léger
                context_content = build_chat_simple_context()
                msg.content = f"{context_content}\n\n---\n\n{msg.content}"
                context_injected = True

        # Créer une copie pour l'API avec contexte (si 1er message)
        messages_for_api = messages.copy()
        messages_for_api.append({"role": "user", "content": msg.content})

        # Sauvegarder en DB SANS le contexte pour éviter croissance historique
        await db_instance.add_message(conversation_id, "user", original_content)

        # Créer FunctionExecutor avec contexte projet si disponible
        # IMPORTANT : Ne PAS passer function_executor à JARVIS_Maître en mode projet
        # pour éviter boucle infinie function calls (get_project_structure, etc.)
        # JARVIS_Maître doit uniquement générer le marqueur [DEMANDE_CODE_CODEUR:]
        function_executor = None
        if conversation["project_id"]:
            project = await db_instance.get_project(conversation["project_id"])
            # Créer function_executor uniquement si agent != JARVIS_Maître
            if conversation["agent_id"] != "JARVIS_Maître":
                function_executor = FunctionExecutor(
                    db_instance=db_instance, project_path=project["path"] if project else None
                )
        else:
            # Chat simple : KB seulement (pas de project_path)
            # JARVIS_Maître en chat simple peut avoir accès à la KB
            function_executor = FunctionExecutor(db_instance=db_instance)

        agent = get_agent(conversation["agent_id"])

        try:
            # Utiliser messages_for_api (avec contexte au 1er message) au lieu de messages
            response = await agent.handle(
                messages_for_api, session_id=conversation_id, function_executor=function_executor
            )

            # Validation : JARVIS_Maître ne doit PAS générer de code directement
            if conversation["agent_id"] == "JARVIS_Maître" and conversation["project_id"]:
                # Détecter blocs de code dans la réponse
                import re
                code_blocks = re.findall(r'```(?:python|javascript|typescript|java|dart|go|rust|cpp|c\+\+)', response, re.IGNORECASE)
                has_delegation_marker = '[DEMANDE_CODE_CODEUR:' in response
                
                if code_blocks and not has_delegation_marker:
                    logger.warning(f"❌ JARVIS_Maître a généré du code directement sans délégation (conversation {conversation_id})")
                    logger.warning(f"Blocs code détectés: {len(code_blocks)}")
                    
                    # Rejeter la réponse et demander reformulation
                    error_response = """❌ **ERREUR DE DÉLÉGATION**

Je ne peux pas générer de code directement. Je dois déléguer au CODEUR.

Format attendu :
```
[DEMANDE_CODE_CODEUR: Crée les fichiers suivants pour [projet] :
- fichier1.py : [description]
- fichier2.py : [description]
Utilise [framework], [dépendances]]
```

Merci de reformuler ta demande."""
                    
                    await db_instance.add_message(conversation_id, "assistant", error_response)
                    
                    return {
                        "response": error_response,
                        "conversation_id": conversation_id,
                        "agent_id": conversation["agent_id"],
                        "delegations": [],
                        "error": "code_without_delegation"
                    }

            # Orchestration : uniquement en mode projet avec Jarvis_maitre
            delegation_results = []
            if conversation["project_id"] and conversation["agent_id"] == "JARVIS_Maître":
                project = await db_instance.get_project(conversation["project_id"])
                project_path = project["path"] if project else None
                # Passer messages_for_api pour l'orchestration (avec contexte si nécessaire)
                response, delegation_results = await orchestrator.process_response(
                    response=response,
                    conversation_history=messages_for_api,
                    session_id=conversation_id,
                    project_path=project_path,
                    function_executor=function_executor,
                    session_state=session_state,
                )
                if delegation_results:
                    logger.info(
                        "Orchestration terminée: %d délégation(s) pour conversation %s",
                        len(delegation_results),
                        conversation_id,
                    )

            await db_instance.add_message(conversation_id, "assistant", response)

        except Exception as e:
            logger.exception(
                f"Error in agent handling or orchestration for conversation {conversation_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {type(e).__name__} - {str(e)}"
            )

        return {
            "response": response,
            "conversation_id": conversation_id,
            "agent_id": conversation["agent_id"],
            "delegations": [
                {
                    "agent": r["agent_name"],
                    "success": r["success"],
                    "passes_used": r.get("passes_used", 0),
                    "stagnation": r.get("stagnation", False),
                    "files_written": [
                        f["path"]
                        for f in r.get("files_written", [])
                        if f.get("status") == "written"
                    ],
                }
                for r in delegation_results
            ]
            if delegation_results
            else None,
        }
    except InvalidRuntimeMessageError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur confirmation action pour conversation {conversation_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/conversations/{conversation_id}/confirm-action")
async def confirm_action(conversation_id: str):
    """
    Confirme une action NON-SAFE bloquée et relance l'exécution.
    """
    try:
        # Vérifier si action bloquée existe
        pending = SimpleOrchestrator._pending_actions.get(conversation_id)
        if not pending:
            raise HTTPException(status_code=404, detail="Aucune action en attente de confirmation")

        # Marquer comme confirmé
        SimpleOrchestrator._pending_actions[conversation_id]["confirmed"] = True

        logger.info("API: confirmation action NON-SAFE pour conversation %s", conversation_id)

        # Relancer orchestration avec bypass_safety=True
        original_response = pending["original_response"]
        conversation_history = pending["conversation_history"]
        project_path = pending["project_path"]
        function_executor = pending["function_executor"]
        session_state = pending["session_state"]

        # Relancer process_response avec réponse originale (bypass activé via flag confirmed=True)
        final_response, delegation_results = await orchestrator.process_response(
            response=original_response,
            conversation_history=conversation_history,
            session_id=conversation_id,
            project_path=project_path,
            function_executor=function_executor,
            session_state=session_state,
        )

        # Sauvegarder réponse en DB (vérifier conversation existe)
        conversation = await db_instance.get_conversation(conversation_id)
        if conversation:
            await db_instance.add_message(conversation_id, "assistant", final_response)
        else:
            logger.error(f"Conversation {conversation_id} not found, cannot add message")

        return {
            "message": final_response,
            "delegations": [
                {
                    "agent": r["agent_name"],
                    "success": r["success"],
                    "files_written": [
                        f["path"]
                        for f in r.get("files_written", [])
                        if f.get("status") == "written"
                    ],
                }
                for r in delegation_results
            ]
            if delegation_results
            else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur confirmation action pour conversation {conversation_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects/{project_id}/files/tree")
async def get_file_tree(project_id: str, max_depth: int = 3):
    try:
        project = await db_instance.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        tree = FileService.get_file_tree(project["path"], max_depth)
        return tree
    except FileServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects/{project_id}/files/list", response_model=DirectoryListing)
async def list_files(project_id: str, path: str = ""):
    try:
        project = await db_instance.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        listing = FileService.list_directory(project["path"], path)
        return listing
    except PathTraversalError:
        raise HTTPException(status_code=403, detail="Access denied: path outside project")
    except FileServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects/{project_id}/files/read", response_model=FileContent)
async def read_file(project_id: str, path: str):
    try:
        project = await db_instance.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        content = FileService.read_file(project["path"], path)
        return content
    except PathTraversalError:
        raise HTTPException(status_code=403, detail="Access denied: path outside project")
    except FileServiceError:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    except FileTooLargeError:
        raise HTTPException(status_code=413, detail="File too large (max 1MB)")
    except UnsupportedFileTypeError:
        raise HTTPException(status_code=415, detail="Unsupported file type")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="Permission denied by OS")
    except EncodingError:
        raise HTTPException(status_code=422, detail="Cannot decode file (binary?)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects/{project_id}/files/search", response_model=list[FileInfo])
async def search_files(project_id: str, pattern: str, max_results: int = 50):
    try:
        project = await db_instance.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        results = FileService.search_files(project["path"], pattern, max_results)
        return results
    except FileServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
def get_agents():
    """
    Liste tous les agents disponibles avec leurs métadonnées.
    """
    try:
        return {"agents": list_available_agents()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/detailed")
def get_agents_detailed():
    """
    Liste tous les agents avec toutes leurs couches de configuration.
    Inclut : config locale, permissions, type, paramètres, prompt cloud.
    """
    try:
        return {"agents": list_agents_detailed()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/library", response_model=list[LibraryDocument])
async def list_library_documents(
    category: str = None, agent: str = None, tag: str = None, search: str = None
):
    """
    Liste tous les documents de la Knowledge Base avec filtres optionnels.
    """
    try:
        documents = await db_instance.list_library_documents(
            category=category, agent=agent, tag=tag, search=search
        )
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/library/{doc_id}", response_model=LibraryDocument)
async def get_library_document(doc_id: str):
    """
    Récupère un document spécifique de la Knowledge Base par son ID.
    """
    try:
        document = await db_instance.get_library_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/library", response_model=LibraryDocument)
async def create_library_document(doc: LibraryDocumentCreate):
    """
    Crée un nouveau document dans la Knowledge Base.
    """
    try:
        document = await db_instance.create_library_document(
            category=doc.category,
            name=doc.name,
            description=doc.description,
            content=doc.content,
            tags=doc.tags,
            agents=doc.agents,
            icon=doc.icon,
        )
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/library/{doc_id}", response_model=LibraryDocument)
async def update_library_document(doc_id: str, update: LibraryDocumentUpdate):
    """
    Met à jour un document existant de la Knowledge Base.
    """
    try:
        success = await db_instance.update_library_document(
            doc_id=doc_id,
            name=update.name,
            description=update.description,
            content=update.content,
            tags=update.tags,
            agents=update.agents,
            icon=update.icon,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        document = await db_instance.get_library_document(doc_id)
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/library/{doc_id}")
async def delete_library_document(doc_id: str):
    """
    Supprime un document de la Knowledge Base.
    """
    try:
        success = await db_instance.delete_library_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS MISSIONS (Workflow 5 Agents)
# ============================================

@router.post("/api/missions/start", response_model=MissionStartResponse)
async def start_mission(request: MissionStartRequest):
    """
    Démarre une nouvelle mission avec workflow unique.
    
    Workflow : ARCHITECTE → validation USER → CODEUR → TESTEUR → VALIDATEUR
    """
    try:
        result = await orchestrator.start_mission(
            user_request=request.user_request,
            project_name=request.project_name,
            project_path=request.project_path
        )
        
        return MissionStartResponse(**result)
    
    except Exception as e:
        logger.error(f"Erreur start_mission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/missions/{mission_id}", response_model=MissionStatusResponse)
async def get_mission_status(mission_id: str):
    """
    Récupère le statut d'une mission.
    """
    try:
        mission = mission_manager.get_mission(mission_id)
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return MissionStatusResponse(
            mission_id=mission.mission_id,
            user_request=mission.user_request,
            project_path=mission.project_path,
            status=mission.status.value,
            current_phase=mission.current_phase.value if mission.current_phase else None,
            architecture_validated=mission.architecture_validated,
            code_validated=mission.code_validated,
            tests_validated=mission.tests_validated,
            files_created=mission.files_created,
            files_modified=mission.files_modified,
            error_count=mission.error_count,
            last_error=mission.last_error,
            created_at=mission.created_at.isoformat(),
            completed_at=mission.completed_at.isoformat() if mission.completed_at else None,
            pending_validation=mission.pending_validation
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get_mission_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/missions/{mission_id}/validate", response_model=MissionValidateResponse)
async def validate_architecture(mission_id: str, request: MissionValidateRequest):
    """
    Valide ou rejette l'architecture proposée par ARCHITECTE.
    
    Si validé (approved=True) : Continue workflow avec CODEUR
    Si rejeté (approved=False) : Relance ARCHITECTE avec feedback
    """
    try:
        mission = mission_manager.get_mission(mission_id)
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.status != MissionStatus.VALIDATING:
            raise HTTPException(
                status_code=400,
                detail=f"Mission not awaiting validation (status: {mission.status.value})"
            )
        
        if request.approved:
            # Approuver validation
            mission.approve_validation()
            mission_manager.update_mission(mission)
            
            logger.info(f"Mission {mission_id}: Architecture validée par USER")
            
            return MissionValidateResponse(
                success=True,
                message="Architecture validée. Workflow continue avec CODEUR.",
                mission_status=mission.status.value
            )
        else:
            # Rejeter validation
            mission.reject_validation()
            mission_manager.update_mission(mission)
            
            logger.info(f"Mission {mission_id}: Architecture rejetée par USER")
            
            # TODO: Relancer ARCHITECTE avec feedback
            
            return MissionValidateResponse(
                success=True,
                message="Architecture rejetée. ARCHITECTE va proposer une nouvelle version.",
                mission_status=mission.status.value
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur validate_architecture: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/missions/{mission_id}/continue", response_model=MissionContinueResponse)
async def continue_mission(mission_id: str):
    """
    Continue une mission après validation architecture.
    
    Lance : CODEUR → TESTEUR → VALIDATEUR
    """
    try:
        result = await orchestrator.continue_complete_mode(mission_id)
        
        return MissionContinueResponse(**result)
    
    except Exception as e:
        logger.error(f"Erreur continue_mission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/missions", response_model=list[MissionStatusResponse])
async def list_missions(
    status: Optional[str] = None,
    project_path: Optional[str] = None
):
    """
    Liste toutes les missions avec filtres optionnels.
    """
    try:
        # Convertir status string → MissionStatus enum
        status_enum = None
        if status:
            try:
                status_enum = MissionStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        missions = mission_manager.list_missions(
            status=status_enum,
            project_path=project_path
        )
        
        return [
            MissionStatusResponse(
                mission_id=m.mission_id,
                user_request=m.user_request,
                project_path=m.project_path,
                status=m.status.value,
                current_phase=m.current_phase.value if m.current_phase else None,
                architecture_validated=m.architecture_validated,
                code_validated=m.code_validated,
                tests_validated=m.tests_validated,
                files_created=m.files_created,
                files_modified=m.files_modified,
                error_count=m.error_count,
                last_error=m.last_error,
                created_at=m.created_at.isoformat(),
                completed_at=m.completed_at.isoformat() if m.completed_at else None
            )
            for m in missions
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur list_missions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
