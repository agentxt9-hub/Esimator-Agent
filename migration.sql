-- =============================================================================
-- MIGRATION: Add Authentication & Multi-Tenancy
-- Run this in pgAdmin BEFORE starting the app for the first time with auth.
-- All statements are idempotent — safe to run on an existing database.
-- =============================================================================

-- 1. Create the companies table (tenant companies)
CREATE TABLE IF NOT EXISTS companies (
    id         SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create the users table
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    company_id    INTEGER NOT NULL REFERENCES companies(id),
    username      VARCHAR(100) UNIQUE NOT NULL,
    email         VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20) NOT NULL DEFAULT 'estimator',  -- 'admin' | 'estimator' | 'viewer'
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Add company_id to existing tables
ALTER TABLE projects          ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id);
ALTER TABLE library_items     ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id);
ALTER TABLE global_properties ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id);
ALTER TABLE company_profile   ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id);

-- 4. Performance indexes
CREATE INDEX IF NOT EXISTS idx_projects_company          ON projects(company_id);
CREATE INDEX IF NOT EXISTS idx_library_items_company     ON library_items(company_id);
CREATE INDEX IF NOT EXISTS idx_global_properties_company ON global_properties(company_id);
CREATE INDEX IF NOT EXISTS idx_users_company             ON users(company_id);

-- =============================================================================
-- AFTER RUNNING THIS SCRIPT:
-- 1. Start the app — it will create the first admin account via /admin
-- 2. Use the bootstrap script below to create your first admin account
-- 3. After creating the admin + first company, assign existing data to that company:
--
-- UPDATE projects          SET company_id = 1 WHERE company_id IS NULL;
-- UPDATE library_items     SET company_id = 1 WHERE company_id IS NULL;
-- UPDATE global_properties SET company_id = 1 WHERE company_id IS NULL;
-- UPDATE company_profile   SET company_id = 1 WHERE company_id IS NULL;
--
-- Replace '1' with the actual id of your first company.
-- =============================================================================
