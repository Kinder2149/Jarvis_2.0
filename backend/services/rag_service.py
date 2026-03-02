"""
Service RAG pour JARVIS 2.0.

Ce service communique avec l'API RAG standalone pour récupérer
du contexte pertinent depuis la Library et enrichir les instructions
envoyées au CODEUR.
"""

import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# Configuration
RAG_API_URL = "http://localhost:5001"
RAG_TIMEOUT = 10.0  # secondes
DEFAULT_N_RESULTS = 3  # nombre de documents à récupérer par défaut


class RAGService:
    """Service pour interagir avec l'API RAG."""
    
    def __init__(self, api_url: str = RAG_API_URL, timeout: float = RAG_TIMEOUT):
        """
        Initialise le service RAG.
        
        Args:
            api_url: URL de l'API RAG
            timeout: Timeout pour les requêtes HTTP
        """
        self.api_url = api_url
        self.timeout = timeout
        self._is_available = None  # Cache du statut de disponibilité
    
    async def check_health(self) -> bool:
        """
        Vérifie si l'API RAG est accessible.
        
        Returns:
            True si l'API est accessible, False sinon
        """
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.api_url}/")
                self._is_available = response.status_code == 200
                return self._is_available
        except Exception as e:
            logger.warning(f"API RAG non accessible: {e}")
            self._is_available = False
            return False
    
    async def search_documents(
        self,
        query: str,
        n_results: int = DEFAULT_N_RESULTS,
        filter_metadata: Optional[dict] = None
    ) -> list[dict]:
        """
        Recherche des documents pertinents dans la Library.
        
        Args:
            query: Requête de recherche
            n_results: Nombre de résultats à retourner
            filter_metadata: Filtres optionnels sur les métadonnées
        
        Returns:
            Liste de documents avec leurs métadonnées et scores
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/rag/search",
                    json={
                        "query": query,
                        "n_results": n_results,
                        "filter_metadata": filter_metadata
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    logger.info(f"RAG search '{query}': {len(results)} résultats")
                    return results
                else:
                    logger.error(f"Erreur RAG search: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur lors de la recherche RAG: {e}")
            return []
    
    async def get_context(
        self,
        query: str,
        n_results: int = DEFAULT_N_RESULTS,
        filter_metadata: Optional[dict] = None
    ) -> str:
        """
        Récupère le contexte formaté pour une requête.
        
        Cette méthode est optimisée pour l'injection dans les prompts LLM.
        
        Args:
            query: Requête de recherche
            n_results: Nombre de résultats à inclure
            filter_metadata: Filtres optionnels sur les métadonnées
        
        Returns:
            Contexte formaté prêt à injecter dans un prompt
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/rag/context",
                    json={
                        "query": query,
                        "n_results": n_results,
                        "filter_metadata": filter_metadata
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    context = data.get("context", "")
                    context_length = data.get("context_length", 0)
                    logger.info(f"RAG context '{query}': {context_length} caractères")
                    return context
                else:
                    logger.error(f"Erreur RAG context: {response.status_code} - {response.text}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contexte RAG: {e}")
            return ""
    
    async def enrich_instruction(
        self,
        instruction: str,
        n_results: int = DEFAULT_N_RESULTS,
        filter_metadata: Optional[dict] = None
    ) -> str:
        """
        Enrichit une instruction avec du contexte Library pertinent.
        
        Args:
            instruction: Instruction originale
            n_results: Nombre de documents Library à inclure
            filter_metadata: Filtres optionnels (ex: {"agent": "CODEUR"})
        
        Returns:
            Instruction enrichie avec contexte Library
        """
        # Vérifier si l'API RAG est disponible
        if self._is_available is None:
            await self.check_health()
        
        if not self._is_available:
            logger.warning("API RAG non disponible, instruction non enrichie")
            return instruction
        
        # Récupérer le contexte
        context = await self.get_context(instruction, n_results, filter_metadata)
        
        if not context:
            logger.warning("Aucun contexte RAG trouvé, instruction non enrichie")
            return instruction
        
        # Formater l'instruction enrichie
        enriched = f"""{instruction}

---
CONTEXTE LIBRARY (pertinent pour cette tâche) :

{context}
---

Utilise le contexte Library ci-dessus pour respecter les standards et patterns recommandés.
"""
        
        logger.info(f"Instruction enrichie: {len(instruction)} → {len(enriched)} caractères")
        return enriched


# Instance globale du service RAG
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Retourne l'instance globale du service RAG.
    
    Returns:
        Instance de RAGService
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
