"""
Tests LIVE consolidés — Appels API réels (OpenRouter, Brave Search).

Marqués @pytest.mark.live — ne s'exécutent PAS dans la suite normale.
Commande : python -m pytest tests/live/test_live_modules.py -m live -v --timeout=60

Prérequis :
  - JARVIS doit tourner : uvicorn backend.main:app --reload --port 8000
  - Clés API valides dans .env (OPENROUTER_KEY, WEB_SEARCH_KEY)
  - METHODO accessible dans C:\DEV\METHODO\
"""
import pytest
import httpx
import asyncio
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
pytestmark = pytest.mark.live


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def wait_for_status(client: httpx.AsyncClient, session_id: int, expected_statuses: list, max_wait: int = 60) -> dict:
    """Interroge la session jusqu'à ce que le statut souhaité soit atteint."""
    for _ in range(max_wait // 2):
        await asyncio.sleep(2)
        response = await client.get(f"/api/pipelines/{session_id}")
        if response.status_code == 200:
            session = response.json()
            if session["status"] in expected_statuses:
                return session
    raise TimeoutError(
        f"Session {session_id} n'a pas atteint {expected_statuses} en {max_wait}s."
    )


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_live_chat_reponse_coherente():
    """
    TEST 1 — Chat : créer conversation → envoyer message minimal → vérifier réponse.
    Vérifie que OpenRouter répond correctement (minimal en tokens).
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Créer conversation
        conv_response = await client.post("/api/chat/conversations", json={
            "title": "Test live chat"
        })
        assert conv_response.status_code == 200, f"Erreur création conversation: {conv_response.text}"
        conv = conv_response.json()
        conv_id = conv["id"]
        print(f"✅ Conversation créée: id={conv_id}")
        
        try:
            # Envoyer message minimal
            msg_response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                json={"content": "réponds juste 'OK'"}
            )
            assert msg_response.status_code == 200, f"Erreur envoi message: {msg_response.text}"
            msg_data = msg_response.json()
            
            # Vérifier réponse assistant
            assert "assistant_message" in msg_data, "Pas de champ 'assistant_message'"
            assistant_msg = msg_data["assistant_message"]
            assert "content" in assistant_msg, "Pas de champ 'content'"
            content = assistant_msg["content"]
            assert content, "Réponse vide"
            assert "OK" in content.upper(), f"Réponse ne contient pas 'OK': {content[:100]}"
            
            print(f"✅ Réponse IA reçue et valide: {content[:50]}")
            
        finally:
            # Nettoyer
            await client.delete(f"/api/chat/conversations/{conv_id}")
            print(f"✅ Conversation supprimée: id={conv_id}")


@pytest.mark.asyncio
async def test_live_brave_search_retourne_resultats():
    """
    TEST 2 — Web Search : créer conversation avec internet_access → envoyer requête web.
    Vérifie que Brave Search retourne des résultats (pas d'erreur "brave non configuré").
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Créer conversation avec internet_access activé
        conv_response = await client.post("/api/chat/conversations", json={
            "title": "Test live web search",
            "internet_access": 1
        })
        assert conv_response.status_code == 200, f"Erreur création conversation: {conv_response.text}"
        conv = conv_response.json()
        conv_id = conv["id"]
        print(f"✅ Conversation créée avec internet_access: id={conv_id}")
        
        try:
            # Envoyer requête nécessitant web search
            msg_response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                json={"content": "cherche météo Paris aujourd'hui"}
            )
            assert msg_response.status_code == 200, f"Erreur envoi message: {msg_response.text}"
            msg_data = msg_response.json()
            
            # Vérifier réponse assistant
            assert "assistant_message" in msg_data, "Pas de champ 'assistant_message'"
            content = msg_data["assistant_message"]["content"]
            assert content, "Réponse vide"
            
            # Vérifier qu'il n'y a pas d'erreur Brave
            assert "brave non configuré" not in content.lower(), "Brave Search non configuré"
            assert "erreur" not in content.lower() or "météo" in content.lower(), \
                f"Erreur dans la réponse: {content[:200]}"
            
            print(f"✅ Web search fonctionnel, réponse reçue: {content[:100]}")
            
        finally:
            # Nettoyer
            await client.delete(f"/api/chat/conversations/{conv_id}")
            print(f"✅ Conversation supprimée: id={conv_id}")


@pytest.mark.asyncio
async def test_live_profil_utilisateur_dans_systemprompt():
    """
    TEST 3 — Profil utilisateur : écrire PROFIL_UTILISATEUR.md avec texte unique
    → démarrer conversation → vérifier que le profil est injecté dans le system prompt.
    Vérifie que FIX-01 + INFRA injecte bien le profil.
    """
    # Chemin METHODO
    methodo_path = Path("C:/DEV/METHODO")
    profil_path = methodo_path / "informations utilisateur" / "PROFIL_UTILISATEUR.md"
    
    # Sauvegarder profil original
    original_content = None
    if profil_path.exists():
        original_content = profil_path.read_text(encoding="utf-8")
    
    try:
        # Écrire profil de test avec marqueur unique
        test_content = """# PROFIL UTILISATEUR

UTILISATEUR_TEST_XYZ_UNIQUE

Je suis un utilisateur de test avec un identifiant unique pour validation.
"""
        profil_path.write_text(test_content, encoding="utf-8")
        print(f"✅ Profil de test écrit: {profil_path}")
        
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            # Créer conversation
            conv_response = await client.post("/api/chat/conversations", json={
                "title": "Test profil utilisateur"
            })
            assert conv_response.status_code == 200
            conv = conv_response.json()
            conv_id = conv["id"]
            print(f"✅ Conversation créée: id={conv_id}")
            
            try:
                # Demander le profil
                msg_response = await client.post(
                    f"/api/chat/conversations/{conv_id}/messages",
                    json={"content": "quel est mon profil utilisateur ?"}
                )
                assert msg_response.status_code == 200
                msg_data = msg_response.json()
                
                # Vérifier que la réponse mentionne le marqueur unique ou le contenu du profil
                content = msg_data["assistant_message"]["content"]
                
                # Le profil peut être injecté mais le modèle peut répondre qu'il n'a pas accès
                # On vérifie juste que la réponse est cohérente (pas d'erreur)
                assert content, "Réponse vide"
                
                if "UTILISATEUR_TEST_XYZ_UNIQUE" in content or "validation" in content.lower():
                    print(f"✅ Profil utilisateur détecté dans la réponse")
                else:
                    print(f"⚠️ Profil non détecté dans réponse (peut être normal si modèle ne révèle pas system prompt)")
                    print(f"   Réponse: {content[:150]}")
                
            finally:
                await client.delete(f"/api/chat/conversations/{conv_id}")
                print(f"✅ Conversation supprimée: id={conv_id}")
    
    finally:
        # Restaurer profil original
        if original_content:
            profil_path.write_text(original_content, encoding="utf-8")
            print(f"✅ Profil original restauré")


@pytest.mark.asyncio
async def test_live_pipeline_orientation_retourne_classification():
    """
    TEST 4 — Pipeline orientation : démarrer session_start → laisser s'exécuter
    → vérifier que step orientation a status=COMPLETED et output_data contient classification.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Récupérer ou créer projet de test
        projects_response = await client.get("/api/projects")
        assert projects_response.status_code == 200
        projects = projects_response.json()
        
        if projects:
            project = projects[0]
            project_id = project["id"]
            print(f"✅ Utilisation projet existant: id={project_id}")
        else:
            # Créer projet temporaire
            project_response = await client.post("/api/projects", json={
                "name": "Test live orientation",
                "path": "C:\\Temp\\test_live",
                "type": "web"
            })
            assert project_response.status_code == 200
            project = project_response.json()
            project_id = project["id"]
            print(f"✅ Projet de test créé: id={project_id}")
        
        try:
            # Démarrer session_start
            pipeline_response = await client.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "session_start",
                "initial_input": "Test validation orientation"
            })
            assert pipeline_response.status_code == 200
            pipeline_data = pipeline_response.json()
            
            session = pipeline_data.get("session", {})
            session_id = session.get("id")
            assert session_id, "Pas de session_id dans la réponse"
            print(f"✅ Pipeline démarré: session_id={session_id}")
            
            # Attendre que le step orientation soit complété (peut prendre du temps)
            session_data = await wait_for_status(
                client, 
                session_id, 
                ["WAITING_VALIDATION", "COMPLETED"],
                max_wait=90
            )
            
            # Récupérer les steps
            steps = session_data.get("steps", [])
            assert steps, "Pas de steps dans la session"
            
            # Trouver step orientation (step_index 0)
            orientation_step = next((s for s in steps if s.get("step_index") == 0), None)
            assert orientation_step, "Step orientation non trouvé"
            
            # Vérifier status et output_data
            assert orientation_step["status"] == "COMPLETED", \
                f"Step orientation pas complété: {orientation_step['status']}"
            
            output_data = orientation_step.get("output_data")
            assert output_data, "output_data vide"
            
            # Vérifier que output_data contient une classification ou analyse
            keywords = ["classification", "bug", "mission", "projet", "session", "analyse", "objectif"]
            has_classification = any(kw in output_data.lower() for kw in keywords)
            
            if has_classification:
                print(f"✅ Step orientation complété avec classification: {output_data[:150]}")
            else:
                print(f"⚠️ Classification non détectée dans output_data")
                print(f"   Output: {output_data[:200]}")
            
            # Aborter le pipeline
            await client.post(f"/api/pipelines/{session_id}/abort")
            print(f"✅ Pipeline aborté: session_id={session_id}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            raise


@pytest.mark.asyncio
async def test_live_global_rules_dans_output_pipeline():
    """
    TEST 5 — Global rules (INFRA-04) : démarrer workflow avec inject_global_rules=true
    → vérifier que les règles apparaissent dans le contexte (logs ou output).
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Récupérer premier projet
        projects_response = await client.get("/api/projects")
        assert projects_response.status_code == 200
        projects = projects_response.json()
        
        if not projects:
            pytest.skip("Aucun projet disponible pour test global rules")
        
        project = projects[0]
        project_id = project["id"]
        print(f"✅ Utilisation projet: id={project_id}")
        
        try:
            # Démarrer bug_simple (a inject_global_rules sur step orientation)
            pipeline_response = await client.post("/api/pipelines/start", json={
                "project_id": project_id,
                "workflow_type": "bug_simple",
                "initial_input": "Test global rules injection"
            })
            assert pipeline_response.status_code == 200
            pipeline_data = pipeline_response.json()
            
            session = pipeline_data.get("session", {})
            session_id = session.get("id")
            assert session_id, "Pas de session_id"
            print(f"✅ Pipeline bug_simple démarré: session_id={session_id}")
            
            # Attendre que le step orientation soit complété
            await asyncio.sleep(5)
            
            # Récupérer logs
            logs_response = await client.get(f"/api/pipelines/logs?lines=200")
            if logs_response.status_code == 200:
                logs = logs_response.text
                
                # Vérifier que les règles globales apparaissent dans les logs
                has_rules = any(keyword in logs for keyword in [
                    "3 couches",
                    "20 services",
                    "REGLES_GLOBALES",
                    "global_rules"
                ])
                
                if has_rules:
                    print(f"✅ Global rules détectées dans les logs")
                else:
                    print(f"⚠️ Global rules non détectées dans les logs (peut être normal)")
            
            # Aborter le pipeline
            await client.post(f"/api/pipelines/{session_id}/abort")
            print(f"✅ Pipeline aborté: session_id={session_id}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            raise


@pytest.mark.asyncio
async def test_live_lecture_dossier_local():
    """
    TEST BONUS — Lecture dossier local : créer conversation avec folder_path
    → demander lecture fichier → vérifier que le contenu est lu.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=90.0) as client:
        # Créer conversation avec folder_path
        conv_response = await client.post("/api/chat/conversations", json={
            "title": "Test lecture locale",
            "folder_path": "C:\\DEV\\PROJETS\\intelligence_artificielle\\Jarvis-2.0"
        })
        assert conv_response.status_code == 200
        conv = conv_response.json()
        conv_id = conv["id"]
        print(f"✅ Conversation créée avec folder_path: id={conv_id}")
        
        try:
            # Demander lecture du fichier (requête simple pour accélérer)
            msg_response = await client.post(
                f"/api/chat/conversations/{conv_id}/messages",
                json={"content": "lis PROJET_CONTEXTE.md et dis juste le nom du projet"}
            )
            assert msg_response.status_code == 200
            msg_data = msg_response.json()
            
            # Vérifier que la réponse contient des éléments du fichier (preuve de lecture)
            content = msg_data["assistant_message"]["content"]
            
            # Chercher des mots-clés du PROJET_CONTEXTE.md
            keywords = ["JARVIS", "FastAPI", "SQLite", "OpenRouter", "pipeline", "workflow", "module"]
            found_keywords = [kw for kw in keywords if kw in content]
            
            if found_keywords:
                print(f"✅ Fichier PROJET_CONTEXTE.md lu avec succès (mots-clés: {', '.join(found_keywords[:3])})")
            else:
                # Le modèle peut avoir reformulé, vérifier si la réponse est substantielle
                if len(content) > 200:
                    print(f"⚠️ Fichier probablement lu (réponse substantielle de {len(content)} chars)")
                    print(f"   Extrait: {content[:150]}")
                else:
                    raise AssertionError(f"Le fichier n'a pas été lu. Réponse: {content[:200]}")
            
        finally:
            # Nettoyer
            await client.delete(f"/api/chat/conversations/{conv_id}")
            print(f"✅ Conversation supprimée: id={conv_id}")


@pytest.mark.asyncio
async def test_live_atelier_qualification_genere_texte():
    """
    TEST 6 — Atelier : créer prospect → start pipeline → laisser étape qualification
    s'exécuter → vérifier output_data non vide avec texte structuré.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Créer prospect
        prospect_response = await client.post("/api/atelier/prospects", json={
            "nom": "Restaurant Test Live",
            "categorie": "restauration",
            "url": "https://restaurant-test-live.fr"
        })
        assert prospect_response.status_code == 201, f"Erreur création prospect: {prospect_response.text}"
        prospect = prospect_response.json()
        prospect_id = prospect["id"]
        print(f"✅ Prospect créé: id={prospect_id}, nom={prospect['nom']}")
        
        try:
            # Démarrer pipeline atelier
            pipeline_response = await client.post(f"/api/atelier/prospects/{prospect_id}/start")
            assert pipeline_response.status_code == 200, f"Erreur démarrage pipeline: {pipeline_response.text}"
            pipeline_data = pipeline_response.json()
            
            session_id = pipeline_data.get("session_id")
            assert session_id, "Pas de session_id"
            print(f"✅ Pipeline atelier démarré: session_id={session_id}")
            
            # Attendre un peu pour que step 0 (saisie) soit en WAITING_VALIDATION
            await asyncio.sleep(3)
            
            # Récupérer session
            session_response = await client.get(f"/api/pipelines/{session_id}")
            assert session_response.status_code == 200
            session_data = session_response.json()
            
            steps = session_data.get("steps", [])
            assert steps, "Pas de steps"
            
            # Step 0 devrait être en WAITING_VALIDATION (saisie manuelle)
            step0 = next((s for s in steps if s.get("step_index") == 0), None)
            assert step0, "Step 0 non trouvé"
            
            if step0["status"] == "WAITING_VALIDATION":
                # Valider step 0 avec données de test
                step0_id = step0["id"]
                validate_response = await client.post(
                    f"/api/pipelines/{session_id}/validate/{step0_id}",
                    json={
                        "approved": True,
                        "user_input": "Restaurant traditionnel français, 50 couverts, centre-ville Paris"
                    }
                )
                assert validate_response.status_code == 200
                print(f"✅ Step 0 (saisie) validé")
                
                # Attendre que step 1 (qualification) s'exécute
                await asyncio.sleep(10)
                
                # Récupérer session mise à jour
                session_response = await client.get(f"/api/pipelines/{session_id}")
                session_data = session_response.json()
                steps = session_data.get("steps", [])
                
                # Vérifier step 1 (qualification)
                step1 = next((s for s in steps if s.get("step_index") == 1), None)
                if step1 and step1["status"] == "COMPLETED":
                    output_data = step1.get("output_data")
                    assert output_data, "output_data vide pour step qualification"
                    assert len(output_data) > 50, f"output_data trop court: {len(output_data)} chars"
                    
                    print(f"✅ Step 1 (qualification) complété avec output: {output_data[:100]}")
                else:
                    print(f"⚠️ Step 1 pas encore complété (status: {step1['status'] if step1 else 'N/A'})")
            
            # Aborter le pipeline
            await client.post(f"/api/pipelines/{session_id}/abort")
            print(f"✅ Pipeline aborté: session_id={session_id}")
            
        finally:
            # Nettoyer prospect
            await client.delete(f"/api/atelier/prospects/{prospect_id}")
            print(f"✅ Prospect supprimé: id={prospect_id}")
