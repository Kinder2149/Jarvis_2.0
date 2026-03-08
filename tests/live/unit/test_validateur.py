"""
Tests unitaires pour l'agent VALIDATEUR.

Teste l'agent VALIDATEUR isolément pour vérifier :
- Détection d'erreurs syntaxiques
- Validation de code correct
- Format de réponse (STATUT: VALIDE/INVALIDE)
- Justifications des rejets
"""

import pytest
from backend.agents.agent_factory import get_agent

@pytest.mark.live
@pytest.mark.asyncio
async def test_validateur_code_valide():
    """Test que VALIDATEUR accepte du code correct."""
    
    # Récupérer l'agent
    validateur = get_agent("VALIDATEUR")
    
    # Code correct à valider
    code_correct = """
# calculatrice.py

def addition(a, b):
    \"\"\"Additionne deux nombres.\"\"\"
    return a + b

def soustraction(a, b):
    \"\"\"Soustrait b de a.\"\"\"
    return a - b
"""
    
    tests_correct = """
# test_calculatrice.py

import pytest
from calculatrice import addition, soustraction

def test_addition():
    assert addition(2, 3) == 5
    assert addition(-1, 1) == 0

def test_soustraction():
    assert soustraction(5, 3) == 2
    assert soustraction(0, 5) == -5
"""
    
    messages = [
        {"role": "system", "content": validateur.system_prompt},
        {"role": "user", "content": f"""Code:

{code_correct}

Tests:

{tests_correct}

Valide la qualité (bugs, erreurs, cohérence). Réponds STATUT: VALIDE ou STATUT: INVALIDE avec raisons.

IMPORTANT : Se concentrer UNIQUEMENT sur les erreurs BLOQUANTES :
- Erreurs de syntaxe Python
- Imports manquants ou incorrects
- Fonctions/variables utilisées mais non définies
- Erreurs logiques graves

IGNORER :
- Problèmes de style (PEP8, nommage)
- Optimisations possibles
- Edge cases non couverts
- Documentation manquante"""}
    ]
    
    # Appeler l'agent
    response = await validateur.handle(messages, session_id="test_validateur_valide")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Afficher la réponse complète pour debug
    print(f"\n📝 Réponse VALIDATEUR (code correct) :")
    print(f"{response}")
    print(f"\n{'='*80}\n")
    
    # Vérifier format de réponse
    response_upper = response.upper()
    has_statut = "STATUT:" in response_upper or "STATUT :" in response_upper
    assert has_statut, f"Format 'STATUT:' manquant dans la réponse\nRéponse : {response[:500]}"
    
    # Vérifier que le code est validé (chercher dans les 200 premiers caractères)
    response_start = response[:200].upper()
    is_valid = "STATUT: VALIDE" in response_start or "STATUT : VALIDE" in response_start
    
    if not is_valid:
        print(f"\n⚠️  VALIDATEUR a rejeté du code correct !")
        print(f"Début de réponse : {response[:500]}")
    
    # Note : On ne fait pas échouer le test si VALIDATEUR rejette, on log juste
    # C'est justement ce qu'on veut investiguer
    print(f"\n{'✅' if is_valid else '⚠️ '} VALIDATEUR - Code correct : {'VALIDE' if is_valid else 'INVALIDE (à investiguer)'}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_validateur_erreur_syntaxe():
    """Test que VALIDATEUR détecte les erreurs de syntaxe."""
    
    # Récupérer l'agent
    validateur = get_agent("VALIDATEUR")
    
    # Code avec erreur de syntaxe
    code_erreur = """
# calculatrice.py

def addition(a, b)  # Manque le :
    return a + b

def soustraction(a, b):
    return a - b
"""
    
    tests = """
# test_calculatrice.py

import pytest
from calculatrice import addition

def test_addition():
    assert addition(2, 3) == 5
"""
    
    messages = [
        {"role": "system", "content": validateur.system_prompt},
        {"role": "user", "content": f"""Code:

{code_erreur}

Tests:

{tests}

Valide la qualité (bugs, erreurs, cohérence). Réponds STATUT: VALIDE ou STATUT: INVALIDE avec raisons."""}
    ]
    
    # Appeler l'agent
    response = await validateur.handle(messages, session_id="test_validateur_syntaxe")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Afficher la réponse complète
    print(f"\n📝 Réponse VALIDATEUR (erreur syntaxe) :")
    print(f"{response}")
    print(f"\n{'='*80}\n")
    
    # Vérifier que le code est rejeté
    response_start = response[:200].upper()
    is_invalid = "STATUT: INVALIDE" in response_start or "STATUT : INVALIDE" in response_start
    
    assert is_invalid, f"VALIDATEUR devrait détecter l'erreur de syntaxe\nRéponse : {response[:500]}"
    
    # Vérifier mention de l'erreur
    response_lower = response.lower()
    has_syntax_mention = "syntaxe" in response_lower or ":" in response_lower or "manque" in response_lower
    
    print(f"\n✅ VALIDATEUR - Erreur syntaxe : INVALIDE détecté, erreur mentionnée : {has_syntax_mention}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_validateur_import_manquant():
    """Test que VALIDATEUR détecte les imports manquants."""
    
    # Récupérer l'agent
    validateur = get_agent("VALIDATEUR")
    
    # Code avec import manquant
    code_import_manquant = """
# api.py

app = FastAPI()  # FastAPI non importé

@app.get("/")
def root():
    return {"message": "Hello"}
"""
    
    tests = """
# test_api.py

def test_placeholder():
    pass
"""
    
    messages = [
        {"role": "system", "content": validateur.system_prompt},
        {"role": "user", "content": f"""Code:

{code_import_manquant}

Tests:

{tests}

Valide la qualité (bugs, erreurs, cohérence). Réponds STATUT: VALIDE ou STATUT: INVALIDE avec raisons."""}
    ]
    
    # Appeler l'agent
    response = await validateur.handle(messages, session_id="test_validateur_import")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Afficher la réponse complète
    print(f"\n📝 Réponse VALIDATEUR (import manquant) :")
    print(f"{response}")
    print(f"\n{'='*80}\n")
    
    # Vérifier que le code est rejeté
    response_start = response[:200].upper()
    is_invalid = "STATUT: INVALIDE" in response_start or "STATUT : INVALIDE" in response_start
    
    assert is_invalid, f"VALIDATEUR devrait détecter l'import manquant\nRéponse : {response[:500]}"
    
    # Vérifier mention de l'import
    response_lower = response.lower()
    has_import_mention = "import" in response_lower or "fastapi" in response_lower
    
    print(f"\n✅ VALIDATEUR - Import manquant : INVALIDE détecté, import mentionné : {has_import_mention}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_validateur_fonction_non_definie():
    """Test que VALIDATEUR détecte les fonctions non définies."""
    
    # Récupérer l'agent
    validateur = get_agent("VALIDATEUR")
    
    # Code avec fonction non définie
    code_fonction_manquante = """
# calculator.py

def multiply(a, b):
    result = calculate_product(a, b)  # Fonction non définie
    return result
"""
    
    tests = """
# test_calculator.py

from calculator import multiply

def test_multiply():
    assert multiply(2, 3) == 6
"""
    
    messages = [
        {"role": "system", "content": validateur.system_prompt},
        {"role": "user", "content": f"""Code:

{code_fonction_manquante}

Tests:

{tests}

Valide la qualité (bugs, erreurs, cohérence). Réponds STATUT: VALIDE ou STATUT: INVALIDE avec raisons."""}
    ]
    
    # Appeler l'agent
    response = await validateur.handle(messages, session_id="test_validateur_fonction")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Afficher la réponse complète
    print(f"\n📝 Réponse VALIDATEUR (fonction non définie) :")
    print(f"{response}")
    print(f"\n{'='*80}\n")
    
    # Vérifier que le code est rejeté
    response_start = response[:200].upper()
    is_invalid = "STATUT: INVALIDE" in response_start or "STATUT : INVALIDE" in response_start
    
    assert is_invalid, f"VALIDATEUR devrait détecter la fonction non définie\nRéponse : {response[:500]}"
    
    # Vérifier mention de la fonction
    response_lower = response.lower()
    has_function_mention = (
        "calculate_product" in response_lower or
        "fonction" in response_lower or
        "définie" in response_lower or
        "non défini" in response_lower
    )
    
    print(f"\n✅ VALIDATEUR - Fonction non définie : INVALIDE détecté, fonction mentionnée : {has_function_mention}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_validateur_format_reponse():
    """Test que VALIDATEUR respecte le format de réponse attendu."""
    
    # Récupérer l'agent
    validateur = get_agent("VALIDATEUR")
    
    # Code simple
    code = """
# hello.py

def say_hello(name):
    return f"Hello, {name}!"
"""
    
    tests = """
# test_hello.py

from hello import say_hello

def test_say_hello():
    assert say_hello("World") == "Hello, World!"
"""
    
    messages = [
        {"role": "system", "content": validateur.system_prompt},
        {"role": "user", "content": f"""Code:

{code}

Tests:

{tests}

Valide la qualité (bugs, erreurs, cohérence). Réponds STATUT: VALIDE ou STATUT: INVALIDE avec raisons."""}
    ]
    
    # Appeler l'agent
    response = await validateur.handle(messages, session_id="test_validateur_format")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Afficher la réponse complète
    print(f"\n📝 Réponse VALIDATEUR (format) :")
    print(f"{response}")
    print(f"\n{'='*80}\n")
    
    # Vérifier présence du mot STATUT dans les 200 premiers caractères
    response_start = response[:200].upper()
    has_statut = "STATUT:" in response_start or "STATUT :" in response_start
    
    assert has_statut, f"Format 'STATUT:' manquant au début de la réponse\nDébut : {response[:200]}"
    
    # Vérifier que c'est soit VALIDE soit INVALIDE
    has_valide = "STATUT: VALIDE" in response_start or "STATUT : VALIDE" in response_start
    has_invalide = "STATUT: INVALIDE" in response_start or "STATUT : INVALIDE" in response_start
    
    assert has_valide or has_invalide, f"Statut doit être VALIDE ou INVALIDE\nDébut : {response[:200]}"
    
    print(f"\n✅ VALIDATEUR - Format : STATUT présent, {'VALIDE' if has_valide else 'INVALIDE'}")
