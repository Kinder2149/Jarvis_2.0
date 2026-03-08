"""
Script Python de lancement complet JARVIS 2.0
Lance automatiquement :
1. Serveur JARVIS (backend + frontend) sur port 8000
2. Serveur RAG (enrichissement contexte) sur port 5001

Usage: python start_jarvis_complete.py [--skip-rag] [--force]
"""

import sys
import os
import subprocess
import time
import signal
import argparse
from pathlib import Path
import socket

# Couleurs pour terminal
class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_title(msg):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*40}")
    print(msg)
    print(f"{'='*40}{Colors.RESET}\n")

def is_port_in_use(port):
    """Vérifie si un port est utilisé"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def check_module(module_name):
    """Vérifie si un module Python est installé"""
    try:
        __import__(module_name.replace('-', '_').replace('.', '_'))
        return True
    except ImportError:
        return False

def main():
    parser = argparse.ArgumentParser(description='Lancer JARVIS 2.0 complet (JARVIS + RAG)')
    parser.add_argument('--skip-rag', action='store_true', help='Lancer sans serveur RAG')
    parser.add_argument('--force', action='store_true', help='Forcer le lancement même si ports occupés')
    args = parser.parse_args()

    print_title("DÉMARRAGE JARVIS 2.0 COMPLET")

    # ========================================
    # 1. VÉRIFICATIONS PRÉALABLES
    # ========================================

    print_info("Vérification de l'environnement...")

    # Vérifier qu'on est à la racine du projet
    if not Path("backend/app.py").exists():
        print_error("Ce script doit être exécuté depuis la racine du projet JARVIS 2.0")
        print_info("Commande correcte: cd 'd:/Coding/AppWindows/Jarvis 2.0' puis python start_jarvis_complete.py")
        sys.exit(1)

    # Vérifier Python
    python_version = sys.version.split()[0]
    print_success(f"Python détecté: {python_version}")

    # Vérifier environnement virtuel
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success(f"Environnement virtuel actif: {sys.prefix}")
    else:
        print_warning("Aucun environnement virtuel détecté")
        print_info("Utilisation de Python système...")

    # Vérifier fichier .env
    if not Path(".env").exists():
        print_warning("Fichier .env non trouvé")
        if Path(".env.example").exists():
            print_info("Copie de .env.example vers .env...")
            import shutil
            shutil.copy(".env.example", ".env")
            print_success("Fichier .env créé")
            print_warning("⚠️  IMPORTANT: Éditer .env et ajouter votre GEMINI_API_KEY")
            print_info("Obtenir une clé: https://aistudio.google.com/app/apikey")
            input("\nAppuyez sur Entrée après avoir configuré .env (ou Ctrl+C pour quitter)...")
        else:
            print_error("Fichier .env.example non trouvé")
            sys.exit(1)
    else:
        print_success("Fichier .env trouvé")

    # ========================================
    # 2. VÉRIFICATION DÉPENDANCES JARVIS
    # ========================================

    print_info("Vérification des dépendances JARVIS...")

    jarvis_deps = ["fastapi", "uvicorn", "google.generativeai", "aiosqlite"]
    missing_jarvis = [dep for dep in jarvis_deps if not check_module(dep)]

    if missing_jarvis:
        print_warning(f"Dépendances JARVIS manquantes: {', '.join(missing_jarvis)}")
        print_info("Installation des dépendances JARVIS...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        if result.returncode != 0:
            print_error("Erreur lors de l'installation des dépendances JARVIS")
            sys.exit(1)
        print_success("Dépendances JARVIS installées")
    else:
        print_success("Toutes les dépendances JARVIS sont installées")

    # ========================================
    # 3. VÉRIFICATION DÉPENDANCES RAG
    # ========================================

    skip_rag = args.skip_rag

    if not skip_rag:
        print_info("Vérification des dépendances RAG...")
        
        if not Path("RAG/requirements-minimal.txt").exists():
            print_warning("Fichier RAG/requirements-minimal.txt non trouvé")
            print_info("Le serveur RAG ne sera pas démarré")
            skip_rag = True
        else:
            rag_deps = ["flask", "chromadb", "sentence_transformers", "langchain"]
            missing_rag = [dep for dep in rag_deps if not check_module(dep)]
            
            if missing_rag:
                print_warning(f"Dépendances RAG manquantes: {', '.join(missing_rag)}")
                print_info("Installation des dépendances RAG (peut prendre quelques minutes)...")
                result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "RAG/requirements-minimal.txt"])
                if result.returncode != 0:
                    print_error("Erreur lors de l'installation des dépendances RAG")
                    print_warning("Le serveur RAG ne sera pas démarré")
                    skip_rag = True
                else:
                    print_success("Dépendances RAG installées")
            else:
                print_success("Toutes les dépendances RAG sont installées")

    # ========================================
    # 4. VÉRIFICATION PORTS
    # ========================================

    print_info("Vérification des ports...")

    # Port 8000 (JARVIS)
    if is_port_in_use(8000) and not args.force:
        print_warning("Port 8000 déjà utilisé (serveur JARVIS probablement déjà lancé)")
        response = input("Continuer quand même? (o/n): ")
        if response.lower() != 'o':
            print_info("Démarrage annulé")
            sys.exit(0)
    elif is_port_in_use(8000):
        print_warning("Port 8000 occupé (mode Force activé)")
    else:
        print_success("Port 8000 disponible")

    # Port 5001 (RAG)
    if not skip_rag:
        if is_port_in_use(5001) and not args.force:
            print_warning("Port 5001 déjà utilisé (serveur RAG probablement déjà lancé)")
            response = input("Continuer quand même? (o/n): ")
            if response.lower() != 'o':
                print_info("Démarrage annulé")
                sys.exit(0)
        elif is_port_in_use(5001):
            print_warning("Port 5001 occupé (mode Force activé)")
        else:
            print_success("Port 5001 disponible")

    # ========================================
    # 5. DÉMARRAGE SERVEUR RAG (si activé)
    # ========================================

    rag_process = None

    if not skip_rag:
        print_title("DÉMARRAGE SERVEUR RAG")
        
        print_info("Lancement du serveur RAG en arrière-plan...")
        print_info("URL: http://localhost:5001")
        
        # Démarrer RAG en arrière-plan
        rag_cwd = Path("RAG").absolute()
        rag_process = subprocess.Popen(
            [sys.executable, "run.py"],
            cwd=str(rag_cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Attendre 5 secondes pour vérifier que le serveur démarre
        time.sleep(5)
        
        if rag_process.poll() is None:
            print_success(f"Serveur RAG démarré (PID: {rag_process.pid})")
            
            # Vérifier que le serveur répond
            if is_port_in_use(5001):
                print_success("Serveur RAG opérationnel ✅")
            else:
                print_warning("Serveur RAG en cours de démarrage...")
        else:
            print_warning("Le serveur RAG n'a pas démarré correctement")
            stdout, stderr = rag_process.communicate()
            if stderr:
                print_error(f"Erreur RAG: {stderr}")
            skip_rag = True
    else:
        print_info("Serveur RAG désactivé (--skip-rag ou dépendances manquantes)")

    # ========================================
    # 6. DÉMARRAGE SERVEUR JARVIS
    # ========================================

    print_title("DÉMARRAGE SERVEUR JARVIS")

    print_info("Lancement du serveur JARVIS...")
    print_info("Backend + Frontend: http://localhost:8000")
    print_info("API Documentation: http://localhost:8000/docs")
    print()
    print_warning("Appuyez sur Ctrl+C pour arrêter les serveurs")
    print()

    # Démarrer JARVIS (bloquant)
    jarvis_process = None
    try:
        jarvis_process = subprocess.Popen(
            [sys.executable, "start_server.py"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        jarvis_process.wait()
    except KeyboardInterrupt:
        print_info("\nArrêt des serveurs...")
    finally:
        # Arrêter le serveur JARVIS
        if jarvis_process and jarvis_process.poll() is None:
            jarvis_process.terminate()
            try:
                jarvis_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                jarvis_process.kill()
        
        # Arrêter le serveur RAG si lancé
        if rag_process and rag_process.poll() is None:
            print_info("Arrêt du serveur RAG...")
            rag_process.terminate()
            try:
                rag_process.wait(timeout=5)
                print_success("Serveur RAG arrêté")
            except subprocess.TimeoutExpired:
                rag_process.kill()
                print_success("Serveur RAG arrêté (forcé)")
        
        print_info("Serveurs arrêtés")

if __name__ == "__main__":
    main()
