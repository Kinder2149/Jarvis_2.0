# Template : Calculatrice Python Simple

**Type** : Application CLI  
**Complexité** : Simple (2-3 fichiers)  
**Stack** : Python 3.11+, pytest  
**Temps estimé** : 2-3 minutes

---

## Description

Application CLI permettant d'effectuer des opérations arithmétiques de base (+, -, *, /).

---

## Architecture

```
calculator/
├── calculator.py       # Classe Calculator avec méthodes
├── main.py             # Interface CLI
├── requirements.txt    # pytest
└── test_calculator.py  # Tests unitaires
```

---

## Fichiers à Créer

### 1. calculator.py

**Responsabilité** : Logique métier (opérations arithmétiques)

**Classes** :
- `Calculator` avec méthodes `add()`, `subtract()`, `multiply()`, `divide()`

**Validation** :
- Vérifier types d'entrée (int/float)
- Gérer division par zéro

---

### 2. main.py

**Responsabilité** : Interface CLI (boucle interactive)

**Fonctionnalités** :
- Afficher menu
- Lire entrées utilisateur
- Appeler Calculator
- Afficher résultats
- Gérer erreurs

---

### 3. test_calculator.py

**Responsabilité** : Tests unitaires

**Tests à couvrir** :
- Cas nominal (opérations valides)
- Cas limites (0, négatifs, floats)
- Cas d'erreur (types invalides, division par zéro)

---

## Patterns Utilisés

- **Encapsulation** : Classe Calculator sépare logique de l'interface
- **Validation** : Vérification types avec `isinstance()`
- **Gestion erreurs** : `raise ValueError`, `raise ZeroDivisionError`

---

## Extensions Futures

- Ajouter opérations avancées (puissance, racine, modulo)
- Ajouter historique des calculs (nécessite storage.py)
- Ajouter interface graphique (Tkinter, PyQt)

---

## Exemple Utilisation

```bash
$ python main.py
=== Calculatrice ===
1. Addition
2. Soustraction
3. Multiplication
4. Division
5. Quitter

Choix : 1
Nombre 1 : 5
Nombre 2 : 3
Résultat : 8
```

---

## Points Clés

- ✅ Pas de sur-ingénierie (pas de models.py ni storage.py)
- ✅ Validation stricte des entrées
- ✅ Tests exhaustifs (couverture 100%)
- ✅ Code minimal fonctionnel
