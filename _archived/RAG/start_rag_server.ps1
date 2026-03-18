# Script PowerShell pour démarrer le serveur RAG
# Usage: .\start_rag_server.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DÉMARRAGE SERVEUR RAG - JARVIS 2.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier qu'on est dans le bon dossier
if (-not (Test-Path "run.py")) {
    Write-Host "❌ Erreur: Ce script doit être exécuté depuis le dossier RAG" -ForegroundColor Red
    Write-Host "   cd RAG" -ForegroundColor Yellow
    Write-Host "   .\start_rag_server.ps1" -ForegroundColor Yellow
    exit 1
}

# Vérifier si Python est installé
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python détecté: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    exit 1
}

# Vérifier si les dépendances sont installées
Write-Host ""
Write-Host "Vérification des dépendances..." -ForegroundColor Yellow

$requiredPackages = @("flask", "chromadb", "sentence_transformers", "langchain")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    $installed = python -c "import $package" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️ Dépendances manquantes détectées:" -ForegroundColor Yellow
    foreach ($pkg in $missingPackages) {
        Write-Host "   - $pkg" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Installation des dépendances minimales..." -ForegroundColor Yellow
    Write-Host "Commande: pip install -r requirements-minimal.txt" -ForegroundColor Cyan
    Write-Host ""
    
    $install = Read-Host "Installer maintenant? (o/n)"
    if ($install -eq "o" -or $install -eq "O") {
        python -m pip install -r requirements-minimal.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Erreur lors de l'installation des dépendances" -ForegroundColor Red
            exit 1
        }
        Write-Host "✅ Dépendances installées avec succès" -ForegroundColor Green
    } else {
        Write-Host "❌ Installation annulée. Le serveur ne peut pas démarrer sans les dépendances." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Toutes les dépendances sont installées" -ForegroundColor Green
}

# Vérifier si le port 5001 est déjà utilisé
Write-Host ""
Write-Host "Vérification du port 5001..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️ Le port 5001 est déjà utilisé" -ForegroundColor Yellow
    Write-Host "   Le serveur RAG est peut-être déjà lancé" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continuer quand même? (o/n)"
    if ($continue -ne "o" -and $continue -ne "O") {
        Write-Host "❌ Démarrage annulé" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Port 5001 disponible" -ForegroundColor Green
}

# Démarrer le serveur
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DÉMARRAGE DU SERVEUR RAG" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URL: http://localhost:5001" -ForegroundColor Green
Write-Host "Appuyez sur Ctrl+C pour arrêter le serveur" -ForegroundColor Yellow
Write-Host ""

# Lancer le serveur
python run.py
