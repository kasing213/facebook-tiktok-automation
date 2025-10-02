-- PostgreSQL Database Setup Script for Facebook/TikTok Automation Project
-- Run this as postgres user: sudo -u postgres psql -f setup_database.sql

-- Create the database user
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'fbauto') THEN
      CREATE USER fbauto WITH PASSWORD 'password';
   END IF;
END
$$;

-- Create the database
SELECT 'CREATE DATABASE fbauto OWNER fbauto'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'fbauto')\gexec

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON DATABASE fbauto TO fbauto;
GRANT CREATE ON SCHEMA public TO fbauto;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fbauto;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fbauto;

-- Set default privileges for future tables/sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO fbauto;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO fbauto;

-- Display confirmation
\echo 'Database setup completed successfully!'
\echo 'User: fbauto'
\echo 'Database: fbauto'
\echo 'Password: password'
\echo ''
\echo 'Connection string: postgresql+psycopg2://fbauto:password@localhost:5432/fbauto'