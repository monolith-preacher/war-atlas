/** Types mirroring the War Atlas REST API responses. */

export type ISODate = string
export type Precision = 'day' | 'month' | 'year' | 'circa' | 'attested'
export type Certainty = 'verified' | 'estimated' | 'interpreted' | 'reconstructed' | 'disputed' | 'unverified'
export type SpatialRole = 'exact_location' | 'approximate_position' | 'area_of_operations' | 'route' | 'territorial_extent' | 'schematic'
export type EntityType =
  | 'conflict' | 'theater' | 'campaign' | 'battle' | 'event' | 'place' | 'polity' | 'unit' | 'person' | 'equipment'
  | 'armed_force' | 'source' | 'map_feature' | 'alliance' | 'uniform' | 'camouflage_pattern'

export interface Temporal {
  valid_from: ISODate | null
  valid_from_precision: Precision | null
  valid_to: ISODate | null
  valid_to_precision: Precision | null
}

export interface Ref {
  type: EntityType
  id: number
  slug: string | null
  name: string
  [extra: string]: unknown
}

export interface Source {
  id: number
  slug: string
  kind: string
  title: string
  authors: string | null
  year: number | null
  publisher: string | null
  place: string | null
  series: string | null
  isbn: string | null
  url: string | null
  license: string | null
  accessed_on: ISODate | null
  reliability_note: string | null
  citation_count?: number
}

export interface Citation {
  source: Source
  field: string | null
  pages: string | null
  quote: string | null
  note: string | null
}

export interface Figure {
  id: number
  metric: string
  side: 'a' | 'b' | 'other' | null
  polity: { id: number; name: string | null } | null
  value_low: number | null
  value_high: number | null
  value_text: string | null
  scope_note: string | null
  as_of_date: ISODate | null
  certainty: Certainty
  pages: string | null
  notes: string | null
  source: Source | null
}

export interface MediaItem {
  id: number
  kind: string
  title: string
  caption: string | null
  file_url: string
  thumbnail_url: string | null
  source_url: string | null
  author: string | null
  license: string | null
  license_url: string | null
  attribution: string | null
}

export interface Documented {
  citations: Citation[]
  media: MediaItem[]
  figures?: Figure[]
  certainty?: Certainty
  provenance_note?: string | null
  wikidata_id?: string | null
}

export interface ConflictSummary {
  id: number
  slug: string
  name: string
  name_original: string | null
  short_name: string | null
  start_date: ISODate
  end_date: ISODate
  summary: string | null
  color: string | null
  default_view: { center: [number, number]; zoom: number } | null
  counts?: { battles: number; events: number; theaters: number }
}

export interface BattleBrief {
  id: number
  slug: string
  name: string
  kind: string
  start_date: ISODate | null
  end_date: ISODate | null
  start_precision: Precision
  end_precision: Precision
  location: [number, number] | null
  parent_id: number | null
  campaign_id: number | null
  theater_id: number | null
  summary: string | null
  zoom: number | null
}

export interface CampaignBrief {
  id: number
  slug: string
  name: string
  kind: string
  codename: string | null
  start_date: ISODate | null
  end_date: ISODate | null
  parent_id: number | null
  theater_id: number | null
  summary: string | null
  center: [number, number] | null
  zoom: number | null
}

export interface EventBrief {
  id: number
  slug: string
  title: string
  kind: string
  start_date: ISODate
  end_date: ISODate | null
  date_precision: Precision
  time_of_day: string | null
  importance: number
  location: [number, number] | null
  spatial_role: SpatialRole
  precision_m: number | null
  battle_id: number | null
  campaign_id: number | null
  summary: string | null
  certainty: Certainty
}

export interface TheaterNode {
  id: number
  slug: string
  name: string
  name_original: string | null
  start_date: ISODate | null
  end_date: ISODate | null
  summary: string | null
  center: [number, number] | null
  zoom: number | null
  campaigns: CampaignBrief[]
  battles: BattleBrief[]
}

export interface Participant extends Temporal {
  polity: Ref & { short_name: string; color: string | null }
  alliance_id: number | null
  role: string | null
  entry_note: string | null
  exit_note: string | null
}

export interface ConflictDetail extends ConflictSummary, Documented {
  description: string | null
  theaters: TheaterNode[]
  alliances: { id: number; slug: string; name: string; name_original: string | null; side: string | null; color: string | null; summary: string | null }[]
  participants: Participant[]
  boundary_datasets: { slug: string; name: string; reference_date: ISODate; valid_from: ISODate | null; valid_to: ISODate | null }[]
}

export interface Timeline {
  conflict: ConflictSummary
  events: EventBrief[]
  battles: BattleBrief[]
  campaigns: CampaignBrief[]
  detailed_days: ISODate[]
}

export interface BoundaryDatasetMeta {
  slug: string
  name: string
  reference_date: ISODate
  valid_from: ISODate | null
  valid_to: ISODate | null
  license: string | null
  precision_note: string | null
  known_issues: string | null
  certainty: Certainty
  source: Source | null
  stale: boolean
}

export interface MapState {
  date: ISODate
  boundary_dataset: BoundaryDatasetMeta | null
  participants: {
    polity_id: number
    slug: string
    name: string
    color: string | null
    role: string | null
    alliance_id: number | null
    alliance_name: string | null
    side: string | null
    alliance_color: string | null
  }[]
  alliances: { id: number; name: string; side: string | null; color: string | null }[]
}

export interface SearchItem {
  type: EntityType
  id: number
  slug: string
  title: string
  subtitle: string | null
  start_date: ISODate | null
  end_date: ISODate | null
  category: string | null
  location: [number, number] | null
}

export interface SearchResponse {
  query: string
  total: number
  groups: { type: EntityType; items: SearchItem[] }[]
}

export interface UnitBrief {
  id: number
  slug: string
  name: string
  name_original: string | null
  nickname: string | null
  echelon: string
  type_label: string | null
  polity_id: number | null
  force_id: number | null
  is_multinational: boolean
  formed_on: ISODate | null
  formed_precision: Precision
  disbanded_on: ISODate | null
  disbanded_precision: Precision
}

export interface TreeNode extends UnitBrief {
  relation: (Temporal & { kind: string; notes: string | null }) | null
  commanders: ({ person: Ref; kind: string; title: string } & Temporal)[]
  children: TreeNode[]
  has_more: boolean
}

export interface ReplayStep {
  date: ISODate
  events: {
    id: number
    slug: string
    title: string
    summary: string | null
    kind: string
    importance: number
    time_of_day: string | null
    date_precision: Precision
    certainty: Certainty
    location: [number, number] | null
    spatial_role: SpatialRole
    precision_m: number | null
  }[]
  features_starting: string[]
}

export interface Replay {
  scope: { type: 'campaign' | 'battle'; slug: string; name: string; start_date: ISODate; end_date: ISODate; center: [number, number] | null; zoom: number | null; conflict: string }
  method: string
  steps: ReplayStep[]
  features: ({ slug: string; label: string; feature_type: string; spatial_role: SpatialRole; certainty: Certainty; method_note: string | null } & Temporal)[]
}

// Detail pages are rich and heterogeneous; panels access them with these loose types.
export type Detail = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
