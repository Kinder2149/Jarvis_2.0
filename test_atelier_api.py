import httpx
import json

base = "http://localhost:8000/api/atelier"
results = {}

print("=== TEST ATELIER API ===\n")

# Test 2 — GET /prospects → []
try:
    r = httpx.get(f"{base}/prospects", timeout=5)
    results["test_2_get_prospects"] = {"status": r.status_code, "data": r.json()}
    print(f"✅ Test 2 — GET /prospects → {r.status_code}")
    print(f"   Data: {r.json()}\n")
except Exception as e:
    results["test_2_get_prospects"] = {"error": str(e)}
    print(f"❌ Test 2 — Erreur: {e}\n")

# Test 3 — POST /prospects
try:
    payload = {"nom": "Test Restaurant", "categorie": "restauration", "url": "https://example.com"}
    r = httpx.post(f"{base}/prospects", json=payload, timeout=5)
    results["test_3_create_prospect"] = {"status": r.status_code, "data": r.json()}
    prospect_id = r.json().get("id")
    print(f"✅ Test 3 — POST /prospects → {r.status_code}")
    print(f"   Data: {r.json()}\n")
except Exception as e:
    results["test_3_create_prospect"] = {"error": str(e)}
    print(f"❌ Test 3 — Erreur: {e}\n")
    prospect_id = None

# Test 4 — GET /prospects/{id}
if prospect_id:
    try:
        r = httpx.get(f"{base}/prospects/{prospect_id}", timeout=5)
        results["test_4_get_prospect"] = {"status": r.status_code, "data": r.json()}
        print(f"✅ Test 4 — GET /prospects/{prospect_id} → {r.status_code}")
        print(f"   Data: {r.json()}\n")
    except Exception as e:
        results["test_4_get_prospect"] = {"error": str(e)}
        print(f"❌ Test 4 — Erreur: {e}\n")

# Test 5 — PATCH /prospects/{id}
if prospect_id:
    try:
        payload = {"statut": "contacté"}
        r = httpx.patch(f"{base}/prospects/{prospect_id}", json=payload, timeout=5)
        results["test_5_update_prospect"] = {"status": r.status_code, "data": r.json()}
        print(f"✅ Test 5 — PATCH /prospects/{prospect_id} → {r.status_code}")
        print(f"   Statut: {r.json().get('statut')}\n")
    except Exception as e:
        results["test_5_update_prospect"] = {"error": str(e)}
        print(f"❌ Test 5 — Erreur: {e}\n")

# Test 6 — POST /prospects/{id}/start
if prospect_id:
    try:
        r = httpx.post(f"{base}/prospects/{prospect_id}/start", timeout=10)
        results["test_6_start_pipeline"] = {"status": r.status_code, "data": r.json()}
        session_id = r.json().get("session_id")
        print(f"✅ Test 6 — POST /prospects/{prospect_id}/start → {r.status_code}")
        print(f"   Session ID: {session_id}\n")
        
        # Vérifier la session
        if session_id:
            r_session = httpx.get(f"http://localhost:8000/api/pipelines/{session_id}", timeout=5)
            print(f"   GET /pipelines/{session_id} → {r_session.status_code}")
            session_data = r_session.json()
            print(f"   Steps count: {len(session_data.get('steps', []))}")
            if session_data.get('steps'):
                first_step = session_data['steps'][0]
                print(f"   Step 0 status: {first_step.get('status')}\n")
    except Exception as e:
        results["test_6_start_pipeline"] = {"error": str(e)}
        print(f"❌ Test 6 — Erreur: {e}\n")

# Test 8 — DELETE /prospects/{id}
if prospect_id:
    try:
        r = httpx.delete(f"{base}/prospects/{prospect_id}", timeout=5)
        results["test_8_delete_prospect"] = {"status": r.status_code}
        print(f"✅ Test 8 — DELETE /prospects/{prospect_id} → {r.status_code}\n")
    except Exception as e:
        results["test_8_delete_prospect"] = {"error": str(e)}
        print(f"❌ Test 8 — Erreur: {e}\n")

print("\n=== RÉSUMÉ ===")
print(json.dumps(results, indent=2))
