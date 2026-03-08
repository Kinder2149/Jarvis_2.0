"""
Script d'intégration des 5 documents CONFIG dans library_seed.json
Automatise l'ajout avec échappement JSON correct
"""

import json
from pathlib import Path

# Chemins
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "docs" / "JARVIS CONFIG"
LIBRARY_SEED = PROJECT_ROOT / "backend" / "db" / "library_seed.json"

# Documents CONFIG à intégrer
CONFIG_DOCS = [
    {
        "file": "KEAMDER_PROFILE.md",
        "name": "KEAMDER_PROFILE",
        "icon": "👤",
        "description": "Profil complet de Keamder — Pilote de projet IA 100%",
        "tags": ["keamder", "profile", "context", "personal"],
        "agents": ["JARVIS_Maitre", "BASE"]
    },
    {
        "file": "KEAMDER_WORKFLOW.md",
        "name": "KEAMDER_WORKFLOW",
        "icon": "⚙️",
        "description": "Méthodologie de travail de Keamder — Workflow 5 phases",
        "tags": ["keamder", "workflow", "methodology", "personal"],
        "agents": ["JARVIS_Maitre", "BASE"]
    },
    {
        "file": "JARVIS_ARCHITECTURE.md",
        "name": "JARVIS_ARCHITECTURE",
        "icon": "🏗️",
        "description": "Architecture JARVIS 2.0 — 4 agents, orchestration, stack",
        "tags": ["jarvis", "architecture", "agents", "personal"],
        "agents": ["JARVIS_Maitre", "BASE"]
    },
    {
        "file": "KEAMDER_DEV_RULES.md",
        "name": "KEAMDER_DEV_RULES",
        "icon": "📜",
        "description": "Règles d'orchestration pour IA — Validation obligatoire, pas d'invention",
        "tags": ["keamder", "rules", "orchestration", "personal"],
        "agents": ["JARVIS_Maitre", "CODEUR", "BASE"]
    },
    {
        "file": "JARVIS_COMPORTEMENT_GENERIQUE.md",
        "name": "JARVIS_COMPORTEMENT_GENERIQUE",
        "icon": "🤖",
        "description": "Comportement générique JARVIS — Workflow 6 phases, communication adaptée",
        "tags": ["jarvis", "behavior", "workflow", "personal"],
        "agents": ["JARVIS_Maitre", "BASE"]
    }
]

def main():
    print("🔄 Intégration des documents CONFIG dans library_seed.json...")
    
    # Lire library_seed.json existant
    with open(LIBRARY_SEED, 'r', encoding='utf-8') as f:
        library = json.load(f)
    
    print(f"✅ Library actuelle : {len(library)} documents")
    
    # Vérifier si documents CONFIG déjà présents
    existing_names = {doc["name"] for doc in library}
    
    # Intégrer chaque document CONFIG
    added = 0
    updated = 0
    
    for config_doc in CONFIG_DOCS:
        file_path = CONFIG_DIR / config_doc["file"]
        
        if not file_path.exists():
            print(f"❌ Fichier non trouvé : {config_doc['file']}")
            continue
        
        # Lire contenu du fichier
        content = file_path.read_text(encoding='utf-8')
        
        # Créer entrée library
        entry = {
            "category": "personal",
            "name": config_doc["name"],
            "icon": config_doc["icon"],
            "description": config_doc["description"],
            "tags": config_doc["tags"],
            "agents": config_doc["agents"],
            "content": content
        }
        
        # Vérifier si déjà présent
        if config_doc["name"] in existing_names:
            # Mettre à jour
            for i, doc in enumerate(library):
                if doc["name"] == config_doc["name"]:
                    library[i] = entry
                    updated += 1
                    print(f"🔄 Mis à jour : {config_doc['name']}")
                    break
        else:
            # Ajouter
            library.append(entry)
            added += 1
            print(f"✅ Ajouté : {config_doc['name']}")
    
    # Sauvegarder library_seed.json
    with open(LIBRARY_SEED, 'w', encoding='utf-8') as f:
        json.dump(library, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Intégration terminée !")
    print(f"   - Documents ajoutés : {added}")
    print(f"   - Documents mis à jour : {updated}")
    print(f"   - Total documents : {len(library)}")

if __name__ == "__main__":
    main()
