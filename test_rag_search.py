"""Test simple de recherche RAG."""
import requests
import json

RAG_API_URL = "http://localhost:5001"

def test_search():
    """Test recherche sémantique."""
    response = requests.post(
        f"{RAG_API_URL}/rag/search",
        json={
            "query": "comment créer une API web avec Python",
            "n_results": 3
        },
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        print(f"\n✅ {len(results)} résultats trouvés")
        for i, result in enumerate(results, 1):
            print(f"\n--- Résultat {i} ---")
            print(f"Source: {result.get('metadata', {}).get('source', 'N/A')}")
            print(f"Distance: {result.get('distance', 'N/A'):.4f}")
            print(f"Contenu: {result.get('document', '')[:200]}...")
    else:
        print(f"❌ Erreur: {response.text}")

if __name__ == "__main__":
    test_search()
