# Investigation Régression Library - Boucle Infinie Function Calls

**Date** : 25 février 2026  
**Statut** : 🔍 EN COURS  
**Objectif** : Comprendre pourquoi Gemini entre en boucle infinie lors de l'enrichissement prompt v4.1

---

## 🎯 Contexte

### Problème Rapporté (22/02/2026)
**Prompt JARVIS_Maître v4.1** avec obligation de consulter Library avant délégation :
- ❌ Réponses vides systématiques (0 chars)
- ❌ Aucune délégation au CODEUR
- ❌ 0 fichier généré sur tous les tests live
- ❌ Hypothèse : Boucle infinie de function calls

**Solution appliquée** : Rollback vers v4.0 (délégation simple)

---

## 🔍 Analyse des Logs

### Logs Disponibles
- `jarvis_audit.log` : Logs backend généraux (755 lignes, jusqu'au 14/02/2026)
- `backend/logs/gemini_api.log` : Logs Gemini spécifiques (7206 lignes, depuis 22/02/2026 17h26)
- `backend/logs/mistral_api.log` : Logs Mistral (non pertinent, migration Gemini effectuée)

### Observations Logs Gemini (22/02/2026)

**Pattern observé** : Tous les appels Gemini retournent `0 tool_calls`
```
2026-02-22 17:38:15 - Gemini response: 531 chars, 0 tool_calls
2026-02-22 17:38:24 - Gemini response: 425 chars, 0 tool_calls
2026-02-22 17:38:34 - Gemini response: 521 chars, 0 tool_calls
```

**⚠️ Problème** : Les logs disponibles datent d'APRÈS le rollback v4.0
- Logs du 22/02 à partir de 17h26 → Tests avec v4.0 (stable)
- Pas de logs de la régression v4.1 (tests live échoués)
- **Impossible de confirmer la boucle infinie dans les logs**

---

## 📊 Analyse du Code

### 1. Gestion Function Calling (`gemini_provider.py`)

**Extraction tool calls** (L98-106) :
```python
elif hasattr(part, "function_call"):
    # Tool call détecté
    fc = part.function_call
    tool_calls.append({
        "id": f"call_{len(tool_calls)}",
        "name": fc.name,
        "arguments": dict(fc.args),
    })
    finish_reason = "tool_calls"
```

**Logs si réponse vide** (L113-117) :
```python
if not content and not tool_calls:
    logger.warning(f"Gemini returned empty response!")
    logger.warning(f"Candidate finish_reason: {response.candidates[0].finish_reason}")
    logger.warning(f"Candidate content parts: {response.candidates[0].content.parts}")
```

✅ **Code robuste** : Logs détaillés en cas de réponse vide

---

### 2. Boucle Function Calling (`base_agent.py`)

**Limite max_iterations** (L196) :
```python
async def _handle_with_function_calling(
    self, messages: list[dict], function_executor=None, max_iterations: int = 3
):
```

**Boucle principale** (L222-275) :
```python
while iteration < max_iterations:
    response = await self.provider.send_message(...)
    content = response.get("content", "")
    tool_calls = response.get("tool_calls", [])
    
    # Si pas de tool calls, retourner le contenu
    if not tool_calls or not function_executor:
        return content
    
    # Exécuter tool calls
    for tool_call in tool_calls:
        result = await function_executor.execute(...)
        conversation_messages.append(tool_result_msg)
    
    iteration += 1

# Max iterations atteintes
return content
```

✅ **Protection anti-boucle** : Max 3 itérations
✅ **Sortie immédiate** : Si pas de tool_calls, retourne content
⚠️ **Problème potentiel** : Si Gemini retourne `content=""` + `tool_calls=[]` → Retourne chaîne vide

---

### 3. Validation Backend (`base_agent.py`)

**Validation content vide pour assistant** (L152-163) :
```python
# Permettre content vide pour assistant (Gemini peut retourner "" avec tool_calls)
if role in ("user", "system", "tool"):
    if not isinstance(content, str) or not content.strip():
        raise InvalidRuntimeMessageError(...)
else:  # role == "assistant"
    if not isinstance(content, str):
        raise InvalidRuntimeMessageError(...)
```

✅ **Correction appliquée** : Autorise `content=""` pour `role="assistant"`

---

### 4. Filtrage Frontend (`chat.js`)

**Filtrage réponses vides** (mentionné dans bilan 22/02) :
```javascript
if (data.response && data.response.trim()) {
    this.addMessage('assistant', data.response);
}
```

✅ **Correction appliquée** : Évite d'ajouter réponses vides à l'historique

---

## 🧪 Hypothèses sur la Boucle Infinie

### Hypothèse 1 : Gemini appelle functions en boucle SANS générer de texte

**Scénario** :
1. Prompt v4.1 : "**TOUJOURS** consulter la Library avant de déléguer"
2. Gemini appelle `get_library_document("FastAPI", "libraries")`
3. Backend exécute et retourne résultat
4. Gemini reçoit résultat mais **ne génère PAS de texte**
5. Gemini appelle une autre function (boucle)
6. Après 3 itérations → Backend retourne `content=""` (vide)
7. Frontend filtre la réponse vide
8. **Pas de délégation au CODEUR**

**Probabilité** : ⭐⭐⭐⭐⭐ TRÈS ÉLEVÉE
**Raison** : Correspond exactement aux symptômes rapportés

---

### Hypothèse 2 : Gemini atteint max_iterations sans générer de texte

**Scénario** :
1. Gemini appelle `get_library_document()` (iteration 1)
2. Gemini appelle `get_library_list()` (iteration 2)
3. Gemini appelle `get_library_document()` à nouveau (iteration 3)
4. Max iterations atteintes → Backend retourne `content` (vide si Gemini n'a rien généré)

**Probabilité** : ⭐⭐⭐⭐ ÉLEVÉE
**Raison** : Protection anti-boucle empêche boucle infinie réelle, mais résultat identique

---

### Hypothèse 3 : Conflit entre obligation Library et délégation

**Scénario** :
1. Prompt v4.1 : "1. CONSULTER LA LIBRARY, 2. ENRICHIR, 3. Déléguer"
2. Gemini se concentre sur étapes 1-2 (consultation Library)
3. Gemini ne génère jamais le marqueur `[DEMANDE_CODE_CODEUR: ...]`
4. Backend retourne réponse vide ou sans délégation

**Probabilité** : ⭐⭐⭐ MOYENNE
**Raison** : Possible, mais ne correspond pas au pattern "0 chars"

---

## 🔬 Test Reproductible Nécessaire

### Objectif
Reproduire la régression v4.1 avec logs détaillés pour confirmer l'hypothèse.

### Plan de Test
1. **Créer prompt v4.1 enrichi** (obligation Library)
2. **Activer logs détaillés** Gemini (niveau DEBUG)
3. **Exécuter test live** (Calculatrice simple)
4. **Analyser logs** :
   - Nombre de tool_calls par itération
   - Contenu des tool_calls (nom fonction, arguments)
   - Réponses Gemini après chaque tool_call
   - Finish_reason à chaque itération

### Prompt v4.1 à Tester
```markdown
✅ TOUJOURS FAIRE :
1. **CONSULTER LA LIBRARY** : Utilise get_library_document() pour récupérer patterns pertinents
2. **ENRICHIR L'INSTRUCTION** : Intègre le contexte Library dans ton instruction au CODEUR
3. Écrire le marqueur : [DEMANDE_CODE_CODEUR: ...]
```

---

## 📝 Conclusions Préliminaires

### Ce Que Nous Savons
1. ✅ Prompt v4.0 (délégation simple) fonctionne parfaitement
2. ✅ Prompt v4.1 (obligation Library) cause régression critique
3. ✅ Code backend robuste (max_iterations=3, logs détaillés)
4. ✅ Corrections appliquées (validation content vide, filtrage frontend)

### Ce Que Nous Ne Savons PAS
1. ❌ Pattern exact des tool_calls lors de la régression v4.1
2. ❌ Pourquoi Gemini ne génère pas de texte après tool_calls
3. ❌ Si c'est une boucle infinie réelle ou max_iterations atteintes

### Prochaines Étapes
1. **Créer test reproductible** avec prompt v4.1
2. **Activer logs DEBUG** pour capturer tous les détails
3. **Analyser comportement Gemini** avec obligation function calling
4. **Tester approches alternatives** :
   - Option A : Library optionnelle (suggestion vs obligation)
   - Option B : Enrichissement côté CODEUR (pas JARVIS_Maître)
   - Option C : Désactiver functions pour JARVIS_Maître

---

**Durée investigation** : ~1h  
**Statut** : Analyse code terminée, test reproductible requis  
**Prochaine action** : Créer script de test avec prompt v4.1 + logs DEBUG
