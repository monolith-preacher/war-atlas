import clsx from 'clsx'
import { CalendarDays, ChevronRight, Crosshair, Flag, Layers, Network, Play, Shirt, Wrench, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useCamouflages, useConflict, useEquipmentList, useMapState, useTimeline, useUniforms } from '../../hooks/queries'
import { formatDate, formatRange } from '../../lib/dates'
import { CAMPAIGN_KINDS, EQUIPMENT_CATEGORIES } from '../../lib/labels'
import { LAYERS, MODES } from '../../lib/layers'
import type { BattleBrief, CampaignBrief, TheaterNode } from '../../lib/types'
import { useExplorer } from '../../store/explorer'
import { Swatch } from '../map/Legend'
import { Citations } from '../common/docs'
import { EmptyState, ErrorState, Loading, Period, PlannedFeature } from '../common/ui'

const TABS = [
  { id: 'structure', label: 'Estrutura', icon: Network },
  { id: 'countries', label: 'Países', icon: Flag },
  { id: 'events', label: 'Eventos', icon: CalendarDays },
  { id: 'layers', label: 'Camadas', icon: Layers },
  { id: 'equipment', label: 'Equipamentos', icon: Wrench },
  { id: 'uniforms', label: 'Uniformes', icon: Shirt },
]

export function Sidebar() {
  const open = useExplorer((s) => s.sidebarOpen)
  const tab = useExplorer((s) => s.sidebarTab)
  const setSidebar = useExplorer((s) => s.setSidebar)
  if (!open) return null
  return (
    <aside className="wa-panel absolute inset-y-0 left-0 z-20 flex w-[min(340px,92vw)] animate-fade-in flex-col border-y-0 border-l-0 md:relative" aria-label="Navegação histórica">
      <nav className="grid grid-cols-6 border-b border-ink-700" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setSidebar(true, t.id)}
            title={t.label}
            className={clsx('flex flex-col items-center gap-0.5 py-2 text-[10px] transition-colors', tab === t.id ? 'border-b-2 border-brass-500 text-brass-400' : 'text-steel-400 hover:text-parchment')}
          >
            <t.icon size={16} />
            <span className="hidden sm:block">{t.label}</span>
          </button>
        ))}
      </nav>
      <button className="wa-icon-btn absolute top-1 right-1 md:hidden" onClick={() => setSidebar(false)} aria-label="Fechar barra lateral">
        <X size={16} />
      </button>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === 'structure' && <StructureTab />}
        {tab === 'countries' && <CountriesTab />}
        {tab === 'events' && <EventsTab />}
        {tab === 'layers' && <LayersTab />}
        {tab === 'equipment' && <EquipmentTab />}
        {tab === 'uniforms' && <UniformsTab />}
      </div>
    </aside>
  )
}

function NeedConflict() {
  return <EmptyState title="Selecione um conflito">Escolha a Primeira ou a Segunda Guerra Mundial no seletor do cabeçalho.</EmptyState>
}

// ------------------------------------------------------------------ structure
function StructureTab() {
  const conflict = useExplorer((s) => s.conflict)
  const q = useConflict(conflict)
  const select = useExplorer((s) => s.select)
  if (!conflict) return <NeedConflict />
  if (q.isLoading) return <Loading />
  if (q.isError) return <ErrorState error={q.error} onRetry={() => q.refetch()} />
  const c = q.data!
  return (
    <div className="pb-4">
      <div className="border-b border-ink-700 p-4">
        <button className="wa-heading text-left text-lg hover:text-brass-300" onClick={() => select({ type: 'conflict', slug: c.slug })}>
          {c.name}
        </button>
        <p className="font-mono text-[11px] text-steel-400">{formatRange(c.start_date, c.end_date)}</p>
        <p className="mt-2 text-[12.5px] leading-relaxed text-steel-300">{c.summary}</p>
      </div>
      <p className="wa-label px-4 pt-3 pb-1">Teatros de operações</p>
      {c.theaters.map((t) => (
        <TheaterItem key={t.id} t={t} />
      ))}
    </div>
  )
}

function TheaterItem({ t }: { t: TheaterNode }) {
  const [open, setOpen] = useState(t.battles.length > 0 || t.campaigns.length > 0)
  const select = useExplorer((s) => s.select)
  const fly = useExplorer((s) => s.fly)
  const empty = !t.battles.length && !t.campaigns.length
  const roots = t.campaigns.filter((c) => !c.parent_id || !t.campaigns.some((x) => x.id === c.parent_id))
  const looseBattles = t.battles.filter((b) => !b.campaign_id && !b.parent_id)
  return (
    <div className="px-2">
      <div className="flex items-center gap-1 rounded px-2 py-1.5 hover:bg-ink-800">
        <button className="text-steel-400" onClick={() => setOpen(!open)} aria-label={open ? 'Recolher' : 'Expandir'} disabled={empty}>
          <ChevronRight size={14} className={clsx('transition-transform', open && !empty && 'rotate-90', empty && 'opacity-30')} />
        </button>
        <button className="flex-1 text-left text-[13px] text-parchment" onClick={() => { select({ type: 'theater', slug: t.slug }); if (t.center) fly(t.center, t.zoom ?? undefined) }}>
          {t.name}
        </button>
        <span className="font-mono text-[10.5px] text-steel-400">{t.start_date?.slice(0, 4) ?? ''}</span>
      </div>
      {open && !empty && (
        <div className="ml-5 border-l border-ink-700 pl-2">
          {roots.map((c) => (
            <CampaignItem key={c.id} c={c} all={t.campaigns} battles={t.battles} />
          ))}
          {looseBattles.map((b) => (
            <BattleItem key={b.id} b={b} all={t.battles} />
          ))}
        </div>
      )}
      {empty && open && <p className="ml-7 pb-1 text-[11.5px] text-steel-400 italic">Estrutura cadastrada; sem batalhas detalhadas ainda.</p>}
    </div>
  )
}

function CampaignItem({ c, all, battles }: { c: CampaignBrief; all: CampaignBrief[]; battles: BattleBrief[] }) {
  const select = useExplorer((s) => s.select)
  const fly = useExplorer((s) => s.fly)
  const setDate = useExplorer((s) => s.setDate)
  const setReplay = useExplorer((s) => s.setReplay)
  const children = all.filter((x) => x.parent_id === c.id)
  const ownBattles = battles.filter((b) => b.campaign_id === c.id && !b.parent_id)
  const [open, setOpen] = useState(false)
  return (
    <div>
      <div className="group flex items-center gap-1 rounded px-1.5 py-1 hover:bg-ink-800">
        <button className="text-steel-400" onClick={() => setOpen(!open)} aria-label="Expandir">
          <ChevronRight size={13} className={clsx('transition-transform', open && 'rotate-90')} />
        </button>
        <button
          className="flex-1 text-left text-[12.5px] text-steel-200"
          onClick={() => {
            select({ type: 'campaign', slug: c.slug })
            if (c.start_date) setDate(c.start_date)
            if (c.center) fly(c.center, c.zoom ?? undefined)
          }}
        >
          <span className="mr-1 text-[10px] text-olive-400 uppercase">{CAMPAIGN_KINDS[c.kind]}</span>
          {c.name}
        </button>
        {!c.parent_id && (
          <button className="opacity-0 group-hover:opacity-100" title="Reproduzir campanha" onClick={() => { setReplay({ scope: 'campaign', slug: c.slug }); if (c.start_date) setDate(c.start_date); if (c.center) fly(c.center, c.zoom ?? undefined) }}>
            <Play size={12} className="text-brass-400" />
          </button>
        )}
      </div>
      {open && (
        <div className="ml-4 border-l border-ink-700 pl-2">
          {children.map((x) => (
            <CampaignItem key={x.id} c={x} all={all} battles={battles} />
          ))}
          {ownBattles.map((b) => (
            <BattleItem key={b.id} b={b} all={battles} />
          ))}
        </div>
      )}
    </div>
  )
}

function BattleItem({ b, all }: { b: BattleBrief; all: BattleBrief[] }) {
  const select = useExplorer((s) => s.select)
  const fly = useExplorer((s) => s.fly)
  const setDate = useExplorer((s) => s.setDate)
  const phases = all.filter((x) => x.parent_id === b.id)
  const [open, setOpen] = useState(false)
  return (
    <div>
      <div className="flex items-center gap-1 rounded px-1.5 py-1 hover:bg-ink-800">
        {phases.length > 0 ? (
          <button className="text-steel-400" onClick={() => setOpen(!open)} aria-label="Expandir fases">
            <ChevronRight size={13} className={clsx('transition-transform', open && 'rotate-90')} />
          </button>
        ) : (
          <Crosshair size={11} className="mx-0.5 text-alert/80" />
        )}
        <button
          className="flex-1 text-left text-[12.5px] text-steel-200"
          onClick={() => {
            select({ type: 'battle', slug: b.slug })
            if (b.start_date) setDate(b.start_date)
            if (b.location) fly(b.location, b.zoom ?? 10)
          }}
        >
          {b.name}
          <span className="ml-1 font-mono text-[10px] text-steel-400">{b.start_date ? formatDate(b.start_date) : ''}</span>
        </button>
      </div>
      {open && (
        <div className="ml-4 border-l border-ink-700 pl-2">
          {phases.map((p) => (
            <BattleItem key={p.id} b={p} all={all} />
          ))}
        </div>
      )}
    </div>
  )
}

// ------------------------------------------------------------------ countries
function CountriesTab() {
  const conflict = useExplorer((s) => s.conflict)
  const date = useExplorer((s) => s.date)
  const select = useExplorer((s) => s.select)
  const conflictQ = useConflict(conflict)
  const stateQ = useMapState(conflict, date)
  if (!conflict) return <NeedConflict />
  if (conflictQ.isLoading) return <Loading />
  const c = conflictQ.data
  if (!c) return null
  const activeIds = new Set(stateQ.data?.participants.map((p) => p.polity_id))
  const byAlliance = c.alliances.map((a) => ({ a, members: c.participants.filter((p) => p.alliance_id === a.id) }))
  return (
    <div className="pb-4">
      <p className="px-4 pt-3 text-[12px] text-steel-400">
        Participantes cadastrados. Em destaque: em guerra em <b className="text-steel-200">{formatDate(date)}</b>. A lista é parcial e cresce com o acervo.
      </p>
      {byAlliance.map(({ a, members }) => (
        <div key={a.id} className="mt-3">
          <div className="flex items-center gap-2 px-4 pb-1">
            <span className="size-2.5 rounded-sm" style={{ background: a.color ?? '#777' }} />
            <span className="wa-label">{a.name}</span>
          </div>
          {members.map((p, i) => {
            const active = activeIds.has(p.polity.id)
            return (
              <button
                key={`${p.polity.id}-${i}`}
                onClick={() => select({ type: 'polity', slug: p.polity.slug! })}
                className={clsx('flex w-full items-center justify-between gap-2 px-4 py-1.5 text-left hover:bg-ink-800', !active && 'opacity-50')}
              >
                <span className="flex items-center gap-2 text-[13px] text-parchment">
                  <span className="size-2 rounded-full" style={{ background: p.polity.color ?? '#777' }} />
                  {p.polity.short_name ?? p.polity.name}
                </span>
                <Period t={p} className="text-[10.5px]" />
              </button>
            )
          })}
        </div>
      ))}
    </div>
  )
}

// ------------------------------------------------------------------ events
function EventsTab() {
  const conflict = useExplorer((s) => s.conflict)
  const date = useExplorer((s) => s.date)
  const setDate = useExplorer((s) => s.setDate)
  const select = useExplorer((s) => s.select)
  const fly = useExplorer((s) => s.fly)
  const q = useTimeline(conflict)
  const [minImportance, setMin] = useState(1)
  const events = useMemo(() => (q.data?.events ?? []).filter((e) => e.importance >= minImportance), [q.data, minImportance])
  if (!conflict) return <NeedConflict />
  if (q.isLoading) return <Loading />
  if (q.isError) return <ErrorState error={q.error} />
  return (
    <div className="pb-4">
      <div className="flex items-center justify-between px-4 py-2">
        <span className="text-[12px] text-steel-400">{events.length} eventos documentados</span>
        <select className="wa-input w-auto py-0.5 text-[11.5px]" value={minImportance} onChange={(e) => setMin(Number(e.target.value))} aria-label="Importância mínima">
          <option value={1}>Todos</option>
          <option value={3}>Importância ≥ 3</option>
          <option value={4}>Importância ≥ 4</option>
          <option value={5}>Principais</option>
        </select>
      </div>
      {events.length === 0 && <EmptyState title="Nenhum evento cadastrado" />}
      <ol className="relative ml-6 border-l border-ink-600">
        {events.map((e) => (
          <li key={e.id} className="relative py-1.5 pr-3 pl-4">
            <span className={clsx('absolute top-3 -left-[5px] size-2.5 rotate-45', e.start_date === date ? 'bg-brass-300' : e.start_date < date! ? 'bg-brass-600' : 'bg-ink-500')} />
            <button
              className="text-left"
              onClick={() => {
                setDate(e.start_date)
                select({ type: 'event', slug: e.slug })
                if (e.location) fly(e.location)
              }}
            >
              <div className="font-mono text-[10.5px] text-steel-400">
                {formatDate(e.start_date, e.date_precision)}
                {e.time_of_day && e.time_of_day.length < 7 ? ` · ${e.time_of_day}` : ''}
              </div>
              <div className={clsx('text-[12.5px] leading-snug', e.start_date === date ? 'text-brass-300' : 'text-steel-200')}>{e.title}</div>
            </button>
          </li>
        ))}
      </ol>
    </div>
  )
}

// ------------------------------------------------------------------ layers
function LayersTab() {
  const layers = useExplorer((s) => s.layers)
  const toggle = useExplorer((s) => s.toggleLayer)
  const mode = useExplorer((s) => s.mode)
  const groups = ['Político', 'Geografia', 'Militar', 'Leitura'] as const
  return (
    <div className="pb-4">
      <p className="px-4 pt-3 text-[12px] text-steel-400">
        Modo <b className="text-steel-200">{MODES[mode].label}</b>: {MODES[mode].description} As camadas podem ser combinadas livremente.
      </p>
      {groups.map((g) => (
        <div key={g} className="mt-3">
          <p className="wa-label px-4 pb-1">{g}</p>
          {LAYERS.filter((l) => l.group === g).map((l) => (
            <label key={l.id} className="flex cursor-pointer items-start gap-2.5 px-4 py-1.5 hover:bg-ink-800">
              <input type="checkbox" className="mt-0.5 accent-[#c9a96a]" checked={layers[l.id]} onChange={() => toggle(l.id)} />
              <span className="mt-1 flex w-4 justify-center">
                <Swatch {...l.swatch} />
              </span>
              <span className="flex-1">
                <span className="block text-[12.5px] text-steel-200">{l.label}</span>
                <span className="block text-[11px] leading-snug text-steel-400">{l.description}</span>
              </span>
            </label>
          ))}
        </div>
      ))}
    </div>
  )
}

// ------------------------------------------------------------------ equipment
function EquipmentTab() {
  const conflict = useExplorer((s) => s.conflict)
  const select = useExplorer((s) => s.select)
  const [category, setCategory] = useState('')
  const [q, setQ] = useState('')
  const [onlyConflict, setOnly] = useState(true)
  const list = useEquipmentList({ category: category || undefined, conflict: onlyConflict ? conflict : undefined, q: q || undefined })
  const grouped = useMemo(() => {
    const g = new Map<string, typeof list.data>()
    for (const e of list.data ?? []) g.set(e.category, [...(g.get(e.category) ?? []), e])
    return [...g.entries()]
  }, [list.data])
  return (
    <div className="pb-4">
      <div className="space-y-2 p-3">
        <input className="wa-input" placeholder="Filtrar por nome…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Filtrar equipamentos" />
        <div className="flex gap-2">
          <select className="wa-input py-1" value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Categoria">
            <option value="">Todas as categorias</option>
            {Object.entries(EQUIPMENT_CATEGORIES).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <label className="flex shrink-0 items-center gap-1 text-[11.5px] text-steel-300">
            <input type="checkbox" checked={onlyConflict} onChange={(e) => setOnly(e.target.checked)} disabled={!conflict} /> Conflito atual
          </label>
        </div>
      </div>
      {list.isLoading && <Loading />}
      {list.data?.length === 0 && <EmptyState title="Nenhum equipamento cadastrado com esses filtros" />}
      {grouped.map(([cat, items]) => (
        <div key={cat}>
          <p className="wa-label px-4 pt-2 pb-1">{EQUIPMENT_CATEGORIES[cat] ?? cat}</p>
          {items!.map((e) => (
            <button key={e.slug} onClick={() => select({ type: 'equipment', slug: e.slug })} className="flex w-full flex-col px-4 py-1.5 text-left hover:bg-ink-800">
              <span className="text-[13px] text-parchment">{e.name}</span>
              <span className="text-[11px] text-steel-400">
                {[e.type_label, e.origin?.name, e.valid_from ? `em serviço desde ${formatDate(e.valid_from, e.valid_from_precision)}` : null].filter(Boolean).join(' · ')}
              </span>
            </button>
          ))}
        </div>
      ))}
    </div>
  )
}

// ------------------------------------------------------------------ uniforms
function UniformsTab() {
  const conflict = useExplorer((s) => s.conflict)
  const uniforms = useUniforms(conflict)
  const camos = useCamouflages()
  return (
    <div className="space-y-3 pb-4">
      <div className="p-3">
        <PlannedFeature phase={2}>Galerias com fotografias licenciadas, insígnias e filtros por teatro e função estão planejadas. Abaixo, os registros já cadastrados.</PlannedFeature>
      </div>
      <p className="wa-label px-4">Uniformes{conflict ? ' do período' : ''}</p>
      {uniforms.isLoading && <Loading />}
      {uniforms.data?.length === 0 && <EmptyState title="Nenhum uniforme cadastrado para este conflito" />}
      {uniforms.data?.map((u) => (
        <div key={u.slug} className="mx-3 rounded-md border border-ink-700 p-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-[13px] text-parchment">{u.name}</p>
              <p className="text-[11px] text-steel-400">{u.polity?.short_name} · <Period t={u} /></p>
            </div>
            <div className="flex gap-1">
              {(u.colors ?? []).map((c: { hex: string; name: string }) => (
                <span key={c.hex} className="size-5 rounded border border-ink-500" style={{ background: c.hex }} title={`${c.name} (aproximação visual)`} />
              ))}
            </div>
          </div>
          <p className="mt-1.5 text-[12px] leading-relaxed text-steel-300">{u.description}</p>
          <div className="mt-2 text-[11px]">
            <Citations items={u.citations} />
          </div>
        </div>
      ))}
      <p className="wa-label px-4 pt-2">Camuflagens</p>
      {camos.data?.map((c) => (
        <div key={c.slug} className="mx-3 rounded-md border border-ink-700 p-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-[13px] text-parchment">{c.name}</p>
              <p className="text-[11px] text-steel-400">
                <Period t={c} />
              </p>
            </div>
            <div className="flex gap-1">
              {(c.colors ?? []).map((x: { hex: string; name: string }) => (
                <span key={x.hex} className="size-5 rounded border border-ink-500" style={{ background: x.hex }} title={`${x.name} (aproximação visual)`} />
              ))}
            </div>
          </div>
          <p className="mt-1.5 text-[12px] leading-relaxed text-steel-300">{c.description}</p>
          {c.usage_note && <p className="mt-1 text-[11px] text-steel-400 italic">{c.usage_note}</p>}
          <div className="mt-2 text-[11px]">
            <Citations items={c.citations} />
          </div>
        </div>
      ))}
      <p className="px-4 text-[11px] text-steel-400">Amostras de cor são aproximações para visualização; tons reais variavam por fabricante, lote e desgaste.</p>
    </div>
  )
}
