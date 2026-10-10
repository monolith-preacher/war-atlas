"""Search: trigram indexes and the unified `search_documents` view.

The view only exposes *published* records. It is a plain view (always consistent);
when the catalogue grows it can be turned into a materialized view refreshed by the
admin workflow without changing the API.

Revision ID: 0002
Revises: 0001
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TRGM_INDEXED = ["conflicts", "theaters", "campaigns", "battles", "places", "polities", "units", "persons", "equipment", "events"]

# IMMUTABLE wrapper so unaccent() can be used in expression indexes.
IMMUTABLE_UNACCENT = """
CREATE OR REPLACE FUNCTION wa_unaccent(text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT AS $$ SELECT public.unaccent('public.unaccent', $1) $$;
"""

VIEW = """
CREATE VIEW search_documents AS
SELECT 'conflict'::text AS entity_type, c.id AS entity_id, c.slug, c.name AS title,
       concat_ws(' ', c.name_original, c.short_name) AS alt_names,
       concat(to_char(c.start_date, 'YYYY'), '–', to_char(c.end_date, 'YYYY')) AS subtitle,
       ARRAY[c.id] AS conflict_ids, NULL::int AS polity_id, NULL::int AS theater_id,
       c.start_date, c.end_date, c.default_center_lon AS lon, c.default_center_lat AS lat,
       NULL::text AS category, NULL::text AS branch
  FROM conflicts c WHERE c.status = 'published'
UNION ALL
SELECT 'theater', t.id, t.slug, t.name, t.name_original, 'Teatro de operações',
       ARRAY[t.conflict_id], NULL, t.id, t.start_date, t.end_date, t.center_lon, t.center_lat, NULL, NULL
  FROM theaters t WHERE t.status = 'published'
UNION ALL
SELECT 'campaign', c.id, c.slug, c.name, concat_ws(' ', c.name_original, c.codename),
       CASE c.kind WHEN 'operation' THEN 'Operação' WHEN 'offensive' THEN 'Ofensiva' ELSE 'Campanha' END,
       ARRAY[c.conflict_id], NULL, c.theater_id, c.start_date, c.end_date,
       COALESCE(c.center_lon, ST_X(ST_PointOnSurface(c.area))), COALESCE(c.center_lat, ST_Y(ST_PointOnSurface(c.area))), c.kind, NULL
  FROM campaigns c WHERE c.status = 'published'
UNION ALL
SELECT 'battle', b.id, b.slug, b.name, b.name_original, 'Batalha',
       ARRAY[b.conflict_id], NULL, b.theater_id, b.start_date, b.end_date,
       ST_X(b.location), ST_Y(b.location), b.kind, NULL
  FROM battles b WHERE b.status = 'published'
UNION ALL
SELECT 'event', e.id, e.slug, e.title, NULL, 'Evento',
       ARRAY[e.conflict_id], NULL, e.theater_id, e.start_date, COALESCE(e.end_date, e.start_date),
       ST_X(ST_PointOnSurface(e.geom)), ST_Y(ST_PointOnSurface(e.geom)), e.kind, NULL
  FROM events e WHERE e.status = 'published'
UNION ALL
SELECT 'place', p.id, p.slug, p.name, concat_ws(' ', p.name_original, p.historical_names),
       concat_ws(' · ', 'Localidade', p.modern_country),
       ARRAY(SELECT DISTINCT b.conflict_id FROM battles b WHERE b.place_id = p.id AND b.status = 'published'
             UNION SELECT DISTINCT e.conflict_id FROM events e WHERE e.place_id = p.id AND e.status = 'published'),
       NULL, NULL, NULL, NULL, ST_X(p.geom), ST_Y(p.geom), p.kind, NULL
  FROM places p
UNION ALL
SELECT 'polity', p.id, p.slug, p.name, concat_ws(' ', p.name_original, p.short_name), 'País / entidade política',
       ARRAY(SELECT cp.conflict_id FROM conflict_participations cp WHERE cp.polity_id = p.id),
       p.id, NULL, p.valid_from, p.valid_to, NULL, NULL, p.kind, NULL
  FROM polities p WHERE p.status = 'published'
UNION ALL
SELECT 'unit', u.id, u.slug, u.name,
       concat_ws(' ', u.name_original, u.nickname, (SELECT string_agg(n.name, ' ') FROM unit_names n WHERE n.unit_id = u.id)),
       concat_ws(' · ', u.type_label, pol.short_name),
       ARRAY(SELECT DISTINCT b.conflict_id FROM battle_units bu JOIN battles b ON b.id = bu.battle_id WHERE bu.unit_id = u.id
             UNION SELECT c.id FROM conflicts c
              WHERE (u.formed_on IS NULL OR u.formed_on <= c.end_date) AND (u.disbanded_on IS NULL OR u.disbanded_on >= c.start_date)
                AND EXISTS (SELECT 1 FROM conflict_participations cp WHERE cp.conflict_id = c.id AND cp.polity_id = u.polity_id)),
       u.polity_id, NULL, u.formed_on, u.disbanded_on, NULL, NULL, u.echelon, af.branch
  FROM units u JOIN polities pol ON pol.id = u.polity_id LEFT JOIN armed_forces af ON af.id = u.force_id
 WHERE u.status = 'published'
UNION ALL
SELECT 'person', p.id, p.slug, p.name, p.name_original,
       concat_ws(' · ', pol.short_name, concat(to_char(p.birth_date, 'YYYY'), '–', to_char(p.death_date, 'YYYY'))),
       ARRAY(SELECT DISTINCT b.conflict_id FROM battle_commanders bc JOIN battles b ON b.id = bc.battle_id WHERE bc.person_id = p.id
             UNION SELECT c.id FROM conflicts c JOIN person_positions pp ON pp.person_id = p.id
              WHERE (pp.valid_from IS NULL OR pp.valid_from <= c.end_date) AND (pp.valid_to IS NULL OR pp.valid_to >= c.start_date)),
       p.nationality_polity_id, NULL, p.birth_date, p.death_date, NULL, NULL, NULL, NULL
  FROM persons p LEFT JOIN polities pol ON pol.id = p.nationality_polity_id
 WHERE p.status = 'published'
UNION ALL
SELECT 'equipment', e.id, e.slug, e.name, e.name_original, concat_ws(' · ', e.type_label, pol.short_name),
       ARRAY(SELECT c.id FROM conflicts c
              WHERE (e.service_from IS NULL OR e.service_from <= c.end_date) AND (e.service_to IS NULL OR e.service_to >= c.start_date)
                AND e.service_from IS NOT NULL),
       e.origin_polity_id, NULL, e.service_from, e.service_to, NULL, NULL, e.category, NULL
  FROM equipment e LEFT JOIN polities pol ON pol.id = e.origin_polity_id
 WHERE e.status = 'published';
"""


def upgrade() -> None:
    op.execute(IMMUTABLE_UNACCENT)
    for table in TRGM_INDEXED:
        col = "title" if table == "events" else "name"
        op.execute(
            f"CREATE INDEX ix_{table}_{col}_trgm ON {table} USING gin (lower(wa_unaccent({col})) gin_trgm_ops)"
        )
    op.execute(VIEW)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS search_documents")
    for table in TRGM_INDEXED:
        col = "title" if table == "events" else "name"
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_{col}_trgm")
    op.execute("DROP FUNCTION IF EXISTS wa_unaccent(text)")
