-- ASTRA - V001 Initial Database Schema
-- PostgreSQL
--
-- Scope:
--   Users, API keys, Clusters, Nodes, Runtimes, Models,
--   Model Classes, Cluster/Node/Runtime Logs,
--   Chat Sessions and Chat Messages.
--
-- Security note:
--   Store only a hash of API keys, never the plaintext secret.
--   RBAC / permissions are intentionally deferred to a later migration.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE user_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'SUSPENDED'
);

CREATE TYPE api_key_status AS ENUM (
    'ACTIVE',
    'REVOKED',
    'EXPIRED'
);

CREATE TYPE api_key_type AS ENUM (
    'USER',
    'NODE_AGENT',
    'SERVICE'
);

CREATE TYPE cluster_status AS ENUM (
    'ONLINE',
    'OFFLINE',
    'DEGRADED',
    'UNKNOWN'
);

CREATE TYPE node_status AS ENUM (
    'ONLINE',
    'OFFLINE',
    'DEGRADED',
    'UNKNOWN'
);

CREATE TYPE runtime_status AS ENUM (
    'CREATING',
    'STARTING',
    'RUNNING',
    'STOPPING',
    'STOPPED',
    'RESTARTING',
    'FAILED',
    'UNKNOWN'
);

CREATE TYPE runtime_type AS ENUM (
    'VISION',
    'SAFETY',
    'ANOMALY',
    'OCR',
    'CUSTOM'
);

CREATE TYPE model_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'DEPRECATED'
);

CREATE TYPE log_level AS ENUM (
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR',
    'CRITICAL'
);

CREATE TYPE chat_role AS ENUM (
    'USER',
    'ASSISTANT',
    'SYSTEM',
    'TOOL'
);

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),

    status user_status NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_status
    ON users(status);

-- ============================================================
-- API KEYS
-- ============================================================
-- Only key_hash is persisted.
-- The plaintext key is returned once at creation time and must
-- not be stored in the database.
--
-- key_prefix is safe to display for identifying a key, e.g.:
--   astra_sk_a1b2c3...
-- ============================================================

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID,

    name VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(32) NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,

    key_type api_key_type NOT NULL DEFAULT 'USER',
    status api_key_status NOT NULL DEFAULT 'ACTIVE',

    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,

    CONSTRAINT fk_api_keys_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_api_keys_user_id
    ON api_keys(user_id);

CREATE INDEX idx_api_keys_status
    ON api_keys(status);

CREATE INDEX idx_api_keys_prefix
    ON api_keys(key_prefix);

-- ============================================================
-- CLUSTERS
-- ============================================================

CREATE TABLE clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    status cluster_status NOT NULL DEFAULT 'UNKNOWN',

    location VARCHAR(255),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_clusters_status
    ON clusters(status);

-- ============================================================
-- NODES
-- ============================================================

CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cluster_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255),
    ip_address INET,

    status node_status NOT NULL DEFAULT 'UNKNOWN',

    agent_version VARCHAR(100),

    cpu_cores INTEGER,
    memory_total_mb BIGINT,
    gpu_name VARCHAR(255),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    last_heartbeat_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_nodes_cluster
        FOREIGN KEY (cluster_id)
        REFERENCES clusters(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_nodes_cluster_name
        UNIQUE (cluster_id, name)
);

CREATE INDEX idx_nodes_cluster_id
    ON nodes(cluster_id);

CREATE INDEX idx_nodes_status
    ON nodes(status);

CREATE INDEX idx_nodes_heartbeat
    ON nodes(last_heartbeat_at);

-- ============================================================
-- NODE API KEYS
-- ============================================================
-- A node agent can authenticate independently from a human user.
-- This avoids forcing an Edge Agent to use a user credential.
-- Again, only a hash is stored.
-- ============================================================

CREATE TABLE node_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    node_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(32) NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,

    status api_key_status NOT NULL DEFAULT 'ACTIVE',

    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,

    CONSTRAINT fk_node_api_keys_node
        FOREIGN KEY (node_id)
        REFERENCES nodes(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_node_api_keys_node_id
    ON node_api_keys(node_id);

CREATE INDEX idx_node_api_keys_status
    ON node_api_keys(status);

-- ============================================================
-- MODELS
-- ============================================================

CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL,
    version VARCHAR(100) NOT NULL,

    description TEXT,

    framework VARCHAR(100),
    task VARCHAR(100),

    artifact_uri TEXT,

    status model_status NOT NULL DEFAULT 'ACTIVE',

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_models_name_version
        UNIQUE (name, version)
);

CREATE INDEX idx_models_status
    ON models(status);

-- ============================================================
-- MODEL CLASSES
-- ============================================================

CREATE TABLE model_classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    model_id UUID NOT NULL,

    class_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_model_classes_model
        FOREIGN KEY (model_id)
        REFERENCES models(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_model_class
        UNIQUE (model_id, class_id)
);

CREATE INDEX idx_model_classes_model_id
    ON model_classes(model_id);

-- ============================================================
-- RUNTIMES
-- ============================================================

CREATE TABLE runtimes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    node_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    type runtime_type NOT NULL,

    status runtime_status NOT NULL DEFAULT 'UNKNOWN',

    image_uri TEXT,
    image_tag VARCHAR(255),

    model_id UUID,

    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    environment JSONB NOT NULL DEFAULT '{}'::jsonb,
    resource_limits JSONB NOT NULL DEFAULT '{}'::jsonb,

    container_id VARCHAR(255),

    started_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_runtimes_node
        FOREIGN KEY (node_id)
        REFERENCES nodes(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_runtimes_model
        FOREIGN KEY (model_id)
        REFERENCES models(id)
        ON DELETE SET NULL,

    CONSTRAINT uq_runtime_node_name
        UNIQUE (node_id, name)
);

CREATE INDEX idx_runtimes_node_id
    ON runtimes(node_id);

CREATE INDEX idx_runtimes_model_id
    ON runtimes(model_id);

CREATE INDEX idx_runtimes_status
    ON runtimes(status);

-- ============================================================
-- CLUSTER LOGS
-- ============================================================

CREATE TABLE cluster_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    cluster_id UUID NOT NULL,

    level log_level NOT NULL,
    event_type VARCHAR(100),

    message TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_cluster_logs_cluster
        FOREIGN KEY (cluster_id)
        REFERENCES clusters(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_cluster_logs_cluster_time
    ON cluster_logs(cluster_id, created_at DESC);

CREATE INDEX idx_cluster_logs_level
    ON cluster_logs(level);

-- ============================================================
-- NODE LOGS
-- ============================================================

CREATE TABLE node_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    node_id UUID NOT NULL,

    level log_level NOT NULL,
    event_type VARCHAR(100),

    message TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_node_logs_node
        FOREIGN KEY (node_id)
        REFERENCES nodes(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_node_logs_node_time
    ON node_logs(node_id, created_at DESC);

CREATE INDEX idx_node_logs_level
    ON node_logs(level);

-- ============================================================
-- RUNTIME LOGS
-- ============================================================

CREATE TABLE runtime_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    runtime_id UUID NOT NULL,

    level log_level NOT NULL,
    event_type VARCHAR(100),

    message TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_runtime_logs_runtime
        FOREIGN KEY (runtime_id)
        REFERENCES runtimes(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_runtime_logs_runtime_time
    ON runtime_logs(runtime_id, created_at DESC);

CREATE INDEX idx_runtime_logs_level
    ON runtime_logs(level);

-- ============================================================
-- CHAT SESSIONS
-- ============================================================

CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    title VARCHAR(255),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_chat_sessions_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_chat_sessions_user_time
    ON chat_sessions(user_id, updated_at DESC);

-- ============================================================
-- CHAT MESSAGES
-- ============================================================

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    session_id UUID NOT NULL,

    role chat_role NOT NULL,

    content TEXT,

    tool_name VARCHAR(255),
    tool_call_id VARCHAR(255),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_chat_messages_session
        FOREIGN KEY (session_id)
        REFERENCES chat_sessions(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_chat_messages_session_time
    ON chat_messages(session_id, created_at ASC);

CREATE INDEX idx_chat_messages_tool_call
    ON chat_messages(tool_call_id);

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_clusters_updated_at
BEFORE UPDATE ON clusters
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_nodes_updated_at
BEFORE UPDATE ON nodes
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_models_updated_at
BEFORE UPDATE ON models
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_runtimes_updated_at
BEFORE UPDATE ON runtimes
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_chat_sessions_updated_at
BEFORE UPDATE ON chat_sessions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();