"""
Tests automatisés frontend V1 - JARVIS
Vérifie la cohérence, les chemins et la validité des pages frontend.
"""

import asyncio
from playwright.async_api import async_playwright, expect
import sys


BASE_URL = "http://localhost:8000"


async def test_index_page():
    """Test page index.html - Module Projets"""
    print("\n🧪 Test 1/5 : Page index.html (Module Projets)")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            # Charger la page
            await page.goto(f"{BASE_URL}/app/index.html")
            await page.wait_for_load_state("networkidle")
            
            # Vérifier titre
            title = await page.title()
            assert "JARVIS" in title, f"Titre incorrect: {title}"
            
            # Vérifier header
            header = await page.locator(".header h1").text_content()
            assert "JARVIS" in header, "Header manquant"
            
            # Vérifier module header
            module_header = await page.locator(".module-header h2").text_content()
            assert "Module Projets" in module_header, "Module header manquant"
            
            # Vérifier bouton Chat
            chat_btn = page.locator('a[href="/app/chat.html"]')
            await expect(chat_btn).to_be_visible()
            
            # Vérifier bouton Paramètres
            settings_btn = page.locator('a[href="/app/settings.html"]')
            await expect(settings_btn).to_be_visible()
            
            # Vérifier bouton Ajouter projet
            add_btn = page.locator('button:has-text("Ajouter un projet")')
            await expect(add_btn).to_be_visible()
            
            # Vérifier grid projets
            grid = page.locator("#projects-grid")
            await expect(grid).to_be_visible()
            
            print("   ✅ Titre, header, module header présents")
            print("   ✅ Boutons navigation présents")
            print("   ✅ Grid projets présente")
            
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            await browser.close()
            return False
        
        await browser.close()
        return True


async def test_chat_page():
    """Test page chat.html - Module Chat"""
    print("\n🧪 Test 2/5 : Page chat.html (Module Chat)")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            # Charger la page
            await page.goto(f"{BASE_URL}/app/chat.html")
            await page.wait_for_load_state("networkidle")
            
            # Vérifier titre
            title = await page.title()
            assert "Chat" in title, f"Titre incorrect: {title}"
            
            # Vérifier header avec module
            module_text = await page.locator(".header").text_content()
            assert "Module Chat" in module_text, "Module Chat manquant dans header"
            
            # Vérifier lien retour JARVIS
            back_link = page.locator('a[href="/app/index.html"]')
            await expect(back_link).to_be_visible()
            
            # Vérifier sidebar
            sidebar = page.locator(".chat-sidebar")
            await expect(sidebar).to_be_visible()
            
            # Vérifier bouton nouvelle conversation
            new_conv_btn = page.locator('button:has-text("Nouvelle conversation")')
            await expect(new_conv_btn).to_be_visible()
            
            # Vérifier zone messages
            messages = page.locator("#chat-messages")
            await expect(messages).to_be_visible()
            
            # Vérifier textarea input
            chat_input = page.locator("#chat-input")
            await expect(chat_input).to_be_visible()
            
            # Vérifier bouton envoyer
            send_btn = page.locator('button:has-text("Envoyer")')
            await expect(send_btn).to_be_visible()
            
            print("   ✅ Titre, header module présents")
            print("   ✅ Sidebar et bouton nouvelle conversation présents")
            print("   ✅ Zone messages et input présents")
            
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            await browser.close()
            return False
        
        await browser.close()
        return True


async def test_project_page():
    """Test page project.html - Modules Missions/Chat"""
    print("\n🧪 Test 3/5 : Page project.html (Modules Missions/Chat)")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            # Charger la page (sans projet, juste structure)
            await page.goto(f"{BASE_URL}/app/project.html?id=999")
            await page.wait_for_load_state("networkidle")
            
            # Vérifier titre
            title = await page.title()
            assert "Projet" in title, f"Titre incorrect: {title}"
            
            # Vérifier header
            header = await page.locator(".header h1").text_content()
            assert "JARVIS" in header, "Header manquant"
            
            # Vérifier onglets avec icônes
            tabs = await page.locator(".tabs .tab").all_text_contents()
            assert any("Contexte" in t for t in tabs), "Onglet Contexte manquant"
            assert any("Missions" in t for t in tabs), "Onglet Missions manquant"
            assert any("Chat" in t for t in tabs), "Onglet Chat manquant"
            assert any("CHANGELOG" in t for t in tabs), "Onglet CHANGELOG manquant"
            assert any("BACKLOG" in t for t in tabs), "Onglet BACKLOG manquant"
            assert any("SESSIONS" in t for t in tabs), "Onglet SESSIONS manquant"
            
            # Vérifier icônes dans onglets
            missions_tab = page.locator('.tab:has-text("Missions")')
            missions_text = await missions_tab.text_content()
            assert "🎯" in missions_text, "Icône Missions manquante"
            
            chat_tab = page.locator('.tab:has-text("Chat")')
            chat_text = await chat_tab.text_content()
            assert "💬" in chat_text, "Icône Chat manquante"
            
            # Vérifier boutons actions
            actions = page.locator("#actions-buttons")
            await expect(actions).to_be_visible()
            
            print("   ✅ Titre, header présents")
            print("   ✅ 6 onglets présents avec icônes")
            print("   ✅ Boutons actions présents")
            
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            await browser.close()
            return False
        
        await browser.close()
        return True


async def test_navigation_links():
    """Test cohérence des liens de navigation"""
    print("\n🧪 Test 4/5 : Cohérence des liens de navigation")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            # Test navigation depuis index
            await page.goto(f"{BASE_URL}/app/index.html")
            await page.wait_for_load_state("networkidle")
            
            # Clic sur Chat
            await page.click('a[href="/app/chat.html"]')
            await page.wait_for_load_state("networkidle")
            assert "chat.html" in page.url, "Navigation vers Chat échouée"
            
            # Retour à index
            await page.click('a[href="/app/index.html"]')
            await page.wait_for_load_state("networkidle")
            assert "index.html" in page.url, "Retour à index échoué"
            
            # Navigation vers settings
            await page.click('a[href="/app/settings.html"]')
            await page.wait_for_load_state("networkidle")
            assert "settings.html" in page.url, "Navigation vers Settings échouée"
            
            print("   ✅ Navigation index → chat → index fonctionne")
            print("   ✅ Navigation index → settings fonctionne")
            
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            await browser.close()
            return False
        
        await browser.close()
        return True


async def test_css_loading():
    """Test chargement CSS et cohérence visuelle"""
    print("\n🧪 Test 5/5 : Chargement CSS et cohérence visuelle")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            # Charger index
            await page.goto(f"{BASE_URL}/app/index.html")
            await page.wait_for_load_state("networkidle")
            
            # Vérifier que le CSS est chargé (background-color du body)
            bg_color = await page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor")
            assert bg_color != "rgba(0, 0, 0, 0)", "CSS non chargé (background transparent)"
            
            # Vérifier variables CSS
            accent_color = await page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--accent')")
            assert accent_color.strip() != "", "Variable CSS --accent manquante"
            
            # Vérifier que les boutons ont le bon style
            btn = page.locator(".btn-primary").first
            btn_bg = await btn.evaluate("el => getComputedStyle(el).backgroundColor")
            assert btn_bg != "rgba(0, 0, 0, 0)", "Bouton sans style"
            
            print("   ✅ CSS chargé correctement")
            print("   ✅ Variables CSS présentes")
            print("   ✅ Styles boutons appliqués")
            
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            await browser.close()
            return False
        
        await browser.close()
        return True


async def main():
    """Exécute tous les tests"""
    print("=" * 60)
    print("🚀 TESTS AUTOMATISÉS FRONTEND V1 - JARVIS")
    print("=" * 60)
    
    results = []
    
    # Exécuter les tests
    results.append(await test_index_page())
    results.append(await test_chat_page())
    results.append(await test_project_page())
    results.append(await test_navigation_links())
    results.append(await test_css_loading())
    
    # Rapport final
    print("\n" + "=" * 60)
    print("📊 RAPPORT FINAL")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Tests réussis : {passed}/{total}")
    print(f"❌ Tests échoués : {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 TOUS LES TESTS PASSENT - Frontend V1 validé !")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué - Vérifier les erreurs ci-dessus")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
