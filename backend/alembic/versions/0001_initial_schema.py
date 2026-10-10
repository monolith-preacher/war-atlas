"""Initial schema: historical, geographic, military, materiel, provenance and admin tables.

Generated with alembic autogenerate from app.models and reviewed by hand.
Temporal exclusion constraints require the btree_gist extension.

Revision ID: 0001
Revises: 
Create Date: 2026-10-10 04:52:20.599048
"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    for ext in ("postgis", "pg_trgm", "unaccent", "btree_gist"):
        op.execute(f"CREATE EXTENSION IF NOT EXISTS {ext}")
    op.create_table('conflicts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('short_name', sa.String(length=40), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('color', sa.String(length=9), nullable=True),
    sa.Column('default_center_lon', sa.Float(), nullable=True),
    sa.Column('default_center_lat', sa.Float(), nullable=True),
    sa.Column('default_zoom', sa.Float(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.CheckConstraint('start_date IS NULL OR end_date IS NULL OR start_date <= end_date', name=op.f('ck_conflicts_valid_interval')),
    sa.ForeignKeyConstraint(['parent_id'], ['conflicts.id'], name=op.f('fk_conflicts_parent_id_conflicts'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conflicts')),
    sa.UniqueConstraint('slug', name=op.f('uq_conflicts_slug'))
    )
    op.create_index(op.f('ix_conflicts_status'), 'conflicts', ['status'], unique=False)
    op.create_index(op.f('ix_conflicts_wikidata_id'), 'conflicts', ['wikidata_id'], unique=False)
    op.create_geospatial_table('places',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('historical_names', sa.Text(), nullable=True),
    sa.Column('modern_country', sa.String(length=80), nullable=True),
    sa.Column('kind', sa.String(length=60), nullable=True),
    sa.Column('geom', Geometry(geometry_type='POINT', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('spatial_role', sa.Enum('exact_location', 'approximate_position', 'area_of_operations', 'route', 'territorial_extent', 'schematic', name='spatialrole', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('precision_m', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_places')),
    sa.UniqueConstraint('slug', name=op.f('uq_places_slug'))
    )
    op.create_geospatial_index('idx_places_geom', 'places', ['geom'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_places_wikidata_id'), 'places', ['wikidata_id'], unique=False)
    op.create_table('polities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('short_name', sa.String(length=80), nullable=True),
    sa.Column('kind', sa.String(length=60), nullable=True),
    sa.Column('color', sa.String(length=9), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_polities_valid_interval')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_polities')),
    sa.UniqueConstraint('slug', name=op.f('uq_polities_slug'))
    )
    op.create_index(op.f('ix_polities_status'), 'polities', ['status'], unique=False)
    op.create_index(op.f('ix_polities_wikidata_id'), 'polities', ['wikidata_id'], unique=False)
    op.create_table('sources',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('kind', sa.Enum('book', 'official_history', 'article', 'archive', 'website', 'dataset', 'encyclopedia', 'map', 'other', name='sourcekind', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('authors', sa.Text(), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('publisher', sa.Text(), nullable=True),
    sa.Column('place', sa.Text(), nullable=True),
    sa.Column('series', sa.Text(), nullable=True),
    sa.Column('isbn', sa.String(length=40), nullable=True),
    sa.Column('url', sa.Text(), nullable=True),
    sa.Column('license', sa.Text(), nullable=True),
    sa.Column('accessed_on', sa.Date(), nullable=True),
    sa.Column('reliability_note', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sources')),
    sa.UniqueConstraint('slug', name=op.f('uq_sources_slug'))
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('display_name', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('admin', 'reviewer', 'editor', name='userrole', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_table('alliances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('conflict_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('side', sa.Enum('a', 'b', 'other', name='side', native_enum=False, create_constraint=True, length=40), nullable=True),
    sa.Column('color', sa.String(length=9), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['conflict_id'], ['conflicts.id'], name=op.f('fk_alliances_conflict_id_conflicts'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_alliances')),
    sa.UniqueConstraint('slug', name=op.f('uq_alliances_slug'))
    )
    op.create_index(op.f('ix_alliances_conflict_id'), 'alliances', ['conflict_id'], unique=False)
    op.create_index(op.f('ix_alliances_status'), 'alliances', ['status'], unique=False)
    op.create_index(op.f('ix_alliances_wikidata_id'), 'alliances', ['wikidata_id'], unique=False)
    op.create_table('armed_forces',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('branch', sa.Enum('army', 'navy', 'air_force', 'marines', 'combined', 'paramilitary', 'other', name='branchkind', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_armed_forces_valid_interval')),
    sa.ForeignKeyConstraint(['parent_id'], ['armed_forces.id'], name=op.f('fk_armed_forces_parent_id_armed_forces'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_armed_forces_polity_id_polities'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_armed_forces')),
    sa.UniqueConstraint('slug', name=op.f('uq_armed_forces_slug'))
    )
    op.create_index(op.f('ix_armed_forces_polity_id'), 'armed_forces', ['polity_id'], unique=False)
    op.create_index(op.f('ix_armed_forces_status'), 'armed_forces', ['status'], unique=False)
    op.create_index(op.f('ix_armed_forces_wikidata_id'), 'armed_forces', ['wikidata_id'], unique=False)
    op.create_table('boundary_datasets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('reference_date', sa.Date(), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('source_id', sa.Integer(), nullable=True),
    sa.Column('license', sa.Text(), nullable=True),
    sa.Column('precision_note', sa.Text(), nullable=True),
    sa.Column('known_issues', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_boundary_datasets_valid_interval')),
    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], name=op.f('fk_boundary_datasets_source_id_sources'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_boundary_datasets')),
    sa.UniqueConstraint('slug', name=op.f('uq_boundary_datasets_slug'))
    )
    op.create_table('citations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source_id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('field', sa.String(length=80), nullable=True),
    sa.Column('pages', sa.String(length=80), nullable=True),
    sa.Column('quote', sa.Text(), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], name=op.f('fk_citations_source_id_sources'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_citations'))
    )
    op.create_index('ix_citations_entity', 'citations', ['entity_type', 'entity_id'], unique=False)
    op.create_index(op.f('ix_citations_source_id'), 'citations', ['source_id'], unique=False)
    op.create_table('equipment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('category', sa.Enum('small_arm', 'machine_gun', 'artillery', 'tank', 'armored_vehicle', 'transport_vehicle', 'aircraft', 'ship', 'submarine', 'landing_craft', 'communications', 'personal_equipment', 'other', name='equipmentcategory', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('type_label', sa.Text(), nullable=True),
    sa.Column('origin_polity_id', sa.Integer(), nullable=True),
    sa.Column('manufacturer', sa.Text(), nullable=True),
    sa.Column('designer', sa.Text(), nullable=True),
    sa.Column('design_period', sa.String(length=60), nullable=True),
    sa.Column('production_period', sa.String(length=60), nullable=True),
    sa.Column('number_built', sa.String(length=80), nullable=True),
    sa.Column('service_from', sa.Date(), nullable=True),
    sa.Column('service_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='service_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('service_to', sa.Date(), nullable=True),
    sa.Column('service_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='service_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('operational_history', sa.Text(), nullable=True),
    sa.Column('specs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.CheckConstraint('service_from IS NULL OR service_to IS NULL OR service_from <= service_to', name=op.f('ck_equipment_service_interval')),
    sa.ForeignKeyConstraint(['origin_polity_id'], ['polities.id'], name=op.f('fk_equipment_origin_polity_id_polities'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_equipment')),
    sa.UniqueConstraint('slug', name=op.f('uq_equipment_slug'))
    )
    op.create_index(op.f('ix_equipment_category'), 'equipment', ['category'], unique=False)
    op.create_index(op.f('ix_equipment_origin_polity_id'), 'equipment', ['origin_polity_id'], unique=False)
    op.create_index(op.f('ix_equipment_status'), 'equipment', ['status'], unique=False)
    op.create_index(op.f('ix_equipment_wikidata_id'), 'equipment', ['wikidata_id'], unique=False)
    op.create_table('figures',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('metric', sa.Enum('strength', 'casualties', 'killed', 'wounded', 'missing', 'captured', 'tanks_lost', 'aircraft_lost', 'civilian_deaths', 'other', name='figuremetric', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('side', sa.Enum('a', 'b', 'other', name='side', native_enum=False, create_constraint=True, length=40), nullable=True),
    sa.Column('polity_id', sa.Integer(), nullable=True),
    sa.Column('value_low', sa.BigInteger(), nullable=True),
    sa.Column('value_high', sa.BigInteger(), nullable=True),
    sa.Column('value_text', sa.Text(), nullable=True),
    sa.Column('scope_note', sa.Text(), nullable=True),
    sa.Column('as_of_date', sa.Date(), nullable=True),
    sa.Column('source_id', sa.Integer(), nullable=True),
    sa.Column('pages', sa.String(length=80), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('value_low IS NOT NULL OR value_high IS NOT NULL OR value_text IS NOT NULL', name=op.f('ck_figures_has_value')),
    sa.CheckConstraint('value_low IS NULL OR value_high IS NULL OR value_low <= value_high', name=op.f('ck_figures_value_range')),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_figures_polity_id_polities'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], name=op.f('fk_figures_source_id_sources'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_figures'))
    )
    op.create_index('ix_figures_entity', 'figures', ['entity_type', 'entity_id'], unique=False)
    op.create_table('import_batches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source_name', sa.String(length=80), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_import_batches_created_by_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_import_batches'))
    )
    op.create_table('media',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('kind', sa.Enum('photo', 'illustration', 'map', 'document', 'insignia', 'scheme', 'other', name='mediakind', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('file_url', sa.Text(), nullable=False),
    sa.Column('thumbnail_url', sa.Text(), nullable=True),
    sa.Column('source_url', sa.Text(), nullable=True),
    sa.Column('author', sa.Text(), nullable=True),
    sa.Column('date_created_text', sa.String(length=80), nullable=True),
    sa.Column('license', sa.String(length=120), nullable=True),
    sa.Column('license_url', sa.Text(), nullable=True),
    sa.Column('attribution', sa.Text(), nullable=True),
    sa.Column('license_verified', sa.Boolean(), nullable=False),
    sa.Column('source_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.CheckConstraint("status <> 'published' OR (license_verified AND license IS NOT NULL)", name=op.f('ck_media_published_requires_license')),
    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], name=op.f('fk_media_source_id_sources'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_media')),
    sa.UniqueConstraint('slug', name=op.f('uq_media_slug'))
    )
    op.create_index(op.f('ix_media_status'), 'media', ['status'], unique=False)
    op.create_table('persons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('birth_date', sa.Date(), nullable=True),
    sa.Column('death_date', sa.Date(), nullable=True),
    sa.Column('birth_place', sa.Text(), nullable=True),
    sa.Column('death_place', sa.Text(), nullable=True),
    sa.Column('nationality_polity_id', sa.Integer(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('biography', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.CheckConstraint('birth_date IS NULL OR death_date IS NULL OR birth_date <= death_date', name=op.f('ck_persons_life_interval')),
    sa.ForeignKeyConstraint(['nationality_polity_id'], ['polities.id'], name=op.f('fk_persons_nationality_polity_id_polities'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_persons')),
    sa.UniqueConstraint('slug', name=op.f('uq_persons_slug'))
    )
    op.create_index(op.f('ix_persons_nationality_polity_id'), 'persons', ['nationality_polity_id'], unique=False)
    op.create_index(op.f('ix_persons_status'), 'persons', ['status'], unique=False)
    op.create_index(op.f('ix_persons_wikidata_id'), 'persons', ['wikidata_id'], unique=False)
    op.create_table('polity_periods',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=False),
    sa.Column('government_type', sa.Text(), nullable=True),
    sa.Column('head_of_state', sa.Text(), nullable=True),
    sa.Column('head_of_government', sa.Text(), nullable=True),
    sa.Column('capital_name', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_polity_periods_valid_interval')),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_polity_periods_polity_id_polities'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_polity_periods'))
    )
    op.create_index(op.f('ix_polity_periods_polity_id'), 'polity_periods', ['polity_id'], unique=False)
    op.create_table('revisions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=30), nullable=False),
    sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_revisions_user_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_revisions'))
    )
    op.create_index('ix_revisions_entity', 'revisions', ['entity_type', 'entity_id'], unique=False)
    op.create_table('theaters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('conflict_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('center_lon', sa.Float(), nullable=True),
    sa.Column('center_lat', sa.Float(), nullable=True),
    sa.Column('zoom', sa.Float(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.CheckConstraint('start_date IS NULL OR end_date IS NULL OR start_date <= end_date', name=op.f('ck_theaters_valid_interval')),
    sa.ForeignKeyConstraint(['conflict_id'], ['conflicts.id'], name=op.f('fk_theaters_conflict_id_conflicts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_id'], ['theaters.id'], name=op.f('fk_theaters_parent_id_theaters'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_theaters')),
    sa.UniqueConstraint('slug', name=op.f('uq_theaters_slug'))
    )
    op.create_index(op.f('ix_theaters_conflict_id'), 'theaters', ['conflict_id'], unique=False)
    op.create_index(op.f('ix_theaters_status'), 'theaters', ['status'], unique=False)
    op.create_index(op.f('ix_theaters_wikidata_id'), 'theaters', ['wikidata_id'], unique=False)
    op.create_table('alliance_memberships',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('alliance_id', sa.Integer(), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=60), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_alliance_memberships_valid_interval')),
    sa.ForeignKeyConstraint(['alliance_id'], ['alliances.id'], name=op.f('fk_alliance_memberships_alliance_id_alliances'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_alliance_memberships_polity_id_polities'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_alliance_memberships'))
    )
    op.create_index(op.f('ix_alliance_memberships_alliance_id'), 'alliance_memberships', ['alliance_id'], unique=False)
    op.create_index(op.f('ix_alliance_memberships_polity_id'), 'alliance_memberships', ['polity_id'], unique=False)
    op.create_table('camouflage_patterns',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('applies_to', sa.String(length=30), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=True),
    sa.Column('force_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('usage_note', sa.Text(), nullable=True),
    sa.Column('colors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_camouflage_patterns_valid_interval')),
    sa.ForeignKeyConstraint(['force_id'], ['armed_forces.id'], name=op.f('fk_camouflage_patterns_force_id_armed_forces'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_camouflage_patterns_polity_id_polities'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_camouflage_patterns')),
    sa.UniqueConstraint('slug', name=op.f('uq_camouflage_patterns_slug'))
    )
    op.create_index(op.f('ix_camouflage_patterns_polity_id'), 'camouflage_patterns', ['polity_id'], unique=False)
    op.create_index(op.f('ix_camouflage_patterns_status'), 'camouflage_patterns', ['status'], unique=False)
    op.create_index(op.f('ix_camouflage_patterns_wikidata_id'), 'camouflage_patterns', ['wikidata_id'], unique=False)
    op.create_geospatial_table('campaigns',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('conflict_id', sa.Integer(), nullable=False),
    sa.Column('theater_id', sa.Integer(), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('kind', sa.Enum('campaign', 'operation', 'offensive', name='campaignkind', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('codename', sa.String(length=120), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('start_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='start_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('end_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='end_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('objectives', sa.Text(), nullable=True),
    sa.Column('outcome', sa.Text(), nullable=True),
    sa.Column('area', Geometry(srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('center_lon', sa.Float(), nullable=True),
    sa.Column('center_lat', sa.Float(), nullable=True),
    sa.Column('zoom', sa.Float(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.CheckConstraint('start_date IS NULL OR end_date IS NULL OR start_date <= end_date', name=op.f('ck_campaigns_valid_interval')),
    sa.ForeignKeyConstraint(['conflict_id'], ['conflicts.id'], name=op.f('fk_campaigns_conflict_id_conflicts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_id'], ['campaigns.id'], name=op.f('fk_campaigns_parent_id_campaigns'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['theater_id'], ['theaters.id'], name=op.f('fk_campaigns_theater_id_theaters'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_campaigns')),
    sa.UniqueConstraint('slug', name=op.f('uq_campaigns_slug'))
    )
    op.create_geospatial_index('idx_campaigns_area', 'campaigns', ['area'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_campaigns_conflict_id'), 'campaigns', ['conflict_id'], unique=False)
    op.create_index(op.f('ix_campaigns_parent_id'), 'campaigns', ['parent_id'], unique=False)
    op.create_index(op.f('ix_campaigns_status'), 'campaigns', ['status'], unique=False)
    op.create_index(op.f('ix_campaigns_theater_id'), 'campaigns', ['theater_id'], unique=False)
    op.create_index(op.f('ix_campaigns_wikidata_id'), 'campaigns', ['wikidata_id'], unique=False)
    op.create_table('conflict_participations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conflict_id', sa.Integer(), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=False),
    sa.Column('alliance_id', sa.Integer(), nullable=True),
    sa.Column('role', sa.String(length=60), nullable=True),
    sa.Column('entry_note', sa.Text(), nullable=True),
    sa.Column('exit_note', sa.Text(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_conflict_participations_valid_interval')),
    sa.ForeignKeyConstraint(['alliance_id'], ['alliances.id'], name=op.f('fk_conflict_participations_alliance_id_alliances'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['conflict_id'], ['conflicts.id'], name=op.f('fk_conflict_participations_conflict_id_conflicts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_conflict_participations_polity_id_polities'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conflict_participations'))
    )
    op.create_index(op.f('ix_conflict_participations_conflict_id'), 'conflict_participations', ['conflict_id'], unique=False)
    op.create_index(op.f('ix_conflict_participations_polity_id'), 'conflict_participations', ['polity_id'], unique=False)
    op.create_table('equipment_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('equipment_id', sa.Integer(), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=False),
    sa.Column('force_id', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_equipment_users_valid_interval')),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], name=op.f('fk_equipment_users_equipment_id_equipment'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['force_id'], ['armed_forces.id'], name=op.f('fk_equipment_users_force_id_armed_forces'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_equipment_users_polity_id_polities'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_equipment_users'))
    )
    op.create_index(op.f('ix_equipment_users_equipment_id'), 'equipment_users', ['equipment_id'], unique=False)
    op.create_index(op.f('ix_equipment_users_polity_id'), 'equipment_users', ['polity_id'], unique=False)
    op.create_table('equipment_variants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('equipment_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('service_from', sa.Date(), nullable=True),
    sa.Column('service_to', sa.Date(), nullable=True),
    sa.Column('specs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.CheckConstraint('service_from IS NULL OR service_to IS NULL OR service_from <= service_to', name=op.f('ck_equipment_variants_service_interval')),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], name=op.f('fk_equipment_variants_equipment_id_equipment'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_equipment_variants')),
    sa.UniqueConstraint('slug', name=op.f('uq_equipment_variants_slug'))
    )
    op.create_index(op.f('ix_equipment_variants_equipment_id'), 'equipment_variants', ['equipment_id'], unique=False)
    op.create_index(op.f('ix_equipment_variants_status'), 'equipment_variants', ['status'], unique=False)
    op.create_geospatial_table('historical_boundaries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dataset_id', sa.Integer(), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=True),
    sa.Column('label', sa.Text(), nullable=False),
    sa.Column('subject_label', sa.Text(), nullable=True),
    sa.Column('border_precision', sa.SmallInteger(), nullable=True),
    sa.Column('geom', Geometry(geometry_type='MULTIPOLYGON', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['dataset_id'], ['boundary_datasets.id'], name=op.f('fk_historical_boundaries_dataset_id_boundary_datasets'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_historical_boundaries_polity_id_polities'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_historical_boundaries'))
    )
    op.create_geospatial_index('idx_historical_boundaries_geom', 'historical_boundaries', ['geom'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_historical_boundaries_dataset_id'), 'historical_boundaries', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_historical_boundaries_polity_id'), 'historical_boundaries', ['polity_id'], unique=False)
    op.create_table('import_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=False),
    sa.Column('external_source', sa.String(length=40), nullable=False),
    sa.Column('external_id', sa.String(length=80), nullable=False),
    sa.Column('external_url', sa.Text(), nullable=True),
    sa.Column('license', sa.String(length=80), nullable=True),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('proposed', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('warnings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='importstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('target_entity_id', sa.Integer(), nullable=True),
    sa.Column('reviewer_id', sa.Integer(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['import_batches.id'], name=op.f('fk_import_records_batch_id_import_batches'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], name=op.f('fk_import_records_reviewer_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_import_records'))
    )
    op.create_index(op.f('ix_import_records_batch_id'), 'import_records', ['batch_id'], unique=False)
    op.create_index('ix_import_records_external', 'import_records', ['external_source', 'external_id'], unique=False)
    op.create_index(op.f('ix_import_records_status'), 'import_records', ['status'], unique=False)
    op.create_table('media_links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('media_id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('caption', sa.Text(), nullable=True),
    sa.Column('role', sa.String(length=40), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['media_id'], ['media.id'], name=op.f('fk_media_links_media_id_media'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_media_links'))
    )
    op.create_index('ix_media_links_entity', 'media_links', ['entity_type', 'entity_id'], unique=False)
    op.create_table('person_ranks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.Integer(), nullable=False),
    sa.Column('rank', sa.Text(), nullable=False),
    sa.Column('rank_original', sa.Text(), nullable=True),
    sa.Column('force_id', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_person_ranks_valid_interval')),
    sa.ForeignKeyConstraint(['force_id'], ['armed_forces.id'], name=op.f('fk_person_ranks_force_id_armed_forces'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name=op.f('fk_person_ranks_person_id_persons'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_person_ranks'))
    )
    op.create_index(op.f('ix_person_ranks_person_id'), 'person_ranks', ['person_id'], unique=False)
    op.create_table('units',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=True),
    sa.Column('is_multinational', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('force_id', sa.Integer(), nullable=True),
    sa.Column('echelon', sa.Enum('supreme_command', 'theater_command', 'army_group', 'field_force', 'army', 'corps', 'division', 'brigade', 'regiment', 'battalion', 'company', 'platoon', 'fleet', 'squadron', 'flotilla', 'air_command', 'wing', 'group', 'other', name='echelon', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('type_label', sa.Text(), nullable=True),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('nickname', sa.Text(), nullable=True),
    sa.Column('formed_on', sa.Date(), nullable=True),
    sa.Column('formed_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='formed_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('disbanded_on', sa.Date(), nullable=True),
    sa.Column('disbanded_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='disbanded_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.CheckConstraint('formed_on IS NULL OR disbanded_on IS NULL OR formed_on <= disbanded_on', name=op.f('ck_units_valid_interval')),
    sa.CheckConstraint('polity_id IS NOT NULL OR is_multinational', name=op.f('ck_units_polity_or_multinational')),
    sa.ForeignKeyConstraint(['force_id'], ['armed_forces.id'], name=op.f('fk_units_force_id_armed_forces'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_units_polity_id_polities'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_units')),
    sa.UniqueConstraint('slug', name=op.f('uq_units_slug'))
    )
    op.create_index(op.f('ix_units_force_id'), 'units', ['force_id'], unique=False)
    op.create_index(op.f('ix_units_polity_id'), 'units', ['polity_id'], unique=False)
    op.create_index(op.f('ix_units_status'), 'units', ['status'], unique=False)
    op.create_index(op.f('ix_units_wikidata_id'), 'units', ['wikidata_id'], unique=False)
    op.create_geospatial_table('battles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('conflict_id', sa.Integer(), nullable=False),
    sa.Column('theater_id', sa.Integer(), nullable=True),
    sa.Column('campaign_id', sa.Integer(), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('kind', sa.Enum('battle', 'landing', 'siege', 'engagement', 'airborne_operation', 'naval_battle', 'liberation', name='battlekind', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('start_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='start_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('end_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='end_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('place_id', sa.Integer(), nullable=True),
    sa.Column('location', Geometry(geometry_type='POINT', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('location_role', sa.Enum('exact_location', 'approximate_position', 'area_of_operations', 'route', 'territorial_extent', 'schematic', name='location_role', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('location_precision_m', sa.Integer(), nullable=True),
    sa.Column('area', Geometry(srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('context', sa.Text(), nullable=True),
    sa.Column('objectives', sa.Text(), nullable=True),
    sa.Column('strategy', sa.Text(), nullable=True),
    sa.Column('result', sa.Text(), nullable=True),
    sa.Column('consequences', sa.Text(), nullable=True),
    sa.Column('zoom', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.CheckConstraint('start_date IS NULL OR end_date IS NULL OR start_date <= end_date', name=op.f('ck_battles_valid_interval')),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], name=op.f('fk_battles_campaign_id_campaigns'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['conflict_id'], ['conflicts.id'], name=op.f('fk_battles_conflict_id_conflicts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_id'], ['battles.id'], name=op.f('fk_battles_parent_id_battles'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['place_id'], ['places.id'], name=op.f('fk_battles_place_id_places'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['theater_id'], ['theaters.id'], name=op.f('fk_battles_theater_id_theaters'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_battles')),
    sa.UniqueConstraint('slug', name=op.f('uq_battles_slug'))
    )
    op.create_geospatial_index('idx_battles_area', 'battles', ['area'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_geospatial_index('idx_battles_location', 'battles', ['location'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_battles_campaign_id'), 'battles', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_battles_conflict_id'), 'battles', ['conflict_id'], unique=False)
    op.create_index(op.f('ix_battles_parent_id'), 'battles', ['parent_id'], unique=False)
    op.create_index(op.f('ix_battles_status'), 'battles', ['status'], unique=False)
    op.create_index(op.f('ix_battles_theater_id'), 'battles', ['theater_id'], unique=False)
    op.create_index(op.f('ix_battles_wikidata_id'), 'battles', ['wikidata_id'], unique=False)
    op.create_table('equipment_camouflages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('equipment_id', sa.Integer(), nullable=False),
    sa.Column('pattern_id', sa.Integer(), nullable=False),
    sa.Column('theater_id', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_equipment_camouflages_valid_interval')),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], name=op.f('fk_equipment_camouflages_equipment_id_equipment'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pattern_id'], ['camouflage_patterns.id'], name=op.f('fk_equipment_camouflages_pattern_id_camouflage_patterns'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['theater_id'], ['theaters.id'], name=op.f('fk_equipment_camouflages_theater_id_theaters'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_equipment_camouflages'))
    )
    op.create_index(op.f('ix_equipment_camouflages_equipment_id'), 'equipment_camouflages', ['equipment_id'], unique=False)
    op.create_index(op.f('ix_equipment_camouflages_pattern_id'), 'equipment_camouflages', ['pattern_id'], unique=False)
    op.create_table('insignia',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('kind', sa.String(length=30), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=True),
    sa.Column('unit_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_insignia_valid_interval')),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_insignia_polity_id_polities'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name=op.f('fk_insignia_unit_id_units'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_insignia')),
    sa.UniqueConstraint('slug', name=op.f('uq_insignia_slug'))
    )
    op.create_index(op.f('ix_insignia_status'), 'insignia', ['status'], unique=False)
    op.create_index(op.f('ix_insignia_unit_id'), 'insignia', ['unit_id'], unique=False)
    op.create_index(op.f('ix_insignia_wikidata_id'), 'insignia', ['wikidata_id'], unique=False)
    op.create_table('person_positions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=True),
    sa.Column('force_id', sa.Integer(), nullable=True),
    sa.Column('polity_id', sa.Integer(), nullable=True),
    sa.Column('kind', sa.Enum('commander', 'acting_commander', 'chief_of_staff', 'deputy', 'staff', 'political', 'other', name='positionkind', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('rank_at_time', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    postgresql.ExcludeConstraint((sa.column('unit_id'), '='), (sa.text("daterange(valid_from, valid_to, '[]')"), '&&'), where=sa.text("kind = 'commander' AND unit_id IS NOT NULL"), using='gist', name='ex_person_positions_single_commander'),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_person_positions_valid_interval')),
    sa.ForeignKeyConstraint(['force_id'], ['armed_forces.id'], name=op.f('fk_person_positions_force_id_armed_forces'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name=op.f('fk_person_positions_person_id_persons'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_person_positions_polity_id_polities'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name=op.f('fk_person_positions_unit_id_units'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_person_positions'))
    )
    op.create_index(op.f('ix_person_positions_person_id'), 'person_positions', ['person_id'], unique=False)
    op.create_index(op.f('ix_person_positions_unit_id'), 'person_positions', ['unit_id'], unique=False)
    op.create_table('uniforms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('name_original', sa.Text(), nullable=True),
    sa.Column('polity_id', sa.Integer(), nullable=False),
    sa.Column('force_id', sa.Integer(), nullable=True),
    sa.Column('unit_id', sa.Integer(), nullable=True),
    sa.Column('theater_id', sa.Integer(), nullable=True),
    sa.Column('camouflage_id', sa.Integer(), nullable=True),
    sa.Column('role_note', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('colors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_uniforms_valid_interval')),
    sa.ForeignKeyConstraint(['camouflage_id'], ['camouflage_patterns.id'], name=op.f('fk_uniforms_camouflage_id_camouflage_patterns'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['force_id'], ['armed_forces.id'], name=op.f('fk_uniforms_force_id_armed_forces'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_uniforms_polity_id_polities'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['theater_id'], ['theaters.id'], name=op.f('fk_uniforms_theater_id_theaters'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name=op.f('fk_uniforms_unit_id_units'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_uniforms')),
    sa.UniqueConstraint('slug', name=op.f('uq_uniforms_slug'))
    )
    op.create_index(op.f('ix_uniforms_polity_id'), 'uniforms', ['polity_id'], unique=False)
    op.create_index(op.f('ix_uniforms_status'), 'uniforms', ['status'], unique=False)
    op.create_index(op.f('ix_uniforms_wikidata_id'), 'uniforms', ['wikidata_id'], unique=False)
    op.create_table('unit_equipment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('equipment_id', sa.Integer(), nullable=False),
    sa.Column('variant_id', sa.Integer(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('quantity_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_unit_equipment_valid_interval')),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], name=op.f('fk_unit_equipment_equipment_id_equipment'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name=op.f('fk_unit_equipment_unit_id_units'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['variant_id'], ['equipment_variants.id'], name=op.f('fk_unit_equipment_variant_id_equipment_variants'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_unit_equipment'))
    )
    op.create_index(op.f('ix_unit_equipment_equipment_id'), 'unit_equipment', ['equipment_id'], unique=False)
    op.create_index(op.f('ix_unit_equipment_unit_id'), 'unit_equipment', ['unit_id'], unique=False)
    op.create_table('unit_names',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('language', sa.String(length=10), nullable=True),
    sa.Column('kind', sa.String(length=30), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_unit_names_valid_interval')),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name=op.f('fk_unit_names_unit_id_units'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_unit_names'))
    )
    op.create_index(op.f('ix_unit_names_unit_id'), 'unit_names', ['unit_id'], unique=False)
    op.create_table('unit_subordinations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('parent_unit_id', sa.Integer(), nullable=True),
    sa.Column('parent_force_id', sa.Integer(), nullable=True),
    sa.Column('relation', sa.Enum('organic', 'attached', 'operational_control', 'administrative', name='subordinationkind', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    postgresql.ExcludeConstraint((sa.column('unit_id'), '='), (sa.text("daterange(valid_from, valid_to, '[]')"), '&&'), where=sa.text("relation = 'organic'"), using='gist', name='ex_unit_subordinations_organic_overlap'),
    sa.CheckConstraint('(parent_unit_id IS NOT NULL) <> (parent_force_id IS NOT NULL)', name=op.f('ck_unit_subordinations_exactly_one_parent')),
    sa.CheckConstraint('parent_unit_id IS NULL OR parent_unit_id <> unit_id', name=op.f('ck_unit_subordinations_not_self')),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_unit_subordinations_valid_interval')),
    sa.ForeignKeyConstraint(['parent_force_id'], ['armed_forces.id'], name=op.f('fk_unit_subordinations_parent_force_id_armed_forces'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_unit_id'], ['units.id'], name=op.f('fk_unit_subordinations_parent_unit_id_units'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name=op.f('fk_unit_subordinations_unit_id_units'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_unit_subordinations'))
    )
    op.create_index(op.f('ix_unit_subordinations_parent_force_id'), 'unit_subordinations', ['parent_force_id'], unique=False)
    op.create_index(op.f('ix_unit_subordinations_parent_unit_id'), 'unit_subordinations', ['parent_unit_id'], unique=False)
    op.create_index(op.f('ix_unit_subordinations_unit_id'), 'unit_subordinations', ['unit_id'], unique=False)
    op.create_table('battle_commanders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('battle_id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.Integer(), nullable=False),
    sa.Column('side', sa.Enum('a', 'b', 'other', name='side', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('role', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['battle_id'], ['battles.id'], name=op.f('fk_battle_commanders_battle_id_battles'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name=op.f('fk_battle_commanders_person_id_persons'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_battle_commanders')),
    sa.UniqueConstraint('battle_id', 'person_id', name='uq_battle_commanders_battle_person')
    )
    op.create_index(op.f('ix_battle_commanders_battle_id'), 'battle_commanders', ['battle_id'], unique=False)
    op.create_index(op.f('ix_battle_commanders_person_id'), 'battle_commanders', ['person_id'], unique=False)
    op.create_table('battle_participants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('battle_id', sa.Integer(), nullable=False),
    sa.Column('polity_id', sa.Integer(), nullable=False),
    sa.Column('side', sa.Enum('a', 'b', 'other', name='side', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('role', sa.String(length=80), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['battle_id'], ['battles.id'], name=op.f('fk_battle_participants_battle_id_battles'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_battle_participants_polity_id_polities'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_battle_participants')),
    sa.UniqueConstraint('battle_id', 'polity_id', name='uq_battle_participants_battle_polity')
    )
    op.create_index(op.f('ix_battle_participants_battle_id'), 'battle_participants', ['battle_id'], unique=False)
    op.create_index(op.f('ix_battle_participants_polity_id'), 'battle_participants', ['polity_id'], unique=False)
    op.create_table('battle_units',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('battle_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('side', sa.Enum('a', 'b', 'other', name='side', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('role', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_battle_units_valid_interval')),
    sa.ForeignKeyConstraint(['battle_id'], ['battles.id'], name=op.f('fk_battle_units_battle_id_battles'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name=op.f('fk_battle_units_unit_id_units'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_battle_units')),
    sa.UniqueConstraint('battle_id', 'unit_id', name='uq_battle_units_battle_unit')
    )
    op.create_index(op.f('ix_battle_units_battle_id'), 'battle_units', ['battle_id'], unique=False)
    op.create_index(op.f('ix_battle_units_unit_id'), 'battle_units', ['unit_id'], unique=False)
    op.create_geospatial_table('events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('conflict_id', sa.Integer(), nullable=False),
    sa.Column('theater_id', sa.Integer(), nullable=True),
    sa.Column('campaign_id', sa.Integer(), nullable=True),
    sa.Column('battle_id', sa.Integer(), nullable=True),
    sa.Column('kind', sa.String(length=60), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('date_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='date_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('time_of_day', sa.String(length=120), nullable=True),
    sa.Column('place_id', sa.Integer(), nullable=True),
    sa.Column('geom', Geometry(srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('spatial_role', sa.Enum('exact_location', 'approximate_position', 'area_of_operations', 'route', 'territorial_extent', 'schematic', name='spatialrole', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('precision_m', sa.Integer(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('importance', sa.SmallInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('provenance_note', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.String(length=20), nullable=True),
    sa.CheckConstraint('start_date IS NULL OR end_date IS NULL OR start_date <= end_date', name=op.f('ck_events_valid_interval')),
    sa.ForeignKeyConstraint(['battle_id'], ['battles.id'], name=op.f('fk_events_battle_id_battles'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], name=op.f('fk_events_campaign_id_campaigns'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['conflict_id'], ['conflicts.id'], name=op.f('fk_events_conflict_id_conflicts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['place_id'], ['places.id'], name=op.f('fk_events_place_id_places'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['theater_id'], ['theaters.id'], name=op.f('fk_events_theater_id_theaters'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_events')),
    sa.UniqueConstraint('slug', name=op.f('uq_events_slug'))
    )
    op.create_geospatial_index('idx_events_geom', 'events', ['geom'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_events_battle_id'), 'events', ['battle_id'], unique=False)
    op.create_index(op.f('ix_events_campaign_id'), 'events', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_events_conflict_id'), 'events', ['conflict_id'], unique=False)
    op.create_index(op.f('ix_events_start_date'), 'events', ['start_date'], unique=False)
    op.create_index(op.f('ix_events_status'), 'events', ['status'], unique=False)
    op.create_index(op.f('ix_events_wikidata_id'), 'events', ['wikidata_id'], unique=False)
    op.create_table('event_persons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=80), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], name=op.f('fk_event_persons_event_id_events'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name=op.f('fk_event_persons_person_id_persons'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_event_persons')),
    sa.UniqueConstraint('event_id', 'person_id', name='uq_event_persons_event_person')
    )
    op.create_index(op.f('ix_event_persons_event_id'), 'event_persons', ['event_id'], unique=False)
    op.create_index(op.f('ix_event_persons_person_id'), 'event_persons', ['person_id'], unique=False)
    op.create_table('event_units',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=80), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], name=op.f('fk_event_units_event_id_events'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name=op.f('fk_event_units_unit_id_units'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_event_units')),
    sa.UniqueConstraint('event_id', 'unit_id', name='uq_event_units_event_unit')
    )
    op.create_index(op.f('ix_event_units_event_id'), 'event_units', ['event_id'], unique=False)
    op.create_index(op.f('ix_event_units_unit_id'), 'event_units', ['unit_id'], unique=False)
    op.create_geospatial_table('map_features',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('conflict_id', sa.Integer(), nullable=False),
    sa.Column('campaign_id', sa.Integer(), nullable=True),
    sa.Column('battle_id', sa.Integer(), nullable=True),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('unit_id', sa.Integer(), nullable=True),
    sa.Column('polity_id', sa.Integer(), nullable=True),
    sa.Column('side', sa.Enum('a', 'b', 'other', name='side', native_enum=False, create_constraint=True, length=40), nullable=True),
    sa.Column('feature_type', sa.Enum('front_line', 'advance_axis', 'withdrawal_axis', 'defensive_line', 'objective', 'unit_position', 'fortification', 'airfield', 'naval_base', 'landing_zone', 'drop_zone', 'area_of_operations', 'territorial_control', 'route', name='mapfeaturetype', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('label', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('geom', Geometry(srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('spatial_role', sa.Enum('exact_location', 'approximate_position', 'area_of_operations', 'route', 'territorial_extent', 'schematic', name='spatialrole', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('certainty', sa.Enum('verified', 'estimated', 'interpreted', 'reconstructed', 'disputed', 'unverified', name='certainty', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('precision_m', sa.Integer(), nullable=True),
    sa.Column('method_note', sa.Text(), nullable=True),
    sa.Column('style', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', name='publicationstatus', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_from_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_from_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('valid_to_precision', sa.Enum('day', 'month', 'year', 'circa', 'attested', name='valid_to_precision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.CheckConstraint('valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to', name=op.f('ck_map_features_valid_interval')),
    sa.ForeignKeyConstraint(['battle_id'], ['battles.id'], name=op.f('fk_map_features_battle_id_battles'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], name=op.f('fk_map_features_campaign_id_campaigns'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['conflict_id'], ['conflicts.id'], name=op.f('fk_map_features_conflict_id_conflicts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], name=op.f('fk_map_features_event_id_events'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['polity_id'], ['polities.id'], name=op.f('fk_map_features_polity_id_polities'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name=op.f('fk_map_features_unit_id_units'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_map_features')),
    sa.UniqueConstraint('slug', name=op.f('uq_map_features_slug'))
    )
    op.create_geospatial_index('idx_map_features_geom', 'map_features', ['geom'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_map_features_battle_id'), 'map_features', ['battle_id'], unique=False)
    op.create_index(op.f('ix_map_features_campaign_id'), 'map_features', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_map_features_conflict_id'), 'map_features', ['conflict_id'], unique=False)
    op.create_index(op.f('ix_map_features_feature_type'), 'map_features', ['feature_type'], unique=False)
    op.create_index(op.f('ix_map_features_status'), 'map_features', ['status'], unique=False)
    op.create_index(op.f('ix_map_features_unit_id'), 'map_features', ['unit_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_map_features_unit_id'), table_name='map_features')
    op.drop_index(op.f('ix_map_features_status'), table_name='map_features')
    op.drop_index(op.f('ix_map_features_feature_type'), table_name='map_features')
    op.drop_index(op.f('ix_map_features_conflict_id'), table_name='map_features')
    op.drop_index(op.f('ix_map_features_campaign_id'), table_name='map_features')
    op.drop_index(op.f('ix_map_features_battle_id'), table_name='map_features')
    op.drop_geospatial_index('idx_map_features_geom', table_name='map_features', postgresql_using='gist', column_name='geom')
    op.drop_geospatial_table('map_features')
    op.drop_index(op.f('ix_event_units_unit_id'), table_name='event_units')
    op.drop_index(op.f('ix_event_units_event_id'), table_name='event_units')
    op.drop_table('event_units')
    op.drop_index(op.f('ix_event_persons_person_id'), table_name='event_persons')
    op.drop_index(op.f('ix_event_persons_event_id'), table_name='event_persons')
    op.drop_table('event_persons')
    op.drop_index(op.f('ix_events_wikidata_id'), table_name='events')
    op.drop_index(op.f('ix_events_status'), table_name='events')
    op.drop_index(op.f('ix_events_start_date'), table_name='events')
    op.drop_index(op.f('ix_events_conflict_id'), table_name='events')
    op.drop_index(op.f('ix_events_campaign_id'), table_name='events')
    op.drop_index(op.f('ix_events_battle_id'), table_name='events')
    op.drop_geospatial_index('idx_events_geom', table_name='events', postgresql_using='gist', column_name='geom')
    op.drop_geospatial_table('events')
    op.drop_index(op.f('ix_battle_units_unit_id'), table_name='battle_units')
    op.drop_index(op.f('ix_battle_units_battle_id'), table_name='battle_units')
    op.drop_table('battle_units')
    op.drop_index(op.f('ix_battle_participants_polity_id'), table_name='battle_participants')
    op.drop_index(op.f('ix_battle_participants_battle_id'), table_name='battle_participants')
    op.drop_table('battle_participants')
    op.drop_index(op.f('ix_battle_commanders_person_id'), table_name='battle_commanders')
    op.drop_index(op.f('ix_battle_commanders_battle_id'), table_name='battle_commanders')
    op.drop_table('battle_commanders')
    op.drop_index(op.f('ix_unit_subordinations_unit_id'), table_name='unit_subordinations')
    op.drop_index(op.f('ix_unit_subordinations_parent_unit_id'), table_name='unit_subordinations')
    op.drop_index(op.f('ix_unit_subordinations_parent_force_id'), table_name='unit_subordinations')
    op.drop_table('unit_subordinations')
    op.drop_index(op.f('ix_unit_names_unit_id'), table_name='unit_names')
    op.drop_table('unit_names')
    op.drop_index(op.f('ix_unit_equipment_unit_id'), table_name='unit_equipment')
    op.drop_index(op.f('ix_unit_equipment_equipment_id'), table_name='unit_equipment')
    op.drop_table('unit_equipment')
    op.drop_index(op.f('ix_uniforms_wikidata_id'), table_name='uniforms')
    op.drop_index(op.f('ix_uniforms_status'), table_name='uniforms')
    op.drop_index(op.f('ix_uniforms_polity_id'), table_name='uniforms')
    op.drop_table('uniforms')
    op.drop_index(op.f('ix_person_positions_unit_id'), table_name='person_positions')
    op.drop_index(op.f('ix_person_positions_person_id'), table_name='person_positions')
    op.drop_table('person_positions')
    op.drop_index(op.f('ix_insignia_wikidata_id'), table_name='insignia')
    op.drop_index(op.f('ix_insignia_unit_id'), table_name='insignia')
    op.drop_index(op.f('ix_insignia_status'), table_name='insignia')
    op.drop_table('insignia')
    op.drop_index(op.f('ix_equipment_camouflages_pattern_id'), table_name='equipment_camouflages')
    op.drop_index(op.f('ix_equipment_camouflages_equipment_id'), table_name='equipment_camouflages')
    op.drop_table('equipment_camouflages')
    op.drop_index(op.f('ix_battles_wikidata_id'), table_name='battles')
    op.drop_index(op.f('ix_battles_theater_id'), table_name='battles')
    op.drop_index(op.f('ix_battles_status'), table_name='battles')
    op.drop_index(op.f('ix_battles_parent_id'), table_name='battles')
    op.drop_index(op.f('ix_battles_conflict_id'), table_name='battles')
    op.drop_index(op.f('ix_battles_campaign_id'), table_name='battles')
    op.drop_geospatial_index('idx_battles_location', table_name='battles', postgresql_using='gist', column_name='location')
    op.drop_geospatial_index('idx_battles_area', table_name='battles', postgresql_using='gist', column_name='area')
    op.drop_geospatial_table('battles')
    op.drop_index(op.f('ix_units_wikidata_id'), table_name='units')
    op.drop_index(op.f('ix_units_status'), table_name='units')
    op.drop_index(op.f('ix_units_polity_id'), table_name='units')
    op.drop_index(op.f('ix_units_force_id'), table_name='units')
    op.drop_table('units')
    op.drop_index(op.f('ix_person_ranks_person_id'), table_name='person_ranks')
    op.drop_table('person_ranks')
    op.drop_index('ix_media_links_entity', table_name='media_links')
    op.drop_table('media_links')
    op.drop_index(op.f('ix_import_records_status'), table_name='import_records')
    op.drop_index('ix_import_records_external', table_name='import_records')
    op.drop_index(op.f('ix_import_records_batch_id'), table_name='import_records')
    op.drop_table('import_records')
    op.drop_index(op.f('ix_historical_boundaries_polity_id'), table_name='historical_boundaries')
    op.drop_index(op.f('ix_historical_boundaries_dataset_id'), table_name='historical_boundaries')
    op.drop_geospatial_index('idx_historical_boundaries_geom', table_name='historical_boundaries', postgresql_using='gist', column_name='geom')
    op.drop_geospatial_table('historical_boundaries')
    op.drop_index(op.f('ix_equipment_variants_status'), table_name='equipment_variants')
    op.drop_index(op.f('ix_equipment_variants_equipment_id'), table_name='equipment_variants')
    op.drop_table('equipment_variants')
    op.drop_index(op.f('ix_equipment_users_polity_id'), table_name='equipment_users')
    op.drop_index(op.f('ix_equipment_users_equipment_id'), table_name='equipment_users')
    op.drop_table('equipment_users')
    op.drop_index(op.f('ix_conflict_participations_polity_id'), table_name='conflict_participations')
    op.drop_index(op.f('ix_conflict_participations_conflict_id'), table_name='conflict_participations')
    op.drop_table('conflict_participations')
    op.drop_index(op.f('ix_campaigns_wikidata_id'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_theater_id'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_status'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_parent_id'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_conflict_id'), table_name='campaigns')
    op.drop_geospatial_index('idx_campaigns_area', table_name='campaigns', postgresql_using='gist', column_name='area')
    op.drop_geospatial_table('campaigns')
    op.drop_index(op.f('ix_camouflage_patterns_wikidata_id'), table_name='camouflage_patterns')
    op.drop_index(op.f('ix_camouflage_patterns_status'), table_name='camouflage_patterns')
    op.drop_index(op.f('ix_camouflage_patterns_polity_id'), table_name='camouflage_patterns')
    op.drop_table('camouflage_patterns')
    op.drop_index(op.f('ix_alliance_memberships_polity_id'), table_name='alliance_memberships')
    op.drop_index(op.f('ix_alliance_memberships_alliance_id'), table_name='alliance_memberships')
    op.drop_table('alliance_memberships')
    op.drop_index(op.f('ix_theaters_wikidata_id'), table_name='theaters')
    op.drop_index(op.f('ix_theaters_status'), table_name='theaters')
    op.drop_index(op.f('ix_theaters_conflict_id'), table_name='theaters')
    op.drop_table('theaters')
    op.drop_index('ix_revisions_entity', table_name='revisions')
    op.drop_table('revisions')
    op.drop_index(op.f('ix_polity_periods_polity_id'), table_name='polity_periods')
    op.drop_table('polity_periods')
    op.drop_index(op.f('ix_persons_wikidata_id'), table_name='persons')
    op.drop_index(op.f('ix_persons_status'), table_name='persons')
    op.drop_index(op.f('ix_persons_nationality_polity_id'), table_name='persons')
    op.drop_table('persons')
    op.drop_index(op.f('ix_media_status'), table_name='media')
    op.drop_table('media')
    op.drop_table('import_batches')
    op.drop_index('ix_figures_entity', table_name='figures')
    op.drop_table('figures')
    op.drop_index(op.f('ix_equipment_wikidata_id'), table_name='equipment')
    op.drop_index(op.f('ix_equipment_status'), table_name='equipment')
    op.drop_index(op.f('ix_equipment_origin_polity_id'), table_name='equipment')
    op.drop_index(op.f('ix_equipment_category'), table_name='equipment')
    op.drop_table('equipment')
    op.drop_index(op.f('ix_citations_source_id'), table_name='citations')
    op.drop_index('ix_citations_entity', table_name='citations')
    op.drop_table('citations')
    op.drop_table('boundary_datasets')
    op.drop_index(op.f('ix_armed_forces_wikidata_id'), table_name='armed_forces')
    op.drop_index(op.f('ix_armed_forces_status'), table_name='armed_forces')
    op.drop_index(op.f('ix_armed_forces_polity_id'), table_name='armed_forces')
    op.drop_table('armed_forces')
    op.drop_index(op.f('ix_alliances_wikidata_id'), table_name='alliances')
    op.drop_index(op.f('ix_alliances_status'), table_name='alliances')
    op.drop_index(op.f('ix_alliances_conflict_id'), table_name='alliances')
    op.drop_table('alliances')
    op.drop_table('users')
    op.drop_table('sources')
    op.drop_index(op.f('ix_polities_wikidata_id'), table_name='polities')
    op.drop_index(op.f('ix_polities_status'), table_name='polities')
    op.drop_table('polities')
    op.drop_index(op.f('ix_places_wikidata_id'), table_name='places')
    op.drop_geospatial_index('idx_places_geom', table_name='places', postgresql_using='gist', column_name='geom')
    op.drop_geospatial_table('places')
    op.drop_index(op.f('ix_conflicts_wikidata_id'), table_name='conflicts')
    op.drop_index(op.f('ix_conflicts_status'), table_name='conflicts')
    op.drop_table('conflicts')
