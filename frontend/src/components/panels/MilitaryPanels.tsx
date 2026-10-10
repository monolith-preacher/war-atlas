/* eslint-disable @typescript-eslint/no-explicit-any */
import clsx from 'clsx'
import { ChevronRight, Info } from 'lucide-react'
import { useState } from 'react'
import { formatDate, formatRange } from '../../lib/dates'
import { BRANCHES, ECHELONS, EQUIPMENT_CATEGORIES, EXISTENCE, POSITION_KINDS, RELATIONS } from '../../lib/labels'
import type { TreeNode } from '../../lib/types'
import { useExplorer } from '../../store/explorer'
import { EntityLink } from '../common/docs'
import { Badge, CertaintyBadge, KeyValue, Period, Section, Undocumented } from '../common/ui'
import { Citations, Figures, MediaGallery, Provenance } from '../common/docs'
import { PanelHeader, Text } from './HistoryPanels'

function DocsBlock({ d, figures = false }: { d: any; figures?: boolean }) {
  return (
    <>
      {figures && d.figures?.length > 0 && (
        <Section title="Efetivos e números documentados">
          <Figures items={d.figures} />
        </Section>
      )}
      <Section title="Imagens, insígnias e documentos" defaultOpen={false}>
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

function DateNote({ date }: { date: string | null }) {
  return (
    <p className="flex items-start gap-1.5 text-[11.5px] text-steel-400">
      <Info size={12} className="mt-0.5 shrink-0" />
      {date
        ? `Exibindo apenas relações documentadas como válidas em ${formatDate(date)}. Mova a linha do tempo para ver outra data.`
        : 'Selecione uma data na linha do tempo para ver a situação naquele dia.'}
    </p>
  )
}

/** Hierarchy built ONLY from documented subordination records valid at the selected date. */
export function UnitTree({ nodes, depth = 0 }: { nodes: TreeNode[]; depth?: number }) {
  return (
    <ul className={clsx(depth > 0 && 'ml-3 border-l border-ink-600 pl-2')}>
      {nodes.map((n) => (
        <TreeItem key={`${n.id}-${depth}`} n={n} depth={depth} />
      ))}
    </ul>
  )
}

function TreeItem({ n, depth }: { n: TreeNode; depth: number }) {
  const [open, setOpen] = useState(depth < 2)
  const has = n.children.length > 0
  const attested = n.relation && (n.relation.valid_from_precision === 'attested' || n.relation.valid_to_precision === 'attested')
  return (
    <li className="py-0.5">
      <div className="flex items-start gap-1">
        <button className="mt-0.5 text-steel-400" onClick={() => setOpen(!open)} disabled={!has} aria-label="Expandir">
          <ChevronRight size={13} className={clsx('transition-transform', open && has && 'rotate-90', !has && 'opacity-20')} />
        </button>
        <div className="min-w-0 flex-1">
          <EntityLink type="unit" slug={n.slug}>
            <span className="text-[12.5px]">{n.name}</span>
          </EntityLink>
          <div className="text-[10.5px] text-steel-400">
            {n.type_label ?? ECHELONS[n.echelon]}
            {n.relation && n.relation.kind !== 'organic' && <span className="text-info"> · {RELATIONS[n.relation.kind]}</span>}
            {attested && <span className="text-warn" title="Relação atestada nesta data; limites reais não documentados"> · ≈ atestada</span>}
            {n.commanders.length > 0 && <> · cmd. {n.commanders.map((c) => c.person.name).join(', ')}</>}
          </div>
        </div>
      </div>
      {open && has && <UnitTree nodes={n.children} depth={depth + 1} />}
      {n.has_more && <p className="ml-5 text-[10.5px] text-steel-400">… mais níveis (abra a ficha da unidade)</p>}
    </li>
  )
}

// ------------------------------------------------------------------ polity
export function PolityPanel({ d }: { d: any }) {
  const date = useExplorer((s) => s.date)
  const currentPeriod = d.periods.find((p: any) => p.valid_at_date)
  const activeParticipation = d.participations.filter((p: any) => p.valid_at_date)
  const activeAlliances = d.alliances.filter((a: any) => a.valid_at_date)
  return (
    <div>
      <PanelHeader title={d.name} original={d.name_original} subtitle={<>{d.kind} · existência: <Period t={d} /></>}>
        <CertaintyBadge value={d.certainty} />
        {date && !d.exists_at_date && <Badge tone="warn">Não existia nesta data</Badge>}
      </PanelHeader>
      <Section title={`Situação em ${formatDate(date)}`}>
        <KeyValue label="Participação">
          {activeParticipation.length ? (
            activeParticipation.map((p: any, i: number) => (
              <span key={i} className="block">
                {p.role} em <EntityLink type="conflict" slug={p.conflict?.slug}>{p.conflict?.name}</EntityLink>
              </span>
            ))
          ) : (
            <span className="text-steel-400">Não em guerra nesta data (segundo os registros)</span>
          )}
        </KeyValue>
        <KeyValue label="Alinhamento">
          {activeAlliances.length ? activeAlliances.map((a: any, i: number) => <span key={i} className="block">{a.alliance.name} ({a.role})</span>) : null}
        </KeyValue>
        <KeyValue label="Governo">{currentPeriod?.government_type}</KeyValue>
        <KeyValue label="Chefe de Estado">{currentPeriod?.head_of_state}</KeyValue>
        <KeyValue label="Chefe de governo">{currentPeriod?.head_of_government}</KeyValue>
        <KeyValue label="Capital">{currentPeriod?.capital_name}</KeyValue>
      </Section>
      <Section title="Contexto">
        <Text value={d.summary ?? d.description} />
        {d.participations.map((p: any, i: number) => (
          <div key={i} className="mt-2 rounded border border-ink-700 p-2 text-[12px]">
            <p className="text-parchment">
              <EntityLink type="conflict" slug={p.conflict?.slug}>{p.conflict?.name}</EntityLink> · <Period t={p} />
            </p>
            {p.summary && <p className="mt-1 text-steel-300">{p.summary}</p>}
            {p.entry_note && <p className="text-steel-400">Entrada: {p.entry_note}</p>}
            {p.exit_note && <p className="text-steel-400">Saída: {p.exit_note}</p>}
          </div>
        ))}
      </Section>
      <Section title="Forças armadas e organização militar">
        <DateNote date={date} />
        {d.armed_forces.length === 0 && <Undocumented>Nenhuma força armada cadastrada.</Undocumented>}
        {d.armed_forces.map((f: any) => (
          <div key={f.id} className={clsx('mt-3', !f.valid_at_date && date && 'opacity-50')}>
            <p className="flex items-center gap-2">
              <EntityLink type="armed_force" slug={f.slug}>
                <span className="text-[13px] font-semibold">{f.name}</span>
              </EntityLink>
              <span className="wa-chip">{BRANCHES[f.branch]}</span>
            </p>
            {f.tree?.length ? <UnitTree nodes={f.tree} /> : date && f.valid_at_date ? <p className="text-[11.5px] text-steel-400 italic">Nenhuma subordinação documentada diretamente a esta força nesta data.</p> : null}
            {f.unplaced_units?.length > 0 && (
              <div className="mt-1.5 text-[11.5px]">
                <p className="text-steel-400">Unidades existentes sem subordinação documentada nesta data:</p>
                <ul className="ml-3 list-disc text-steel-300">
                  {f.unplaced_units.map((u: any) => <li key={u.id}><EntityLink type="unit" slug={u.slug}>{u.name}</EntityLink></li>)}
                </ul>
              </div>
            )}
          </div>
        ))}
      </Section>
      <Section title={`Comandantes ${date ? 'na data' : ''} (${d.commanders.length})`}>
        {d.commanders.length ? (
          <ul className="space-y-1 text-[12.5px]">
            {d.commanders.map((c: any, i: number) => (
              <li key={i}>
                <EntityLink type="person" slug={c.person.slug}>{c.person.name}</EntityLink>
                <span className="block text-[11px] text-steel-400">{c.title} · <Period t={c} /></span>
              </li>
            ))}
          </ul>
        ) : (
          <Undocumented>Nenhum comando documentado nesta data.</Undocumented>
        )}
      </Section>
      <Section title={`Batalhas e campanhas (${d.battles.length})`} defaultOpen={false}>
        <ul className="space-y-0.5 text-[12.5px]">
          {d.battles.map((b: any) => (
            <li key={b.battle.id}>
              <EntityLink type="battle" slug={b.battle.slug} location={b.battle.location}>{b.battle.name}</EntityLink>
              <span className="ml-1 font-mono text-[10.5px] text-steel-400">{formatRange(b.battle.start_date, b.battle.end_date)}</span>
            </li>
          ))}
        </ul>
        {d.campaigns.length > 0 && (
          <ul className="mt-2 space-y-0.5 text-[12.5px]">
            {d.campaigns.map((c: any) => <li key={c.id}><EntityLink type="campaign" slug={c.slug}>{c.name}</EntityLink></li>)}
          </ul>
        )}
      </Section>
      <Section title={`Equipamentos em serviço nacional${date ? ' na data' : ''} (${d.equipment.length})`} defaultOpen={false}>
        <p className="mb-1 text-[11px] text-steel-400">Serviço nacional não implica uso por todas as unidades.</p>
        <ul className="space-y-0.5 text-[12.5px]">
          {d.equipment.map((e: any) => (
            <li key={e.equipment.id}>
              <EntityLink type="equipment" slug={e.equipment.slug}>{e.equipment.name}</EntityLink>
              <span className="ml-1 text-[10.5px] text-steel-400">{EQUIPMENT_CATEGORIES[e.equipment.category]}</span>
            </li>
          ))}
        </ul>
      </Section>
      <DocsBlock d={d} />
    </div>
  )
}

// ------------------------------------------------------------------ armed force
export function ForcePanel({ d }: { d: any }) {
  const date = useExplorer((s) => s.date)
  return (
    <div>
      <PanelHeader title={d.name} original={d.name_original} subtitle={<>{BRANCHES[d.branch]} · <EntityLink type="polity" slug={d.polity?.slug}>{d.polity?.name}</EntityLink> · <Period t={d} /></>} />
      <Section title="Resumo">
        <Text value={d.summary ?? d.description} />
      </Section>
      <Section title="Hierarquia documentada">
        <DateNote date={date} />
        {d.tree?.length ? <div className="mt-2"><UnitTree nodes={d.tree} /></div> : <Undocumented>Nenhuma unidade subordinada documentada nesta data.</Undocumented>}
        {d.unplaced_units?.length > 0 && (
          <div className="mt-2 text-[11.5px]">
            <p className="text-steel-400">Unidades existentes sem subordinação documentada nesta data:</p>
            <ul className="ml-3 list-disc">
              {d.unplaced_units.map((u: any) => <li key={u.id}><EntityLink type="unit" slug={u.slug}>{u.name}</EntityLink></li>)}
            </ul>
          </div>
        )}
      </Section>
      <DocsBlock d={d} />
    </div>
  )
}

// ------------------------------------------------------------------ unit
export function UnitPanel({ d }: { d: any }) {
  const date = useExplorer((s) => s.date)
  const [history, setHistory] = useState(false)
  const at = d.at_date
  const currentName = at?.names?.[0]?.name
  return (
    <div>
      <PanelHeader
        title={d.name}
        original={currentName && currentName !== d.name ? `Nome na data: ${currentName}` : d.name_original}
        subtitle={
          <>
            {d.type_label ?? ECHELONS[d.echelon]}
            {d.polity && <> · <EntityLink type="polity" slug={d.polity.slug}>{d.polity.short_name ?? d.polity.name}</EntityLink></>}
            {d.force && <> · <EntityLink type="armed_force" slug={d.force.slug}>{d.force.name}</EntityLink></>}
            {d.is_multinational && ' · comando multinacional'}
          </>
        }
      >
        <CertaintyBadge value={d.certainty} />
        {d.nickname && <span className="wa-chip">“{d.nickname}”</span>}
        {date && d.existence_at_date !== 'active' && EXISTENCE[d.existence_at_date] && <Badge tone="warn">{EXISTENCE[d.existence_at_date]}</Badge>}
      </PanelHeader>

      <Section title={`Situação em ${formatDate(date)}`}>
        <DateNote date={date} />
        {at && (
          <div className="mt-2">
            <KeyValue label="Subordinação">
              {at.parents.length
                ? at.parents.map((p: any, i: number) => (
                    <span key={i} className="block">
                      <EntityLink type={p.target.type} slug={p.target.slug}>{p.target.name}</EntityLink>
                      <span className="text-[11px] text-steel-400"> · {RELATIONS[p.kind]} · <Period t={p} /></span>
                    </span>
                  ))
                : null}
            </KeyValue>
            <KeyValue label="Comandante">
              {at.commanders.length
                ? at.commanders.map((c: any, i: number) => (
                    <span key={i} className="block">
                      <EntityLink type="person" slug={c.person.slug}>{c.person.name}</EntityLink>
                      <span className="text-[11px] text-steel-400"> · {POSITION_KINDS[c.kind]} · <Period t={c} /></span>
                    </span>
                  ))
                : null}
            </KeyValue>
            <KeyValue label="Subordinadas">
              {at.children.length
                ? at.children.map((c: any, i: number) => (
                    <span key={i} className="block">
                      <EntityLink type="unit" slug={c.target.slug}>{c.target.name}</EntityLink>
                      {c.kind !== 'organic' && <span className="text-[11px] text-info"> · {RELATIONS[c.kind]}</span>}
                    </span>
                  ))
                : null}
            </KeyValue>
            <KeyValue label="Equipamentos">
              {at.equipment.length ? at.equipment.map((e: any, i: number) => <span key={i} className="block"><EntityLink type="equipment" slug={e.equipment.slug}>{e.equipment.name}</EntityLink>{e.notes && <span className="text-[11px] text-steel-400"> · {e.notes}</span>}</span>) : null}
            </KeyValue>
          </div>
        )}
      </Section>

      <Section title="Histórico e formação">
        <KeyValue label="Formação">{d.formed_on ? formatDate(d.formed_on, d.formed_precision) : null}</KeyValue>
        <KeyValue label="Dissolução">{d.disbanded_on ? formatDate(d.disbanded_on, d.disbanded_precision) : null}</KeyValue>
        <div className="mt-2">
          <Text value={d.summary ?? d.description} />
        </div>
      </Section>

      <Section title="Linha do tempo documentada (todas as datas)" defaultOpen={history} right={<button className="wa-link text-[11px]" onClick={(e) => { e.preventDefault(); setHistory(!history) }}>{history ? 'ocultar' : 'mostrar'}</button>}>
        <p className="mb-2 text-[11px] text-steel-400">Cada item vale apenas para o intervalo indicado; nada aqui é extrapolado para outras datas.</p>
        <p className="wa-label mb-1">Nomes e designações</p>
        {d.names.length ? d.names.map((n: any, i: number) => <div key={i} className="flex justify-between gap-2 text-[12.5px]"><span>{n.name} <span className="text-[10.5px] text-steel-400">{n.kind}</span></span><Period t={n} /></div>) : <Undocumented />}
        <p className="wa-label mt-3 mb-1">Subordinação</p>
        {d.subordination_history.length ? d.subordination_history.map((s: any, i: number) => (
          <div key={i} className={clsx('flex justify-between gap-2 text-[12.5px]', s.valid_at_date && 'text-brass-300')}>
            <span><EntityLink type={s.target.type} slug={s.target.slug}>{s.target.name}</EntityLink> <span className="text-[10.5px] text-steel-400">{RELATIONS[s.kind]}</span></span>
            <Period t={s} />
          </div>
        )) : <Undocumented />}
        <p className="wa-label mt-3 mb-1">Comandantes</p>
        {d.command_history.length ? d.command_history.map((c: any, i: number) => (
          <div key={i} className="flex justify-between gap-2 text-[12.5px]">
            <span><EntityLink type="person" slug={c.person.slug}>{c.person.name}</EntityLink>{c.rank_at_time && <span className="text-[10.5px] text-steel-400"> · {c.rank_at_time}</span>}</span>
            <Period t={c} />
          </div>
        )) : <Undocumented />}
        <p className="wa-label mt-3 mb-1">Unidades subordinadas</p>
        {d.subordinate_history.length ? d.subordinate_history.map((s: any, i: number) => (
          <div key={i} className="flex justify-between gap-2 text-[12.5px]">
            <EntityLink type="unit" slug={s.target.slug}>{s.target.name}</EntityLink>
            <Period t={s} />
          </div>
        )) : <Undocumented />}
        <p className="wa-label mt-3 mb-1">Equipamentos documentados</p>
        {d.equipment_history.length ? d.equipment_history.map((e: any, i: number) => (
          <div key={i} className="flex justify-between gap-2 text-[12.5px]">
            <EntityLink type="equipment" slug={e.equipment.slug}>{e.equipment.name}</EntityLink>
            <Period t={e} />
          </div>
        )) : <Undocumented>Nenhum equipamento associado especificamente a esta unidade.</Undocumented>}
      </Section>

      <Section title={`Batalhas e eventos (${d.battles.length + d.events.length})`}>
        <ul className="space-y-0.5 text-[12.5px]">
          {d.battles.map((b: any) => (
            <li key={`b${b.battle.id}`}><EntityLink type="battle" slug={b.battle.slug}>{b.battle.name}</EntityLink>{b.role && <span className="text-[11px] text-steel-400"> · {b.role}</span>}</li>
          ))}
          {d.events.map((e: any) => (
            <li key={`e${e.event.id}`}><EntityLink type="event" slug={e.event.slug}>{e.event.name}</EntityLink> <span className="font-mono text-[10.5px] text-steel-400">{formatDate(e.event.start_date)}</span></li>
          ))}
        </ul>
        {d.battles.length + d.events.length === 0 && <Undocumented />}
      </Section>
      <Section title="Uniformes e insígnias" defaultOpen={false}>
        {d.uniforms.length ? d.uniforms.map((u: any) => <p key={u.id}>{u.name}</p>) : <Undocumented>Nenhum uniforme associado especificamente a esta unidade.</Undocumented>}
      </Section>
      <DocsBlock d={d} figures />
    </div>
  )
}

// ------------------------------------------------------------------ person
export function PersonPanel({ d }: { d: any }) {
  const date = useExplorer((s) => s.date)
  const current = d.positions.filter((p: any) => p.valid_at_date)
  return (
    <div>
      <PanelHeader
        title={d.name}
        original={d.name_original}
        subtitle={
          <>
            {d.nationality && <EntityLink type="polity" slug={d.nationality.slug}>{d.nationality.short_name ?? d.nationality.name}</EntityLink>}
            <span className="font-mono"> · {formatDate(d.birth_date)} – {formatDate(d.death_date)}</span>
          </>
        }
      >
        <CertaintyBadge value={d.certainty} />
        {date && d.alive_at_date === false && <Badge tone="neutral">{d.death_date && date > d.death_date ? 'Falecido nesta data' : 'Ainda não nascido'}</Badge>}
      </PanelHeader>
      <Section title={`Funções em ${formatDate(date)}`}>
        {current.length ? (
          current.map((p: any, i: number) => (
            <div key={i} className="text-[12.5px]">
              <span className="text-parchment">{p.title}</span>
              {p.unit && <> — <EntityLink type="unit" slug={p.unit.slug}>{p.unit.name}</EntityLink></>}
              <span className="block text-[11px] text-steel-400">{p.rank_at_time} · <Period t={p} /></span>
            </div>
          ))
        ) : (
          <Undocumented>Nenhuma função documentada nesta data.</Undocumented>
        )}
      </Section>
      <Section title="Trajetória">
        <Text value={d.summary} />
        {d.biography && <Text value={d.biography} />}
      </Section>
      <Section title={`Postos e funções exercidas (${d.positions.length})`}>
        {d.positions.length ? (
          <ul className="space-y-1.5">
            {d.positions.map((p: any, i: number) => (
              <li key={i} className={clsx('text-[12.5px]', p.valid_at_date && 'border-l-2 border-brass-500 pl-2')}>
                <span className="text-parchment">{p.title}</span>
                {p.unit && <> — <EntityLink type="unit" slug={p.unit.slug}>{p.unit.name}</EntityLink></>}
                {p.force && !p.unit && <> — <EntityLink type="armed_force" slug={p.force.slug}>{p.force.name}</EntityLink></>}
                <span className="block text-[11px] text-steel-400">{p.rank_at_time ? `${p.rank_at_time} · ` : ''}<Period t={p} /></span>
                {p.notes && <span className="block text-[11px] text-steel-400 italic">{p.notes}</span>}
              </li>
            ))}
          </ul>
        ) : (
          <Undocumented />
        )}
        {d.ranks.length > 0 && (
          <>
            <p className="wa-label mt-3 mb-1">Postos</p>
            {d.ranks.map((r: any, i: number) => <div key={i} className="flex justify-between text-[12.5px]"><span>{r.rank}</span><Period t={r} /></div>)}
          </>
        )}
      </Section>
      <Section title={`Batalhas (${d.battles.length})`}>
        {d.battles.length ? (
          <ul className="space-y-0.5 text-[12.5px]">
            {d.battles.map((b: any) => (
              <li key={b.battle.id}><EntityLink type="battle" slug={b.battle.slug}>{b.battle.name}</EntityLink>{b.role && <span className="text-[11px] text-steel-400"> · {b.role}</span>}</li>
            ))}
          </ul>
        ) : (
          <Undocumented />
        )}
      </Section>
      {d.events.length > 0 && (
        <Section title="Eventos">
          <ul className="space-y-0.5 text-[12.5px]">
            {d.events.map((e: any) => <li key={e.event.id}><EntityLink type="event" slug={e.event.slug}>{e.event.name}</EntityLink> <span className="font-mono text-[10.5px] text-steel-400">{formatDate(e.event.start_date)}</span></li>)}
          </ul>
        </Section>
      )}
      <Section title="Decisões estratégicas documentadas" defaultOpen={false}>
        <Undocumented>Ainda não modeladas como registros próprios (planejado para fases futuras); veja eventos e fontes.</Undocumented>
      </Section>
      <DocsBlock d={d} />
    </div>
  )
}
