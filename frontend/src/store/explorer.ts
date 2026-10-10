import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Granularity } from '../lib/dates'
import { type LayerId, type MapMode, presetFor } from '../lib/layers'
import type { EntityType } from '../lib/types'

export interface Selection {
  type: EntityType
  slug: string
}

export interface FlyTarget {
  center: [number, number]
  zoom?: number
  key: number
}

interface ExplorerState {
  conflict: string | null
  date: string | null
  granularity: Granularity
  playing: boolean
  /** days per second, or 0 for "event by event" stepping */
  speed: number
  mode: MapMode
  layers: Record<LayerId, boolean>
  eventWindow: number
  sidebarOpen: boolean
  sidebarTab: string
  stack: Selection[]
  flyTo: FlyTarget | null
  replay: { scope: 'campaign' | 'battle'; slug: string } | null
  reduceMotion: boolean

  setConflict: (slug: string | null, date?: string | null) => void
  setDate: (date: string) => void
  setGranularity: (g: Granularity) => void
  setPlaying: (p: boolean) => void
  setSpeed: (s: number) => void
  setMode: (m: MapMode) => void
  toggleLayer: (id: LayerId, value?: boolean) => void
  setEventWindow: (n: number) => void
  setSidebar: (open: boolean, tab?: string) => void
  select: (sel: Selection, opts?: { replace?: boolean }) => void
  back: () => void
  closePanel: () => void
  fly: (center: [number, number], zoom?: number) => void
  setReplay: (r: ExplorerState['replay']) => void
  setReduceMotion: (v: boolean) => void
}

export const useExplorer = create<ExplorerState>()(
  persist(
    (set, get) => ({
      conflict: null,
      date: null,
      granularity: 'day',
      playing: false,
      speed: 7,
      mode: 'political',
      layers: presetFor('political'),
      eventWindow: 3,
      sidebarOpen: typeof window !== 'undefined' ? window.innerWidth > 900 : true,
      sidebarTab: 'structure',
      stack: [],
      flyTo: null,
      replay: null,
      reduceMotion: false,

      setConflict: (slug, date = null) => set({ conflict: slug, date, playing: false, stack: [], replay: null }),
      setDate: (date) => set({ date }),
      setGranularity: (granularity) => set({ granularity }),
      setPlaying: (playing) => set({ playing }),
      setSpeed: (speed) => set({ speed }),
      setMode: (mode) => set({ mode, layers: presetFor(mode) }),
      toggleLayer: (id, value) => set({ layers: { ...get().layers, [id]: value ?? !get().layers[id] } }),
      setEventWindow: (eventWindow) => set({ eventWindow }),
      setSidebar: (sidebarOpen, tab) => set({ sidebarOpen, sidebarTab: tab ?? get().sidebarTab }),
      select: (sel, opts) => {
        const stack = get().stack
        const top = stack[stack.length - 1]
        if (top && top.type === sel.type && top.slug === sel.slug) return
        set({ stack: opts?.replace ? [sel] : [...stack.slice(-19), sel] })
      },
      back: () => set({ stack: get().stack.slice(0, -1) }),
      closePanel: () => set({ stack: [] }),
      fly: (center, zoom) => set({ flyTo: { center, zoom, key: Date.now() } }),
      setReplay: (replay) => set({ replay, playing: false }),
      setReduceMotion: (reduceMotion) => set({ reduceMotion }),
    }),
    {
      name: 'waratlas-explorer',
      partialize: (s) => ({ granularity: s.granularity, speed: s.speed, mode: s.mode, layers: s.layers, eventWindow: s.eventWindow, reduceMotion: s.reduceMotion }),
    },
  ),
)
