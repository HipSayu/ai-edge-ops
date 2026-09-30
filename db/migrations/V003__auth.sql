-- V003 Password login + roles for users
--
-- Passwords are stored as Argon2 hashes only. Refresh tokens live in Redis, not here.
-- ============================================================

CREATE TYPE user_role AS ENUM (
    'ADMIN',
    'OPERATOR',
    'VIEWER'
);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_hash TEXT,
    ADD COLUMN IF NOT EXISTS role user_role NOT NULL DEFAULT 'VIEWER';
