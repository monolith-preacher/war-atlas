"""Search view: link units and equipment to conflicts only through documented, dated relations.

Previously a unit was associated with every conflict overlapping its (often open-ended) existence
in which its polity took part, and equipment with every conflict overlapping its service period.
That is an automatic inference the data policy forbids (e.g. a WWI division appearing under WWII).
Now: units via battles, events, dated subordinations or commands; persons via battles or dated
posts; equipment via dated national
service (equipment_users) or documented unit use (unit_equipment).

Revision ID: 0003
Revises: 0002
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

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
       ARRAY(SELECT b.conflict_id FROM battle_units bu JOIN battles b ON b.id = bu.battle_id WHERE bu.unit_id = u.id
             UNION SELECT e.conflict_id FROM event_units eu JOIN events e ON e.id = eu.event_id WHERE eu.unit_id = u.id
             UNION SELECT c.id FROM conflicts c JOIN unit_subordinations s ON s.unit_id = u.id
              WHERE (s.valid_from IS NULL OR s.valid_from <= c.end_date) AND (s.valid_to IS NULL OR s.valid_to >= c.start_date)
                AND (s.valid_from IS NOT NULL OR s.valid_to IS NOT NULL)
             UNION SELECT c.id FROM conflicts c JOIN person_positions pp ON pp.unit_id = u.id
              WHERE (pp.valid_from IS NULL OR pp.valid_from <= c.end_date) AND (pp.valid_to IS NULL OR pp.valid_to >= c.start_date)
                AND (pp.valid_from IS NOT NULL OR pp.valid_to IS NOT NULL)),
       u.polity_id, NULL, u.formed_on, u.disbanded_on, NULL, NULL, u.echelon, af.branch
  FROM units u LEFT JOIN polities pol ON pol.id = u.polity_id LEFT JOIN armed_forces af ON af.id = u.force_id
 WHERE u.status = 'published'
UNION ALL
SELECT 'person', p.id, p.slug, p.name, p.name_original,
       concat_ws(' · ', pol.short_name, concat(to_char(p.birth_date, 'YYYY'), '–', to_char(p.death_date, 'YYYY'))),
       ARRAY(SELECT DISTINCT b.conflict_id FROM battle_commanders bc JOIN battles b ON b.id = bc.battle_id WHERE bc.person_id = p.id
             UNION SELECT c.id FROM conflicts c JOIN person_positions pp ON pp.person_id = p.id
              WHERE (pp.valid_from IS NULL OR pp.valid_from <= c.end_date) AND (pp.valid_to IS NULL OR pp.valid_to >= c.start_date)
                AND (pp.valid_from IS NOT NULL OR pp.valid_to IS NOT NULL)),
       p.nationality_polity_id, NULL, p.birth_date, p.death_date, NULL, NULL, NULL, NULL
  FROM persons p LEFT JOIN polities pol ON pol.id = p.nationality_polity_id
 WHERE p.status = 'published'
UNION ALL
SELECT 'equipment', e.id, e.slug, e.name, e.name_original, concat_ws(' · ', e.type_label, pol.short_name),
       ARRAY(SELECT c.id FROM conflicts c JOIN equipment_users eu ON eu.equipment_id = e.id
              WHERE (eu.valid_from IS NULL OR eu.valid_from <= c.end_date) AND (eu.valid_to IS NULL OR eu.valid_to >= c.start_date)
                AND (eu.valid_from IS NOT NULL OR eu.valid_to IS NOT NULL)
             UNION SELECT c.id FROM conflicts c JOIN unit_equipment ue ON ue.equipment_id = e.id
              WHERE (ue.valid_from IS NULL OR ue.valid_from <= c.end_date) AND (ue.valid_to IS NULL OR ue.valid_to >= c.start_date)
                AND (ue.valid_from IS NOT NULL OR ue.valid_to IS NOT NULL)),
       e.origin_polity_id, NULL, e.service_from, e.service_to, NULL, NULL, e.category, NULL
  FROM equipment e LEFT JOIN polities pol ON pol.id = e.origin_polity_id
 WHERE e.status = 'published';
"""


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS search_documents")
    op.execute(VIEW)


def downgrade() -> None:
    # restore the 0002 definition
    op.execute("DROP VIEW IF EXISTS search_documents")
    from pathlib import Path

    src = (Path(__file__).parent / "0002_search_view.py").read_text()
    op.execute(src[src.index('VIEW = """') + len('VIEW = """'):src.index('"""\n\n\ndef upgrade')])
