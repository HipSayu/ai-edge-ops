-- V002 Deployments + DEGRADED runtime status
--
-- A deployment is the desired state of one runtime on one node.
-- Status is advanced by DeploymentEvent results published by the Edge Agent.
-- ============================================================

ALTER TYPE runtime_status ADD VALUE IF NOT EXISTS 'DEGRADED' AFTER 'RUNNING';

CREATE TYPE deployment_status AS ENUM (
    'PENDING',
    'IN_PROGRESS',
    'SUCCEEDED',
    'FAILED',
    'REMOVING',
    'REMOVED'
);

-- runtime_id has no FK: the runtime row is deleted once removal is confirmed,
-- while the deployment row is kept as history.
CREATE TABLE deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cluster_id UUID NOT NULL,
    node_id UUID NOT NULL,
    runtime_id UUID NOT NULL,

    spec JSONB NOT NULL,

    status deployment_status NOT NULL DEFAULT 'PENDING',
    last_command_id VARCHAR(64),
    message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_deployments_cluster
        FOREIGN KEY (cluster_id)
        REFERENCES clusters(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_deployments_node
        FOREIGN KEY (node_id)
        REFERENCES nodes(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_deployments_node_id
    ON deployments(node_id);

CREATE INDEX idx_deployments_runtime_id
    ON deployments(runtime_id);

CREATE INDEX idx_deployments_status
    ON deployments(status);

CREATE TRIGGER trg_deployments_updated_at
BEFORE UPDATE ON deployments
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
