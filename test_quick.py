import httpx

# Test si le serveur répond
r = httpx.get("http://localhost:8000/api/projects/", timeout=5)
print(f"GET /api/projects/ → {r.status_code}")

# Test la route atelier
r2 = httpx.get("http://localhost:8000/api/atelier/prospects", timeout=5)
print(f"GET /api/atelier/prospects → {r2.status_code}")
if r2.status_code != 200:
    print(f"   Error: {r2.text}")
