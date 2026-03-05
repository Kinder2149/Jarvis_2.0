"""Test de l'enrichissement RAG pour le CODEUR."""
import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.rag_service import get_rag_service

async def test_enrichment():
    """Test enrichissement instruction CODEUR."""
    print("=" * 60)
    print("TEST ENRICHISSEMENT RAG POUR CODEUR")
    print("=" * 60)
    
    # Instruction de test
    instruction = "Crée une API FastAPI avec des tests pytest"
    
    print(f"\n📝 Instruction originale :\n{instruction}\n")
    
    # Récupérer le service RAG
    rag_service = get_rag_service()
    
    # Vérifier disponibilité
    print("1. Vérification API RAG...")
    is_available = await rag_service.check_health()
    
    if not is_available:
        print("❌ API RAG non disponible")
        return
    
    print("✅ API RAG disponible\n")
    
    # Enrichir l'instruction
    print("2. Enrichissement de l'instruction...")
    enriched = await rag_service.enrich_instruction(
        instruction,
        n_results=3
        # Pas de filtre pour l'instant
    )
    
    print(f"\n📚 Instruction enrichie :\n{enriched}\n")
    
    # Statistiques
    original_length = len(instruction)
    enriched_length = len(enriched)
    context_added = enriched_length - original_length
    
    print("=" * 60)
    print("STATISTIQUES")
    print("=" * 60)
    print(f"Longueur originale : {original_length} caractères")
    print(f"Longueur enrichie  : {enriched_length} caractères")
    print(f"Contexte ajouté    : {context_added} caractères")
    print(f"Ratio              : {enriched_length / original_length:.2f}x")
    
    if context_added > 0:
        print("\n✅ Enrichissement réussi !")
    else:
        print("\n⚠️ Aucun contexte ajouté")

if __name__ == "__main__":
    asyncio.run(test_enrichment())
