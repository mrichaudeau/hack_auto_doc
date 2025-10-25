#!/bin/bash
# Database initialization script for PostgreSQL with pgvector
# This script runs automatically when the PostgreSQL container is first created

set -e

echo "==============================================="
echo "Initializing Technology Watch Platform Database"
echo "==============================================="

# Enable pgvector extension
echo "Enabling pgvector extension..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create pgvector extension
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Verify extension is installed
    SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

    -- Display success message
    \echo '✓ pgvector extension enabled successfully'
EOSQL

echo "==============================================="
echo "Database initialization completed!"
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"
echo "Extensions: pgvector"
echo "==============================================="
