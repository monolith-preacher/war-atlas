import { AlertTriangle, ChevronDown, Map as MapIcon } from 'lucide-react'
import { useState } from 'react'
import { formatDate } from '../../lib/dates'
import type { MapState } from '../../lib/types'
import { useExplorer } from '../../store/explorer'
import { SourceLine } from '../common/docs'

/** Always states which border snapshot is on screen and whether it is valid for the date. */
export function BoundaryNotice({ state }: { state?: MapState }) {
  const [open, setOpen] = useState(false)
  const layers = useExplorer((s) => s.layers)
  if (!state || !(layers.boundaries || layers.participants || layers.alliances)) return null
  const ds = state.boundary_dataset
  if (!ds)
    return (
      <div className="wa-panel absolute top-3 left-3 max-w-md rounded-md px-3 py-1.5 text-[12px] text-warn">
        Nenhum conjunto de fronteiras históricas cadastrado para esta data.
      </div>
    )
  return (
    <div className="absolute top-3 left-3 z-10 w-[min(520px,calc(100%-5rem))]">
      <button
        onClick={() => setOpen(!open)}
        className={`wa-panel flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-left text-[12px] ${ds.stale ? 'border-warn/60 text-warn' : 'text-steel-300'}`}
        aria-expanded={open}
      >
        {ds.stale ? <AlertTriangle size={14} className="shrink-0" /> : <MapIcon size={14} className="shrink-0 text-brass-500" />}
        <span className="flex-1 truncate">
          {ds.stale
            ? `Fronteiras desatualizadas: snapshot de ${ds.reference_date.slice(0, 4)}, aplicável até ${formatDate(ds.valid_to)}. Mudanças posteriores ainda não cadastradas.`
            : `Fronteiras: ${ds.name} — aproximadas`}
        </span>
        <ChevronDown size={14} className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="wa-panel mt-1 animate-fade-in space-y-2 rounded-md p-3 text-[12px] text-steel-300">
          <p>{ds.precision_note}</p>
          {ds.known_issues && (
            <p className="text-warn/90">
              <b>Limitações conhecidas:</b> {ds.known_issues}
            </p>
          )}
          <p className="text-steel-400">
            Aplicabilidade registrada: {formatDate(ds.valid_from)} – {formatDate(ds.valid_to)} · Licença: {ds.license}
          </p>
          {ds.source && (
            <p className="text-[11.5px]">
              Fonte: <SourceLine s={ds.source} />
            </p>
          )}
          <p className="text-steel-400">Colônias e territórios dependentes aparecem em tom mais claro da cor do país soberano participante.</p>
        </div>
      )}
    </div>
  )
}
