-- ============================================================
-- V004: node metric history + node-health early warning (TimescaleDB)
-- ============================================================
-- node_metrics            one row / node / sampling tick (5 s): the MVP feature row the Edge model scored
-- node_health_predictions risk score per tick
-- node_health_alarms      one row per alarm episode; `outcome` is filled later to measure the model in prod
-- Raw rows are compressed after 1 day and dropped after 90 days; alarms are kept.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE node_metrics (
    ts                     TIMESTAMPTZ NOT NULL,
    node_id                UUID NOT NULL,
    cluster_id             UUID NOT NULL,

    -- connectivity (Edge-side proxies)
    heartbeat_age_sec      REAL,
    connection_error_count INTEGER,
    -- hardware
    cpu_usage_pct          REAL,
    memory_usage_pct       REAL,
    gpu_usage_pct          REAL,
    gpu_temperature_c      REAL,
    disk_usage_pct         REAL,
    -- runtime (aggregated over the node's runtimes: min fps, max latency, summed counters)
    inference_fps          REAL,
    inference_latency_ms   REAL,
    runtime_restart_count  INTEGER,
    runtime_error_count    INTEGER,

    extra                  JSONB NOT NULL DEFAULT '{}'::jsonb,

    PRIMARY KEY (node_id, ts),
    CONSTRAINT fk_node_metrics_node FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

SELECT create_hypertable('node_metrics', 'ts', chunk_time_interval => INTERVAL '1 day');
ALTER TABLE node_metrics SET (timescaledb.compress, timescaledb.compress_segmentby = 'node_id');
SELECT add_compression_policy('node_metrics', INTERVAL '1 day');
SELECT add_retention_policy('node_metrics', INTERVAL '90 days');

CREATE TABLE node_health_predictions (
    ts            TIMESTAMPTZ NOT NULL,
    node_id       UUID NOT NULL,
    risk          REAL NOT NULL,
    alarm         BOOLEAN NOT NULL,
    threshold     REAL NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    source        VARCHAR(10) NOT NULL DEFAULT 'edge',   -- edge | cloud

    PRIMARY KEY (node_id, ts),
    CONSTRAINT fk_health_predictions_node FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

SELECT create_hypertable('node_health_predictions', 'ts', chunk_time_interval => INTERVAL '1 day');
ALTER TABLE node_health_predictions SET (timescaledb.compress, timescaledb.compress_segmentby = 'node_id');
SELECT add_compression_policy('node_health_predictions', INTERVAL '1 day');
SELECT add_retention_policy('node_health_predictions', INTERVAL '90 days');

CREATE TABLE node_health_alarms (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    node_id       UUID NOT NULL,
    started_at    TIMESTAMPTZ NOT NULL,
    ended_at      TIMESTAMPTZ,
    peak_risk     REAL NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    outcome       VARCHAR(20),          -- NULL (unreviewed) | TRUE_POSITIVE | FALSE_ALARM

    CONSTRAINT fk_health_alarms_node FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE,
    CONSTRAINT uq_health_alarms_node_start UNIQUE (node_id, started_at),
    CONSTRAINT ck_health_alarms_outcome CHECK (outcome IN ('TRUE_POSITIVE', 'FALSE_ALARM'))
);

CREATE INDEX idx_health_alarms_open ON node_health_alarms(node_id) WHERE ended_at IS NULL;
CREATE INDEX idx_health_alarms_started ON node_health_alarms(started_at DESC);
