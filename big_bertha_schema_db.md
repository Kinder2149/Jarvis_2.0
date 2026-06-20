# Schéma de base de données — Big Bertha (V1)

Document figé. SQLite, sqlite3 natif, zéro ORM. Toutes les tables sont créées
via `CREATE TABLE IF NOT EXISTS` dans `init_db()`.

---

## 1. conversations

Une conversation regroupe l'historique d'échanges avec un utilisateur.
Nouvelle conversation = ardoise vierge (pinned_context et historique repartent à zéro).

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant |
| title | TEXT | — | NULL | titre affiché dans l'UI (libre, pas de génération auto prévue en V1) |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage création |
| updated_at | TEXT | NOT NULL | datetime('now') | dernière activité, mis à jour par l'app à chaque nouveau message |

```sql
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 2. agents

Catalogue des agents disponibles. Seedée au démarrage depuis `agents_templates.json`.
Extensible en V2 sans migration : ajouter un agent = une ligne en plus, pas de
colonne à toucher.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant interne |
| code | TEXT | NOT NULL, UNIQUE | — | identifiant stable utilisé dans le JSON de routing du Boss (ex: 'ANALYSTE') |
| name | TEXT | NOT NULL | — | nom affiché |
| description | TEXT | — | NULL | description du rôle, injectée dans le prompt de routing du Boss |
| system_prompt | TEXT | NOT NULL | — | prompt système de l'agent |
| is_active | INTEGER | NOT NULL, CHECK (0,1) | 1 | permet de désactiver un agent sans le supprimer |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage |

```sql
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Justification** : `code` est séparé de `id` pour que le JSON de routing référence
un identifiant stable ('ANALYSTE') et non un id numérique qui pourrait changer
entre environnements.

---

## 3. messages

Le fil de conversation tel que vu par l'utilisateur : ses messages et les réponses
finales du Boss. Les appels internes aux agents ne sont pas dans cette table
(leur trace est dans `jobs`).

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant |
| conversation_id | INTEGER | NOT NULL, FK → conversations(id) | — | rattachement |
| role | TEXT | NOT NULL, CHECK ('user','boss') | — | qui parle |
| content | TEXT | NOT NULL | — | contenu du message |
| agent_code | TEXT | — | NULL | NULL si role='user' ; code de l'agent si role='boss' (ex: 'ANALYSTE', 'BOSS') — utilisé pour afficher les badges dans l'UI sans jointure |
| job_id | INTEGER | FK → jobs(id) | NULL | pour role='boss', le job qui a produit cette réponse ; NULL pour role='user' |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage |

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'boss')),
    content TEXT NOT NULL,
    agent_code TEXT,
    job_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

**Justification `agent_code`** : dénormalisé depuis jobs pour éviter la jointure
`messages → jobs → agents` à chaque affichage de l'historique. Requête la plus
fréquente de l'app — une colonne TEXT simple suffit.

---

## 4. jobs

Le cœur du tracking. Une ligne par message utilisateur, qui trace l'intégralité
du cycle de vie : routing → agent → synthèse.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant, c'est le `/api/jobs/{id}` pollé par le frontend |
| conversation_id | INTEGER | NOT NULL, FK → conversations(id) | — | rattachement |
| user_message_id | INTEGER | NOT NULL, FK → messages(id) | — | le message qui a déclenché ce job |
| status | TEXT | NOT NULL, CHECK (cf. liste) | 'PENDING' | état courant |
| selected_agent_id | INTEGER | FK → agents(id) | NULL | rempli après la phase ROUTING |
| routing_output | TEXT | — | NULL | JSON brut produit par le Boss en Phase 1 |
| agent_input | TEXT | — | NULL | tâche envoyée à l'agent sélectionné |
| agent_output | TEXT | — | NULL | résultat brut renvoyé par l'agent |
| final_response | TEXT | — | NULL | réponse finale composée par le Boss en Phase 2 |
| error_message | TEXT | — | NULL | rempli si status='ERROR' |
| created_at | TEXT | NOT NULL | datetime('now') | création du job |
| updated_at | TEXT | NOT NULL | datetime('now') | mis à jour à chaque changement de statut |
| completed_at | TEXT | — | NULL | rempli quand status passe à DONE ou ERROR |

```sql
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    user_message_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','ROUTING','AGENT_RUNNING','SYNTHESIZING','DONE','ERROR')),
    selected_agent_id INTEGER,
    routing_output TEXT,
    agent_input TEXT,
    agent_output TEXT,
    final_response TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (user_message_id) REFERENCES messages(id),
    FOREIGN KEY (selected_agent_id) REFERENCES agents(id)
);
```

**Justification** : 4 colonnes séparées (`routing_output`, `agent_input`,
`agent_output`, `final_response`) plutôt qu'un blob JSON — debug et requêtes
triviales sans parsing.

---

## 5. pinned_context

Éléments épinglés, scopés par conversation. Deux sources possibles.
Réinjectés dans le contexte du Boss à chaque nouveau message de la conversation.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant |
| conversation_id | INTEGER | NOT NULL, FK → conversations(id) | — | scope |
| content | TEXT | NOT NULL | — | contenu épinglé |
| source | TEXT | NOT NULL, CHECK ('boss','user') | — | qui a épinglé |
| job_id | INTEGER | FK → jobs(id) | NULL | si source='boss', le job pendant lequel l'épinglage a eu lieu |
| is_active | INTEGER | NOT NULL, CHECK (0,1) | 1 | soft-delete : permet de désépingler sans perdre l'historique |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage |

```sql
CREATE TABLE IF NOT EXISTS pinned_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('boss','user')),
    job_id INTEGER,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

---

## 6. company_profile

Une seule ligne. Contexte entreprise injecté dans chaque appel LLM.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY, CHECK (id = 1) | — | force une ligne unique |
| name | TEXT | NOT NULL | — | nom de l'entreprise cliente |
| sector | TEXT | — | NULL | secteur d'activité |
| tone | TEXT | — | NULL | ton de communication attendu |
| business_rules | TEXT | — | NULL | règles métier libres, injectées dans le contexte LLM |
| updated_at | TEXT | NOT NULL | datetime('now') | dernière modification |

```sql
CREATE TABLE IF NOT EXISTS company_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    sector TEXT,
    tone TEXT,
    business_rules TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Unicité garantie par le schéma** : `CHECK (id = 1)` + PRIMARY KEY interdit
toute ligne dont l'id ≠ 1. L'app fait toujours `INSERT OR IGNORE (id=1, ...)` puis
`UPDATE WHERE id=1`. Aucune logique applicative à coder.

---

## 7. model_decision_log

Une ligne par appel LLM. 3 lignes par message utilisateur (routing, appel agent, synthèse).

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | — | identifiant |
| job_id | INTEGER | NOT NULL, FK → jobs(id) | — | rattachement au job |
| conversation_id | INTEGER | NOT NULL, FK → conversations(id) | — | dénormalisé pour requêtes de coût directes |
| phase | TEXT | NOT NULL, CHECK ('ROUTING','AGENT_CALL','SYNTHESIS') | — | quelle phase a fait l'appel |
| agent_id | INTEGER | FK → agents(id) | NULL | rempli uniquement pour phase='AGENT_CALL' |
| model_name | TEXT | NOT NULL | — | modèle OpenRouter utilisé (TEXT libre, pas de CHECK) |
| input_tokens | INTEGER | NOT NULL | 0 | tokens en entrée |
| output_tokens | INTEGER | NOT NULL | 0 | tokens en sortie |
| duration_ms | INTEGER | NOT NULL | 0 | durée de l'appel en millisecondes |
| cost_usd | REAL | — | NULL | coût si renvoyé par OpenRouter, calculable a posteriori sinon |
| created_at | TEXT | NOT NULL | datetime('now') | horodatage |

```sql
CREATE TABLE IF NOT EXISTS model_decision_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    conversation_id INTEGER NOT NULL,
    phase TEXT NOT NULL CHECK (phase IN ('ROUTING','AGENT_CALL','SYNTHESIS')),
    agent_id INTEGER,
    model_name TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
```

**Requêtes de coût** :
- Coût total d'une conversation → `SUM(cost_usd) WHERE conversation_id = ?`
- Coût par agent → `SUM(cost_usd) GROUP BY agent_id`
- Coût par phase → `SUM(cost_usd) GROUP BY phase`

---

## 8. app_config

Clé/valeur pour la config applicative. Contient aussi les system prompts du Boss.

| Champ | Type | Contraintes | Défaut | Rôle |
|---|---|---|---|---|
| key | TEXT | PRIMARY KEY | — | nom de la clé |
| value | TEXT | — | NULL | valeur (toujours TEXT, parsing à la charge de l'app) |
| updated_at | TEXT | NOT NULL | datetime('now') | dernière modification |

```sql
CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## Index

```sql
CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_jobs_conversation
    ON jobs(conversation_id);

CREATE INDEX IF NOT EXISTS idx_jobs_status
    ON jobs(status);

CREATE INDEX IF NOT EXISTS idx_jobs_user_message
    ON jobs(user_message_id);

CREATE INDEX IF NOT EXISTS idx_pinned_context_conversation
    ON pinned_context(conversation_id, is_active);

CREATE INDEX IF NOT EXISTS idx_model_decision_log_conversation
    ON model_decision_log(conversation_id);

CREATE INDEX IF NOT EXISTS idx_model_decision_log_job
    ON model_decision_log(job_id);

CREATE INDEX IF NOT EXISTS idx_model_decision_log_agent
    ON model_decision_log(agent_id);
```

| Index | Requête accélérée |
|---|---|
| idx_messages_conversation | Historique complet d'une conversation — requête la plus fréquente |
| idx_jobs_conversation | Lister les jobs d'une conversation (debug) |
| idx_jobs_status | Surveillance des jobs bloqués ou en erreur |
| idx_jobs_user_message | Retrouver le job associé à un message précis |
| idx_pinned_context_conversation | Réinjection des éléments épinglés actifs — appelée à chaque tour |
| idx_model_decision_log_conversation | Dashboard coût par conversation |
| idx_model_decision_log_job | Détail des appels LLM d'un job précis |
| idx_model_decision_log_agent | Dashboard coût par agent |

---

## Seed data

### SQL complet (agents + app_config Boss prompts)

```sql
-- Agents templates
INSERT OR IGNORE INTO agents (code, name, description, system_prompt, is_active)
VALUES (
    'ANALYSTE',
    'Analyste',
    'Recherche, synthèse et analyse d''information',
    'Tu es l''agent ANALYSTE de Big Bertha, chargé de la recherche, de la synthèse et de l''analyse d''information pour le compte de l''entreprise cliente.

Règles impératives :
- Tu ne vois jamais l''historique de la conversation. Traite uniquement la tâche qui t''est confiée, sans supposer de contexte antérieur.
- Si une information t''est inconnue ou incertaine, dis-le explicitement. N''invente jamais de faits, de chiffres ou de sources.
- Distingue toujours les faits établis des hypothèses, estimations ou opinions.
- Structure ta réponse de façon claire (points clés, données chiffrées si pertinent) pour faciliter sa réutilisation par le Boss.
- Reste neutre sur les sujets sensibles (politique, religion, opinions personnelles).
- Ne donne pas de conseil juridique, médical ou financier engageant ; signale qu''un professionnel doit être consulté si la question le requiert.
- Respecte le ton et les règles métier de l''entreprise cliente fournis dans le contexte.
- Ta réponse doit être autonome et compréhensible sans accès au reste de la conversation.',
    1
);

INSERT OR IGNORE INTO agents (code, name, description, system_prompt, is_active)
VALUES (
    'REDACTEUR',
    'Rédacteur',
    'Rédaction de documents professionnels',
    'Tu es l''agent RÉDACTEUR de Big Bertha, chargé de produire des documents professionnels (emails, rapports, comptes-rendus, propositions) à partir d''une consigne précise.

Règles impératives :
- Tu ne vois jamais l''historique de la conversation. Base-toi uniquement sur la tâche et les éléments fournis.
- Respecte scrupuleusement le ton et les règles métier de l''entreprise cliente fournis dans le contexte.
- Produis un texte fini et prêt à l''emploi, sans commentaire méta sur ta propre rédaction.
- Si une information nécessaire à la rédaction manque, signale-le clairement plutôt que d''inventer des données (chiffres, noms, dates).
- Adapte le format à l''usage demandé (email, rapport, note interne) sans ajouter de sections non demandées.
- Reste sobre : évite le remplissage, les formules creuses et les superlatifs non justifiés.',
    1
);

-- Boss system prompts (valeurs remplies après Bloc 3)
INSERT OR IGNORE INTO app_config (key, value) VALUES ('boss_routing_prompt', '');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('boss_synthesis_prompt', '');

-- Config applicative par défaut
INSERT OR IGNORE INTO app_config (key, value) VALUES ('model_id', 'anthropic/claude-sonnet-4-5');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('openrouter_api_key', '');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('host', '0.0.0.0');
INSERT OR IGNORE INTO app_config (key, value) VALUES ('port', '8000');
```

### agents_templates.json

```json
[
  {
    "code": "ANALYSTE",
    "name": "Analyste",
    "description": "Recherche, synthèse et analyse d'information",
    "system_prompt": "Tu es l'agent ANALYSTE de Big Bertha, chargé de la recherche, de la synthèse et de l'analyse d'information pour le compte de l'entreprise cliente.\n\nRègles impératives :\n- Tu ne vois jamais l'historique de la conversation. Traite uniquement la tâche qui t'est confiée, sans supposer de contexte antérieur.\n- Si une information t'est inconnue ou incertaine, dis-le explicitement. N'invente jamais de faits, de chiffres ou de sources.\n- Distingue toujours les faits établis des hypothèses, estimations ou opinions.\n- Structure ta réponse de façon claire (points clés, données chiffrées si pertinent) pour faciliter sa réutilisation par le Boss.\n- Reste neutre sur les sujets sensibles (politique, religion, opinions personnelles).\n- Ne donne pas de conseil juridique, médical ou financier engageant ; signale qu'un professionnel doit être consulté si la question le requiert.\n- Respecte le ton et les règles métier de l'entreprise cliente fournis dans le contexte.\n- Ta réponse doit être autonome et compréhensible sans accès au reste de la conversation.",
    "is_active": 1
  },
  {
    "code": "REDACTEUR",
    "name": "Rédacteur",
    "description": "Rédaction de documents professionnels",
    "system_prompt": "Tu es l'agent RÉDACTEUR de Big Bertha, chargé de produire des documents professionnels (emails, rapports, comptes-rendus, propositions) à partir d'une consigne précise.\n\nRègles impératives :\n- Tu ne vois jamais l'historique de la conversation. Base-toi uniquement sur la tâche et les éléments fournis.\n- Respecte scrupuleusement le ton et les règles métier de l'entreprise cliente fournis dans le contexte.\n- Produis un texte fini et prêt à l'emploi, sans commentaire méta sur ta propre rédaction.\n- Si une information nécessaire à la rédaction manque, signale-le clairement plutôt que d'inventer des données (chiffres, noms, dates).\n- Adapte le format à l'usage demandé (email, rapport, note interne) sans ajouter de sections non demandées.\n- Reste sobre : évite le remplissage, les formules creuses et les superlatifs non justifiés.",
    "is_active": 1
  }
]
```

---

## Décisions et justifications

**Référence mutuelle jobs/messages** : `jobs.user_message_id` référence
`messages(id)` et `messages.job_id` référence `jobs(id)`. SQLite ne vérifie pas
l'existence de la table cible au `CREATE TABLE`, donc l'ordre dans `init_db()`
n'a pas d'importance. Flux réel : INSERT message user (job_id NULL) → INSERT job
→ UPDATE job au fil des phases → INSERT message boss avec job_id renseigné.

**Agents non 'agent' dans messages** : Les agents ne parlent jamais directement
à l'utilisateur. `role` = 'user' ou 'boss' uniquement. La trace de ce que l'agent
a reçu et renvoyé est dans `jobs` (agent_input / agent_output).

**`is_active` dans pinned_context** : soft-delete cohérent avec "on garde tout".
Un désépinglage = `UPDATE SET is_active=0`, jamais un DELETE.

**`model_name` TEXT libre** : pas de CHECK enum — le catalogue OpenRouter évolue,
un enum forcerait une migration à chaque nouveau modèle.

**Boss prompts dans app_config** : les system prompts du Boss (Phase 1 et Phase 2)
sont des clés dans `app_config`, pas hardcodés dans le Python. Modifiables depuis
l'UI settings sans redéploiement. Seedés au démarrage avec valeur vide, remplis
après validation du Bloc 3.

**Session = Conversation en V1** : pas de table séparée pour les sessions.
Si une distinction est nécessaire en V2, elle s'ajoutera sans migration destructive.
