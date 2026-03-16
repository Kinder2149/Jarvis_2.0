"""
Orchestration Workflow 5 Agents - JARVIS 2.0
Gestion workflow unique : ARCHITECTE → Validation USER → CODEUR → TESTEUR → VALIDATEUR
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
from backend.models.mission import Mission, MissionStatus, MissionPhase
from backend.models.mission_context import MissionContext, ArchitectureDecision
from backend.services.mission_manager import MissionManager
from backend.services.project_manager import ProjectManager
from backend.services.version_manager import VersionManager
from backend.services.rag_auto_indexer import RAGAutoIndexer
from backend.services.code_parser import CodeParser
from backend.services.rag_client import RAGClient
from backend.services.architecture_parser import ArchitectureParser
from backend.services.validation_parser import ValidationParser

logger = logging.getLogger(__name__)


class SimpleOrchestrator:
    """
    Orchestrateur workflow unique 5 agents
    
    Workflow UNIQUE (toutes les missions) :
    - JARVIS_Maître → ARCHITECTE → (validation USER) → CODEUR → TESTEUR → VALIDATEUR
    """
    
    # Stockage temporaire actions bloquées (conversation_id -> action_data)
    _pending_actions = {}
    
    def __init__(self):
        self.mission_manager = MissionManager()
        self.project_manager = ProjectManager()
        self.version_manager = VersionManager()
        self.rag_indexer = RAGAutoIndexer()
        self.rag_client = RAGClient()
        self.architecture_parser = ArchitectureParser()
        self.validation_parser = ValidationParser()
    
    
    def detect_project_type(self, user_request: str) -> str:
        """
        Détecte type de projet depuis demande utilisateur.
        
        Args:
            user_request: Demande utilisateur
        
        Returns:
            Type projet : "calculatrice" | "todo" | "api_rest" | "crud" | "cli" | "general"
        """
        request_lower = user_request.lower()
        
        # Ordre prioritaire (du plus spécifique au plus général)
        if any(kw in request_lower for kw in ["calculatrice", "calcul", "opération", "arithmétique", "calculator"]):
            logger.info("Type projet: calculatrice")
            return "calculatrice"
        
        elif any(kw in request_lower for kw in ["api rest", "api", "fastapi", "endpoint", "route", "rest api"]):
            logger.info("Type projet: api_rest")
            return "api_rest"
        
        elif any(kw in request_lower for kw in ["todo", "task", "tâche", "todolist", "todo list"]):
            logger.info("Type projet: todo")
            return "todo"
        
        elif any(kw in request_lower for kw in ["crud", "create read update delete", "gestion", "manager"]):
            logger.info("Type projet: crud")
            return "crud"
        
        elif any(kw in request_lower for kw in ["cli", "ligne de commande", "terminal", "argparse", "command line"]):
            logger.info("Type projet: cli")
            return "cli"
        
        else:
            logger.info("Type projet: general")
            return "general"
    
    def build_rag_query(self, project_type: str, user_request: str) -> str:
        """
        Construit query RAG optimale selon type projet.
        
        Args:
            project_type: Type projet (detect_project_type)
            user_request: Demande utilisateur
        
        Returns:
            Query RAG optimisée
        """
        # Mapping type → query template
        query_templates = {
            "calculatrice": "pattern Python fonctions calcul arithmétique validation types",
            "todo": "pattern CRUD Python Pydantic storage JSON persistence",
            "api_rest": "pattern API REST FastAPI endpoints CRUD validation",
            "crud": "pattern CRUD Python Pydantic storage models manager",
            "cli": "pattern CLI Python argparse commandes",
            "general": "pattern Python best practices structure"
        }
        
        template = query_templates.get(project_type, query_templates["general"])
        
        logger.info(f"Query RAG: {template}")
        return template
    
    
    async def execute_complete_mode(
        self,
        mission: Mission,
        user_request: str,
        project_path: str
    ) -> Dict:
        """
        Exécute workflow COMPLET (avec ARCHITECTE)
        
        Workflow :
        1. JARVIS_Maître → Analyse besoin
        2. ARCHITECTE → Propose architecture
        3. Attente validation USER
        4. CODEUR → Génère code
        5. TESTEUR → Génère tests
        6. VALIDATEUR → Valide
        
        Args:
            mission: Mission en cours
            user_request: Demande utilisateur
            project_path: Chemin projet
        
        Returns:
            Dict avec success, architecture_doc, files_created, validation_result
        """
        from backend.agents.agent_factory import get_agent
        
        print(f"🚀 [EXECUTE_COMPLETE_MODE] Démarré pour mission {mission.mission_id}")
        logger.info(f"Orchestration: Workflow unique pour mission {mission.mission_id}")
        
        mission.current_phase = MissionPhase.ARCHITECTURE
        mission.status = MissionStatus.IN_PROGRESS
        self.mission_manager.update_mission(mission)
        
        files_created = []
        validation_result = "PENDING"
        correction_attempts = 0
        max_corrections = 2
        architecture_doc = None
        
        try:
            # 1. ARCHITECTE : Propose architecture
            print(f"📞 [EXECUTE_COMPLETE_MODE] Appel ARCHITECTE...")
            logger.info(f"Mission {mission.mission_id}: Appel ARCHITECTE")
            architecte = get_agent("ARCHITECTE")
            print(f"✅ [EXECUTE_COMPLETE_MODE] ARCHITECTE récupéré : {architecte.name}")
            
            architecte_messages = [
                {"role": "system", "content": architecte.system_prompt or "Tu es ARCHITECTE, agent conception architecture."},
                {"role": "user", "content": f"Projet: {project_path}\n\nDemande: {user_request}\n\nConçois l'architecture AVANT le code. Propose structure fichiers, justifie choix, explique en langage simple."}
            ]
            
            print(f"📤 [EXECUTE_COMPLETE_MODE] Envoi messages à ARCHITECTE ({len(architecte_messages)} messages)...")
            logger.info(f"Mission {mission.mission_id}: Envoi {len(architecte_messages)} messages à ARCHITECTE")
            
            # IMPORTANT : ARCHITECTE ne doit PAS avoir function_executor (pas de tools)
            architecture_response = await architecte.handle(architecte_messages, session_id=mission.mission_id, function_executor=None)
            
            print(f"✅ [EXECUTE_COMPLETE_MODE] ARCHITECTE réponse reçue ({len(architecture_response)} chars)")
            print(f"📄 [EXECUTE_COMPLETE_MODE] Architecture (premiers 500 chars):\n{architecture_response[:500]}...")
            architecture_doc = architecture_response
            logger.info(f"Mission {mission.mission_id}: ARCHITECTE réponse ({len(architecture_response)} chars)")
            logger.info(f"Mission {mission.mission_id}: Architecture preview: {architecture_response[:500]}...")
            
            # 2. Demander validation USER
            logger.info(f"Mission {mission.mission_id}: Demande validation architecture USER")
            mission.current_phase = MissionPhase.VALIDATION_ARCHI
            mission.status = MissionStatus.VALIDATING
            mission.request_validation("architecture", {"architecture": architecture_response})
            self.mission_manager.update_mission(mission)
            
            # Note: Le workflow s'arrête ici en attendant validation USER
            # L'API devra appeler continue_complete_mode() après validation
            
            return {
                "success": True,
                "mode": "COMPLETE",
                "architecture_doc": architecture_doc,
                "files_created": [],
                "validation_result": "AWAITING_USER_VALIDATION",
                "requires_user_validation": True,
                "mission_id": mission.mission_id,
                "user_message": f"""
✅ **Architecture proposée par l'ARCHITECTE**

{architecture_doc}

---

⏸️ **Le workflow est en pause**

Consultez le bloc "Workflow" à gauche pour valider l'architecture.
Cliquez sur "✅ Valider l'architecture" pour continuer le workflow.
"""
            }
            
        except Exception as e:
            logger.error(f"Mission {mission.mission_id}: Erreur workflow (phase architecture): {e}")
            mission.mark_failed(str(e))
            self.mission_manager.update_mission(mission)
            
            return {
                "success": False,
                "mode": "COMPLETE",
                "error": str(e),
                "architecture_doc": None,
                "files_created": [],
                "validation_result": "ERROR"
            }
    
    async def continue_complete_mode(
        self,
        mission_id: str
    ) -> Dict:
        """
        Continue workflow COMPLET après validation USER de l'architecture
        
        Workflow :
        1. CODEUR → Génère code selon architecture
        2. TESTEUR → Génère tests
        3. VALIDATEUR → Valide code + tests + architecture
        
        Args:
            mission_id: ID mission à continuer
        
        Returns:
            Dict avec success, files_created, validation_result
        """
        from backend.agents.agent_factory import get_agent
        
        mission = self.mission_manager.get_mission(mission_id)
        
        if not mission:
            return {"success": False, "error": "Mission not found"}
        
        if not mission.architecture_validated:
            return {"success": False, "error": "Architecture not validated"}
        
        logger.info(f"Mission {mission_id}: Continuation workflow après validation architecture")
        
        mission.current_phase = MissionPhase.GENERATION_CODE
        mission.status = MissionStatus.IN_PROGRESS
        self.mission_manager.update_mission(mission)
        
        files_created = []
        validation_result = "PENDING"
        correction_attempts = 0
        max_corrections = 2
        
        # Récupérer architecture depuis pending_validation
        architecture_doc = mission.pending_validation.get("data", {}).get("architecture", "") if mission.pending_validation else ""
        
        try:
            # 1. Enrichir contexte avec RAG
            logger.info(f"Mission {mission_id}: Enrichissement contexte RAG")
            
            # Détecter type projet
            project_type = self.detect_project_type(mission.user_request)
            print(f"🔍 [RAG] Type projet détecté: {project_type}")
            logger.info(f"Mission {mission_id}: Type projet détecté = {project_type}")
            
            # Construire query RAG
            rag_query = self.build_rag_query(project_type, mission.user_request)
            print(f"🔍 [RAG] Query construite: {rag_query}")
            logger.info(f"Mission {mission_id}: RAG query = {rag_query}")
            
            # Enrichir contexte avec RAG
            rag_context = await self.rag_client.search(
                query=rag_query,
                top_k=3
            )
            print(f"📚 [RAG] Context reçu ({len(rag_context)} chars):")
            print(f"{rag_context[:500]}...")
            print(f"{'='*80}")
            logger.info(f"Mission {mission_id}: RAG context complet: {rag_context}")
            
            # 2. CODEUR : Génère code selon architecture + RAG
            print(f"📞 [CONTINUE_COMPLETE_MODE] Appel CODEUR...")
            logger.info(f"Mission {mission_id}: Appel CODEUR avec architecture + RAG")
            codeur = get_agent("CODEUR")
            print(f"✅ [CONTINUE_COMPLETE_MODE] CODEUR récupéré : {codeur.name}")
            
            # Construire message avec DEMANDE UTILISATEUR en priorité
            if rag_context:
                user_message = f"""=== DEMANDE UTILISATEUR (PRIORITÉ ABSOLUE) ===
{mission.user_request}

---

=== ARCHITECTURE VALIDÉE ===
{architecture_doc}

---

=== CONTEXTE RAG (patterns de référence) ===
{rag_context}

---

INSTRUCTIONS :
Génère le code pour répondre à la DEMANDE UTILISATEUR ci-dessus.
Respecte EXACTEMENT l'architecture validée.
Utilise les patterns RAG comme référence pour la qualité du code UNIQUEMENT.

⚠️ IMPORTANT : Génère le code pour la DEMANDE UTILISATEUR, PAS pour les exemples du contexte RAG.

FORMAT DE RÉPONSE OBLIGATOIRE :
Pour CHAQUE fichier, utilise ce format EXACT :

# chemin/vers/fichier.ext

```langage
code complet
```

RÈGLE CRITIQUE : Il DOIT y avoir une ligne vide entre le chemin et le bloc de code."""
            else:
                user_message = f"""=== DEMANDE UTILISATEUR ===
{mission.user_request}

---

=== ARCHITECTURE VALIDÉE ===
{architecture_doc}

---

INSTRUCTIONS :
Génère le code pour répondre à la DEMANDE UTILISATEUR ci-dessus.
Respecte EXACTEMENT l'architecture validée.

FORMAT DE RÉPONSE OBLIGATOIRE :
Pour CHAQUE fichier, utilise ce format EXACT :

# chemin/vers/fichier.ext

```langage
code complet
```

RÈGLE CRITIQUE : Il DOIT y avoir une ligne vide entre le chemin et le bloc de code."""
            
            codeur_messages = [
                {"role": "system", "content": codeur.system_prompt or "Tu es CODEUR, agent spécialisé génération code."},
                {"role": "user", "content": user_message}
            ]
            
            print(f"📤 [CODEUR] Prompt user (premiers 1000 chars):")
            print(f"{user_message[:1000]}...")
            print(f"{'='*80}")
            logger.info(f"Mission {mission_id}: CODEUR prompt user complet: {user_message}")
            
            code_response = await codeur.handle(codeur_messages, session_id=mission_id)
            print(f"✅ [CONTINUE_COMPLETE_MODE] CODEUR réponse reçue ({len(code_response)} chars)")
            print(f"📄 [CONTINUE_COMPLETE_MODE] Code (premiers 500 chars):\n{code_response[:500]}...")
            logger.info(f"Mission {mission_id}: CODEUR réponse ({len(code_response)} chars)")
            
            # 2. TESTEUR : Génère tests
            print(f"📞 [CONTINUE_COMPLETE_MODE] Appel TESTEUR...")
            logger.info(f"Mission {mission_id}: Appel TESTEUR")
            testeur = get_agent("TESTEUR")
            print(f"✅ [CONTINUE_COMPLETE_MODE] TESTEUR récupéré : {testeur.name}")
            
            testeur_messages = [
                {"role": "system", "content": testeur.system_prompt or "Tu es TESTEUR, agent spécialisé génération tests."},
                {"role": "user", "content": f"Code généré:\n\n{code_response}\n\nGénère les tests exhaustifs (80%+ couverture)."}
            ]
            
            tests_response = await testeur.handle(testeur_messages, session_id=mission_id)
            logger.info(f"Mission {mission_id}: TESTEUR réponse ({len(tests_response)} chars)")
            
            # 3. VALIDATEUR : Valide code + tests + architecture
            while correction_attempts <= max_corrections:
                logger.info(f"Mission {mission_id}: Appel VALIDATEUR (tentative {correction_attempts + 1}/{max_corrections + 1})")
                validateur = get_agent("VALIDATEUR")
                
                # Récupérer MissionContext
                mission_context = self.mission_manager.get_mission_context(mission_id)
                
                validateur_messages = [
                    {"role": "system", "content": validateur.system_prompt or "Tu es VALIDATEUR, agent contrôle qualité."},
                    {"role": "user", "content": f"""=== CONTEXTE MISSION ===
{mission_context.get_summary() if mission_context else 'Aucun contexte disponible'}

---

=== CODE À VALIDER ===
{code_response}

---

=== TESTS ===
{tests_response}

---

INSTRUCTIONS :
Valide le code et les tests selon les critères définis dans ton prompt système.
Vérifie la cohérence avec l'architecture prévue (voir CONTEXTE MISSION).
Si des tentatives de validation précédentes ont échoué, vérifie que les corrections ont été appliquées."""}
                ]
                
                validation_response = await validateur.handle(validateur_messages, session_id=mission_id)
                print(f"📋 [VALIDATEUR] Réponse complète ({len(validation_response)} chars):")
                print(f"{validation_response}")
                print(f"{'='*80}")
                logger.info(f"Mission {mission_id}: VALIDATEUR réponse complète: {validation_response}")
                
                # Détecter si VALIDE ou INVALIDE (chercher "STATUT: VALIDE" dans les 500 premiers chars)
                response_start = validation_response[:500].upper()
                print(f"🔍 [VALIDATEUR] Détection dans (500 premiers chars): '{response_start[:200]}...'")
                
                # Détection flexible : chercher variations possibles
                is_valid = (
                    "STATUT: VALIDE" in response_start or
                    "STATUT:VALIDE" in response_start or
                    "STATUS: VALID" in response_start or
                    "STATUS:VALID" in response_start
                )
                
                print(f"🔍 [VALIDATEUR] Contient 'STATUT: VALIDE' ? {'OUI' if is_valid else 'NON'}")
                
                if is_valid:
                    validation_result = "VALID"
                    print(f"✅ [VALIDATEUR] Code VALIDÉ")
                    logger.info(f"Mission {mission_id}: Code VALIDÉ")
                    break
                else:
                    validation_result = "INVALID"
                    print(f"❌ [VALIDATEUR] Code INVALIDE (tentative {correction_attempts + 1})")
                    logger.warning(f"Mission {mission_id}: Code INVALIDE (tentative {correction_attempts + 1})")
                    
                    if correction_attempts < max_corrections:
                        # 4. CODEUR : Correction
                        logger.info(f"Mission {mission_id}: Appel CODEUR pour correction")
                        
                        correction_messages = [
                            {"role": "system", "content": codeur.system_prompt or "Tu es CODEUR, agent spécialisé génération code."},
                            {"role": "user", "content": f"""Architecture:
{architecture_doc}

Code actuel:
{code_response}

Problèmes BLOQUANTS détectés par VALIDATEUR:
{validation_response}

Corrige UNIQUEMENT les erreurs BLOQUANTES listées ci-dessus :
- Ajoute les imports manquants
- Corrige les erreurs de syntaxe
- Définis les fonctions/variables manquantes

Ne modifie PAS le reste du code.
Ne change PAS la structure ou la logique existante.
Respecte l'architecture définie."""}
                        ]
                        
                        code_response = await codeur.handle(correction_messages, session_id=mission_id)
                        logger.info(f"Mission {mission_id}: CODEUR correction ({len(code_response)} chars)")
                        
                        correction_attempts += 1
                    else:
                        logger.error(f"Mission {mission_id}: Max corrections atteint, code reste INVALIDE")
                        break
            
            # 5. Marquer mission selon résultat
            if validation_result == "VALID":
                mission.code_validated = True
                mission.tests_validated = True
                
                # 6. Écrire fichiers sur disque
                project_path = mission.project_path
                
                print(f"💾 [ORCHESTRATION] Écriture fichiers (validation RÉUSSIE)...")
                logger.info(f"Mission {mission_id}: Écriture fichiers code")
                code_write_result = CodeParser.parse_and_write(code_response, project_path)
                
                logger.info(f"Mission {mission_id}: Écriture fichiers tests")
                tests_write_result = CodeParser.parse_and_write(tests_response, project_path)
                
                # Combiner résultats
                files_created = code_write_result["files_created"] + tests_write_result["files_created"]
                files_updated = code_write_result["files_updated"] + tests_write_result["files_updated"]
                
                mission.files_created = files_created
                mission.files_modified = files_updated
                
                logger.info(f"Mission {mission_id}: {len(files_created)} fichiers créés, {len(files_updated)} mis à jour")
                logger.info(f"Mission {mission_id}: Workflow complété avec succès")
            else:
                # Mode debug : Écrire fichiers même si validation échoue (pour inspection)
                print(f"⚠️ [ORCHESTRATION] Validation ÉCHOUÉE mais écriture fichiers pour debug...")
                logger.warning(f"Mission {mission_id}: Validation échouée, écriture fichiers pour debug")
                
                project_path = mission.project_path
                
                code_write_result = CodeParser.parse_and_write(code_response, project_path)
                tests_write_result = CodeParser.parse_and_write(tests_response, project_path)
                
                # Combiner résultats
                files_created = code_write_result["files_created"] + tests_write_result["files_created"]
                files_updated = code_write_result["files_updated"] + tests_write_result["files_updated"]
                
                mission.files_created = files_created
                mission.files_modified = files_updated
                
                print(f"📁 [ORCHESTRATION] {len(files_created)} fichiers créés malgré validation échouée")
                logger.warning(f"Mission {mission_id}: {len(files_created)} fichiers créés (mode debug)")
                logger.error(f"Mission {mission_id}: Workflow échoué (validation)")
            
            self.mission_manager.update_mission(mission)
            
            return {
                "success": validation_result == "VALID",
                "mode": "COMPLETE",
                "files_created": files_created,
                "validation_result": validation_result,
                "architecture_doc": architecture_doc,
                "code_response": code_response,
                "tests_response": tests_response,
                "validation_response": validation_response,
                "correction_attempts": correction_attempts
            }
            
        except Exception as e:
            logger.error(f"Mission {mission_id}: Erreur workflow (phase code): {e}")
            mission.mark_failed(str(e))
            self.mission_manager.update_mission(mission)
            
            return {
                "success": False,
                "mode": "COMPLETE",
                "error": str(e),
                "files_created": [],
                "validation_result": "ERROR"
            }
    
    async def start_mission(
        self,
        user_request: str,
        project_name: str,
        project_path: str
    ) -> Dict:
        """
        Démarre nouvelle mission avec workflow unique
        
        Args:
            user_request: Demande utilisateur
            project_name: Nom projet
            project_path: Chemin projet
        
        Returns:
            Dict avec mission_id, mode, status
        """
        # 1. Vérifier projet existant
        existing = self.project_manager.detect_existing_project(project_name)
        
        if existing["exists"] and existing["action"] == "ask_user":
            # Projet existe → Demander action utilisateur
            return {
                "success": False,
                "requires_user_action": True,
                "message": self.project_manager.propose_action_message(existing),
                "existing_project": existing
            }
        
        # 2. Créer mission
        import uuid
        mission_id = f"mission_{uuid.uuid4().hex[:12]}"
        
        mission = self.mission_manager.create_mission(
            mission_id=mission_id,
            user_request=user_request,
            project_path=project_path
        )
        
        print(f"📋 [ORCHESTRATION] Mission {mission_id} créée")
        logger.info(f"Mission {mission_id} créée - Workflow unique (ARCHITECTE → CODEUR → TESTEUR → VALIDATEUR)")
        
        # 3. Exécuter workflow unique (toujours COMPLET)
        result = await self.execute_complete_mode(mission, user_request, project_path)
        
        return {
            "success": True,
            "mission_id": mission_id,
            "mode": result["mode"],
            "status": mission.status.value
        }
    
    async def process_response(
        self,
        response: str,
        conversation_history: List[Dict],
        session_id: str,
        project_path: Optional[str] = None,
        function_executor = None,
        session_state = None
    ) -> tuple[str, List]:
        """
        Traite réponse agent et orchestre workflow si nécessaire
        
        Détecte les délégations dans la réponse de JARVIS_Maître :
        - [DEMANDE_CODE_CODEUR: ...] → Lance workflow 5 agents
        
        Args:
            response: Réponse de l'agent
            conversation_history: Historique conversation
            session_id: ID session
            project_path: Chemin projet (optionnel)
            function_executor: Exécuteur fonctions (optionnel)
            session_state: État session (optionnel)
        
        Returns:
            Tuple (response, delegation_results)
        """
        import re
        
        # Logs console pour diagnostic
        print(f"\n🔍 [ORCHESTRATION] process_response appelé - session {session_id}")
        print(f"📝 [ORCHESTRATION] Réponse ({len(response)} chars): {response[:200]}...")
        
        logger.info(f"Orchestration: process_response appelé pour session {session_id}")
        logger.info(f"Orchestration: Réponse complète ({len(response)} chars): {response[:500]}...")
        
        # Détecter [DEMANDE_CODE_CODEUR: ...]
        delegation_pattern = r'\[DEMANDE_CODE_CODEUR:\s*(.*?)\]'
        match = re.search(delegation_pattern, response, re.DOTALL)
        
        if not match:
            print(f"❌ [ORCHESTRATION] Aucune délégation détectée")
            print(f"⚠️  [ORCHESTRATION] Pattern recherché: {delegation_pattern}")
            print(f"⚠️  [ORCHESTRATION] Réponse ne contient pas [DEMANDE_CODE_CODEUR:]")
            
            logger.warning(f"Orchestration: ❌ Aucune délégation détectée pour session {session_id}")
            logger.warning(f"Orchestration: Pattern recherché: {delegation_pattern}")
            logger.warning(f"Orchestration: Réponse ne contient pas de marqueur [DEMANDE_CODE_CODEUR:]")
            return response, []
        
        print(f"✅ [ORCHESTRATION] Marqueur [DEMANDE_CODE_CODEUR:] détecté")
        logger.info(f"Orchestration: ✅ Délégation détectée pour session {session_id}")
        
        # Extraire la demande utilisateur
        user_request = match.group(1).strip()
        logger.info(f"Orchestration: Demande extraite ({len(user_request)} chars)")
        
        # Vérifier que project_path est disponible
        if not project_path:
            logger.error(f"Orchestration: project_path manquant pour session {session_id}")
            error_msg = "\n\n❌ **ERREUR** : Impossible de démarrer le workflow (project_path manquant)"
            return response + error_msg, []
        
        # Détecter nom projet depuis project_path
        from pathlib import Path
        project_name = Path(project_path).name
        
        try:
            # Démarrer la mission avec workflow unique
            print(f"🚀 [ORCHESTRATION] Démarrage mission pour projet '{project_name}'")
            logger.info(f"Orchestration: Démarrage mission pour projet '{project_name}'")
            
            mission_result = await self.start_mission(
                user_request=user_request,
                project_name=project_name,
                project_path=project_path
            )
            
            logger.info(f"Orchestration: Mission démarrée - {mission_result}")
            
            # Construire réponse enrichie
            if mission_result.get("success"):
                mission_id = mission_result.get("mission_id")
                mode = mission_result.get("mode")
                user_message = mission_result.get("user_message", "")
                
                # Si user_message existe (workflow en pause pour validation), l'afficher
                if user_message:
                    enriched_response = f"""{response}

---

{user_message}"""
                else:
                    # Sinon, message standard de démarrage
                    enriched_response = f"""{response}

---

✅ **Workflow démarré**

- **Mission ID** : `{mission_id}`
- **Mode** : {mode}
- **Projet** : {project_name}

Le workflow est en cours d'exécution. Consultez le bloc "Workflow" à gauche pour suivre l'avancement."""
                
                delegation_results = [{
                    "agent_name": mode,
                    "success": True,
                    "mission_id": mission_id,
                    "files_written": []
                }]
                
                return enriched_response, delegation_results
            
            else:
                error_msg = mission_result.get("message", "Erreur inconnue")
                enriched_response = f"""{response}

---

❌ **Erreur workflow**

{error_msg}"""
                
                return enriched_response, []
        
        except Exception as e:
            logger.exception(f"Orchestration: Erreur démarrage mission pour session {session_id}")
            error_response = f"""{response}

---

❌ **ERREUR** : {str(e)}"""
            
            return error_response, []
    
    async def finalize_mission(self, mission_id: str) -> Dict:
        """
        Finalise mission complétée (versioning + indexation RAG)
        
        Args:
            mission_id: ID mission
        
        Returns:
            Dict avec success, version, indexed
        """
        mission = self.mission_manager.get_mission(mission_id)
        
        if not mission:
            return {"success": False, "error": "Mission not found"}
        
        if not mission.is_complete():
            return {"success": False, "error": "Mission not complete"}
        
        # 1. Incrémenter version projet
        current_version = self.version_manager.get_project_version(mission.project_path)
        change_type = self.version_manager.detect_change_type(mission.user_request)
        new_version = self.version_manager.increment_version(current_version, change_type)
        
        self.version_manager.save_version(
            project_path=mission.project_path,
            version=new_version,
            mission_id=mission_id,
            files_modified=mission.files_created + mission.files_modified
        )
        
        logger.info(f"Mission {mission_id}: Version {current_version} → {new_version}")
        
        # 2. Indexer dans RAG (si pas déjà indexé)
        if not self.rag_indexer.is_project_indexed(mission.project_path):
            project_name = mission.project_path.split("/")[-1]
            
            indexation_result = self.rag_indexer.index_completed_mission(
                mission_id=mission_id,
                project_path=mission.project_path,
                project_name=project_name,
                user_request=mission.user_request,
                files_created=mission.files_created,
                architecture_doc=None  # TODO: Récupérer depuis mission
            )
            
            logger.info(f"Mission {mission_id}: Indexé dans RAG - {indexation_result['rag_path']}")
        else:
            logger.info(f"Mission {mission_id}: Déjà indexé dans RAG (skip)")
        
        # 3. Marquer mission comme complétée
        mission.mark_completed()
        self.mission_manager.update_mission(mission)
        
        return {
            "success": True,
            "version": new_version,
            "indexed": True,
            "mission_status": mission.status.value
        }
