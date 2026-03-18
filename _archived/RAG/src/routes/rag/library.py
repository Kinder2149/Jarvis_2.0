"""
Routes pour lister les documents de la librairie RAG.
"""

import os
import logging
from pathlib import Path
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

# Créer le blueprint pour les routes de librairie
library_bp = Blueprint('rag_library', __name__)


@library_bp.route('/library/list', methods=['GET'])
def list_library_documents():
    """
    Liste tous les documents disponibles dans la librairie RAG.
    
    Scanne le dossier library/ et retourne la liste des fichiers
    organisés par catégorie (patterns, rules, templates).
    
    Returns:
        JSON avec la liste des documents
    """
    try:
        # Chemin vers la librairie RAG
        rag_root = Path(__file__).parent.parent.parent.parent
        library_path = rag_root / 'library'
        
        if not library_path.exists():
            return jsonify({
                "status": "error",
                "message": "Dossier library/ non trouvé"
            }), 404
        
        documents = []
        
        # Scanner les sous-dossiers (patterns, rules, templates)
        for category_dir in library_path.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith('.'):
                continue
            
            category = category_dir.name
            
            # Scanner les fichiers dans chaque catégorie
            for file_path in category_dir.iterdir():
                if file_path.is_file() and file_path.suffix in ['.md', '.txt']:
                    try:
                        # Lire le contenu du fichier
                        content = file_path.read_text(encoding='utf-8')
                        
                        # Extraire titre et description depuis le contenu
                        lines = content.split('\n')
                        title = file_path.stem.replace('_', ' ').title()
                        description = ""
                        
                        # Chercher le premier paragraphe non vide comme description
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                description = line[:200]  # Max 200 chars
                                break
                        
                        documents.append({
                            "name": file_path.stem,
                            "title": title,
                            "category": category,
                            "description": description,
                            "file_path": str(file_path.relative_to(library_path)),
                            "size": file_path.stat().st_size,
                            "extension": file_path.suffix
                        })
                    except Exception as e:
                        logger.warning(f"Erreur lecture fichier {file_path}: {e}")
                        continue
        
        # Grouper par catégorie
        categories = {}
        for doc in documents:
            cat = doc['category']
            if cat not in categories:
                categories[cat] = {
                    "name": cat.capitalize(),
                    "count": 0,
                    "documents": []
                }
            categories[cat]['documents'].append(doc)
            categories[cat]['count'] += 1
        
        return jsonify({
            "status": "success",
            "total_documents": len(documents),
            "categories": list(categories.values()),
            "documents": documents
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors du listing de la librairie: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@library_bp.route('/library/document/<category>/<name>', methods=['GET'])
def get_library_document(category: str, name: str):
    """
    Récupère le contenu complet d'un document de la librairie.
    
    Args:
        category: Catégorie du document (patterns, rules, templates)
        name: Nom du document (sans extension)
    
    Returns:
        JSON avec le contenu du document
    """
    try:
        # Chemin vers la librairie RAG
        rag_root = Path(__file__).parent.parent.parent.parent
        library_path = rag_root / 'library' / category
        
        if not library_path.exists():
            return jsonify({
                "status": "error",
                "message": f"Catégorie '{category}' non trouvée"
            }), 404
        
        # Chercher le fichier (essayer .md puis .txt)
        file_path = None
        for ext in ['.md', '.txt']:
            candidate = library_path / f"{name}{ext}"
            if candidate.exists():
                file_path = candidate
                break
        
        if not file_path:
            return jsonify({
                "status": "error",
                "message": f"Document '{name}' non trouvé dans '{category}'"
            }), 404
        
        # Lire le contenu
        content = file_path.read_text(encoding='utf-8')
        
        return jsonify({
            "status": "success",
            "document": {
                "name": name,
                "category": category,
                "content": content,
                "size": file_path.stat().st_size,
                "extension": file_path.suffix
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du document: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
