@echo off
REM Fix 2026-04-16 : Lancement uvicorn avec --reload + ouverture navigateur
REM Problème résolu : fenêtre CMD ne se fermait pas (start /B retiré), --reload ajouté, pause finale
REM Utilise python -m uvicorn pour compatibilité PATH Windows
echo Demarrage de JARVIS...
start /min python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
timeout /t 2 /nobreak > nul
start http://localhost:8000
echo JARVIS est pret sur http://localhost:8000
echo.
echo Appuyez sur une touche pour arreter le serveur...
pause > nul
