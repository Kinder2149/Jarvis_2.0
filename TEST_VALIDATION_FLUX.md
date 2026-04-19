# Test Validation Flux — JARVIS V2

## Build

- Méthode : --onedir
- Taille exe : à mesurer après build
- Taille dossier complet : à mesurer après build
- Python embarqué : 3.11

> **Note portabilité** : Le launcher démarre uvicorn via `subprocess` avec `["python", "-m", "uvicorn", ...]`.
> Cela fonctionne sur une machine avec Python installé. Sur une machine sans Python,
> il faudrait migrer vers `uvicorn.run()` en thread. Pour l'instant le package portable
> cible des machines avec Python 3.11+.

## Test A — Chat Simple

- Statut : ⏳ À tester
- Modèle utilisé : ...
- Temps réponse : ~X secondes
- Erreurs : ...

## Test B — Module Code

- Statut : ⏳ À tester
- Steps affichés : X
- Comportement polling : ...
- Erreurs : ...

## Test C — Page Projet

- Statut : ⏳ À tester
- Navigation sidebar → projet : ...
- Instructions sauvegardées : ...

## Package Portable

- Dossier : dist/JARVIS_Portable/
- Taille : à mesurer
- Inno Setup disponible : à vérifier (`C:\Program Files (x86)\Inno Setup 6\ISCC.exe`)
- Installateur généré : non (lancer `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" launcher\installer.iss` si installé)

## Bugs détectés

- Aucun à ce stade

## Prochaines étapes

1. Lancer `launcher\build.bat` → génère `dist\JARVIS\`
2. Tester `dist\JARVIS\JARVIS.exe` → clic Démarrer → vérifier flux chat + module code
3. Lancer `launcher\package.bat` → génère `dist\JARVIS_Portable\`
4. (Optionnel) Générer l'installateur si Inno Setup est installé
5. Remplir les résultats des tests A/B/C ci-dessus
