-- Initialize database extensions and setup
-- This script runs when PostgreSQL container is first created

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create indexes for text search (will be used by application)
-- These are just placeholders - actual tables created by Alembic migrations

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE aam TO aam;
