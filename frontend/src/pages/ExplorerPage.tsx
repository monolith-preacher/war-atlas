import { useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useConflicts, useHealth } from '../hooks/queries'
import { clamp, isValidISO } from '../lib/dates'
import { MODES, type MapMode } from '../lib/layers'
import type { EntityType } from '../lib/types'
import { useExplorer } from '../store/explorer'
import { Header } from '../components/layout/Header'
import { Welcome } from '../components/layout/Welcome'
import { MapView } from '../components/map/MapView'
import { ContextPanel } from '../components/panels/ContextPanel'
import { ReplayBar } from '../components/replay/ReplayBar'
import { Sidebar } from '../components/sidebar/Sidebar'
import { Timeline } from '../components/timeline/Timeline'

/** Keeps conflict, date, mode and selection in the URL so views can be shared. */
function useUrlSync() {
  const [params, setParams] = useSearchParams()
  const conflicts = useConflicts()
  const initialised = useRef(false)
  const { conflict, date, mode, stack } = useExplorer()

  useEffect(() => {
    if (initialised.current || !conflicts.data) return
    initialised.current = true
    const c = params.get('c')
    const found = conflicts.data.find((x) => x.slug === c)
    const s = useExplorer.getState()
    if (found) {
      const d = params.get('d')
      s.setConflict(found.slug, d && isValidISO(d) ? clamp(d, found.start_date, found.end_date) : found.start_date)
    } else if (s.conflict && !conflicts.data.some((x) => x.slug === s.conflict)) {
      s.setConflict(null)
    }
    const m = params.get('m') as MapMode | null
    if (m && m in MODES) s.setMode(m)
    const sel = params.get('sel')
    if (sel && sel.includes(':')) {
      const [type, slug] = sel.split(':')
      s.select({ type: type as EntityType, slug })
    }
  }, [conflicts.data, params])

  useEffect(() => {
    if (!initialised.current) return
    const next = new URLSearchParams()
    if (conflict) next.set('c', conflict)
    if (date) next.set('d', date)
    next.set('m', mode)
    const top = stack[stack.length - 1]
    if (top) next.set('sel', `${top.type}:${top.slug}`)
    if (next.toString() !== params.toString()) setParams(next, { replace: true })
  }, [conflict, date, mode, stack]) // eslint-disable-line react-hooks/exhaustive-deps
}

export function ExplorerPage() {
  useUrlSync()
  const conflict = useExplorer((s) => s.conflict)
  const health = useHealth()
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Header />
      {health.isError && (
        <div className="bg-alert/90 px-3 py-1 text-center text-[12px] text-white" role="alert">
          API indisponível — verifique se o backend e o banco de dados estão em execução. Nova tentativa automática em alguns segundos.
        </div>
      )}
      {health.data && !health.data.has_content && (
        <div className="bg-warn/90 px-3 py-1 text-center text-[12px] text-ink-950">Banco conectado, mas sem conteúdo. Execute o carregamento dos dados iniciais (README → “Dados iniciais”).</div>
      )}
      <div className="relative flex min-h-0 flex-1">
        <Sidebar />
        <main className="relative flex min-w-0 flex-1 flex-col">
          <div className="relative min-h-0 flex-1">
            <MapView />
            <ReplayBar />
            <ContextPanel />
          </div>
          {conflict && <Timeline />}
        </main>
      </div>
      {!conflict && <Welcome />}
    </div>
  )
}
