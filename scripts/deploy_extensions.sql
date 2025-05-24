-- KREDILAKAY/scripts/deploy_extensions.sql
-- Script d'activation des extensions PostgreSQL pour Render.com

DO $$
BEGIN
    -- 1. Extension pgcrypto (cryptographie)
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto'
    ) THEN
        CREATE EXTENSION pgcrypto;
        RAISE NOTICE 'Extension pgcrypto installée avec succès';
    ELSE
        RAISE NOTICE 'Extension pgcrypto déjà présente';
    END IF;

    -- 2. Extension unaccent (recherche insensible aux accents)
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'unaccent'
    ) THEN
        CREATE EXTENSION unaccent;
        RAISE NOTICE 'Extension unaccent installée avec succès';
    ELSE
        RAISE NOTICE 'Extension unaccent déjà présente';
    END IF;

    -- 3. Extension pg_trgm (recherche avancée)
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'
    ) THEN
        CREATE EXTENSION pg_trgm;
        RAISE NOTICE 'Extension pg_trgm installée avec succès';
    ELSE
        RAISE NOTICE 'Extension pg_trgm déjà présente';
    END IF;

    -- 4. Extension uuid-ossp (génération d'UUID)
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp'
    ) THEN
        CREATE EXTENSION "uuid-ossp";
        RAISE NOTICE 'Extension uuid-ossp installée avec succès';
    ELSE
        RAISE NOTICE 'Extension uuid-ossp déjà présente';
    END IF;

EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Erreur lors de l''installation des extensions: %', SQLERRM;
END $$;

-- Création du schéma principal si inexistant
CREATE SCHEMA IF NOT EXISTS kredilakay;

-- Configuration spécifique pour les performances sur Render
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET effective_cache_size = '1536MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET work_mem = '32MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET timezone = 'America/Port-au-Prince';

-- Appliquer les changements de configuration
SELECT pg_reload_conf();

-- Vérification finale
SELECT extname, extversion 
FROM pg_extension 
WHERE extname IN ('pgcrypto', 'unaccent', 'pg_trgm', 'uuid-ossp');
