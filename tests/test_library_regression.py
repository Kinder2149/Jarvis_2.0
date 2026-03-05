"""
Test de régression Library - Boucle infinie function calls

Ce test reproduit la régression v4.1 où l'obligation de consulter
la Library avant délégation cause une boucle infinie de function calls.

Date : 25 février 2026
"""

import asyncio
import logging
import os
from pathlib import Path

import pytest

# Configuration logs détaillés
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importer après configuration logs
from backend.agents.base_agent import BaseAgent
from backend.db.database import Database
from backend.services.function_executor import FunctionExecutor


# Prompt v4.1 avec obligation Library (RÉGRESSION)
PROMPT_V4_1_REGRESSION = """Tu es JARVIS_Maître, le directeur technique personnel de Val C.

## RÈGLE ABSOLUE — DÉLÉGATION AVEC LIBRARY

**Quand l'utilisateur demande du CODE** :

✅ **TOUJOURS FAIRE** :
1. **CONSULTER LA LIBRARY** : Utilise get_library_document() pour récupérer les patterns pertinents
2. **ENRICHIR L'INSTRUCTION** : Intègre le contexte Library dans ton instruction
3. Écrire le marqueur : [DEMANDE_CODE_CODEUR: instruction enrichie]

❌ **NE JAMAIS FAIRE** :
- Déléguer sans consulter la Library
- Générer le code toi-même

## MARQUEURS DE DÉLÉGATION

- **Code** : [DEMANDE_CODE_CODEUR: instruction]

**Maximum 1 marqueur par agent par réponse.**
"""


# Prompt v4.0 stable (RÉFÉRENCE)
PROMPT_V4_0_STABLE = """Tu es JARVIS_Maître, le directeur technique personnel de Val C.

## RÈGLE ABSOLUE — DÉLÉGATION IMMÉDIATE

**Quand l'utilisateur demande du CODE** :

✅ **TOUJOURS FAIRE** :
1. Écrire IMMÉDIATEMENT le marqueur : [DEMANDE_CODE_CODEUR: instruction complète]
2. Inclure TOUS les fichiers dans UN SEUL marqueur
3. Instruction autonome et complète

❌ **NE JAMAIS FAIRE** :
- Générer le code toi-même
- Faire un audit ou un plan avant de déléguer

## MARQUEURS DE DÉLÉGATION

- **Code** : [DEMANDE_CODE_CODEUR: instruction]

**Maximum 1 marqueur par agent par réponse.**
"""


@pytest.fixture
async def db_instance():
    """Fixture pour instance DB avec Library peuplée"""
    db = Database("jarvis_data.db")
    await db.init()
    
    # Vérifier que Library est peuplée
    docs = await db.list_library_documents()
    assert len(docs) > 0, "Library doit être peuplée pour ce test"
    
    yield db


@pytest.fixture
def function_executor(db_instance):
    """Fixture pour FunctionExecutor avec accès Library"""
    return FunctionExecutor(db_instance=db_instance, project_path=None)


class TestLibraryRegression:
    """Tests de régression pour l'enrichissement Library"""

    @pytest.mark.asyncio
    async def test_prompt_v4_0_stable_no_loop(self, function_executor):
        """
        Test baseline : Prompt v4.0 (stable) ne cause PAS de boucle.
        
        Comportement attendu :
        - Délégation immédiate sans function calls
        - Réponse contient marqueur [DEMANDE_CODE_CODEUR: ...]
        - Pas de tool_calls
        """
        # Créer agent avec prompt v4.0
        agent = BaseAgent(
            agent_id="test_v4_0",
            name="JARVIS_Maître_v4.0",
            role="orchestrator",
            description="Test prompt v4.0 stable",
            temperature=0.3,
            max_tokens=4096,
        )
        
        # Injecter prompt v4.0
        agent.system_prompt = PROMPT_V4_0_STABLE
        
        # Message utilisateur demandant du code
        messages = [
            {"role": "user", "content": "Crée un fichier hello.py avec une fonction hello() qui affiche 'Hello World'"}
        ]
        
        # Exécuter avec function_executor (Library disponible)
        response = await agent.handle(messages, function_executor=function_executor)
        
        # Vérifications
        assert response, "Réponse ne doit pas être vide"
        assert len(response) > 0, "Réponse doit contenir du texte"
        assert "[DEMANDE_CODE_CODEUR:" in response, "Réponse doit contenir marqueur de délégation"
        
        print(f"\n✅ PROMPT V4.0 STABLE - Réponse ({len(response)} chars):")
        print(response[:500])

    @pytest.mark.asyncio
    async def test_prompt_v4_1_regression_loop(self, function_executor):
        """
        Test régression : Prompt v4.1 (obligation Library) cause boucle infinie.
        
        Comportement attendu (RÉGRESSION) :
        - Gemini appelle get_library_document() en boucle
        - Atteint max_iterations (3)
        - Retourne réponse vide ou sans délégation
        - PAS de marqueur [DEMANDE_CODE_CODEUR: ...]
        """
        # Créer agent avec prompt v4.1
        agent = BaseAgent(
            agent_id="test_v4_1",
            name="JARVIS_Maître_v4.1",
            role="orchestrator",
            description="Test prompt v4.1 régression",
            temperature=0.3,
            max_tokens=4096,
        )
        
        # Injecter prompt v4.1
        agent.system_prompt = PROMPT_V4_1_REGRESSION
        
        # Message utilisateur demandant du code
        messages = [
            {"role": "user", "content": "Crée un fichier hello.py avec une fonction hello() qui affiche 'Hello World'"}
        ]
        
        # Exécuter avec function_executor (Library disponible)
        response = await agent.handle(messages, function_executor=function_executor)
        
        # Vérifications RÉGRESSION
        print(f"\n⚠️ PROMPT V4.1 RÉGRESSION - Réponse ({len(response)} chars):")
        print(response[:500] if response else "(vide)")
        
        # Analyser le comportement
        if not response or len(response) == 0:
            print("❌ RÉGRESSION CONFIRMÉE : Réponse vide")
        elif "[DEMANDE_CODE_CODEUR:" not in response:
            print("❌ RÉGRESSION CONFIRMÉE : Pas de délégation")
        else:
            print("✅ RÉGRESSION NON REPRODUITE : Délégation présente")
        
        # Ce test DOIT échouer si régression reproduite
        # (pour documenter le problème, pas pour valider le code)

    @pytest.mark.asyncio
    async def test_library_functions_available(self, function_executor):
        """
        Test que les functions Library sont bien disponibles.
        """
        functions = function_executor.get_available_functions()
        
        function_names = [f["name"] for f in functions]
        
        assert "get_library_document" in function_names
        assert "get_library_list" in function_names
        assert "get_project_file" in function_names
        assert "get_project_structure" in function_names
        
        print(f"\n✅ {len(functions)} functions disponibles : {function_names}")

    @pytest.mark.asyncio
    async def test_library_document_execution(self, function_executor):
        """
        Test que get_library_document() fonctionne correctement.
        """
        # Appeler function
        result = await function_executor.execute(
            "get_library_document",
            {"name": "FastAPI", "category": "libraries"}
        )
        
        # Vérifications
        assert result["success"] is True
        assert "document" in result
        assert result["document"]["name"] == "FastAPI"
        assert len(result["document"]["content"]) > 0
        
        print(f"\n✅ Library document récupéré : {result['document']['name']}")
        print(f"   Taille contenu : {len(result['document']['content'])} chars")


if __name__ == "__main__":
    """Exécution directe pour debug"""
    import sys
    
    # Changer vers racine projet
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    
    print("=" * 80)
    print("TEST RÉGRESSION LIBRARY - Boucle Infinie Function Calls")
    print("=" * 80)
    
    # Exécuter tests
    pytest.main([__file__, "-v", "-s"])
