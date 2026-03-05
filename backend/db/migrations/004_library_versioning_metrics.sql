-- Migration 004 : Ajout versioning et métriques pour library_documents
-- Date : 2026-03-05
-- Description : Ajoute les colonnes de versioning et les tables de métriques

-- 1. Ajouter colonnes de versioning à library_documents
ALTER TABLE library_documents ADD COLUMN version INTEGER DEFAULT 1 NOT NULL;
ALTER TABLE library_documents ADD COLUMN previous_version_id TEXT;
ALTER TABLE library_documents ADD COLUMN is_active INTEGER DEFAULT 1 NOT NULL;

-- 2. Créer table d'historique des versions
CREATE TABLE IF NOT EXISTS library_document_versions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    icon TEXT,
    description TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    agents TEXT,
    created_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    change_summary TEXT,
    FOREIGN KEY (document_id) REFERENCES library_documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_library_versions_document_id ON library_document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_library_versions_version ON library_document_versions(version);

-- 3. Créer table de métriques d'utilisation
CREATE TABLE IF NOT EXISTS library_document_metrics (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TEXT,
    total_read_time_seconds INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES library_documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, agent_id)
);

CREATE INDEX IF NOT EXISTS idx_library_metrics_document_id ON library_document_metrics(document_id);
CREATE INDEX IF NOT EXISTS idx_library_metrics_agent_id ON library_document_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_library_metrics_access_count ON library_document_metrics(access_count DESC);

-- 4. Créer table de logs d'accès détaillés
CREATE TABLE IF NOT EXISTS library_access_logs (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    accessed_at TEXT NOT NULL,
    access_type TEXT NOT NULL CHECK(access_type IN ('read', 'search', 'reference')),
    context TEXT,
    FOREIGN KEY (document_id) REFERENCES library_documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_library_logs_document_id ON library_access_logs(document_id);
CREATE INDEX IF NOT EXISTS idx_library_logs_agent_id ON library_access_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_library_logs_accessed_at ON library_access_logs(accessed_at DESC);
