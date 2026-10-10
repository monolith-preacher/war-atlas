import { ChevronDown, Layers } from 'lucide-react'
import { useState } from 'react'
import { LAYERS, MODES } from '../../lib/layers'
import { useExplorer } from '../../store/explorer'

export function Swatch({ kind, color }: { kind: string; color: string }) {
  if (kind === 'fill') return <span className="inline-block size-3 rounded-sm" style={{ background: color, opacity: 0.8 }} />
  if (kind === 'line') return <span className="inline-block h-0.5 w-4" style={{ background: color }} />
  if (kind === 'dash') return <span className="inline-block h-0 w-4 border-t-2 border-dashed" style={{ borderColor: color }} />
  if (kind === 'point') return <span className="inline-block size-2.5 rounded-full" style={{ background: color }} />
  return <span className="inline-block size-2.5 rotate-45" style={{ background: color }} />
}

/** Legend of active layers with the number of records rendered for the current date. */
export function Legend({ counts }: { counts: Record<string, number> }) {
  const [open, setOpen] = useState(true)
  const layers = useExplorer((s) => s.layers)
  const mode = useExplorer((s) => s.mode)
  const active = LAYERS.filter((l) => layers[l.id] && l.featureLayers)
  const countFor = (id: string) => {
    const l = LAYERS.find((x) => x.id === id)!
    if (l.branch) return counts[`unit_position:${l.branch}`] ?? 0
    return (l.featureLayers ?? []).reduce((n, k) => n + (counts[k] ?? 0), 0)
  }
  return (
    <div className="wa-panel absolute bottom-3 left-3 z-10 hidden w-60 rounded-md text-[11.5px] sm:block">
      <button className="flex w-full items-center gap-2 px-3 py-2" onClick={() => setOpen(!open)} aria-expanded={open}>
        <Layers size={13} className="text-brass-500" />
        <span className="wa-label flex-1 text-left">Legenda · modo {MODES[mode].label.toLowerCase()}</span>
        <ChevronDown size={13} className={`transition-transform ${open ? '' : '-rotate-90'}`} />
      </button>
      {open && (
        <div className="max-h-[38vh] space-y-1 overflow-y-auto px-3 pb-2.5">
          {active.length === 0 && <p className="text-steel-400">Nenhuma camada militar ativa.</p>}
          {active.map((l) => {
            const n = countFor(l.id)
            return (
              <div key={l.id} className="flex items-center gap-2">
                <span className="flex w-4 justify-center">
                  <Swatch {...l.swatch} />
                </span>
                <span className={`flex-1 ${n ? 'text-steel-200' : 'text-steel-400'}`}>{l.label}</span>
                <span className={`font-mono ${n ? 'text-brass-400' : 'text-steel-400'}`} title={n ? 'registros nesta data' : 'nenhum registro cadastrado para esta data'}>
                  {n || '—'}
                </span>
              </div>
            )
          })}
          <div className="mt-2 border-t border-ink-700 pt-2 text-steel-400">
            <div className="flex items-center gap-2">
              <span className="inline-block h-0 w-4 border-t-2 border-dashed border-steel-300" /> tracejado = aproximado/esquemático
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-block size-3 rounded-full border border-parchment/40" /> halo = precisão declarada
            </div>
            <div className="mt-1">“—” indica ausência de registros cadastrados, não ausência histórica.</div>
          </div>
        </div>
      )}
    </div>
  )
}
