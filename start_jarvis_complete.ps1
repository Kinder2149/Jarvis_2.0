# ========================================
# SCRIPT DE LANCEMENT COMPLET JARVIS 2.0
# ========================================
# Lance automatiquement :
# 1. Serveur JARVIS (backend + frontend) sur port 8000
# 2. Serveur RAG (enrichissement contexte) sur port 5001
#
# Usage: .\start_jarvis_complete.ps1
# ========================================

param(
    [switch]$SkipRAG,  # Lancer sans RAG
    [switch]$Force     # Forcer le lancement même si ports occupés
)

$ErrorActionPreference = "Continue"

# Couleurs
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Write-Title { param($msg) Write-Host "`n========================================" -ForegroundColor Cyan; Write-Host "$msg" -ForegroundColor Cyan; Write-Host "========================================`n" -ForegroundColor Cyan }

Write-Title "DÉMARRAGE JARVIS 2.0 COMPLET"

# ========================================
# 1. VÉRIFICATIONS PRÉALABLES
# ========================================

Write-Info "Vérification de l'environnement..."

# Vérifier qu'on est à la racine du projet
if (-not (Test-Path "backend\app.py")) {
    Write-Error "Ce script doit être exécuté depuis la racine du projet JARVIS 2.0"
    Write-Info "Commande correcte: cd 'd:\Coding\AppWindows\Jarvis 2.0' puis .\start_jarvis_complete.ps1"
    exit 1
}

# Vérifier Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python détecté: $pythonVersion"
} catch {
    Write-Error "Python n'est pas installé ou n'est pas dans le PATH"
    exit 1
}

# Vérifier environnement virtuel
if ($env:VIRTUAL_ENV) {
    Write-Success "Environnement virtuel actif: $env:VIRTUAL_ENV"
} else {
    Write-Warning "Aucun environnement virtuel détecté"
    Write-Info "Activation de l'environnement virtuel..."
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
        Write-Success "Environnement virtuel activé"
    } else {
        Write-Warning "Pas d'environnement virtuel trouvé (venv\Scripts\Activate.ps1)"
        Write-Info "Continuation avec Python système..."
    }
}

# Vérifier fichier .env
if (-not (Test-Path ".env")) {
    Write-Warning "Fichier .env non trouvé"
    if (Test-Path ".env.example") {
        Write-Info "Copie de .env.example vers .env..."
        Copy-Item ".env.example" ".env"
        Write-Success "Fichier .env créé"
        Write-Warning "⚠️  IMPORTANT: Éditer .env et ajouter votre GEMINI_API_KEY"
        Write-Info "Obtenir une clé: https://aistudio.google.com/app/apikey"
        $continue = Read-Host "`nAppuyez sur Entrée après avoir configuré .env (ou 'q' pour quitter)"
        if ($continue -eq "q") { exit 0 }
    } else {
        Write-Error "Fichier .env.example non trouvé"
        exit 1
    }
} else {
    Write-Success "Fichier .env trouvé"
}

# ========================================
# 2. VÉRIFICATION DÉPENDANCES JARVIS
# ========================================

Write-Info "Vérification des dépendances JARVIS..."

$jarvisDeps = @("fastapi", "uvicorn", "google.generativeai", "aiosqlite")
$missingJarvis = @()

foreach ($dep in $jarvisDeps) {
    $module = $dep -replace '\.', '_'
    try {
        $null = python -c "import $module" 2>&1
        if ($LASTEXITCODE -ne 0) {
            $missingJarvis += $dep
        }
    } catch {
        $missingJarvis += $dep
    }
    $LASTEXITCODE = 0
}

if ($missingJarvis.Count -gt 0) {
    Write-Warning "Dépendances JARVIS manquantes: $($missingJarvis -join ', ')"
    Write-Info "Installation des dépendances JARVIS..."
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Erreur lors de l'installation des dépendances JARVIS"
        exit 1
    }
    Write-Success "Dépendances JARVIS installées"
} else {
    Write-Success "Toutes les dépendances JARVIS sont installées"
}

# ========================================
# 3. VÉRIFICATION DÉPENDANCES RAG
# ========================================

if (-not $SkipRAG) {
    Write-Info "Vérification des dépendances RAG..."
    
    if (-not (Test-Path "RAG\requirements-minimal.txt")) {
        Write-Warning "Fichier RAG\requirements-minimal.txt non trouvé"
        Write-Info "Le serveur RAG ne sera pas démarré"
        $SkipRAG = $true
    } else {
        $ragDeps = @("flask", "chromadb", "sentence_transformers", "langchain")
        $missingRAG = @()
        
        foreach ($dep in $ragDeps) {
            $module = $dep -replace '-', '_'
            try {
                $null = python -c "import $module" 2>&1
                if ($LASTEXITCODE -ne 0) {
                    $missingRAG += $dep
                }
            } catch {
                $missingRAG += $dep
            }
            $LASTEXITCODE = 0
        }
        
        if ($missingRAG.Count -gt 0) {
            Write-Warning "Dépendances RAG manquantes: $($missingRAG -join ', ')"
            Write-Info "Installation des dépendances RAG (peut prendre quelques minutes)..."
            python -m pip install -r RAG\requirements-minimal.txt
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Erreur lors de l'installation des dépendances RAG"
                Write-Warning "Le serveur RAG ne sera pas démarré"
                $SkipRAG = $true
            } else {
                Write-Success "Dépendances RAG installées"
            }
        } else {
            Write-Success "Toutes les dépendances RAG sont installées"
        }
    }
}

# ========================================
# 4. VÉRIFICATION PORTS
# ========================================

Write-Info "Vérification des ports..."

# Port 8000 (JARVIS)
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000 -and -not $Force) {
    Write-Warning "Port 8000 déjà utilisé (serveur JARVIS probablement déjà lancé)"
    $continue = Read-Host "Continuer quand même? (o/n)"
    if ($continue -ne "o" -and $continue -ne "O") {
        Write-Info "Démarrage annulé"
        exit 0
    }
} elseif ($port8000) {
    Write-Warning "Port 8000 occupé (mode Force activé)"
} else {
    Write-Success "Port 8000 disponible"
}

# Port 5001 (RAG)
if (-not $SkipRAG) {
    $port5001 = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue
    if ($port5001 -and -not $Force) {
        Write-Warning "Port 5001 déjà utilisé (serveur RAG probablement déjà lancé)"
        $continue = Read-Host "Continuer quand même? (o/n)"
        if ($continue -ne "o" -and $continue -ne "O") {
            Write-Info "Démarrage annulé"
            exit 0
        }
    } elseif ($port5001) {
        Write-Warning "Port 5001 occupé (mode Force activé)"
    } else {
        Write-Success "Port 5001 disponible"
    }
}

# ========================================
# 5. DÉMARRAGE SERVEUR RAG (si activé)
# ========================================

$ragJob = $null

if (-not $SkipRAG) {
    Write-Title "DÉMARRAGE SERVEUR RAG"
    
    Write-Info "Lancement du serveur RAG en arrière-plan..."
    Write-Info "URL: http://localhost:5001"
    
    # Démarrer RAG en arrière-plan
    $ragJob = Start-Job -ScriptBlock {
        param($projectRoot)
        Set-Location "$projectRoot\RAG"
        python run.py
    } -ArgumentList (Get-Location).Path
    
    # Attendre 3 secondes pour vérifier que le serveur démarre
    Start-Sleep -Seconds 3
    
    $ragState = Get-Job -Id $ragJob.Id
    if ($ragState.State -eq "Running") {
        Write-Success "Serveur RAG démarré (Job ID: $($ragJob.Id))"
        
        # Vérifier que le serveur répond
        try {
            Start-Sleep -Seconds 2
            $response = Invoke-WebRequest -Uri "http://localhost:5001/" -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "Serveur RAG opérationnel ✅"
            } else {
                Write-Warning "Serveur RAG démarré mais ne répond pas encore"
            }
        } catch {
            Write-Warning "Serveur RAG en cours de démarrage..."
        }
    } else {
        Write-Warning "Le serveur RAG n'a pas démarré correctement"
        Write-Info "Logs du serveur RAG:"
        Receive-Job -Id $ragJob.Id
        $SkipRAG = $true
    }
} else {
    Write-Info "Serveur RAG désactivé (--SkipRAG ou dépendances manquantes)"
}

# ========================================
# 6. DÉMARRAGE SERVEUR JARVIS
# ========================================

Write-Title "DÉMARRAGE SERVEUR JARVIS"

Write-Info "Lancement du serveur JARVIS..."
Write-Info "Backend + Frontend: http://localhost:8000"
Write-Info "API Documentation: http://localhost:8000/docs"
Write-Info ""
Write-Warning "Appuyez sur Ctrl+C pour arrêter les serveurs"
Write-Info ""

# Démarrer JARVIS (bloquant)
try {
    python start_server.py
} finally {
    # Arrêter le serveur RAG si lancé
    if ($ragJob) {
        Write-Info "`nArrêt du serveur RAG..."
        Stop-Job -Id $ragJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $ragJob.Id -ErrorAction SilentlyContinue
        Write-Success "Serveur RAG arrêté"
    }
    
    Write-Info "`nServeurs arrêtés"
}
