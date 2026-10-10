import type { ReactElement } from 'react'
import { ArrowLeft, X } from 'lucide-react'
import { useDetail } from '../../hooks/queries'
import { formatDate } from '../../lib/dates'
import { entityLabel } from '../../lib/labels'
import { useExplorer } from '../../store/explorer'
import { ErrorState, Loading } from '../common/ui'
import { BattlePanel, CampaignPanel, ConflictPanel, EventPanel, MapFeaturePanel, PlacePanel, TheaterPanel } from './HistoryPanels'
import { EquipmentPanel, SourcePanel } from './MaterielPanels'
import { ForcePanel, PersonPanel, PolityPanel, UnitPanel } from './MilitaryPanels'
import { DATE_AWARE } from '../../hooks/queries'

const PANELS: Record<string, (p: { d: any }) => ReactElement> = { // eslint-disable-line @typescript-eslint/no-explicit-any
  conflict: ConflictPanel, theater: TheaterPanel, campaign: CampaignPanel, battle: BattlePanel, event: EventPanel, place: PlacePanel,
  map_feature: MapFeaturePanel, polity: PolityPanel, armed_force: ForcePanel, unit: UnitPanel, person: PersonPanel, equipment: EquipmentPanel, source: SourcePanel,
}

export function ContextPanel() {
  const stack = useExplorer((s) => s.stack)
  const back = useExplorer((s) => s.back)
  const close = useExplorer((s) => s.closePanel)
  const date = useExplorer((s) => s.date)
  const conflict = useExplorer((s) => s.conflict)
  const sel = stack[stack.length - 1]
  const q = useDetail(sel?.type ?? '', sel?.slug ?? '', date, conflict)
  if (!sel) return null
  const Panel = PANELS[sel.type]
  return (
    <aside
      key={`${sel.type}:${sel.slug}`}
      className="wa-panel absolute inset-y-0 right-0 z-20 flex w-full animate-slide-in flex-col border-y-0 border-r-0 sm:w-[420px]"
      aria-label={`Ficha: ${entityLabel(sel.type)}`}
    >
      <div className="flex items-center gap-1 border-b border-ink-700 px-2 py-1.5">
        <button className="wa-icon-btn" onClick={back} disabled={stack.length < 2} aria-label="Voltar" title="Voltar">
          <ArrowLeft size={16} />
        </button>
        <span className="wa-label flex-1 truncate">{entityLabel(sel.type)}</span>
        {DATE_AWARE.has(sel.type) && date && <span className="wa-chip border-brass-600/60 text-brass-300">situação em {formatDate(date)}</span>}
        <button className="wa-icon-btn" onClick={close} aria-label="Fechar ficha" title="Fechar">
          <X size={16} />
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {q.isLoading && <Loading />}
        {q.isError && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
        {q.data && Panel && <Panel d={q.data} />}
      </div>
    </aside>
  )
}
