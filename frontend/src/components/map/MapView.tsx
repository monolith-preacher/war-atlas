import * as maplibregl from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useBoundaries, useConflict, useMapFeatures, useMapState } from '../../hooks/queries'
import { formatDate } from '../../lib/dates'
import { LAYERS } from '../../lib/layers'
import { SPATIAL_ROLES } from '../../lib/labels'
import type { EntityType } from '../../lib/types'
import { useExplorer } from '../../store/explorer'
import { Spinner } from '../common/ui'
import { BoundaryNotice } from './BoundaryNotice'
import { arrowheadsFor, registerIcons } from './icons'
import { Legend } from './Legend'
import { buildStyle, COLORS, TOGGLE_TO_STYLE } from './mapStyle'

// MapLibre 6 ships an ES-module worker; point to it explicitly so it works under Vite (dev and build).
maplibregl.setWorkerUrl(workerUrl)

const EMPTY: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }
const POINT_LAYER_TOGGLES: Record<string, string> = { objectives: 'objective', fortifications: 'fortification', airfields: 'airfield', naval_bases: 'naval_base' }
const INTERACTIVE = ['battles', 'battle-clusters', 'events', 'places-dot', 'points-features', 'lines-front', 'lines-axes', 'lines-landing', 'lines-defensive', 'lines-routes', 'areas-fill', 'boundaries-fill']

function escapeHtml(s: string) {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!)
}

function lighten(hex: string, amount = 0.45): string {
  const n = parseInt(hex.slice(1), 16)
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255
  const mix = (c: number) => Math.round(c + (40 - c) * amount)
  return `rgb(${mix(r)},${mix(g)},${mix(b)})`
}

export function MapView() {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)
  const [ready, setReady] = useState(false)
  const [mapError, setMapError] = useState<string | null>(null)

  const conflict = useExplorer((s) => s.conflict)
  const date = useExplorer((s) => s.date)
  const layers = useExplorer((s) => s.layers)
  const eventWindow = useExplorer((s) => s.eventWindow)
  const flyTo = useExplorer((s) => s.flyTo)
  const stack = useExplorer((s) => s.stack)
  const reduceMotion = useExplorer((s) => s.reduceMotion)

  const conflictQ = useConflict(conflict)
  const stateQ = useMapState(conflict, date)
  const boundariesQ = useBoundaries(stateQ.data?.boundary_dataset?.slug)
  const featuresQ = useMapFeatures(conflict, date, eventWindow)

  // ---------------------------------------------------------------- init
  useEffect(() => {
    if (!container.current || mapRef.current) return
    let map: maplibregl.Map
    try {
      map = new maplibregl.Map({
        container: container.current,
        style: buildStyle(),
        center: [8, 46],
        zoom: 3,
        minZoom: 1.5,
        maxZoom: 15,
        attributionControl: { compact: true },
        dragRotate: false,
        pitchWithRotate: false,
      })
    } catch (e) {
      setMapError('Não foi possível iniciar o mapa (WebGL indisponível neste navegador).')
      console.error(e)
      return
    }
    mapRef.current = map
    if (import.meta.env.DEV) (window as unknown as { __map: maplibregl.Map }).__map = map
    // keep the canvas in sync with layout changes (sidebar/panel toggles, timeline height)
    const ro = new ResizeObserver(() => map.resize())
    ro.observe(container.current)
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right')
    map.on('load', () => {
      registerIcons(map)
      setReady(true)
    })
    map.on('error', (e) => console.warn('map error', e.error?.message))

    const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 14, maxWidth: '280px' })
    popupRef.current = popup

    map.on('mousemove', (e) => {
      const feats = map.queryRenderedFeatures(e.point, { layers: INTERACTIVE.filter((l) => map.getLayer(l)) })
      const f = feats[0]
      map.getCanvas().style.cursor = f ? 'pointer' : ''
      if (!f) {
        popup.remove()
        return
      }
      const p = f.properties as Record<string, unknown>
      let html = ''
      if (f.layer.id === 'battle-clusters') html = `<b>${p.point_count} batalhas</b><div class="text-[11px] text-steel-400">clique para aproximar</div>`
      else if (f.layer.id === 'boundaries-fill') {
        html = `<b>${escapeHtml(String(p.polity_name ?? p.label))}</b>`
        if (!p.polity_slug) html += `<div class="text-[11px] text-steel-400">Rótulo do conjunto de dados; sem ficha curada.</div>`
      } else {
        const approx = p.approximate || p.spatial_role === 'schematic' || p.spatial_role === 'approximate_position'
        html = `<b>${escapeHtml(String(p.name ?? ''))}</b>`
        if (p.start_date) html += `<div class="text-[11px] text-steel-400">${formatDate(String(p.start_date))}${p.end_date && p.end_date !== p.start_date ? ' – ' + formatDate(String(p.end_date)) : ''}</div>`
        if (approx) html += `<div class="text-[11px]" style="color:#e0a43f">≈ ${escapeHtml(SPATIAL_ROLES[String(p.spatial_role)] ?? 'aproximado')}${p.precision_m ? ` (±${Math.round(Number(p.precision_m) / 100) / 10} km)` : ''}</div>`
      }
      popup.setLngLat(e.lngLat).setHTML(html).addTo(map)
    })
    map.on('mouseout', () => popup.remove())

    map.on('click', async (e) => {
      const feats = map.queryRenderedFeatures(e.point, { layers: INTERACTIVE.filter((l) => map.getLayer(l)) })
      const f = feats[0]
      if (!f) return
      const p = f.properties as Record<string, unknown>
      const select = useExplorer.getState().select
      if (f.layer.id === 'battle-clusters') {
        const src = map.getSource('battles') as maplibregl.GeoJSONSource
        const zoom = await src.getClusterExpansionZoom(Number(p.cluster_id))
        map.easeTo({ center: (f.geometry as GeoJSON.Point).coordinates as [number, number], zoom })
        return
      }
      if (f.layer.id === 'boundaries-fill') {
        if (p.polity_slug) select({ type: 'polity', slug: String(p.polity_slug) })
        return
      }
      const layer = String(p.layer)
      const type: EntityType = layer === 'battle' ? 'battle' : layer === 'event' ? 'event' : layer === 'place' ? 'place' : 'map_feature'
      select({ type, slug: String(p.slug) })
    })

    return () => {
      ro.disconnect()
      popup.remove()
      map.remove()
      mapRef.current = null
    }
  }, [])

  // ---------------------------------------------------------------- data → sources
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    ;(map.getSource('boundaries') as maplibregl.GeoJSONSource).setData(boundariesQ.data ?? EMPTY)
  }, [ready, boundariesQ.data])

  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    const fc = featuresQ.data ?? EMPTY
    const battles = fc.features.filter((f) => f.properties?.layer === 'battle')
    const others = fc.features.filter((f) => f.properties?.layer !== 'battle')
    ;(map.getSource('battles') as maplibregl.GeoJSONSource).setData({ type: 'FeatureCollection', features: battles })
    const rest: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: others }
    ;(map.getSource('features') as maplibregl.GeoJSONSource).setData(rest)
    ;(map.getSource('arrows') as maplibregl.GeoJSONSource).setData(arrowheadsFor(rest))
  }, [ready, featuresQ.data])

  // ---------------------------------------------------------------- boundary colouring (participation / alliances at date)
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    const st = stateQ.data
    const showParticipants = layers.participants
    const showAlliances = layers.alliances
    if (!st || (!showParticipants && !showAlliances)) {
      map.setPaintProperty('boundaries-fill', 'fill-color', 'rgba(0,0,0,0)')
      return
    }
    const direct: (number | string)[] = []
    const subject: (number | string)[] = []
    for (const p of st.participants) {
      const color = (showAlliances ? p.alliance_color : null) ?? p.color ?? COLORS.neutral
      direct.push(p.polity_id, color)
      subject.push(p.polity_id, lighten(color))
    }
    const fallback = showParticipants ? '#272c30' : 'rgba(0,0,0,0)'
    const expr = direct.length
      ? ['match', ['get', 'polity_id'], ...direct, ['match', ['get', 'subject_polity_id'], ...subject, fallback]]
      : fallback
    map.setPaintProperty('boundaries-fill', 'fill-color', expr as never)
  }, [ready, stateQ.data, layers.participants, layers.alliances])

  // stale boundary snapshot → dashed, faded borders
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    const stale = !!stateQ.data?.boundary_dataset?.stale
    map.setPaintProperty('boundaries-line', 'line-dasharray', stale ? [3, 2] : [1, 0])
    map.setPaintProperty('boundaries-line', 'line-opacity', stale ? 0.35 : 0.55)
    // fill fades as the user zooms in so terrain and military symbols stay legible
    map.setPaintProperty('boundaries-fill', 'fill-opacity', ['interpolate', ['linear'], ['zoom'], 3, stale ? 0.24 : 0.42, 9, stale ? 0.06 : 0.12] as never)
  }, [ready, stateQ.data?.boundary_dataset?.stale])

  // ---------------------------------------------------------------- layer visibility
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    for (const [toggle, styleLayers] of Object.entries(TOGGLE_TO_STYLE)) {
      const visible = layers[toggle as keyof typeof layers]
      for (const id of styleLayers) if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', visible ? 'visible' : 'none')
    }
    map.setLayoutProperty('boundaries-fill', 'visibility', layers.participants || layers.alliances ? 'visible' : 'none')
    // With detailed OSM water available, the background becomes "land" when zoomed in and the
    // water polygons define the coastline precisely (the 1:50m basemap is too coarse at that scale).
    const detailedWater = layers.rivers && !!map.getLayer('modern-water')
    map.setPaintProperty('background', 'background-color', detailedWater ? (['interpolate', ['linear'], ['zoom'], 7, COLORS.ocean, 7.5, COLORS.land] as never) : COLORS.ocean)
    map.setPaintProperty('land', 'fill-opacity', detailedWater ? (['interpolate', ['linear'], ['zoom'], 7, 1, 7.5, 0] as never) : 1)
    // point features share one style layer: filter by enabled toggles
    const kinds = Object.entries(POINT_LAYER_TOGGLES).filter(([t]) => layers[t as keyof typeof layers]).map(([, k]) => k)
    const branches = LAYERS.filter((l) => l.branch && layers[l.id]).map((l) => l.branch!)
    map.setFilter('points-features', [
      'any',
      ['in', ['get', 'layer'], ['literal', kinds]],
      ['all', ['==', ['get', 'layer'], 'unit_position'], ['in', ['coalesce', ['get', 'branch'], 'army'], ['literal', branches]]],
    ])
  }, [ready, layers])

  // ---------------------------------------------------------------- selection highlight
  const selected = stack[stack.length - 1]
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    const slug = selected && ['battle', 'event', 'map_feature'].includes(selected.type) ? selected.slug : '__none__'
    map.setFilter('selected-point', ['all', ['==', ['geometry-type'], 'Point'], ['==', ['get', 'slug'], slug]])
    map.setFilter('selected-line', ['all', ['!=', ['geometry-type'], 'Point'], ['==', ['get', 'slug'], slug]])
    map.setFilter('selected-battle', ['==', ['get', 'slug'], selected?.type === 'battle' ? selected.slug : '__none__'])
    const polityId = selected?.type === 'polity' ? (boundariesQ.data?.features.find((f) => f.properties?.polity_slug === selected.slug)?.properties?.polity_id ?? -999) : -999
    map.setFilter('boundaries-selected', ['==', ['get', 'polity_id'], polityId])
  }, [ready, selected, boundariesQ.data])

  // ---------------------------------------------------------------- camera
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map || !flyTo) return
    const opts = { center: flyTo.center, zoom: flyTo.zoom ?? Math.max(map.getZoom(), 8), essential: true }
    if (reduceMotion) map.jumpTo(opts)
    else map.flyTo({ ...opts, speed: 1.4 })
  }, [ready, flyTo, reduceMotion])

  const view = conflictQ.data?.default_view
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map || !view) return
    map.flyTo({ center: view.center, zoom: view.zoom, essential: true, duration: reduceMotion ? 0 : 1600 })
  }, [ready, conflictQ.data?.slug]) // eslint-disable-line react-hooks/exhaustive-deps

  const counts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const f of featuresQ.data?.features ?? []) {
      const l = String(f.properties?.layer)
      c[l] = (c[l] ?? 0) + 1
      if (l === 'unit_position') c[`unit_position:${f.properties?.branch ?? 'army'}`] = (c[`unit_position:${f.properties?.branch ?? 'army'}`] ?? 0) + 1
    }
    return c
  }, [featuresQ.data])

  return (
    <div className="absolute inset-0">
      <div ref={container} className="absolute inset-0" aria-label="Mapa interativo" role="application" />
      {mapError && <div className="absolute inset-0 flex items-center justify-center bg-ink-950 p-6 text-center text-parchment">{mapError}</div>}
      {(featuresQ.isFetching || stateQ.isFetching || boundariesQ.isFetching) && (
        <div className="wa-panel absolute top-3 right-14 flex items-center gap-2 rounded px-2 py-1 text-[11px] text-steel-300">
          <Spinner className="size-3.5" /> atualizando camadas
        </div>
      )}
      {featuresQ.isError && <div className="wa-panel absolute top-12 right-14 rounded px-2 py-1 text-[11px] text-alert">Falha ao carregar camadas militares.</div>}
      <BoundaryNotice state={stateQ.data} />
      <Legend counts={counts} />
    </div>
  )
}
