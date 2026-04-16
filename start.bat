@echo off
REM Fix 2026-04-16 : Lancement uvicorn avec --reload + ouverture navigateur
REM Problème résolu : fenêtre CMD ne se fermait pas (start /B retiré), --reload ajouté, pause finale
echo Demarrage de JARVIS...
start /min uvicorn backend.main:app --reload --port 8000
timeout /t 2 /nobreak > nul
start http://localhost:8000/app/index.html
echo JARVIS est pret sur http://localhost:8000/app/index.html
echo.
echo Appuyez sur une touche pour arreter le serveur...
pause > nul
