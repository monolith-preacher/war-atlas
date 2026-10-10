import { ChevronLeft, ChevronRight, Info, X } from 'lucide-react'
import { useEffect, useMemo, useRef } from 'react'
import { useReplay } from '../../hooks/queries'
import { formatDate } from '../../lib/dates'
import { useExplorer } from '../../store/explorer'
import { CertaintyBadge, Spinner } from '../common/ui'

/**
 * Campaign/battle replay driven exclusively by documented events and dated map
 * features. Nothing is interpolated: between two steps the map shows only what is
 * valid on the current date.
 */
export function ReplayBar() {
  const replay = useExplorer((s) => s.replay)
  const setReplay = useExplorer((s) => s.setReplay)
  const date = useExplorer((s) => s.date)
  const setDate = useExplorer((s) => s.setDate)
  const fly = useExplorer((s) => s.fly)
  const select = useExplorer((s) => s.select)
  const q = useReplay(replay?.scope ?? null, replay?.slug ?? null)
  const steps = q.data?.steps ?? []
  const idx = useMemo(() => {
    let i = -1
    steps.forEach((s, k) => {
      if (s.date <= (date ?? '')) i = k
    })
    return i
  }, [steps, date])
  const current = idx >= 0 ? steps[idx] : null
  const lastFlown = useRef<string | null>(null)

  useEffect(() => {
    if (!current || current.date !== date || lastFlown.current === current.date) return
    const loc = current.events.find((e) => e.location)?.location
    if (loc) fly(loc, 10)
    lastFlown.current = current.date
  }, [current, date, fly])

  if (!replay) return null
  return (
    <div className="wa-panel absolute top-14 left-3 z-10 w-[min(560px,calc(100%-1.5rem))] animate-fade-in rounded-md shadow-xl">
      <div className="flex items-center gap-2 border-b border-ink-700 px-3 py-2">
        <span className="wa-label text-brass-400">Reprodução histórica</span>
        <span className="flex-1 truncate text-[13px] text-parchment">{q.data?.scope.name ?? '…'}</span>
        {q.isLoading && <Spinner className="size-4" />}
        <span className="font-mono text-[11px] text-steel-400">
          passo {Math.max(idx + 1, 0)}/{steps.length}
        </span>
        <button className="wa-icon-btn size-7" onClick={() => idx > 0 && setDate(steps[idx - 1].date)} disabled={idx <= 0} aria-label="Passo anterior">
          <ChevronLeft size={15} />
        </button>
        <button className="wa-icon-btn size-7" onClick={() => idx < steps.length - 1 && setDate(steps[idx + 1].date)} disabled={idx >= steps.length - 1} aria-label="Próximo passo">
          <ChevronRight size={15} />
        </button>
        <button className="wa-icon-btn size-7" onClick={() => setReplay(null)} aria-label="Sair da reprodução" title="Sair da reprodução">
          <X size={15} />
        </button>
      </div>
      <div className="max-h-44 overflow-y-auto px-3 py-2">
        {!current && <p className="text-[12px] text-steel-400">Antes do primeiro evento documentado. Use ▶ ou “próximo passo”.</p>}
        {current && (
          <>
            <p className="font-mono text-[11px] text-brass-400">
              {formatDate(current.date, 'day', 'long')}
              {current.date !== date && <span className="text-steel-400"> · (último passo documentado antes de {formatDate(date)})</span>}
            </p>
            <ul className="mt-1 space-y-1.5">
              {current.events.map((e) => (
                <li key={e.id} className="text-[12.5px]">
                  <button className="wa-link text-left" onClick={() => select({ type: 'event', slug: e.slug })}>
                    {e.time_of_day ? `${e.time_of_day} · ` : ''}
                    {e.title}
                  </button>
                  {e.certainty !== 'verified' && <span className="ml-1"><CertaintyBadge value={e.certainty} /></span>}
                  {e.summary && <p className="text-[11.5px] text-steel-400">{e.summary}</p>}
                </li>
              ))}
              {current.features_starting.length > 0 && <li className="text-[11.5px] text-steel-400">+ {current.features_starting.length} feição(ões) cartográfica(s) passam a valer nesta data</li>}
            </ul>
          </>
        )}
      </div>
      <p className="flex items-start gap-1.5 border-t border-ink-700 px-3 py-1.5 text-[10.5px] text-steel-400">
        <Info size={11} className="mt-0.5 shrink-0" /> {q.data?.method ?? 'Reconstrução baseada em eventos documentados.'}
      </p>
    </div>
  )
}
