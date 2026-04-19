import httpx
import json

base = "http://localhost:8000"
results = {}

try:
    # Health
    r = httpx.get(f"{base}/docs", timeout=5)
    results["docs"] = r.status_code
    
    # Projects
    r = httpx.get(f"{base}/api/projects/", timeout=5)
    results["projects_list"] = r.status_code
    projects = r.json() if r.status_code == 200 else []
    
    # Config (clés API)
    r = httpx.get(f"{base}/api/config/", timeout=5)
    results["config_get"] = r.status_code
    
    # Models
    r = httpx.get(f"{base}/api/config/models/available", timeout=5)
    results["models_list"] = r.status_code
    
    # Conversations
    r = httpx.get(f"{base}/api/chat/conversations/", timeout=5)
    results["convs_list"] = r.status_code
    
except Exception as e:
    results["error"] = str(e)

print(json.dumps(results, indent=2))
