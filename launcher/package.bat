@echo off
cd ..
echo ========================================
echo   JARVIS V2 - Package Portable
echo ========================================
echo.

if not exist dist\JARVIS\JARVIS.exe (
    echo ERREUR : Build non trouve. Lancer d'abord build.bat
    pause
    exit /b 1
)

echo Creation du package portable...
set PACKAGE_DIR=dist\JARVIS_Portable

REM Nettoyer et recreer
if exist %PACKAGE_DIR% rmdir /s /q %PACKAGE_DIR%
mkdir %PACKAGE_DIR%

REM Copier tout le build
xcopy /E /I /Q dist\JARVIS %PACKAGE_DIR%

REM README utilisateur
echo JARVIS V2 - Interface IA Locale> %PACKAGE_DIR%\LANCEMENT.txt
echo ================================>> %PACKAGE_DIR%\LANCEMENT.txt
echo.>> %PACKAGE_DIR%\LANCEMENT.txt
echo Double-cliquez sur JARVIS.exe>> %PACKAGE_DIR%\LANCEMENT.txt
echo Cliquez "Demarrer" dans la fenetre launcher>> %PACKAGE_DIR%\LANCEMENT.txt
echo Le navigateur s'ouvre automatiquement>> %PACKAGE_DIR%\LANCEMENT.txt
echo.>> %PACKAGE_DIR%\LANCEMENT.txt
echo Configuration : bouton Parametres dans l'interface>> %PACKAGE_DIR%\LANCEMENT.txt

echo.
echo Package cree : %PACKAGE_DIR%\
echo.
echo Pour distribuer :
echo   ZIP le dossier JARVIS_Portable et l'envoyer
echo   Taille : environ 150-200 MB
echo.
pause
