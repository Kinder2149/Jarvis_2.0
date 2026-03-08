"""
Tests unitaires pour l'agent CODEUR.

Teste l'agent CODEUR isolément pour vérifier :
- Génération de code fonctionnel
- Respect du format markdown attendu
- Qualité du code généré
"""

import pytest
import re
from backend.agents.agent_factory import get_agent

@pytest.mark.live
@pytest.mark.asyncio
async def test_codeur_format_markdown():
    """Test que CODEUR respecte le format markdown avec chemins de fichiers."""
    
    # Récupérer l'agent
    codeur = get_agent("CODEUR")
    
    # Préparer le message
    messages = [
        {"role": "system", "content": codeur.system_prompt},
        {"role": "user", "content": """Génère le code pour une fonction Python simple d'addition.

FORMAT DE RÉPONSE OBLIGATOIRE :
# chemin/vers/fichier.ext

```langage
code complet
```

RÈGLE CRITIQUE : Il DOIT y avoir une ligne vide entre le chemin et le bloc de code.

Fichier à créer : calculatrice.py avec une fonction addition(a, b)."""}
    ]
    
    # Appeler l'agent
    response = await codeur.handle(messages, session_id="test_codeur_format")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    assert len(response) > 50, f"Réponse trop courte ({len(response)} chars)"
    
    # Vérifier format markdown : # chemin/fichier.ext
    pattern_filepath = r'#\s+([a-zA-Z0-9_/\\.-]+\.py)'
    matches = re.findall(pattern_filepath, response, re.MULTILINE)
    assert len(matches) > 0, f"Aucun chemin de fichier trouvé. Format attendu : '# calculatrice.py'\nRéponse : {response[:500]}"
    
    # Vérifier présence de blocs de code
    pattern_code_block = r'```python\n(.*?)\n```'
    code_blocks = re.findall(pattern_code_block, response, re.DOTALL)
    assert len(code_blocks) > 0, f"Aucun bloc de code Python trouvé\nRéponse : {response[:500]}"
    
    # Vérifier que le code contient la fonction addition
    code_content = '\n'.join(code_blocks)
    assert "def addition" in code_content, "Fonction addition non trouvée dans le code"
    
    print(f"\n✅ CODEUR - Format markdown : {len(matches)} fichier(s), {len(code_blocks)} bloc(s) de code")
    print(f"Fichiers : {matches}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_codeur_code_fonctionnel():
    """Test que CODEUR génère du code fonctionnel (syntaxe valide)."""
    
    # Récupérer l'agent
    codeur = get_agent("CODEUR")
    
    # Préparer le message
    messages = [
        {"role": "system", "content": codeur.system_prompt},
        {"role": "user", "content": """Génère une classe Python simple pour gérer une liste de tâches.

Classe TodoList avec méthodes :
- add_task(task: str)
- remove_task(task: str)
- get_tasks() -> list

Format : # todo.py suivi du code."""}
    ]
    
    # Appeler l'agent
    response = await codeur.handle(messages, session_id="test_codeur_fonctionnel")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Extraire le code Python
    pattern_code_block = r'```python\n(.*?)\n```'
    code_blocks = re.findall(pattern_code_block, response, re.DOTALL)
    assert len(code_blocks) > 0, "Aucun bloc de code trouvé"
    
    code_content = '\n'.join(code_blocks)
    
    # Vérifier syntaxe Python (compilation)
    try:
        compile(code_content, '<string>', 'exec')
        syntax_valid = True
    except SyntaxError as e:
        syntax_valid = False
        print(f"\n❌ Erreur syntaxe : {e}")
        print(f"Code : {code_content[:500]}")
    
    assert syntax_valid, "Code généré contient des erreurs de syntaxe"
    
    # Vérifier présence de la classe et méthodes
    assert "class TodoList" in code_content, "Classe TodoList non trouvée"
    assert "def add_task" in code_content, "Méthode add_task non trouvée"
    assert "def remove_task" in code_content, "Méthode remove_task non trouvée"
    assert "def get_tasks" in code_content, "Méthode get_tasks non trouvée"
    
    print(f"\n✅ CODEUR - Code fonctionnel : {len(code_content)} chars, syntaxe valide")


@pytest.mark.live
@pytest.mark.asyncio
async def test_codeur_multifichiers():
    """Test que CODEUR peut générer plusieurs fichiers."""
    
    # Récupérer l'agent
    codeur = get_agent("CODEUR")
    
    # Préparer le message
    messages = [
        {"role": "system", "content": codeur.system_prompt},
        {"role": "user", "content": """Génère le code pour une calculatrice avec tests.

Fichiers à créer :
1. calculatrice.py : fonctions addition et soustraction
2. test_calculatrice.py : tests unitaires pytest

Format : # chemin/fichier.ext suivi du code pour CHAQUE fichier."""}
    ]
    
    # Appeler l'agent
    response = await codeur.handle(messages, session_id="test_codeur_multifichiers")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Vérifier présence de plusieurs fichiers
    pattern_filepath = r'#\s+([a-zA-Z0-9_/\\.-]+\.py)'
    matches = re.findall(pattern_filepath, response, re.MULTILINE)
    assert len(matches) >= 2, f"Moins de 2 fichiers trouvés ({len(matches)}). Attendu : calculatrice.py et test_calculatrice.py"
    
    # Vérifier présence des fichiers attendus
    filenames = [m.lower() for m in matches]
    assert any("calculatrice.py" in f for f in filenames), "calculatrice.py non trouvé"
    assert any("test" in f for f in filenames), "Fichier de test non trouvé"
    
    # Vérifier présence de blocs de code
    pattern_code_block = r'```python\n(.*?)\n```'
    code_blocks = re.findall(pattern_code_block, response, re.DOTALL)
    assert len(code_blocks) >= 2, f"Moins de 2 blocs de code trouvés ({len(code_blocks)})"
    
    print(f"\n✅ CODEUR - Multi-fichiers : {len(matches)} fichier(s), {len(code_blocks)} bloc(s) de code")
    print(f"Fichiers : {matches}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_codeur_gestion_erreurs():
    """Test que CODEUR inclut la gestion d'erreurs quand demandé."""
    
    # Récupérer l'agent
    codeur = get_agent("CODEUR")
    
    # Préparer le message
    messages = [
        {"role": "system", "content": codeur.system_prompt},
        {"role": "user", "content": """Génère une fonction Python de division avec gestion d'erreurs.

Fonction division(a, b) qui :
- Retourne a / b
- Gère la division par zéro (raise ValueError)
- Valide que a et b sont des nombres

Format : # operations.py suivi du code."""}
    ]
    
    # Appeler l'agent
    response = await codeur.handle(messages, session_id="test_codeur_erreurs")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Extraire le code
    pattern_code_block = r'```python\n(.*?)\n```'
    code_blocks = re.findall(pattern_code_block, response, re.DOTALL)
    assert len(code_blocks) > 0, "Aucun bloc de code trouvé"
    
    code_content = '\n'.join(code_blocks)
    
    # Vérifier gestion d'erreurs
    assert "def division" in code_content, "Fonction division non trouvée"
    
    # Vérifier présence de gestion d'erreurs (au moins un de ces patterns)
    error_handling_patterns = [
        "raise ValueError",
        "raise ZeroDivisionError",
        "if b == 0",
        "try:",
        "except"
    ]
    
    found_patterns = [p for p in error_handling_patterns if p in code_content]
    assert len(found_patterns) > 0, f"Aucune gestion d'erreurs trouvée. Patterns cherchés : {error_handling_patterns}"
    
    print(f"\n✅ CODEUR - Gestion erreurs : {len(found_patterns)} pattern(s) trouvé(s)")
    print(f"Patterns : {found_patterns}")
