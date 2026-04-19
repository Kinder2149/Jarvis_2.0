@echo off
cd ..
echo ========================================
echo   JARVIS V2 - Build Final
echo ========================================
echo.

echo Nettoyage builds precedents...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo.
echo Installation PyInstaller...
pip install pyinstaller --quiet

echo.
echo Compilation (--onedir, Python + dependances inclus)...
echo Cela peut prendre 3-5 minutes...
echo.

python -m PyInstaller ^
  --onedir ^
  --windowed ^
  --name JARVIS ^
  --icon=launcher\launcher.ico ^
  --add-data "frontend;frontend" ^
  --add-data "backend;backend" ^
  --add-data "requirements.txt;." ^
  --hidden-import=sqlite3 ^
  --hidden-import=httpx ^
  --hidden-import=fastapi ^
  --hidden-import=uvicorn ^
  --hidden-import=uvicorn.logging ^
  --hidden-import=uvicorn.loops ^
  --hidden-import=uvicorn.loops.auto ^
  --hidden-import=uvicorn.protocols ^
  --hidden-import=uvicorn.protocols.http ^
  --hidden-import=uvicorn.protocols.http.auto ^
  --hidden-import=uvicorn.protocols.websockets ^
  --hidden-import=uvicorn.protocols.websockets.auto ^
  --hidden-import=uvicorn.lifespan ^
  --hidden-import=uvicorn.lifespan.on ^
  --hidden-import=fastapi.middleware.cors ^
  --hidden-import=fastapi.staticfiles ^
  --hidden-import=multipart ^
  --hidden-import=email.mime ^
  --hidden-import=email.mime.text ^
  --collect-all uvicorn ^
  --collect-all fastapi ^
  --collect-all starlette ^
  launcher\launcher.py

echo.
echo ========================================
echo   Build termine ! Copie des donnees...
echo ========================================
echo.

REM Copier les donnees runtime (DB, config) dans le bon dossier
if not exist dist\JARVIS\backend\data mkdir dist\JARVIS\backend\data
if exist backend\data\jarvis.db (
    copy backend\data\jarvis.db dist\JARVIS\backend\data\
    echo [OK] jarvis.db copie
)
if exist backend\data\config.json (
    copy backend\data\config.json dist\JARVIS\backend\data\
    echo [OK] config.json copie
)

echo.
echo ========================================
echo   Package dist\JARVIS\ pret !
echo ========================================
echo.
echo Contenu :
dir dist\JARVIS /B
echo.
echo Double-clic sur dist\JARVIS\JARVIS.exe pour lancer.
echo.
pause
