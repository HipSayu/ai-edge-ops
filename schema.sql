-- AI Edge Ops reference schema for PostgreSQL.
-- Generated from server/app/modules/*/models.py. init_db() creates these
-- on boot; apply this file for a schema release (see DEPLOY.md).
--
-- The fleet's REPORTED state (health, running image, online) is NOT here:
-- it lives in the in-memory FleetRegistry, rebuilt from MQTT. So are model
-- metrics samples (ring buffer) and the model catalog (read from GHCR).

BEGIN;

CREATE TABLE IF NOT EXISTS alerts (
	id SERIAL NOT NULL, 
	type VARCHAR(32) NOT NULL, 
	severity VARCHAR(32) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	title VARCHAR(256) NOT NULL, 
	description TEXT, 
	device_id VARCHAR(64), 
	deployment_id INTEGER, 
	context JSON NOT NULL, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_alerts_device_id ON alerts (device_id);
CREATE INDEX IF NOT EXISTS ix_alerts_type ON alerts (type);
CREATE INDEX IF NOT EXISTS ix_alerts_status ON alerts (status);
CREATE INDEX IF NOT EXISTS ix_alerts_severity ON alerts (severity);

CREATE TABLE IF NOT EXISTS app_settings (
	key VARCHAR(128) NOT NULL, 
	value JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (key)
);

CREATE TABLE IF NOT EXISTS audit_logs (
	id SERIAL NOT NULL, 
	action VARCHAR(128) NOT NULL, 
	actor VARCHAR(128) NOT NULL, 
	detail TEXT, 
	created_at VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS camera_groups (
	id SERIAL NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	description TEXT, 
	site VARCHAR(128) NOT NULL, 
	camera_ids JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_camera_groups_name ON camera_groups (name);

CREATE TABLE IF NOT EXISTS cameras (
	id SERIAL NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	source VARCHAR(512) NOT NULL, 
	zone VARCHAR(128) NOT NULL, 
	device_id VARCHAR(64), 
	enabled BOOLEAN NOT NULL, 
	metadata_json JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_cameras_name ON cameras (name);

CREATE TABLE IF NOT EXISTS chat_messages (
	id SERIAL NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	text TEXT NOT NULL, 
	created_at VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS devices (
	device_id VARCHAR(64) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	site VARCHAR(128) NOT NULL, 
	labels JSON NOT NULL, 
	desired_image VARCHAR(512), 
	cameras JSON NOT NULL, 
	inference JSON NOT NULL, 
	agent_config JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (device_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_devices_name ON devices (name);
CREATE INDEX IF NOT EXISTS ix_devices_site ON devices (site);

CREATE TABLE IF NOT EXISTS permissions (
	id SERIAL NOT NULL, 
	code VARCHAR(128) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	description TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_permissions_code ON permissions (code);

CREATE TABLE IF NOT EXISTS roles (
	id SERIAL NOT NULL, 
	code VARCHAR(64) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	description TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_roles_code ON roles (code);

CREATE TABLE IF NOT EXISTS users (
	id SERIAL NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255), 
	active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS violations (
	id SERIAL NOT NULL, 
	device_id VARCHAR(64) NOT NULL, 
	zone VARCHAR(128) NOT NULL, 
	violation_type VARCHAR(64) NOT NULL, 
	confidence FLOAT NOT NULL, 
	image_path VARCHAR(512), 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_violations_recorded_at ON violations (recorded_at);
CREATE INDEX IF NOT EXISTS ix_violations_zone ON violations (zone);
CREATE INDEX IF NOT EXISTS ix_violations_violation_type ON violations (violation_type);
CREATE INDEX IF NOT EXISTS ix_violations_device_id ON violations (device_id);

CREATE TABLE IF NOT EXISTS role_permissions (
	role_id INTEGER NOT NULL, 
	permission_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
	FOREIGN KEY(permission_id) REFERENCES permissions (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS snapshots (
	id SERIAL NOT NULL, 
	camera_id INTEGER, 
	image_path VARCHAR(512) NOT NULL, 
	captured_at VARCHAR(64) NOT NULL, 
	labels JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(camera_id) REFERENCES cameras (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS user_roles (
	user_id INTEGER NOT NULL, 
	role_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (user_id, role_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE
);

COMMIT;
