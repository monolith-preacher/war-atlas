import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { ConflictDetail, ConflictSummary, Detail, MapState, Replay, SearchResponse, Source, Timeline } from '../lib/types'

const STATIC = { staleTime: 5 * 60_000 }

export const useHealth = () => useQuery({ queryKey: ['health'], queryFn: () => api.get<{ status: string; has_content: boolean }>('/health'), retry: 1, refetchInterval: (q) => (q.state.error ? 10_000 : false) })

export const useConflicts = () => useQuery({ queryKey: ['conflicts'], queryFn: () => api.get<ConflictSummary[]>('/conflicts'), ...STATIC })

export const useConflict = (slug: string | null) =>
  useQuery({ queryKey: ['conflict', slug], queryFn: () => api.get<ConflictDetail>(`/conflicts/${slug}`), enabled: !!slug, ...STATIC })

export const useTimeline = (slug: string | null) =>
  useQuery({ queryKey: ['timeline', slug], queryFn: () => api.get<Timeline>(`/conflicts/${slug}/timeline`), enabled: !!slug, ...STATIC })

export const useMapState = (conflict: string | null, date: string | null) =>
  useQuery({
    queryKey: ['map-state', conflict, date],
    queryFn: () => api.get<MapState>('/map/state', { conflict, date }),
    enabled: !!conflict && !!date,
    placeholderData: keepPreviousData,
    ...STATIC,
  })

export const useBoundaries = (dataset: string | null | undefined) =>
  useQuery({
    queryKey: ['boundaries', dataset],
    queryFn: () => api.get<GeoJSON.FeatureCollection>(`/map/boundary-datasets/${dataset}/geojson`),
    enabled: !!dataset,
    staleTime: Infinity,
  })

export const useMapFeatures = (conflict: string | null, date: string | null, window: number) =>
  useQuery({
    queryKey: ['map-features', conflict, date, window],
    queryFn: ({ signal }) => api.get<GeoJSON.FeatureCollection>('/map/features', { conflict, date, window }, signal),
    enabled: !!conflict && !!date,
    placeholderData: keepPreviousData,
    ...STATIC,
  })

const DETAIL_PATH: Record<string, string> = {
  conflict: 'conflicts', theater: 'theaters', campaign: 'campaigns', battle: 'battles', event: 'events', place: 'places',
  polity: 'polities', unit: 'units', person: 'persons', equipment: 'equipment', armed_force: 'forces', source: 'sources', map_feature: 'map/features',
}

/** Entities whose sheet depends on the reference date. */
export const DATE_AWARE = new Set(['polity', 'unit', 'person', 'equipment', 'armed_force'])

export function detailPath(type: string, slug: string) {
  return `/${DETAIL_PATH[type] ?? type}/${slug}`
}

export const useDetail = (type: string, slug: string, date: string | null, conflict: string | null) =>
  useQuery({
    queryKey: ['detail', type, slug, DATE_AWARE.has(type) ? date : null, type === 'polity' ? conflict : null],
    queryFn: () => api.get<Detail>(detailPath(type, slug), {
      date: DATE_AWARE.has(type) ? date : undefined,
      conflict: type === 'polity' ? conflict : undefined,
    }),
    enabled: !!slug && !!DETAIL_PATH[type],
    placeholderData: keepPreviousData,
    ...STATIC,
  })

export interface SearchFilters {
  types?: string
  conflict?: string | null
  polity?: string
  theater?: string
  date_from?: string
  date_to?: string
  category?: string
  branch?: string
}

export const useSearch = (q: string, filters: SearchFilters) =>
  useQuery({
    queryKey: ['search', q, filters],
    queryFn: ({ signal }) => api.get<SearchResponse>('/search', { q, ...filters }, signal),
    enabled: q.trim().length >= 2,
    placeholderData: keepPreviousData,
  })

export const useReplay = (scope: string | null, slug: string | null) =>
  useQuery({ queryKey: ['replay', scope, slug], queryFn: () => api.get<Replay>(`/replay/${scope}/${slug}`), enabled: !!scope && !!slug, ...STATIC })

export const useEquipmentList = (params: { category?: string; conflict?: string | null; polity?: string; q?: string }) =>
  useQuery({ queryKey: ['equipment', params], queryFn: () => api.get<Detail[]>('/equipment', params), placeholderData: keepPreviousData, ...STATIC })

export const usePolities = (conflict: string | null) =>
  useQuery({ queryKey: ['polities', conflict], queryFn: () => api.get<Detail[]>('/polities', { conflict }), ...STATIC })

export const useUniforms = (conflict: string | null) =>
  useQuery({ queryKey: ['uniforms', conflict], queryFn: () => api.get<Detail[]>('/uniforms', { conflict }), ...STATIC })

export const useCamouflages = () => useQuery({ queryKey: ['camouflages'], queryFn: () => api.get<Detail[]>('/camouflages'), ...STATIC })

export const useSources = () => useQuery({ queryKey: ['sources'], queryFn: () => api.get<Source[]>('/sources'), ...STATIC })
