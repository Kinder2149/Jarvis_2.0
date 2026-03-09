"""
Orchestration Workflow 5 Agents - JARVIS 2.0
Gestion workflow adaptatif avec modes RAPIDE et COMPLET
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
    Orchestrateur workflow 5 agents avec modes adaptatifs
    
    Workflow RAPIDE (≤3 fichiers) :
    - JARVIS_Maître → CODEUR → TESTEUR → VALIDATEUR
    
    Workflow COMPLET (>3 fichiers) :
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
    
    def detect_project_complexity(self, user_request: str) -> str:
        """
        Détecte complexité projet depuis demande utilisateur
        
        Args:
            user_request: Demande utilisateur
        
        Returns:
            "SIMPLE" (≤3 fichiers) ou "COMPLEX" (>3 fichiers)
        """
        request_lower = user_request.lower()
        
        # PRIORITÉ 1 : Mots-clés explicites "simple" ou "basique"
        if "simple" in request_lower or "basique" in request_lower:
            logger.info(f"Complexité: SIMPLE (mot-clé explicite)")
            return "SIMPLE"
        
        # PRIORITÉ 2 : Mots-clés projets simples
        simple_keywords = [
            "calculatrice", "petit", "rapide", "script",
            "fonction", "classe unique"
        ]
        
        if any(keyword in request_lower for keyword in simple_keywords):
            logger.info(f"Complexité: SIMPLE (mot-clé projet simple)")
            return "SIMPLE"
        
        # PRIORITÉ 3 : Mots-clés projets complexes
        complex_keywords = [
            "api rest", "api complète", "backend complet",
            "authentification", "auth", "base de données",
            "crud complet", "plusieurs", "multi",
            "architecture", "système", "application complète",
            "frontend", "backend", "fullstack"
        ]
        
        if any(keyword in request_lower for keyword in complex_keywords):
            logger.info(f"Complexité: COMPLEX (mot-clé projet complexe)")
            return "COMPLEX"
        
        # Estimation nombre fichiers par mots-clés
        file_indicators = {
            "fichier": 1,
            "classe": 1,
            "modèle": 1,
            "service": 1,
            "controller": 1,
            "route": 1,
            "composant": 1,
            "page": 1
        }
        
        estimated_files = 0
        for keyword, count in file_indicators.items():
            if keyword in request_lower:
                estimated_files += count
        
        # Si >3 fichiers estimés → COMPLEX
        if estimated_files > 3:
            return "COMPLEX"
        
        # Par défaut : SIMPLE (principe de précaution)
        return "SIMPLE"
    
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
    
    async def execute_fast_mode(
        self,
        mission: Mission,
        user_request: str,
        project_path: str
    ) -> Dict:
        """
        Exécute workflow RAPIDE (sans ARCHITECTE)
        
        Workflow :
        1. JARVIS_Maître → Analyse besoin
        2. CODEUR → Génère code
        3. TESTEUR → Génère tests
        4. VALIDATEUR → Valide
        
        Args:
            mission: Mission en cours
            user_request: Demande utilisateur
            project_path: Chemin projet
        
        Returns:
            Dict avec success, files_created, validation_result
        """
        from backend.agents.agent_factory import get_agent
        
        logger.info(f"Orchestration: Mode RAPIDE pour mission {mission.mission_id}")
        
        mission.current_phase = MissionPhase.GENERATION_CODE
        mission.status = MissionStatus.IN_PROGRESS
        self.mission_manager.update_mission(mission)
        
        # Créer contexte mission pour suivre le workflow
        mission_context = MissionContext(
            mission_id=mission.mission_id,
            user_request=user_request,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        logger.info(f"Mission {mission.mission_id}: MissionContext créé")
        
        files_created = []
        files_updated = []
        validation_result = "PENDING"
        correction_attempts = 0
        max_corrections = 2  # 2 tentatives suffisent, sinon problème structurel
        code_response = ""
        tests_response = ""
        validation_response = ""
        
        try:
            # 1. Enrichir contexte avec RAG
            logger.info(f"Mission {mission.mission_id}: Enrichissement contexte RAG")
            
            # Détecter type projet
            project_type = self.detect_project_type(user_request)
            logger.info(f"Mission {mission.mission_id}: Type projet détecté = {project_type}")
            
            # Construire query RAG optimisée
            rag_query = self.build_rag_query(project_type, user_request)
            
            # Enrichir contexte avec RAG
            rag_context = await self.rag_client.search(
                query=rag_query,
                top_k=3
            )
            logger.info(f"Mission {mission.mission_id}: RAG context = {len(rag_context)} chars")
            
            # 2. CODEUR : Génère code
            logger.info(f"Mission {mission.mission_id}: Appel CODEUR")
            codeur = get_agent("CODEUR")
            
            # Construire message avec MissionContext + RAG si disponible
            if rag_context:
                user_message = f"""=== CONTEXTE MISSION ===
{mission_context.get_summary()}

---

=== CONTEXTE RAG (patterns validés) ===
{rag_context}

---

=== DEMANDE UTILISATEUR ===
{mission.user_request}

INSTRUCTIONS :
Utilise les patterns RAG ci-dessus comme référence pour générer le code.
Respecte EXACTEMENT la structure et les conventions des patterns.
Si des fichiers ont déjà été créés (voir CONTEXTE MISSION), ne les recrée pas.

FORMAT DE RÉPONSE OBLIGATOIRE :
Pour CHAQUE fichier, utilise ce format EXACT :

# chemin/vers/fichier.ext

```langage
code complet
```

RÈGLE CRITIQUE : Il DOIT y avoir une ligne vide entre le chemin et le bloc de code."""
            else:
                user_message = f"""=== CONTEXTE MISSION ===
{mission_context.get_summary()}

---

=== DEMANDE UTILISATEUR ===
{mission.user_request}

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
            
            code_response = await codeur.handle(codeur_messages, session_id=mission.mission_id)
            logger.info(f"Mission {mission.mission_id}: CODEUR réponse ({len(code_response)} chars)")
            
            # 2. TESTEUR : Génère tests
            logger.info(f"Mission {mission.mission_id}: Appel TESTEUR")
            testeur = get_agent("TESTEUR")
            
            testeur_messages = [
                {"role": "system", "content": testeur.system_prompt or "Tu es TESTEUR, agent spécialisé génération tests."},
                {"role": "user", "content": f"Code généré:\n\n{code_response}\n\nGénère les tests exhaustifs (80%+ couverture)."}
            ]
            
            tests_response = await testeur.handle(testeur_messages, session_id=mission.mission_id)
            logger.info(f"Mission {mission.mission_id}: TESTEUR réponse ({len(tests_response)} chars)")
            
            # 3. VALIDATEUR : Valide code + tests
            while correction_attempts <= max_corrections:
                logger.info(f"Mission {mission.mission_id}: Appel VALIDATEUR (tentative {correction_attempts + 1}/{max_corrections + 1})")
                validateur = get_agent("VALIDATEUR")
                
                validateur_messages = [
                    {"role": "system", "content": validateur.system_prompt or "Tu es VALIDATEUR, agent contrôle qualité."},
                    {"role": "user", "content": f"""=== CONTEXTE MISSION ===
{mission_context.get_summary()}

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
                
                validation_response = await validateur.handle(validateur_messages, session_id=mission.mission_id)
                logger.info(f"Mission {mission.mission_id}: VALIDATEUR réponse: {validation_response[:200]}")
                
                # Parser feedback VALIDATEUR
                is_valid = self.validation_parser.is_valid(validation_response)
                corrections = self.validation_parser.parse_corrections(validation_response)
                
                # Mettre à jour MissionContext
                mission_context.add_validation_attempt(
                    status="VALID" if is_valid else "INVALID",
                    errors=[c["description"] for c in corrections],
                    corrections=[]
                )
                
                if is_valid:
                    validation_result = "VALID"
                    logger.info(f"Mission {mission.mission_id}: Code VALIDÉ")
                    break
                else:
                    validation_result = "INVALID"
                    logger.warning(f"Mission {mission.mission_id}: Code INVALIDE - {len(corrections)} corrections nécessaires")
                    
                    if correction_attempts < max_corrections:
                        # 4. CODEUR : Correction avec détails parsés
                        logger.info(f"Mission {mission.mission_id}: Appel CODEUR pour correction")
                        
                        # Construire liste corrections détaillées
                        corrections_detail = "\n".join([
                            f"- {c['file']} ligne {c['line']}: {c['description']}"
                            for c in corrections
                        ]) if corrections else "Aucune correction spécifique détectée"
                        
                        correction_messages = [
                            {"role": "system", "content": codeur.system_prompt or "Tu es CODEUR, agent spécialisé génération code."},
                            {"role": "user", "content": f"""Code actuel:
{code_response}

CORRECTIONS NÉCESSAIRES (tentative {correction_attempts + 1}/{max_corrections}) :
{corrections_detail}

FEEDBACK COMPLET VALIDATEUR:
{validation_response}

INSTRUCTIONS :
Corrige UNIQUEMENT les erreurs listées ci-dessus.
Pour chaque correction, applique exactement ce qui est demandé.
Ne modifie PAS le reste du code.
Ne change PAS la structure ou la logique existante."""}
                        ]
                        
                        code_response = await codeur.handle(correction_messages, session_id=mission.mission_id)
                        logger.info(f"Mission {mission.mission_id}: CODEUR correction ({len(code_response)} chars)")
                        
                        correction_attempts += 1
                    else:
                        logger.error(f"Mission {mission.mission_id}: Max corrections atteint, code reste INVALIDE")
                        break
            
            # 5. Marquer mission selon résultat
            if validation_result == "VALID":
                mission.code_validated = True
                mission.tests_validated = True
                
                # 6. Écrire fichiers sur disque
                logger.info(f"Mission {mission.mission_id}: Écriture fichiers code")
                code_write_result = CodeParser.parse_and_write(code_response, project_path)
                
                logger.info(f"Mission {mission.mission_id}: Écriture fichiers tests")
                tests_write_result = CodeParser.parse_and_write(tests_response, project_path)
                
                # Combiner résultats
                files_created = code_write_result["files_created"] + tests_write_result["files_created"]
                files_updated = code_write_result["files_updated"] + tests_write_result["files_updated"]
                
                # Mettre à jour MissionContext avec fichiers créés
                for filepath in files_created:
                    mission_context.add_file(filepath, "created")
                
                mission.files_created = files_created
                mission.files_modified = files_updated
                
                logger.info(f"Mission {mission.mission_id}: {len(files_created)} fichiers créés, {len(files_updated)} mis à jour")
                logger.info(f"Mission {mission.mission_id}: Mode RAPIDE complété avec succès")
            else:
                logger.error(f"Mission {mission.mission_id}: Mode RAPIDE échoué (validation)")
            
            # Logger résumé MissionContext
            logger.info(f"Mission {mission.mission_id}: Résumé contexte:\n{mission_context.get_summary()}")
            
            self.mission_manager.update_mission(mission)
            
            return {
                "success": validation_result == "VALID",
                "mode": "FAST",
                "files_created": files_created,
                "validation_result": validation_result,
                "code_response": code_response,
                "tests_response": tests_response,
                "validation_response": validation_response,
                "correction_attempts": correction_attempts,
                "mission_context": mission_context.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Mission {mission.mission_id}: Erreur mode RAPIDE: {e}")
            mission.mark_failed(str(e))
            self.mission_manager.update_mission(mission)
            
            return {
                "success": False,
                "mode": "FAST",
                "error": str(e),
                "files_created": [],
                "validation_result": "ERROR"
            }
    
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
        
        logger.info(f"Orchestration: Mode COMPLET pour mission {mission.mission_id}")
        
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
            logger.info(f"Mission {mission.mission_id}: Appel ARCHITECTE")
            architecte = get_agent("ARCHITECTE")
            
            architecte_messages = [
                {"role": "system", "content": architecte.system_prompt or "Tu es ARCHITECTE, agent conception architecture."},
                {"role": "user", "content": f"Projet: {project_path}\n\nDemande: {user_request}\n\nConçois l'architecture AVANT le code. Propose structure fichiers, justifie choix, explique en langage simple."}
            ]
            
            architecture_response = await architecte.handle(architecte_messages, session_id=mission.mission_id)
            architecture_doc = architecture_response
            logger.info(f"Mission {mission.mission_id}: ARCHITECTE réponse ({len(architecture_response)} chars)")
            
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
                "mission_id": mission.mission_id
            }
            
        except Exception as e:
            logger.error(f"Mission {mission.mission_id}: Erreur mode COMPLET (phase architecture): {e}")
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
        
        logger.info(f"Mission {mission_id}: Continuation mode COMPLET après validation architecture")
        
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
            logger.info(f"Mission {mission_id}: Type projet détecté = {project_type}")
            
            # Construire query RAG optimisée
            rag_query = self.build_rag_query(project_type, mission.user_request)
            
            # Enrichir contexte avec RAG
            rag_context = await self.rag_client.search(
                query=rag_query,
                top_k=3
            )
            logger.info(f"Mission {mission_id}: RAG context = {len(rag_context)} chars")
            
            # 2. CODEUR : Génère code selon architecture + RAG
            logger.info(f"Mission {mission_id}: Appel CODEUR avec architecture + RAG")
            codeur = get_agent("CODEUR")
            
            # Construire message avec RAG + Architecture
            if rag_context:
                user_message = f"""=== CONTEXTE RAG (patterns validés) ===
{rag_context}

---

=== ARCHITECTURE VALIDÉE ===
{architecture_doc}

---

INSTRUCTIONS :
Génère le code selon l'architecture ci-dessus.
Utilise les patterns RAG comme référence pour la qualité du code.
Respecte EXACTEMENT la structure définie dans l'architecture.

FORMAT DE RÉPONSE OBLIGATOIRE :
Pour CHAQUE fichier, utilise ce format EXACT :

# chemin/vers/fichier.ext

```langage
code complet
```

RÈGLE CRITIQUE : Il DOIT y avoir une ligne vide entre le chemin et le bloc de code."""
            else:
                user_message = f"""=== ARCHITECTURE VALIDÉE ===
{architecture_doc}

---

INSTRUCTIONS :
Génère le code selon l'architecture ci-dessus.

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
            
            code_response = await codeur.handle(codeur_messages, session_id=mission_id)
            logger.info(f"Mission {mission_id}: CODEUR réponse ({len(code_response)} chars)")
            
            # 2. TESTEUR : Génère tests
            logger.info(f"Mission {mission_id}: Appel TESTEUR")
            testeur = get_agent("TESTEUR")
            
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
                logger.info(f"Mission {mission_id}: VALIDATEUR réponse: {validation_response[:200]}")
                
                # Détecter si VALIDE ou INVALIDE (chercher "STATUT: VALIDE" au début de la réponse)
                response_start = validation_response[:100].upper()
                if "STATUT: VALIDE" in response_start:
                    validation_result = "VALID"
                    logger.info(f"Mission {mission_id}: Code VALIDÉ")
                    break
                else:
                    validation_result = "INVALID"
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
                logger.info(f"Mission {mission_id}: Mode COMPLET complété avec succès")
            else:
                logger.error(f"Mission {mission_id}: Mode COMPLET échoué (validation)")
            
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
            logger.error(f"Mission {mission_id}: Erreur mode COMPLET (phase code): {e}")
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
        Démarre nouvelle mission avec workflow adaptatif
        
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
        
        # 3. Détecter complexité
        complexity = self.detect_project_complexity(user_request)
        
        logger.info(f"Mission {mission_id} créée - Complexité: {complexity}")
        
        # 4. Exécuter workflow adaptatif
        if complexity == "SIMPLE":
            result = await self.execute_fast_mode(mission, user_request, project_path)
        else:
            result = await self.execute_complete_mode(mission, user_request, project_path)
        
        return {
            "success": True,
            "mission_id": mission_id,
            "complexity": complexity,
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
        
        Méthode de compatibilité avec API existante.
        Pour l'instant, retourne simplement la réponse sans orchestration.
        
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
        # TODO Phase 6.2-6.3 : Implémenter détection délégation et orchestration
        # Pour l'instant, mode passthrough (compatibilité)
        logger.info(f"Orchestration: process_response appelé pour session {session_id}")
        
        return response, []
    
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
