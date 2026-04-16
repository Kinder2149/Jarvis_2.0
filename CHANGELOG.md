# CHANGELOG — JARVIS

| Date | Mission | Description | Fichiers |
|------|---------|-------------|----------|
| 2026-04-16 | Module chat enrichi backend | Lecture dossier local (folder_path nullable, h\u00e9ritage projet, read_local_folder, read_local_file, s\u00e9curit\u00e9 path traversal, GRAPH_REPORT prioritaire). Recherche web (search_web via Brave API, d\u00e9tection auto, d\u00e9sactivation gracieuse). 159/159 tests. | database.py, chat_service.py, chat.py, config.py, tests/ |
| 2026-04-16 | Clôture module chat | Fix start.bat (lancement uvicorn + navigateur fonctionnel). Confirmation project_id nullable sur conversations (déjà implémenté). 142/142 tests passent. | start.bat |
| 2026-04-16 | Module chat | Backend complet (chat_service.py, routers/chat.py, 2 tables DB). Frontend complet (chat.html, settings section, styles). System prompt JARVIS défini. METHODO injectée via JARVIS_INDEX.md. 142/142 tests. | database.py, chat_service.py, chat.py, chat.html, settings.html, style.css, index.html, tests/ |
| 2026-04-16 | Méthode JARVIS documentée | GUIDE.md, REGLES_GLOBALES.md, REGLES_CASCADE_SETTINGS.md mis à jour. JARVIS = outil principal, Cascade = fallback. JARVIS_INDEX.md créé. | METHODO/ |
| 2026-04-16 | Validation module code — P1 | 5 missions robustesse : erreurs API lisibles, logs jarvis.log + endpoint /logs, parsing apply_files 3 fallbacks, rollback atomique, architecture context_manager respectée. 120/120 tests. | model_router.py, main.py, pipelines.py, pipeline.html, file_service.py, context_manager.py, pipeline_engine.py, tests/ |
| 2026-04-16 | Tests et prompts P1 | 6 workflows testés live, 25 prompts audités et corrigés (JSON pur + format bloc code), tests live session_end/mission_complexe/nouveau_projet/projet_existant | prompts.json, tests/live/ |
| 2026-04-15 | Session validation complète | Roadmap modèles 6 slugs validés live, 95 tests (unitaires + intégration), plans METHODO + JARVIS formalisés, 5 prompts Cascade exécutés | config.json, models.py, settings.html, tests/ |
| 2026-04-15 | MVP JARVIS | Création complète MVP en 5 phases : backend + frontend + 6 workflows | 27 fichiers créés |
| 2026-04-15 | Corrections frontend | Fix clés API masquées + phase bar + mode édition + bannière session + tabs BACKLOG/SESSIONS | settings.html, pipeline.html, project.html, projects.py, style.css |
| 2026-04-15 | Initialisation méthode | PROJET_CONTEXTE.md créé, .gitignore ajouté | .gitignore, PROJET_CONTEXTE.md, config.example.json |
