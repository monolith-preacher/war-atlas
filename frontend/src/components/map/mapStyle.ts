/**
 * Base MapLibre style. The physical basemap (Natural Earth, public domain) contains NO
 * modern political borders: political geography comes only from the historical
 * boundary snapshots served by the API. The optional "modern reference" layer is
 * clearly labelled as such in the UI.
 */
import type { StyleSpecification } from 'maplibre-gl'
import { config } from '../../lib/config'

export const COLORS = {
  ocean: '#0f1519',
  land: '#1d2225',
  landEdge: '#2c3337',
  lake: '#142029',
  river: '#36566e',
  border: '#c9b48a',
  sideA: '#6f9fd6',
  sideB: '#d9705a',
  neutral: '#9aa3ab',
  gold: '#d8bd84',
  label: '#e8dfc9',
  halo: '#0d1012',
}

const EMPTY: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }

export const SIDE_COLOR = ['match', ['get', 'side'], 'a', COLORS.sideA, 'b', COLORS.sideB, COLORS.neutral]

export function buildStyle(): StyleSpecification {
  const sources: StyleSpecification['sources'] = {
    land: { type: 'geojson', data: '/basemap/land.geojson', attribution: '<a href="https://www.naturalearthdata.com" target="_blank">Natural Earth</a>' },
    lakes: { type: 'geojson', data: '/basemap/lakes.geojson' },
    rivers: { type: 'geojson', data: '/basemap/rivers.geojson' },
    boundaries: { type: 'geojson', data: EMPTY, attribution: 'Fronteiras: <a href="https://github.com/aourednik/historical-basemaps" target="_blank">historical-basemaps</a> (GPL-3.0)' },
    features: { type: 'geojson', data: EMPTY },
    arrows: { type: 'geojson', data: EMPTY },
    battles: { type: 'geojson', data: EMPTY, cluster: true, clusterRadius: 42, clusterMaxZoom: 9 },
  }
  if (config.terrainTilesUrl) {
    sources.dem = {
      type: 'raster-dem', tiles: [config.terrainTilesUrl], encoding: 'terrarium', tileSize: 256, maxzoom: 13,
      attribution: 'Relevo: <a href="https://registry.opendata.aws/terrain-tiles/" target="_blank">Terrain Tiles (AWS Open Data / Mapzen)</a>',
    }
  }
  if (config.modernTilesUrl) {
    sources.modern = {
      type: 'vector', url: config.modernTilesUrl,
      attribution: 'Referência moderna: <a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> © <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>',
    }
  }

  const layers: StyleSpecification['layers'] = [
    { id: 'background', type: 'background', paint: { 'background-color': COLORS.ocean } },
    { id: 'land', type: 'fill', source: 'land', paint: { 'fill-color': COLORS.land, 'fill-outline-color': COLORS.landEdge } },
  ]
  if (sources.dem) {
    layers.push({
      id: 'hillshade', type: 'hillshade', source: 'dem', layout: { visibility: 'none' },
      paint: { 'hillshade-exaggeration': 0.45, 'hillshade-shadow-color': '#05080a', 'hillshade-highlight-color': '#5d6560', 'hillshade-accent-color': '#2a302c' },
    })
  }
  layers.push(
    { id: 'lakes', type: 'fill', source: 'lakes', paint: { 'fill-color': COLORS.lake } },
    { id: 'rivers', type: 'line', source: 'rivers', paint: { 'line-color': COLORS.river, 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 0.4, 8, 1.4, 12, 2.4] } },
  )
  if (sources.modern) {
    layers.push(
      // Detailed coastline/water (physical geography only) replaces the coarse 1:50m basemap when zoomed in.
      {
        id: 'modern-water', type: 'fill', source: 'modern', 'source-layer': 'water', minzoom: 6, layout: { visibility: 'none' },
        paint: { 'fill-color': ['match', ['get', 'class'], 'ocean', COLORS.ocean, COLORS.lake], 'fill-opacity': ['interpolate', ['linear'], ['zoom'], 6, 0, 7.5, 1] },
      },
      { id: 'modern-waterway', type: 'line', source: 'modern', 'source-layer': 'waterway', minzoom: 8, layout: { visibility: 'none' }, paint: { 'line-color': COLORS.river, 'line-width': 1 } },
      {
        id: 'modern-roads', type: 'line', source: 'modern', 'source-layer': 'transportation', minzoom: 7, layout: { visibility: 'none' },
        filter: ['in', ['get', 'class'], ['literal', ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'minor']]],
        paint: {
          'line-color': '#4a4f52',
          'line-width': ['interpolate', ['linear'], ['zoom'], 7, ['match', ['get', 'class'], ['motorway', 'trunk'], 1.2, 0.4], 14, ['match', ['get', 'class'], ['motorway', 'trunk', 'primary'], 4, 1.5]],
          'line-opacity': 0.7,
        },
      },
      {
        id: 'modern-places', type: 'symbol', source: 'modern', 'source-layer': 'place', minzoom: 6, layout: {
          visibility: 'none', 'text-field': ['coalesce', ['get', 'name:pt'], ['get', 'name']], 'text-font': config.fontItalic,
          'text-size': ['match', ['get', 'class'], 'city', 12, 'town', 11, 10],
        },
        filter: ['in', ['get', 'class'], ['literal', ['city', 'town', 'village']]],
        paint: { 'text-color': '#9aa0a2', 'text-halo-color': COLORS.halo, 'text-halo-width': 1.2 },
      },
    )
  }
  layers.push(
    { id: 'boundaries-fill', type: 'fill', source: 'boundaries', paint: { 'fill-color': 'rgba(0,0,0,0)', 'fill-opacity': 0.42 } },
    {
      id: 'boundaries-line', type: 'line', source: 'boundaries',
      paint: { 'line-color': COLORS.border, 'line-opacity': 0.55, 'line-width': ['interpolate', ['linear'], ['zoom'], 2, 0.5, 6, 1.1, 10, 1.6] },
    },
    { id: 'boundaries-selected', type: 'line', source: 'boundaries', filter: ['==', ['get', 'polity_id'], -999], paint: { 'line-color': COLORS.gold, 'line-width': 2.5 } },
    { id: 'areas-fill', type: 'fill', source: 'features', filter: ['in', ['get', 'layer'], ['literal', ['area_of_operations', 'territorial_control']]], paint: { 'fill-color': SIDE_COLOR as never, 'fill-opacity': 0.18 } },
    {
      id: 'lines-front', type: 'line', source: 'features', filter: ['==', ['get', 'layer'], 'front_line'], layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#e0715a', 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 2, 12, 4], 'line-dasharray': ['case', ['get', 'approximate'], ['literal', [2, 1.4]], ['literal', [1, 0]]] as never },
    },
    {
      id: 'lines-defensive', type: 'line', source: 'features', filter: ['==', ['get', 'layer'], 'defensive_line'],
      paint: { 'line-color': '#b08a5a', 'line-width': 2.5, 'line-dasharray': ['case', ['get', 'approximate'], ['literal', [2, 1.4]], ['literal', [1, 0]]] as never },
    },
    { id: 'lines-routes', type: 'line', source: 'features', filter: ['==', ['get', 'layer'], 'route'], paint: { 'line-color': COLORS.gold, 'line-width': 1.6, 'line-dasharray': [3, 2] } },
    {
      id: 'lines-landing', type: 'line', source: 'features', filter: ['in', ['get', 'layer'], ['literal', ['landing_zone', 'drop_zone']]], layout: { 'line-cap': 'round' },
      paint: { 'line-color': '#6fc3c9', 'line-width': ['interpolate', ['linear'], ['zoom'], 7, 3, 12, 8], 'line-opacity': 0.85, 'line-dasharray': ['case', ['get', 'approximate'], ['literal', [1.5, 0.8]], ['literal', [1, 0]]] as never },
    },
    {
      id: 'lines-axes', type: 'line', source: 'features', filter: ['in', ['get', 'layer'], ['literal', ['advance_axis', 'withdrawal_axis']]], layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': SIDE_COLOR as never, 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 2, 12, 5], 'line-opacity': 0.9, 'line-dasharray': ['case', ['get', 'approximate'], ['literal', [2, 1]], ['literal', [1, 0]]] as never },
    },
    {
      id: 'arrowheads', type: 'symbol', source: 'arrows', layout: {
        'icon-image': 'arrowhead', 'icon-rotate': ['get', 'bearing'], 'icon-rotation-alignment': 'map', 'icon-allow-overlap': true, 'icon-ignore-placement': true,
        'icon-size': ['interpolate', ['linear'], ['zoom'], 6, 0.5, 12, 1],
      },
      paint: { 'icon-color': SIDE_COLOR as never },
    },
    {
      id: 'uncertainty', type: 'circle', source: 'features', filter: ['all', ['==', ['geometry-type'], 'Point'], ['has', 'precision_m']],
      paint: {
        // radius in pixels ≈ precision (m) / metres-per-pixel at ~50°N
        'circle-radius': ['interpolate', ['exponential', 2], ['zoom'], 0, ['/', ['coalesce', ['get', 'precision_m'], 0], 100000], 22, ['/', ['*', ['coalesce', ['get', 'precision_m'], 0], 4194304], 100000]],
        'circle-color': 'rgba(255,255,255,0.03)', 'circle-stroke-color': 'rgba(232,223,201,0.35)', 'circle-stroke-width': 1,
      },
    },
    {
      id: 'points-features', type: 'symbol', source: 'features',
      filter: ['in', ['get', 'layer'], ['literal', ['objective', 'fortification', 'airfield', 'naval_base', 'unit_position']]],
      layout: {
        'icon-image': ['match', ['get', 'layer'], 'objective', 'objective', 'fortification', 'fortification', 'airfield', 'airfield', 'naval_base', 'naval', 'unit'],
        'icon-size': ['interpolate', ['linear'], ['zoom'], 5, 0.55, 12, 0.9], 'icon-allow-overlap': true,
        'text-field': ['step', ['zoom'], '', 9, ['get', 'name']], 'text-font': config.fontRegular, 'text-size': 11, 'text-offset': [0, 1.4], 'text-anchor': 'top', 'text-optional': true, 'text-max-width': 12,
      },
      paint: { 'text-color': COLORS.label, 'text-halo-color': COLORS.halo, 'text-halo-width': 1.4 },
    },
    { id: 'places-dot', type: 'circle', source: 'features', minzoom: 7, filter: ['==', ['get', 'layer'], 'place'], paint: { 'circle-radius': 2.5, 'circle-color': '#b9b2a0', 'circle-stroke-color': COLORS.halo, 'circle-stroke-width': 1 } },
    {
      id: 'places-label', type: 'symbol', source: 'features', minzoom: 8, filter: ['==', ['get', 'layer'], 'place'],
      layout: { 'text-field': ['get', 'name'], 'text-font': config.fontItalic, 'text-size': 11, 'text-offset': [0.6, 0], 'text-anchor': 'left', 'text-optional': true },
      paint: { 'text-color': '#b9b2a0', 'text-halo-color': COLORS.halo, 'text-halo-width': 1.3 },
    },
    {
      id: 'events', type: 'symbol', source: 'features', filter: ['==', ['get', 'layer'], 'event'],
      layout: {
        'icon-image': 'event', 'icon-allow-overlap': true,
        'icon-size': ['interpolate', ['linear'], ['zoom'], 3, ['*', 0.12, ['get', 'importance']], 10, ['*', 0.2, ['get', 'importance']]],
        'symbol-sort-key': ['-', 10, ['get', 'importance']],
        'text-field': ['step', ['zoom'], '', 7, ['get', 'name']], 'text-font': config.fontRegular, 'text-size': 11, 'text-offset': [0, 1.2], 'text-anchor': 'top', 'text-optional': true, 'text-max-width': 14,
      },
      paint: {
        'icon-opacity': ['interpolate', ['linear'], ['get', 'days_ago'], 0, 1, 7, 0.35],
        'text-color': COLORS.gold, 'text-halo-color': COLORS.halo, 'text-halo-width': 1.4,
      },
    },
    {
      id: 'battle-clusters', type: 'circle', source: 'battles', filter: ['has', 'point_count'],
      paint: { 'circle-color': '#7a2f28', 'circle-stroke-color': '#e0715a', 'circle-stroke-width': 1.5, 'circle-radius': ['step', ['get', 'point_count'], 14, 5, 18, 10, 22] },
    },
    {
      id: 'battle-cluster-count', type: 'symbol', source: 'battles', filter: ['has', 'point_count'],
      layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': config.fontBold, 'text-size': 12 }, paint: { 'text-color': '#fff' },
    },
    {
      id: 'battles', type: 'symbol', source: 'battles', filter: ['all', ['!', ['has', 'point_count']], ['any', ['!', ['get', 'is_phase']], ['>=', ['zoom'], 8.5]]],
      layout: {
        'icon-image': ['case', ['==', ['get', 'state'], 'active'], 'battle-active', 'battle-past'],
        'icon-size': ['interpolate', ['linear'], ['zoom'], 3, ['case', ['get', 'is_phase'], 0.5, 0.65], 10, ['case', ['get', 'is_phase'], 0.75, 1]],
        'icon-allow-overlap': true,
        'text-field': ['get', 'name'], 'text-font': config.fontBold, 'text-size': ['case', ['get', 'is_phase'], 10.5, 12],
        'text-offset': [0, 1.5], 'text-anchor': 'top', 'text-optional': true, 'text-max-width': 12,
      },
      paint: {
        'icon-opacity': ['case', ['==', ['get', 'state'], 'active'], 1, 0.6],
        'text-color': ['case', ['==', ['get', 'state'], 'active'], '#f2c6bc', '#9aa3ab'], 'text-halo-color': COLORS.halo, 'text-halo-width': 1.5,
      },
    },
    {
      id: 'boundaries-label', type: 'symbol', source: 'boundaries', minzoom: 2.6,
      filter: ['==', ['geometry-type'], 'Point'],
      layout: {
        'symbol-sort-key': ['-', 0, ['coalesce', ['get', 'area'], 0]],
        'text-field': ['coalesce', ['get', 'polity_name'], ['get', 'label']], 'text-font': config.fontItalic,
        'text-size': ['interpolate', ['linear'], ['zoom'], 3, 10, 6, 13], 'text-transform': 'uppercase', 'text-letter-spacing': 0.12, 'text-max-width': 8,
        'symbol-placement': 'point',
      },
      // curated polities in parchment; raw dataset labels dimmer (they have no curated record)
      paint: { 'text-color': ['case', ['get', 'curated'], '#d8cba8', '#8d939a'], 'text-halo-color': COLORS.halo, 'text-halo-width': 1.3, 'text-opacity': 0.9 },
    },
    {
      id: 'lines-labels', type: 'symbol', source: 'features', minzoom: 8.5,
      filter: ['in', ['get', 'layer'], ['literal', ['front_line', 'landing_zone', 'defensive_line', 'advance_axis']]],
      layout: { 'text-field': ['get', 'name'], 'text-font': config.fontRegular, 'text-size': 11, 'symbol-placement': 'line', 'text-max-angle': 30 },
      paint: { 'text-color': COLORS.label, 'text-halo-color': COLORS.halo, 'text-halo-width': 1.4 },
    },
    {
      id: 'selected-point', type: 'circle', source: 'features', filter: ['==', ['get', 'slug'], '__none__'],
      paint: { 'circle-radius': 16, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': COLORS.gold, 'circle-stroke-width': 2.5 },
    },
    {
      id: 'selected-battle', type: 'circle', source: 'battles', filter: ['==', ['get', 'slug'], '__none__'],
      paint: { 'circle-radius': 18, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': COLORS.gold, 'circle-stroke-width': 2.5 },
    },
    {
      id: 'selected-line', type: 'line', source: 'features', filter: ['==', ['get', 'slug'], '__none__'],
      paint: { 'line-color': COLORS.gold, 'line-width': 6, 'line-opacity': 0.5 },
    },
  )

  return {
    version: 8,
    glyphs: config.glyphsUrl ?? undefined,
    sources,
    layers: config.glyphsUrl ? layers : layers.filter((l) => l.type !== 'symbol' || !('text-field' in (l.layout ?? {}))),
  }
}

/** Style layers controlled by each toggle in the layer panel. */
export const TOGGLE_TO_STYLE: Record<string, string[]> = {
  boundaries: ['boundaries-line'],
  labels: ['boundaries-label', 'lines-labels'],
  places: ['places-dot', 'places-label'],
  terrain: ['hillshade'],
  rivers: ['rivers', 'lakes', 'modern-water', 'modern-waterway'],
  modern: ['modern-roads', 'modern-places'],
  battles: ['battles', 'battle-clusters', 'battle-cluster-count', 'selected-battle'],
  events: ['events'],
  front_lines: ['lines-front'],
  axes: ['lines-axes', 'arrowheads'],
  defensive_lines: ['lines-defensive'],
  landing_zones: ['lines-landing'],
  routes: ['lines-routes'],
  areas: ['areas-fill'],
  uncertainty: ['uncertainty'],
}
