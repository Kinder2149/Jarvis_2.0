"""
Client pour interroger le serveur RAG
"""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RAGClient:
    """Client pour interroger le serveur RAG."""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
    
    async def search(self, query: str, top_k: int = 3) -> str:
        """
        Recherche patterns/exemples dans la librairie RAG.
        
        Args:
            query: Requête (ex: "pattern CRUD Python")
            top_k: Nombre de résultats
        
        Returns:
            Contexte enrichi (patterns, exemples)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json={"query": query, "top_k": top_k},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    context = "\n\n".join([
                        f"=== {r['source']} ===\n{r['content']}"
                        for r in results.get("results", [])
                    ])
                    logger.info(f"RAG: {len(results.get('results', []))} résultats trouvés")
                    return context
                else:
                    logger.warning(f"RAG: Erreur {response.status_code}")
                    return ""
        except httpx.TimeoutException:
            logger.error("RAG: Timeout (10s)")
            return ""
        except httpx.ConnectError:
            logger.error("RAG: Serveur non accessible (port 5001)")
            return ""
        except Exception as e:
            logger.error(f"RAG: Erreur connexion - {e}")
            return ""
    
    async def health_check(self) -> bool:
        """
        Vérifie si le serveur RAG est accessible.
        
        Returns:
            True si accessible, False sinon
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception:
            return False
