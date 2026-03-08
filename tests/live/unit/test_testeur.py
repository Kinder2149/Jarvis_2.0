"""
Tests unitaires pour l'agent TESTEUR.

Teste l'agent TESTEUR isolément pour vérifier :
- Génération de tests unitaires
- Couverture des cas de tests
- Format pytest
"""

import pytest
import re
from backend.agents.agent_factory import get_agent

@pytest.mark.live
@pytest.mark.asyncio
async def test_testeur_genere_tests_pytest():
    """Test que TESTEUR génère des tests pytest valides."""
    
    # Récupérer l'agent
    testeur = get_agent("TESTEUR")
    
    # Préparer le message avec code à tester
    code_to_test = """
# calculatrice.py

def addition(a, b):
    return a + b

def soustraction(a, b):
    return a - b
"""
    
    messages = [
        {"role": "system", "content": testeur.system_prompt},
        {"role": "user", "content": f"""Génère des tests unitaires pytest pour ce code :

{code_to_test}

Format : # test_calculatrice.py suivi du code des tests."""}
    ]
    
    # Appeler l'agent
    response = await testeur.handle(messages, session_id="test_testeur_pytest")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Vérifier format fichier de test
    pattern_filepath = r'#\s+([a-zA-Z0-9_/\\.-]+\.py)'
    matches = re.findall(pattern_filepath, response, re.MULTILINE)
    assert len(matches) > 0, "Aucun fichier de test trouvé"
    assert any("test" in m.lower() for m in matches), "Nom de fichier ne contient pas 'test'"
    
    # Extraire le code des tests
    pattern_code_block = r'```python\n(.*?)\n```'
    code_blocks = re.findall(pattern_code_block, response, re.DOTALL)
    assert len(code_blocks) > 0, "Aucun bloc de code trouvé"
    
    test_code = '\n'.join(code_blocks)
    
    # Vérifier imports pytest
    assert "import pytest" in test_code or "from pytest" in test_code, "Import pytest manquant"
    
    # Vérifier présence de fonctions de test
    test_functions = re.findall(r'def (test_\w+)', test_code)
    assert len(test_functions) > 0, "Aucune fonction de test trouvée (format: def test_xxx)"
    
    # Vérifier présence d'assertions
    assert "assert" in test_code, "Aucune assertion trouvée dans les tests"
    
    print(f"\n✅ TESTEUR - Tests pytest : {len(test_functions)} fonction(s) de test")
    print(f"Fonctions : {test_functions}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_testeur_couverture_cas():
    """Test que TESTEUR couvre plusieurs cas (nominal + edge cases)."""
    
    # Récupérer l'agent
    testeur = get_agent("TESTEUR")
    
    # Préparer le message avec code à tester
    code_to_test = """
# division.py

def division(a, b):
    if b == 0:
        raise ValueError("Division par zéro impossible")
    return a / b
"""
    
    messages = [
        {"role": "system", "content": testeur.system_prompt},
        {"role": "user", "content": f"""Génère des tests unitaires exhaustifs pour ce code :

{code_to_test}

Couvre :
- Cas nominal (division normale)
- Cas edge (division par zéro)
- Cas limites (nombres négatifs, zéro au numérateur)

Format : # test_division.py suivi du code."""}
    ]
    
    # Appeler l'agent
    response = await testeur.handle(messages, session_id="test_testeur_couverture")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Extraire le code
    pattern_code_block = r'```python\n(.*?)\n```'
    code_blocks = re.findall(pattern_code_block, response, re.DOTALL)
    assert len(code_blocks) > 0, "Aucun bloc de code trouvé"
    
    test_code = '\n'.join(code_blocks)
    
    # Vérifier présence de plusieurs tests
    test_functions = re.findall(r'def (test_\w+)', test_code)
    assert len(test_functions) >= 2, f"Couverture insuffisante : {len(test_functions)} test(s). Attendu : au moins 2"
    
    # Vérifier test de l'exception (division par zéro)
    has_exception_test = (
        "pytest.raises" in test_code or
        "with pytest.raises" in test_code or
        "ValueError" in test_code
    )
    assert has_exception_test, "Test de l'exception (division par zéro) manquant"
    
    print(f"\n✅ TESTEUR - Couverture : {len(test_functions)} test(s), exception testée")
    print(f"Tests : {test_functions}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_testeur_imports_corrects():
    """Test que TESTEUR inclut les imports nécessaires."""
    
    # Récupérer l'agent
    testeur = get_agent("TESTEUR")
    
    # Préparer le message
    code_to_test = """
# todo.py

class TodoList:
    def __init__(self):
        self.tasks = []
    
    def add_task(self, task):
        self.tasks.append(task)
    
    def get_tasks(self):
        return self.tasks
"""
    
    messages = [
        {"role": "system", "content": testeur.system_prompt},
        {"role": "user", "content": f"""Génère des tests pour cette classe :

{code_to_test}

Format : # test_todo.py suivi du code."""}
    ]
    
    # Appeler l'agent
    response = await testeur.handle(messages, session_id="test_testeur_imports")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Extraire le code
    pattern_code_block = r'```python\n(.*?)\n```'
    code_blocks = re.findall(pattern_code_block, response, re.DOTALL)
    assert len(code_blocks) > 0, "Aucun bloc de code trouvé"
    
    test_code = '\n'.join(code_blocks)
    
    # Vérifier import pytest
    assert "import pytest" in test_code or "from pytest" in test_code, "Import pytest manquant"
    
    # Vérifier import du module à tester
    has_import = (
        "from todo import" in test_code or
        "import todo" in test_code or
        "from .todo import" in test_code
    )
    assert has_import, "Import du module à tester (todo) manquant"
    
    # Vérifier import de la classe
    assert "TodoList" in test_code, "Classe TodoList non utilisée dans les tests"
    
    print(f"\n✅ TESTEUR - Imports : pytest + module à tester présents")


@pytest.mark.live
@pytest.mark.asyncio
async def test_testeur_assertions_pertinentes():
    """Test que TESTEUR génère des assertions pertinentes."""
    
    # Récupérer l'agent
    testeur = get_agent("TESTEUR")
    
    # Préparer le message
    code_to_test = """
# calculator.py

def multiply(a, b):
    return a * b

def is_even(n):
    return n % 2 == 0
"""
    
    messages = [
        {"role": "system", "content": testeur.system_prompt},
        {"role": "user", "content": f"""Génère des tests pour ces fonctions :

{code_to_test}

Format : # test_calculator.py suivi du code."""}
    ]
    
    # Appeler l'agent
    response = await testeur.handle(messages, session_id="test_testeur_assertions")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Extraire le code
    pattern_code_block = r'```python\n(.*?)\n```'
    code_blocks = re.findall(pattern_code_block, response, re.DOTALL)
    assert len(code_blocks) > 0, "Aucun bloc de code trouvé"
    
    test_code = '\n'.join(code_blocks)
    
    # Vérifier présence d'assertions
    assertions = re.findall(r'assert\s+', test_code)
    assert len(assertions) >= 2, f"Assertions insuffisantes : {len(assertions)}. Attendu : au moins 2"
    
    # Vérifier types d'assertions (égalité, booléens)
    has_equality = "assert" in test_code and "==" in test_code
    has_boolean = (
        "assert True" in test_code or
        "assert False" in test_code or
        "is True" in test_code or
        "is False" in test_code
    )
    
    assert has_equality or has_boolean, "Aucune assertion d'égalité ou booléenne trouvée"
    
    print(f"\n✅ TESTEUR - Assertions : {len(assertions)} assertion(s) trouvée(s)")
