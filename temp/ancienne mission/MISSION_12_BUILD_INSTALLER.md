# MISSION 12 — Build Final + Package Portable + Validation Flux

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Build Final V2 + Package Portable + Validation Flux Complet

OBJECTIF :
1. Reconstruire JARVIS.exe avec le Frontend V2 complet et le Backend mis à jour
2. Créer un package portable fonctionnel pour déploiement sur un autre PC
3. Créer un script installateur Windows (Inno Setup)
4. Valider le flux complet : chat simple + lancement Module Code

Le build actuel (--onefile) ne peut pas fonctionner seul sur un autre PC car
il attend que frontend/ et backend/data/ soient à côté de l'exe.
On va corriger ça avec une approche --onedir + packaging propre.

PÉRIMÈTRE :
Fichiers à modifier :
- launcher/build.bat
- launcher/launcher.py  (ajustement chemin DB pour --onedir)

Fichiers à créer :
- launcher/package.bat       (script de packaging portable)
- launcher/installer.iss     (script Inno Setup pour installateur Windows)
- TEST_VALIDATION_FLUX.md    (résultats des tests de validation)

---

## PARTIE 1 — REBUILD AVEC --ONEDIR

### Problème avec --onefile actuel
Avec `--onefile`, PyInstaller extrait tout dans un dossier TEMP (_MEIPASS).
Le launcher.py cherche frontend/ et backend/data/ à côté de l'exe.
→ L'exe seul ne fonctionne pas, il faut les dossiers à côté.
→ Avec --onedir, tous les fichiers sont dans dist/JARVIS/ (propre et prévisible).

### Modifier launcher/build.bat

Remplacer le build actuel par :
```bat
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
echo   Build termine ! Packaging...
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
```

### Modifier launcher/launcher.py — Chemins pour --onedir

Avec --onedir, `sys.executable` = `dist/JARVIS/JARVIS.exe`.
`Path(sys.executable).parent` = `dist/JARVIS/` (correct !).
Les données (frontend/, backend/) sont dans `dist/JARVIS/_internal/` avec PyInstaller 6+
OU directement dans `dist/JARVIS/` avec versions antérieures.

Modifier la partie frozen de launcher.py :

```python
if getattr(sys, 'frozen', False):
    # --onedir : exe est dans dist/JARVIS/, les data à côté
    exe_dir = Path(sys.executable).parent
    
    # PyInstaller 6+ met les données dans _internal/
    # Versions antérieures les mettent directement à côté
    internal_dir = exe_dir / '_internal'
    if internal_dir.exists():
        self.jarvis_root = internal_dir
    else:
        self.jarvis_root = exe_dir
    
    # DB et config restent dans exe_dir/backend/data/ (writable)
    self.data_dir = exe_dir / 'backend' / 'data'
    self.data_dir.mkdir(parents=True, exist_ok=True)
    
    # Ajouter les chemins au sys.path pour les imports
    for path in [str(self.jarvis_root), str(self.jarvis_root / 'backend')]:
        if path not in sys.path:
            sys.path.insert(0, path)
else:
    self.jarvis_root = Path(__file__).parent.parent
    self.data_dir = self.jarvis_root / 'backend' / 'data'
```

Chercher dans launcher.py où la commande uvicorn est construite et passer les bons chemins :
```python
# La commande uvicorn doit pointer vers le bon dossier
# Vérifier que backend.main est importable depuis jarvis_root
```

**Important** : Chercher et afficher la méthode `_start_server()` ou équivalent dans launcher.py
pour voir comment uvicorn est lancé, puis adapter les chemins si nécessaire.

---

## PARTIE 2 — SCRIPT PACKAGING PORTABLE

Créer `launcher/package.bat` :

```bat
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

REM Nettoyer et recréer
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

REM Calculer la taille
for /f %%i in ('dir %PACKAGE_DIR% /s /q ^| findstr "fichier(s)"') do echo Taille approximative : %%i

pause
```

---

## PARTIE 3 — SCRIPT INNO SETUP (Installateur Windows)

Créer `launcher/installer.iss` :

```iss
; Script Inno Setup — JARVIS V2 Installateur Windows
; Requiert Inno Setup 6+ (https://jrsoftware.org/isinfo.php)

#define AppName "JARVIS"
#define AppVersion "2.0"
#define AppPublisher "JARVIS IA"
#define AppURL "http://localhost:8000"
#define AppExeName "JARVIS.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=JARVIS_Setup_v2
SetupIconFile=launcher\launcher.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Lancer JARVIS au démarrage de Windows"; GroupDescription: "Options de démarrage"; Flags: unchecked

[Files]
; Le dossier de build complet
Source: "dist\JARVIS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Désinstaller {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\backend\data"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
```

Pour générer l'installateur (nécessite Inno Setup installé) :
```bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" launcher\installer.iss
```

**Note** : Si Inno Setup n'est pas installé, le noter dans le rapport.
L'installateur est optionnel — le package portable suffit pour le déploiement immédiat.

---

## PARTIE 4 — VALIDATION FLUX COMPLET

Après le build, tester les 3 flux critiques.
**Le serveur doit être lancé depuis l'EXE (pas depuis Python) pour ce test.**

Lancer `dist\JARVIS\JARVIS.exe` → clic "Démarrer" → attendre que le navigateur s'ouvre.

### Test A — Chat Simple

1. Dans la sidebar, cliquer "💬 Nouveau Chat"
2. Sélectionner un projet (ou "Sans projet")
3. Valider → redirection vers chat.html
4. Dans le dropdown modèle (header du chat), choisir un modèle
5. Taper : "Bonjour ! Dis-moi juste 'OK' pour confirmer que tu fonctionnes."
6. Envoyer (Ctrl+Entrée)
7. **Attendu** : réponse IA dans les 5-10 secondes

Résultat à noter :
- [ ] Chat créé et page chargée
- [ ] Modèle sélectionnable
- [ ] Message envoyé sans erreur
- [ ] Réponse IA reçue
- [ ] Pas d'erreur JS console (F12)

### Test B — Module Code (session_start)

1. Dans la sidebar, cliquer "⚙️ Module Code"
2. Sélectionner le projet JARVIS
3. Workflow : `session_start`
4. Demande initiale : "Analyse rapide du projet JARVIS — résume l'état actuel en 3 points."
5. Cliquer "Lancer"
6. **Attendu** : redirect vers module-code.html, les steps s'affichent et progressent

Résultat à noter :
- [ ] Module Code créé et redirect OK
- [ ] Steps visibles avec indicateurs (spinner, ✅)
- [ ] Polling actif (mise à jour automatique)
- [ ] Si checkpoint de validation → boutons Approuver/Rejeter visibles
- [ ] Session se termine sans erreur

### Test C — Page Projet (instructions)

1. Cliquer sur le projet JARVIS dans la sidebar
2. **Attendu** : page projet.html s'ouvre
3. Cliquer ✏️ sur "Instructions du projet"
4. Écrire : "Projet JARVIS V2 — Interface IA locale. Backend FastAPI stable."
5. Sauvegarder
6. **Attendu** : toast "Instructions sauvegardées" + affichage mis à jour

Résultat à noter :
- [ ] Page projet accessible depuis sidebar (clic sur le nom)
- [ ] Instructions éditables et sauvegardées
- [ ] Conversations du projet listées

---

## RAPPORT À PRODUIRE

Créer `TEST_VALIDATION_FLUX.md` avec :

```markdown
# Test Validation Flux — JARVIS V2

## Build
- Méthode : --onedir
- Taille exe : X MB
- Taille dossier complet : X MB
- Python embarqué : X.X

## Test A — Chat Simple
- Statut : ✅ / ❌
- Modèle utilisé : ...
- Temps réponse : ~X secondes
- Erreurs : aucune / [erreur]

## Test B — Module Code
- Statut : ✅ / ❌
- Steps affichés : X
- Comportement polling : OK / KO
- Erreurs : aucune / [erreur]

## Test C — Page Projet
- Statut : ✅ / ❌
- Navigation sidebar → projet : OK / KO
- Instructions sauvegardées : OK / KO

## Package Portable
- Dossier : dist/JARVIS_Portable/
- Taille : X MB
- Inno Setup disponible : oui/non
- Installateur généré : oui/non → dist/JARVIS_Setup_v2.exe

## Bugs détectés
- [liste]

## Prochaines étapes
- [liste]
```

---

FIN DE MISSION :
- Build --onedir réussi
- Package portable créé (dist/JARVIS_Portable/)
- Installateur Inno Setup (si disponible) ou noté comme prochaine étape
- Tests A + B + C effectués et documentés dans TEST_VALIDATION_FLUX.md
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
