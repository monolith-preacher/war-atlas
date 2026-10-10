/* eslint-disable @typescript-eslint/no-explicit-any */
import { Crosshair, MapPin, Play } from 'lucide-react'
import type { ReactNode } from 'react'
import { formatDate, formatRange } from '../../lib/dates'
import { BATTLE_KINDS, CAMPAIGN_KINDS, ECHELONS, SPATIAL_ROLES } from '../../lib/labels'
import { useExplorer } from '../../store/explorer'
import { Citations, EntityLink, Figures, MediaGallery, Provenance } from '../common/docs'
import { Badge, CertaintyBadge, KeyValue, Period, Section, Undocumented } from '../common/ui'

export function PanelHeader({ title, subtitle, original, children }: { title: string; subtitle?: ReactNode; original?: string | null; children?: ReactNode }) {
  return (
    <div className="border-b border-ink-700 px-4 pt-3 pb-3">
      <h2 className="wa-heading text-[21px] leading-tight">{title}</h2>
      {original && original !== title && <p className="mt-0.5 text-[12px] text-steel-400 italic">{original}</p>}
      {subtitle && <div className="mt-1 text-[12px] text-steel-300">{subtitle}</div>}
      {children && <div className="mt-2 flex flex-wrap items-center gap-2">{children}</div>}
    </div>
  )
}

export function Text({ value }: { value?: string | null }) {
  if (!value) return <Undocumented />
  return (
    <div className="wa-prose text-[13px] text-steel-200">
      {value.split(/\n{2,}/).map((p, i) => (
        <p key={i}>{p}</p>
      ))}
    </div>
  )
}

function FocusButtons({ location, zoom, date, replay }: { location?: [number, number] | null; zoom?: number | null; date?: string | null; replay?: { scope: 'campaign' | 'battle'; slug: string } }) {
  const fly = useExplorer((s) => s.fly)
  const setDate = useExplorer((s) => s.setDate)
  const setReplay = useExplorer((s) => s.setReplay)
  const conflictDate = useExplorer((s) => s.date)
  return (
    <>
      {location && (
        <button className="wa-btn" onClick={() => fly(location, zoom ?? 10)}>
          <MapPin size={13} /> Localizar no mapa
        </button>
      )}
      {date && date !== conflictDate && (
        <button className="wa-btn" onClick={() => setDate(date)}>
          <Crosshair size={13} /> Ir para {formatDate(date)}
        </button>
      )}
      {replay && (
        <button
          className="wa-btn wa-btn-primary"
          onClick={() => {
            setReplay(replay)
            if (date) setDate(date)
            if (location) fly(location, zoom ?? 9)
          }}
        >
          <Play size={13} /> Reproduzir cronologia
        </button>
      )}
    </>
  )
}

function EventList({ events }: { events: any[] }) {
  const setDate = useExplorer((s) => s.setDate)
  const select = useExplorer((s) => s.select)
  const fly = useExplorer((s) => s.fly)
  if (!events?.length) return <Undocumented>Nenhum evento cadastrado.</Undocumented>
  return (
    <ol className="relative ml-1 border-l border-ink-600">
      {events.map((e) => (
        <li key={e.id} className="relative py-1 pl-3">
          <span className="absolute top-2.5 -left-[4px] size-2 rotate-45 bg-brass-600" />
          <button
            className="text-left"
            onClick={() => {
              setDate(e.start_date)
              select({ type: 'event', slug: e.slug })
              if (e.location) fly(e.location)
            }}
          >
            <span className="font-mono text-[10.5px] text-steel-400">
              {formatDate(e.start_date, e.date_precision)}
              {e.time_of_day ? ` · ${e.time_of_day}` : ''}
            </span>
            <span className="block text-[12.5px] leading-snug text-steel-200 hover:text-brass-300">{e.title}</span>
          </button>
        </li>
      ))}
    </ol>
  )
}

function SidesTable({ participants, commanders, units }: { participants: any[]; commanders: any[]; units?: any[] }) {
  const sides = ['a', 'b']
  return (
    <div className="grid grid-cols-2 gap-3 text-[12.5px]">
      {sides.map((side) => (
        <div key={side}>
          <p className="mb-1 text-[11px] text-steel-400 uppercase">{side === 'a' ? 'Lado A' : 'Lado B'}</p>
          <ul className="space-y-0.5">
            {participants.filter((p) => p.side === side).map((p) => (
              <li key={p.polity.id} className="flex items-center gap-1.5">
                <span className="size-2 rounded-full" style={{ background: p.polity.color ?? '#777' }} />
                <EntityLink type="polity" slug={p.polity.slug}>
                  {p.polity.short_name ?? p.polity.name}
                </EntityLink>
                {p.role && <span className="text-[10.5px] text-steel-400">({p.role})</span>}
              </li>
            ))}
          </ul>
          {commanders.filter((c) => c.side === side).length > 0 && <p className="mt-2 mb-1 text-[11px] text-steel-400 uppercase">Comandantes</p>}
          <ul className="space-y-0.5">
            {commanders.filter((c) => c.side === side).map((c) => (
              <li key={c.person.id}>
                <EntityLink type="person" slug={c.person.slug}>
                  {c.person.name}
                </EntityLink>
                {c.role && <span className="block text-[10.5px] text-steel-400">{c.role}</span>}
              </li>
            ))}
          </ul>
          {units && units.filter((u) => u.side === side).length > 0 && <p className="mt-2 mb-1 text-[11px] text-steel-400 uppercase">Unidades</p>}
          <ul className="space-y-0.5">
            {(units ?? []).filter((u) => u.side === side).map((u) => (
              <li key={u.unit.id}>
                <EntityLink type="unit" slug={u.unit.slug}>
                  {u.unit.name}
                </EntityLink>
                <span className="block text-[10.5px] text-steel-400">
                  {ECHELONS[u.unit.echelon]}
                  {u.role ? ` · ${u.role}` : ''}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

function DocsSections({ d, figures = false }: { d: any; figures?: boolean }) {
  return (
    <>
      {figures && (
        <Section title="Números documentados (efetivos, baixas)">
          <Figures items={d.figures} />
        </Section>
      )}
      <Section title="Imagens e documentos" defaultOpen={false}>
        <MediaGallery items={d.media} />
      </Section>
      <Section title={`Fontes (${d.citations?.length ?? 0})`}>
        <Provenance d={d} />
        <div className="mt-2">
          <Citations items={d.citations} />
        </div>
      </Section>
    </>
  )
}

// ------------------------------------------------------------------ conflict
export function ConflictPanel({ d }: { d: any }) {
  return (
    <div>
      <PanelHeader title={d.name} original={d.name_original} subtitle={<span className="font-mono">{formatRange(d.start_date, d.end_date)}</span>} />
      <Section title="Resumo">
        <Text value={d.summary} />
        {d.description && <Text value={d.description} />}
      </Section>
      <Section title="Alianças">
        {d.alliances.map((a: any) => (
          <div key={a.id} className="mb-2">
            <p className="flex items-center gap-2 text-[13px] text-parchment">
              <span className="size-2.5 rounded-sm" style={{ background: a.color }} /> {a.name}
            </p>
            {a.summary && <p className="text-[12px] text-steel-400">{a.summary}</p>}
          </div>
        ))}
      </Section>
      <Section title={`Teatros de operações (${d.theaters.length})`}>
        <ul className="space-y-1">
          {d.theaters.map((t: any) => (
            <li key={t.id} className="flex justify-between gap-2 text-[12.5px]">
              <EntityLink type="theater" slug={t.slug} location={t.center} zoom={t.zoom}>
                {t.name}
              </EntityLink>
              <span className="font-mono text-[10.5px] text-steel-400">{t.battles.length} batalhas</span>
            </li>
          ))}
        </ul>
      </Section>
      <Section title="Fronteiras históricas disponíveis" defaultOpen={false}>
        {d.boundary_datasets.length ? (
          <ul className="text-[12px]">
            {d.boundary_datasets.map((b: any) => (
              <li key={b.slug}>
                {b.name} — aplicável {formatRange(b.valid_from, b.valid_to)}
              </li>
            ))}
          </ul>
        ) : (
          <Undocumented />
        )}
      </Section>
      <DocsSections d={d} />
    </div>
  )
}

// ------------------------------------------------------------------ theater
export function TheaterPanel({ d }: { d: any }) {
  return (
    <div>
      <PanelHeader title={d.name} original={d.name_original} subtitle={<>Teatro de operações · <EntityLink type="conflict" slug={d.conflict?.slug}>{d.conflict?.name}</EntityLink></>}>
        <FocusButtons location={d.center} zoom={d.zoom} />
      </PanelHeader>
      <Section title="Período">
        <span className="font-mono text-[12px]">{formatRange(d.start_date, d.end_date)}</span>
      </Section>
      <Section title="Resumo">
        <Text value={d.summary ?? d.description} />
      </Section>
      <Section title={`Campanhas e operações (${d.campaigns.length})`}>
        {d.campaigns.length ? (
          <ul className="space-y-1 text-[12.5px]">
            {d.campaigns.map((c: any) => (
              <li key={c.id}>
                <EntityLink type="campaign" slug={c.slug} location={c.center} zoom={c.zoom}>{c.name}</EntityLink>
                <span className="ml-1 font-mono text-[10.5px] text-steel-400">{formatRange(c.start_date, c.end_date)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <Undocumented>Nenhuma campanha cadastrada neste teatro ainda.</Undocumented>
        )}
      </Section>
      <Section title={`Batalhas (${d.battles.length})`}>
        {d.battles.length ? (
          <ul className="space-y-1 text-[12.5px]">
            {d.battles.map((b: any) => (
              <li key={b.id}>
                <EntityLink type="battle" slug={b.slug} location={b.location} zoom={b.zoom}>{b.name}</EntityLink>
                <span className="ml-1 font-mono text-[10.5px] text-steel-400">{formatRange(b.start_date, b.end_date)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <Undocumented>Nenhuma batalha cadastrada neste teatro ainda.</Undocumented>
        )}
      </Section>
      <DocsSections d={d} />
    </div>
  )
}

// ------------------------------------------------------------------ campaign
export function CampaignPanel({ d }: { d: any }) {
  return (
    <div>
      <PanelHeader
        title={d.name}
        original={d.name_original}
        subtitle={
          <>
            {CAMPAIGN_KINDS[d.kind]}
            {d.codename && <> · codinome <b className="text-parchment">{d.codename}</b></>}
            {d.parent && <> · parte de <EntityLink type="campaign" slug={d.parent.slug}>{d.parent.name}</EntityLink></>}
            {d.theater && <> · <EntityLink type="theater" slug={d.theater.slug}>{d.theater.name}</EntityLink></>}
          </>
        }
      >
        <FocusButtons location={d.center} zoom={d.zoom} date={d.start_date} replay={!d.parent ? { scope: 'campaign', slug: d.slug } : undefined} />
        <CertaintyBadge value={d.certainty} />
      </PanelHeader>
      <Section title="Período">
        <span className="font-mono text-[12px]">{formatRange(d.start_date, d.end_date, d.start_precision, d.end_precision)}</span>
      </Section>
      <Section title="Contexto e objetivos">
        <Text value={d.summary} />
        {d.description && <Text value={d.description} />}
        {d.objectives && (
          <>
            <p className="wa-label mt-2 mb-1">Objetivos</p>
            <Text value={d.objectives} />
          </>
        )}
        {d.outcome && (
          <>
            <p className="wa-label mt-2 mb-1">Desfecho</p>
            <Text value={d.outcome} />
          </>
        )}
      </Section>
      {d.operations.length > 0 && (
        <Section title={`Operações (${d.operations.length})`}>
          <ul className="space-y-1 text-[12.5px]">
            {d.operations.map((o: any) => (
              <li key={o.id}>
                <EntityLink type="campaign" slug={o.slug} location={o.center} zoom={o.zoom}>{o.name}</EntityLink>
                <span className="ml-1 font-mono text-[10.5px] text-steel-400">{formatRange(o.start_date, o.end_date)}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}
      <Section title={`Batalhas (${d.battles.length})`}>
        {d.battles.length ? (
          <ul className="space-y-1 text-[12.5px]">
            {d.battles.map((b: any) => (
              <li key={b.id}>
                <EntityLink type="battle" slug={b.slug} location={b.location} zoom={b.zoom}>{b.name}</EntityLink>
                <span className="ml-1 font-mono text-[10.5px] text-steel-400">{formatRange(b.start_date, b.end_date)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <Undocumented />
        )}
      </Section>
      <Section title={`Comandantes (${d.commanders.length})`} defaultOpen={false}>
        {d.commanders.length ? (
          <ul className="grid grid-cols-2 gap-1 text-[12.5px]">
            {d.commanders.map((c: any) => (
              <li key={c.person.id}>
                <EntityLink type="person" slug={c.person.slug}>{c.person.name}</EntityLink>
              </li>
            ))}
          </ul>
        ) : (
          <Undocumented />
        )}
      </Section>
      <Section title={`Cronologia (${d.events.length} eventos)`}>
        <EventList events={d.events} />
      </Section>
      <DocsSections d={d} figures />
    </div>
  )
}

// ------------------------------------------------------------------ battle
export function BattlePanel({ d }: { d: any }) {
  return (
    <div>
      <PanelHeader
        title={d.name}
        original={d.name_original}
        subtitle={
          <>
            {BATTLE_KINDS[d.kind]} · <span className="font-mono">{formatRange(d.start_date, d.end_date, d.start_precision, d.end_precision)}</span>
            {d.parent && <> · fase de <EntityLink type="battle" slug={d.parent.slug}>{d.parent.name}</EntityLink></>}
            {d.campaign && <> · <EntityLink type="campaign" slug={d.campaign.slug}>{d.campaign.name}</EntityLink></>}
            {d.theater && <> · <EntityLink type="theater" slug={d.theater.slug}>{d.theater.name}</EntityLink></>}
          </>
        }
      >
        <FocusButtons location={d.location} zoom={d.zoom} date={d.start_date} replay={d.events.length ? { scope: 'battle', slug: d.slug } : undefined} />
        <CertaintyBadge value={d.certainty} />
      </PanelHeader>
      <Section title="Localização">
        {d.location ? (
          <p className="text-[12.5px]">
            {SPATIAL_ROLES[d.location_role]}
            {d.location_precision_m && <span className="text-steel-400"> · precisão ±{(d.location_precision_m / 1000).toLocaleString('pt-BR')} km</span>}
            {d.place && <> · <EntityLink type="place" slug={d.place.slug}>{d.place.name}</EntityLink></>}
          </p>
        ) : (
          <Undocumented>Localização não cadastrada.</Undocumented>
        )}
      </Section>
      <Section title="Resumo">
        <Text value={d.summary} />
      </Section>
      {(d.context || d.objectives || d.strategy) && (
        <Section title="Contexto, objetivos e estratégia">
          {d.context && <><p className="wa-label mb-1">Contexto</p><Text value={d.context} /></>}
          {d.objectives && <><p className="wa-label mt-2 mb-1">Objetivos</p><Text value={d.objectives} /></>}
          {d.strategy && <><p className="wa-label mt-2 mb-1">Estratégia</p><Text value={d.strategy} /></>}
        </Section>
      )}
      <Section title="Participantes, comandantes e unidades">
        {d.participants.length ? <SidesTable participants={d.participants} commanders={d.commanders} units={d.units} /> : <Undocumented />}
      </Section>
      <Section title="Resultado e consequências">
        <KeyValue label="Resultado">{d.result}</KeyValue>
        {d.consequences && <Text value={d.consequences} />}
      </Section>
      {d.phases.length > 0 && (
        <Section title={`Fases (${d.phases.length})`}>
          <ul className="space-y-1 text-[12.5px]">
            {d.phases.map((p: any) => (
              <li key={p.id} className="flex justify-between gap-2">
                <EntityLink type="battle" slug={p.slug} location={p.location} zoom={p.zoom}>{p.name}</EntityLink>
                <span className="shrink-0 font-mono text-[10.5px] text-steel-400">{formatRange(p.start_date, p.end_date)}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}
      <Section title={`Cronologia (${d.events.length})`}>
        <EventList events={d.events} />
      </Section>
      <DocsSections d={d} figures />
    </div>
  )
}

// ------------------------------------------------------------------ event
export function EventPanel({ d }: { d: any }) {
  return (
    <div>
      <PanelHeader
        title={d.title}
        subtitle={
          <span className="font-mono">
            {formatDate(d.start_date, d.date_precision, 'long')}
            {d.end_date && d.end_date !== d.start_date ? ` – ${formatDate(d.end_date)}` : ''}
            {d.time_of_day ? ` · ${d.time_of_day}` : ''}
          </span>
        }
      >
        <FocusButtons location={d.location} zoom={11} date={d.start_date} />
        <CertaintyBadge value={d.certainty} />
      </PanelHeader>
      <Section title="Descrição">
        <Text value={d.summary} />
        {d.description && <Text value={d.description} />}
      </Section>
      <Section title="Contexto">
        <KeyValue label="Batalha">{d.battle && <EntityLink type="battle" slug={d.battle.slug}>{d.battle.name}</EntityLink>}</KeyValue>
        <KeyValue label="Campanha">{d.campaign && <EntityLink type="campaign" slug={d.campaign.slug}>{d.campaign.name}</EntityLink>}</KeyValue>
        <KeyValue label="Local">{d.place && <EntityLink type="place" slug={d.place.slug}>{d.place.name}</EntityLink>}</KeyValue>
        <KeyValue label="Geometria">
          {d.location ? (
            <span>
              {SPATIAL_ROLES[d.spatial_role]}
              {d.precision_m ? ` · ±${(d.precision_m / 1000).toLocaleString('pt-BR')} km` : ''}
            </span>
          ) : null}
        </KeyValue>
      </Section>
      {(d.units.length > 0 || d.persons.length > 0) && (
        <Section title="Envolvidos">
          <ul className="space-y-0.5 text-[12.5px]">
            {d.units.map((u: any) => (
              <li key={`u${u.unit.id}`}><EntityLink type="unit" slug={u.unit.slug}>{u.unit.name}</EntityLink> {u.role && <span className="text-steel-400">({u.role})</span>}</li>
            ))}
            {d.persons.map((p: any) => (
              <li key={`p${p.person.id}`}><EntityLink type="person" slug={p.person.slug}>{p.person.name}</EntityLink> {p.role && <span className="text-steel-400">({p.role})</span>}</li>
            ))}
          </ul>
        </Section>
      )}
      <DocsSections d={d} />
    </div>
  )
}

// ------------------------------------------------------------------ place
export function PlacePanel({ d }: { d: any }) {
  return (
    <div>
      <PanelHeader title={d.name} original={d.name_original} subtitle={[d.kind, d.modern_country].filter(Boolean).join(' · ')}>
        <FocusButtons location={d.location} zoom={12} />
      </PanelHeader>
      <Section title="Localização">
        <KeyValue label="Coordenadas">{d.location && <span className="font-mono">{d.location[1].toFixed(4)}, {d.location[0].toFixed(4)}</span>}</KeyValue>
        <KeyValue label="Significado">{SPATIAL_ROLES[d.spatial_role]}</KeyValue>
        <KeyValue label="Precisão">{d.precision_m ? `±${d.precision_m} m` : null}</KeyValue>
        {d.notes && <p className="mt-1 text-[12px] text-steel-400 italic">{d.notes}</p>}
      </Section>
      <Section title="Batalhas e eventos">
        <ul className="space-y-0.5 text-[12.5px]">
          {d.battles.map((b: any) => <li key={b.id}><EntityLink type="battle" slug={b.slug}>{b.name}</EntityLink></li>)}
        </ul>
        <EventList events={d.events} />
      </Section>
      <DocsSections d={d} />
    </div>
  )
}

// ------------------------------------------------------------------ map feature
export function MapFeaturePanel({ d }: { d: any }) {
  const approx = ['schematic', 'approximate_position'].includes(d.spatial_role) || ['reconstructed', 'estimated'].includes(d.certainty)
  return (
    <div>
      <PanelHeader title={d.label} subtitle={<Period t={d} />}>
        <CertaintyBadge value={d.certainty} />
        <Badge tone={approx ? 'warn' : 'neutral'}>{SPATIAL_ROLES[d.spatial_role]}</Badge>
      </PanelHeader>
      {approx && (
        <div className="mx-4 mt-3 rounded-md border border-warn/40 bg-warn/10 p-3 text-[12px] text-parchment">
          Esta geometria é uma <b>{SPATIAL_ROLES[d.spatial_role].toLowerCase()}</b>
          {d.precision_m ? ` com erro esperado de até ±${(d.precision_m / 1000).toLocaleString('pt-BR')} km` : ''}. Ela não deve ser lida como traçado exato.
        </div>
      )}
      <Section title="Método de produção da geometria">
        <Text value={d.method_note} />
      </Section>
      {d.description && (
        <Section title="Descrição">
          <Text value={d.description} />
        </Section>
      )}
      <Section title="Vínculos">
        <KeyValue label="Batalha">{d.battle && <EntityLink type="battle" slug={d.battle.slug}>{d.battle.name}</EntityLink>}</KeyValue>
        <KeyValue label="Campanha">{d.campaign && <EntityLink type="campaign" slug={d.campaign.slug}>{d.campaign.name}</EntityLink>}</KeyValue>
        <KeyValue label="Unidade">{d.unit && <EntityLink type="unit" slug={d.unit.slug}>{d.unit.name}</EntityLink>}</KeyValue>
      </Section>
      <DocsSections d={d} />
    </div>
  )
}
