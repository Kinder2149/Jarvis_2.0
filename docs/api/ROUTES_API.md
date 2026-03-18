# Documentation API - JARVIS 2.0

Documentation complète des routes API pour le chat simple multi-agents.

## Base URL

```
http://localhost:8000
```

## Endpoints Disponibles

### 1. Health Check

Vérification de l'état du serveur.

**Endpoint** : `GET /health`

**Réponse** :
```json
{
  "status": "ok",
  "message": "JARVIS 2.0 - Chat Simple"
}
```

**Exemple curl** :
```bash
curl http://localhost:8000/health
```

---

### 2. Lister les Agents

Récupère la liste des agents IA disponibles.

**Endpoint** : `GET /agents`

**Réponse** :
```json
{
  "agents": [
    {
      "id": "JARVIS_MAITRE",
      "name": "JARVIS Maître",
      "role": "Assistant personnel, orchestrateur"
    },
    {
      "id": "ARCHITECTE",
      "name": "Architecte",
      "role": "Conception architecture projets"
    },
    {
      "id": "CODEUR",
      "name": "Codeur",
      "role": "Génération de code Python"
    },
    {
      "id": "TESTEUR",
      "name": "Testeur",
      "role": "Génération tests pytest"
    },
    {
      "id": "VALIDATEUR",
      "name": "Validateur",
      "role": "Contrôle qualité code"
    }
  ]
}
```

**Exemple curl** :
```bash
curl http://localhost:8000/agents
```

---

### 3. Créer une Conversation

Crée une nouvelle conversation avec un agent spécifique.

**Endpoint** : `POST /api/conversations`

**Body** :
```json
{
  "agent_id": "JARVIS_MAITRE",
  "title": "Ma conversation"
}
```

**Paramètres** :
- `agent_id` (string, requis) : ID de l'agent (JARVIS_MAITRE, ARCHITECTE, CODEUR, TESTEUR, VALIDATEUR)
- `title` (string, optionnel) : Titre de la conversation

**Réponse** :
```json
{
  "id": "conv_123456",
  "agent_id": "JARVIS_MAITRE",
  "title": "Ma conversation",
  "created_at": "2026-03-18T20:00:00"
}
```

**Codes d'erreur** :
- `400` : Agent ID invalide
- `500` : Erreur serveur

**Exemple curl** :
```bash
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "JARVIS_MAITRE", "title": "Test"}'
```

---

### 4. Lister les Conversations

Récupère toutes les conversations existantes.

**Endpoint** : `GET /api/conversations`

**Réponse** :
```json
[
  {
    "id": "conv_123456",
    "agent_id": "JARVIS_MAITRE",
    "title": "Ma conversation",
    "created_at": "2026-03-18T20:00:00"
  },
  {
    "id": "conv_789012",
    "agent_id": "CODEUR",
    "title": "Génération code",
    "created_at": "2026-03-18T20:05:00"
  }
]
```

**Exemple curl** :
```bash
curl http://localhost:8000/api/conversations
```

---

### 5. Récupérer une Conversation

Récupère les détails d'une conversation spécifique.

**Endpoint** : `GET /api/conversations/{conversation_id}`

**Paramètres URL** :
- `conversation_id` (string, requis) : ID de la conversation

**Réponse** :
```json
{
  "id": "conv_123456",
  "agent_id": "JARVIS_MAITRE",
  "title": "Ma conversation",
  "created_at": "2026-03-18T20:00:00"
}
```

**Codes d'erreur** :
- `404` : Conversation non trouvée

**Exemple curl** :
```bash
curl http://localhost:8000/api/conversations/conv_123456
```

---

### 6. Supprimer une Conversation

Supprime une conversation et tous ses messages.

**Endpoint** : `DELETE /api/conversations/{conversation_id}`

**Paramètres URL** :
- `conversation_id` (string, requis) : ID de la conversation

**Réponse** :
```json
{
  "message": "Conversation supprimée"
}
```

**Codes d'erreur** :
- `404` : Conversation non trouvée

**Exemple curl** :
```bash
curl -X DELETE http://localhost:8000/api/conversations/conv_123456
```

---

### 7. Récupérer les Messages

Récupère l'historique des messages d'une conversation.

**Endpoint** : `GET /api/conversations/{conversation_id}/messages`

**Paramètres URL** :
- `conversation_id` (string, requis) : ID de la conversation

**Paramètres Query** :
- `limit` (integer, optionnel) : Nombre maximum de messages (défaut: 50)

**Réponse** :
```json
[
  {
    "id": "msg_001",
    "conversation_id": "conv_123456",
    "role": "user",
    "content": "Bonjour",
    "timestamp": "2026-03-18T20:01:00"
  },
  {
    "id": "msg_002",
    "conversation_id": "conv_123456",
    "role": "assistant",
    "content": "Bonjour ! Comment puis-je vous aider ?",
    "timestamp": "2026-03-18T20:01:05"
  }
]
```

**Codes d'erreur** :
- `404` : Conversation non trouvée

**Exemple curl** :
```bash
curl http://localhost:8000/api/conversations/conv_123456/messages?limit=10
```

---

### 8. Envoyer un Message

Envoie un message dans une conversation et reçoit la réponse de l'agent.

**Endpoint** : `POST /api/conversations/{conversation_id}/messages`

**Paramètres URL** :
- `conversation_id` (string, requis) : ID de la conversation

**Body** :
```json
{
  "content": "Peux-tu m'aider à créer une fonction Python ?"
}
```

**Paramètres** :
- `content` (string, requis) : Contenu du message

**Réponse** :
```json
{
  "user_message": {
    "id": "msg_003",
    "conversation_id": "conv_123456",
    "role": "user",
    "content": "Peux-tu m'aider à créer une fonction Python ?",
    "timestamp": "2026-03-18T20:02:00"
  },
  "assistant_message": {
    "id": "msg_004",
    "conversation_id": "conv_123456",
    "role": "assistant",
    "content": "Bien sûr ! Quelle fonction souhaitez-vous créer ?",
    "timestamp": "2026-03-18T20:02:05"
  },
  "response": "Bien sûr ! Quelle fonction souhaitez-vous créer?"
}
```

**Codes d'erreur** :
- `404` : Conversation non trouvée
- `500` : Erreur lors de l'appel à l'agent IA

**Exemple curl** :
```bash
curl -X POST http://localhost:8000/api/conversations/conv_123456/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "Bonjour"}'
```

---

## Modèles de Données

### Conversation

```json
{
  "id": "string",
  "agent_id": "string",
  "title": "string",
  "created_at": "string (ISO 8601)"
}
```

### Message

```json
{
  "id": "string",
  "conversation_id": "string",
  "role": "user | assistant",
  "content": "string",
  "timestamp": "string (ISO 8601)"
}
```

### Agent

```json
{
  "id": "string",
  "name": "string",
  "role": "string"
}
```

---

## Utilisation depuis le Frontend

### Créer une conversation et envoyer un message

```javascript
// 1. Créer une conversation
const response1 = await fetch('http://localhost:8000/api/conversations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_id: 'JARVIS_MAITRE',
    title: 'Ma conversation'
  })
});
const conversation = await response1.json();

// 2. Envoyer un message
const response2 = await fetch(
  `http://localhost:8000/api/conversations/${conversation.id}/messages`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: 'Bonjour' })
  }
);
const result = await response2.json();
console.log(result.response); // Réponse de l'agent
```

---

## Notes Importantes

1. **Stockage** : Les conversations sont stockées dans `backend/data/conversations.json`
2. **Agents** : 5 agents disponibles avec des spécialisations différentes
3. **Pas d'authentification** : API ouverte (usage local uniquement)
4. **CORS** : Configuré pour localhost uniquement
5. **Format** : Toutes les réponses sont en JSON
6. **Timestamps** : Format ISO 8601 (ex: 2026-03-18T20:00:00)

---

## Codes d'Erreur HTTP

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 400 | Requête invalide |
| 404 | Ressource non trouvée |
| 500 | Erreur serveur |

---

## Contact & Support

Pour toute question sur l'API, consultez :
- Architecture : `docs/architecture/ARCHITECTURE.md`
- Méthode de travail : `docs/guides/METHODE_TRAVAIL.md`
