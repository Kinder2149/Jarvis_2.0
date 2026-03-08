"""
Script de lancement du serveur JARVIS 2.0
Gère les imports correctement depuis la racine du projet
"""

import sys
from pathlib import Path

# Ajouter le dossier racine au PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importer et lancer l'application
from backend.app import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Démarrage JARVIS 2.0...")
    print(f"📁 Racine projet : {project_root}")
    print(f"🌐 Serveur : http://localhost:8000")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
