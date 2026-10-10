-- Executed once, when the database volume is first created.
-- Migrations also run CREATE EXTENSION IF NOT EXISTS, so this file is a convenience.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS btree_gist;
