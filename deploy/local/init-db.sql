-- =============================================================================
-- Initialize database extensions and setup
-- This script runs when PostgreSQL container is first created
-- =============================================================================

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For trigram-based text search

-- Grant permissions (user comes from POSTGRES_USER env var)
GRANT ALL PRIVILEGES ON DATABASE aam TO aam;
