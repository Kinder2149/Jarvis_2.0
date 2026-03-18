"""
Script d'indexation de la Library JARVIS dans le système RAG.

Ce script :
1. Lance l'API RAG si elle n'est pas déjà lancée
2. Lit tous les documents de backend/db/library_seed.json
3. Les indexe dans ChromaDB via l'API RAG

Usage:
    python index_jarvis_library.py
"""

import json
import sys
import time
from pathlib import Path
import requests

# Configuration
RAG_API_URL = "http://localhost:5001"
LIBRARY_SEED_PATH = Path(__file__).parent.parent / "backend" / "db" / "library_seed.json"
RAG_COLLECTION_NAME = "jarvis_library"


def check_rag_api_health():
    """Vérifie si l'API RAG est accessible."""
    try:
        response = requests.get(f"{RAG_API_URL}/", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def clear_collection():
    """Vide la collection RAG existante."""
    try:
        response = requests.delete(f"{RAG_API_URL}/rag/collection/clear")
        if response.status_code == 200:
            print("✅ Collection RAG vidée avec succès")
            return True
        else:
            print(f"⚠️ Erreur lors du vidage de la collection: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion lors du vidage: {e}")
        return False


def index_document(name: str, content: str, metadata: dict):
    """Indexe un document dans le RAG."""
    try:
        # Préparer les métadonnées
        full_metadata = {
            "name": name,
            "category": metadata.get("category", "unknown"),
            "agent": metadata.get("agent", "all"),
            "tags": ",".join(metadata.get("tags", [])),
        }
        
        # Appeler l'API RAG pour ajouter le texte
        response = requests.post(
            f"{RAG_API_URL}/rag/documents",
            json={
                "text": content,
                "source": name,
                "metadata": full_metadata
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            chunks_count = data.get("chunks_added", 0)
            print(f"  ✅ {name}: {chunks_count} chunks indexés")
            return True
        else:
            print(f"  ❌ {name}: Erreur {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ {name}: Erreur de connexion - {e}")
        return False


def main():
    """Fonction principale."""
    print("=" * 60)
    print("INDEXATION LIBRARY JARVIS DANS RAG")
    print("=" * 60)
    
    # 1. Vérifier que l'API RAG est accessible
    print("\n1. Vérification de l'API RAG...")
    if not check_rag_api_health():
        print("❌ L'API RAG n'est pas accessible sur http://localhost:5001")
        print("\nPour démarrer l'API RAG :")
        print("  cd RAG")
        print("  python run.py")
        sys.exit(1)
    print("✅ API RAG accessible")
    
    # 2. Charger library_seed.json
    print(f"\n2. Chargement de {LIBRARY_SEED_PATH}...")
    if not LIBRARY_SEED_PATH.exists():
        print(f"❌ Fichier introuvable: {LIBRARY_SEED_PATH}")
        sys.exit(1)
    
    with open(LIBRARY_SEED_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    print(f"✅ {len(documents)} documents trouvés")
    
    # 3. Vider la collection existante (optionnel)
    print("\n3. Vidage de la collection existante...")
    clear_collection()
    
    # 4. Indexer chaque document
    print(f"\n4. Indexation des {len(documents)} documents...")
    success_count = 0
    failed_count = 0
    
    for doc in documents:
        name = doc.get("name", "Unknown")
        content = doc.get("content", "")
        metadata = {
            "category": doc.get("category", "unknown"),
            "agent": doc.get("agent", "all"),
            "tags": doc.get("tags", []),
        }
        
        if index_document(name, content, metadata):
            success_count += 1
        else:
            failed_count += 1
        
        # Petite pause pour ne pas surcharger l'API
        time.sleep(0.5)
    
    # 5. Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DE L'INDEXATION")
    print("=" * 60)
    print(f"✅ Succès : {success_count}/{len(documents)}")
    print(f"❌ Échecs : {failed_count}/{len(documents)}")
    
    if failed_count == 0:
        print("\n🎉 Indexation terminée avec succès !")
        print("\nVous pouvez maintenant tester la recherche :")
        print('  curl -X POST http://localhost:5001/rag/search \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"query": "API FastAPI", "n_results": 3}\'')
    else:
        print(f"\n⚠️ {failed_count} document(s) n'ont pas pu être indexés")
        sys.exit(1)


if __name__ == "__main__":
    main()
