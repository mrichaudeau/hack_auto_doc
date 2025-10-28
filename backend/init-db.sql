-- PostgreSQL Database Initialization Script
-- This script is automatically executed when the database is first created
-- Location: /docker-entrypoint-initdb.d/init-db.sql

-- Enable pgvector extension for vector similarity search
-- Required for semantic embeddings storage and cosine similarity operations
-- Used by: Recommendation Engine (Bloc 5) and AI Content Pipeline (Bloc 3)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension installation and log version
-- This query helps troubleshoot extension issues during container startup
DO $$
DECLARE
    ext_version TEXT;
BEGIN
    SELECT extversion INTO ext_version
    FROM pg_extension
    WHERE extname = 'vector';

    IF ext_version IS NOT NULL THEN
        RAISE NOTICE 'pgvector extension successfully installed (version: %)', ext_version;
    ELSE
        RAISE WARNING 'pgvector extension not found after installation attempt';
    END IF;
END $$;

-- Display installed extensions for verification
SELECT extname AS "Extension", extversion AS "Version"
FROM pg_extension
WHERE extname = 'vector';
