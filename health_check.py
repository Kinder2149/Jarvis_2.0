#!/usr/bin/env python3
"""
JARVIS Health Check — Vérification rapide post-développement
Vérifie que les 3 modules fonctionnent correctement en moins de 60 secondes.
Usage: python health_check.py (nécessite serveur démarré via start.bat)
"""
import httpx
import sys
import time
import tempfile

BASE_URL = "http://localhost:8000"
TIMEOUT_MESSAGE = 30  # Timeout pour les messages chat
TIMEOUT_DEFAULT = 10  # Timeout par défaut

# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header():
    print("\n╔══════════════════════════════════════╗")
    print("║     JARVIS — Health Check            ║")
    print("╚══════════════════════════════════════╝\n")

def print_result(success: bool, message: str):
    icon = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
    print(f"{icon} {message}")

def check_server():
    """Vérifie que le serveur répond."""
    try:
        response = httpx.get(f"{BASE_URL}/", timeout=5)
        return True, "localhost:8000 répond"
    except Exception as e:
        return False, f"Serveur inaccessible : {str(e)}"

def check_api_keys():
    """Vérifie que les clés API sont configurées."""
    try:
        response = httpx.get(f"{BASE_URL}/api/config/", timeout=5)
        if response.status_code != 200:
            return False, f"Erreur config (status {response.status_code})"
        
        config = response.json()
        api_keys = config.get("api_keys", {})
        
        keys_info = []
        for key_name in ["openrouter_key", "anthropic_key", "google_key"]:
            key_value = api_keys.get(key_name, "")
            if key_value and len(key_value) > 20:
                keys_info.append(f"{key_name.split('_')[0].capitalize()} ({len(key_value)} chars)")
            else:
                keys_info.append(f"{key_name.split('_')[0].capitalize()} (manquante)")
        
        return True, " · ".join(keys_info)
    except Exception as e:
        return False, f"Erreur vérification clés : {str(e)}"

def check_module_chat():
    """Vérifie le module Chat (3 checks)."""
    project_id = None
    conversation_id = None
    
    try:
        start_time = time.time()
        
        # 1. Créer projet temporaire
        temp_path = tempfile.mkdtemp()
        response = httpx.post(
            f"{BASE_URL}/api/projects/",
            json={"name": "Health Check Test", "local_path": temp_path, "module_type": "dev"},
            timeout=TIMEOUT_DEFAULT
        )
        if response.status_code != 200:
            return False, f"Création projet échouée (status {response.status_code})"
        
        project_id = response.json()["id"]
        
        # 2. Créer conversation
        response = httpx.post(
            f"{BASE_URL}/api/chat/conversations",
            json={"title": "Health Check", "project_id": project_id},
            timeout=TIMEOUT_DEFAULT
        )
        if response.status_code != 200:
            return False, f"Création conversation échouée (status {response.status_code})"
        
        conversation_id = response.json()["id"]
        
        # 3. Envoyer message et attendre réponse (TIMEOUT 30s)
        response = httpx.post(
            f"{BASE_URL}/api/chat/conversations/{conversation_id}/messages",
            json={"content": "dis juste OK"},
            timeout=TIMEOUT_MESSAGE
        )
        
        if response.status_code == 500:
            return False, f"Erreur serveur 500 (vérifier clés API)"
        
        if response.status_code != 200:
            return False, f"Envoi message échoué (status {response.status_code})"
        
        message = response.json()
        if not message.get("content"):
            return False, "Réponse IA vide"
        
        elapsed = time.time() - start_time
        return True, f"Conversation créée · Message envoyé · Réponse reçue ({elapsed:.1f}s)"
        
    except httpx.TimeoutException:
        return False, "Timeout (> 30s)"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        # Nettoyage
        try:
            if conversation_id:
                httpx.delete(f"{BASE_URL}/api/chat/conversations/{conversation_id}", timeout=5)
            if project_id:
                httpx.delete(f"{BASE_URL}/api/projects/{project_id}", timeout=5)
        except:
            pass

def check_module_code():
    """Vérifie le module Code (3 checks)."""
    project_id = None
    session_id = None
    
    try:
        # 1. Créer projet temporaire
        temp_path = tempfile.mkdtemp()
        response = httpx.post(
            f"{BASE_URL}/api/projects/",
            json={"name": "Health Check Code", "local_path": temp_path, "module_type": "dev"},
            timeout=TIMEOUT_DEFAULT
        )
        if response.status_code != 200:
            return False, f"Création projet échouée (status {response.status_code})"
        
        project_id = response.json()["id"]
        
        # 2. Démarrer session session_start
        response = httpx.post(
            f"{BASE_URL}/api/pipelines/start",
            json={
                "workflow_type": "session_start",
                "project_id": project_id,
                "user_input": "Health check test"
            },
            timeout=TIMEOUT_DEFAULT
        )
        if response.status_code != 200:
            return False, f"Démarrage session échoué (status {response.status_code})"
        
        session_id = response.json()["session_id"]
        
        # 3. Vérifier status et steps
        response = httpx.get(f"{BASE_URL}/api/pipelines/{session_id}", timeout=TIMEOUT_DEFAULT)
        if response.status_code != 200:
            return False, f"Status session échoué (status {response.status_code})"
        
        session_data = response.json()
        steps_count = len(session_data.get("steps", []))
        
        if steps_count == 0:
            return False, "Aucun step créé"
        
        # 4. Abort session
        response = httpx.post(f"{BASE_URL}/api/pipelines/{session_id}/abort", timeout=TIMEOUT_DEFAULT)
        if response.status_code != 200:
            return False, f"Abort échoué (status {response.status_code})"
        
        return True, f"Session créée ({steps_count} steps) · Abort OK"
        
    except httpx.TimeoutException:
        return False, "Timeout (> 10s)"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        # Nettoyage
        try:
            if project_id:
                httpx.delete(f"{BASE_URL}/api/projects/{project_id}", timeout=5)
        except:
            pass

def check_module_atelier():
    """Vérifie le module Atelier (2 checks)."""
    prospect_id = None
    
    try:
        # 1. Créer prospect
        response = httpx.post(
            f"{BASE_URL}/api/atelier/prospects",
            json={"nom": "Health Check Test", "email": "test@healthcheck.com"},
            timeout=TIMEOUT_DEFAULT
        )
        if response.status_code != 200:
            return False, f"Création prospect échouée (status {response.status_code})"
        
        prospect_id = response.json()["id"]
        
        # 2. Vérifier liste
        response = httpx.get(f"{BASE_URL}/api/atelier/prospects", timeout=TIMEOUT_DEFAULT)
        if response.status_code != 200:
            return False, f"Liste prospects échouée (status {response.status_code})"
        
        prospects = response.json()
        if len(prospects) == 0:
            return False, "Liste vide après création"
        
        # 3. DELETE prospect (nettoyage)
        response = httpx.delete(f"{BASE_URL}/api/atelier/prospects/{prospect_id}", timeout=TIMEOUT_DEFAULT)
        if response.status_code != 200:
            return False, f"Suppression prospect échouée (status {response.status_code})"
        
        return True, "Prospect créé · Liste OK · Nettoyage OK"
        
    except httpx.TimeoutException:
        return False, "Timeout (> 10s)"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        # Nettoyage de sécurité (au cas où le DELETE explicite échoue)
        try:
            if prospect_id:
                httpx.delete(f"{BASE_URL}/api/atelier/prospects/{prospect_id}", timeout=5)
        except:
            pass

def main():
    print_header()
    
    all_success = True
    
    # Vérifier serveur
    success, message = check_server()
    print_result(success, f"Serveur {message}")
    if not success:
        print(f"\n{RED}→ Démarrer JARVIS avec start.bat{RESET}\n")
        return 1
    
    # Vérifier clés API
    success, message = check_api_keys()
    print_result(success, f"Clés API {message}")
    if not success:
        all_success = False
        print(f"{RED}→ Vérifier les clés dans Paramètres → Sauvegarder{RESET}")
    
    print()
    
    # Module Chat
    success, message = check_module_chat()
    print_result(success, f"Module Chat {message}")
    if not success:
        all_success = False
    
    # Module Code
    success, message = check_module_code()
    print_result(success, f"Module Code {message}")
    if not success:
        all_success = False
    
    # Module Atelier
    success, message = check_module_atelier()
    print_result(success, f"Module Atelier {message}")
    if not success:
        all_success = False
    
    print("\n" + "═" * 40)
    if all_success:
        print(f"Résultat : {GREEN}✅ TOUT OK{RESET} — JARVIS est opérationnel\n")
        return 0
    else:
        print(f"Résultat : {RED}❌ PROBLÈMES DÉTECTÉS{RESET} — Vérifier les erreurs ci-dessus\n")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{RED}Interrompu par l'utilisateur{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Erreur fatale : {str(e)}{RESET}\n")
        sys.exit(1)
