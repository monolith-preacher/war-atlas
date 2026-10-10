/* eslint-disable @typescript-eslint/no-explicit-any */
import clsx from 'clsx'
import { ExternalLink } from 'lucide-react'
import { formatDate } from '../../lib/dates'
import { ECHELONS, EQUIPMENT_CATEGORIES, SOURCE_KINDS, entityLabel } from '../../lib/labels'
import { useExplorer } from '../../store/explorer'
import { Citations, EntityLink, MediaGallery, Provenance } from '../common/docs'
import { CertaintyBadge, KeyValue, Period, Section, Undocumented } from '../common/ui'
import { PanelHeader, Text } from './HistoryPanels'

export function EquipmentPanel({ d }: { d: any }) {
  const date = useExplorer((s) => s.date)
  return (
    <div>
      <PanelHeader
        title={d.name}
        original={d.name_original}
        subtitle={
          <>
            {EQUIPMENT_CATEGORIES[d.category]}
            {d.type_label && ` · ${d.type_label}`}
            {d.origin && <> · <EntityLink type="polity" slug={d.origin.slug}>{d.origin.name}</EntityLink></>}
          </>
        }
      >
        <CertaintyBadge value={d.certainty} />
      </PanelHeader>
      <Section title="Identificação">
        <KeyValue label="Fabricante">{d.manufacturer}</KeyValue>
        <KeyValue label="Projetista">{d.designer}</KeyValue>
        <KeyValue label="Projeto">{d.design_period}</KeyValue>
        <KeyValue label="Produção">{d.production_period}</KeyValue>
        <KeyValue label="Unidades produzidas">{d.number_built}</KeyValue>
        <KeyValue label="Em serviço">{d.valid_from || d.valid_to ? <Period t={d} /> : null}</KeyValue>
      </Section>
      <Section title="Descrição e histórico operacional">
        <Text value={d.summary} />
        {d.description && <Text value={d.description} />}
        {d.operational_history && <Text value={d.operational_history} />}
      </Section>
      <Section title="Características técnicas">
        {d.specs.length ? (
          <table className="w-full text-[12.5px]">
            <tbody>
              {d.specs.map((s: any) => (
                <tr key={s.key} className="border-t border-ink-700/70">
                  <td className="w-[42%] py-1 pr-2 text-steel-400">{s.label}</td>
                  <td className="py-1 text-steel-200">
                    {s.value} {s.unit && <span className="text-steel-400">{s.unit}</span>}
                    {s.note && <span className="block text-[11px] text-steel-400">{s.note}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Undocumented>Especificações ainda não transcritas de fontes.</Undocumented>
        )}
        {d.specs.length > 0 && <p className="mt-1.5 text-[11px] text-steel-400">Valores transcritos das fontes citadas; campos ausentes não foram estimados.</p>}
      </Section>
      {d.variants.length > 0 && (
        <Section title="Variantes">
          {d.variants.map((v: any) => (
            <p key={v.slug} className="text-[12.5px]"><b>{v.name}</b> — {v.summary}</p>
          ))}
        </Section>
      )}
      <Section title={`Países usuários (${d.users.length})`}>
        {d.users.length ? (
          <ul className="space-y-0.5 text-[12.5px]">
            {d.users.map((u: any, i: number) => (
              <li key={i} className={clsx('flex justify-between gap-2', date && !u.valid_at_date && 'opacity-50')}>
                <EntityLink type="polity" slug={u.polity.slug}>{u.polity.short_name ?? u.polity.name}</EntityLink>
                <Period t={u} />
              </li>
            ))}
          </ul>
        ) : (
          <Undocumented />
        )}
      </Section>
      <Section title={`Unidades com uso documentado (${d.units.length})`}>
        <p className="mb-1.5 text-[11px] text-steel-400">Apenas associações explícitas e documentadas; o serviço nacional não implica uso por todas as unidades do país.</p>
        {d.units.length ? (
          <ul className="space-y-1 text-[12.5px]">
            {d.units.map((u: any, i: number) => (
              <li key={i} className={clsx(date && !u.valid_at_date && 'opacity-60')}>
                <EntityLink type="unit" slug={u.unit.slug}>{u.unit.name}</EntityLink>
                <span className="block text-[11px] text-steel-400">
                  {u.unit.polity} · {ECHELONS[u.unit.echelon]} · <Period t={u} />
                  {u.notes && ` · ${u.notes}`}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <Undocumented>Nenhuma unidade associada ainda.</Undocumented>
        )}
      </Section>
      <Section title="Esquemas de pintura e camuflagens" defaultOpen={false}>
        {d.camouflages.length ? d.camouflages.map((c: any, i: number) => <p key={i}>{c.pattern.name}</p>) : <Undocumented>Nenhum esquema documentado cadastrado.</Undocumented>}
      </Section>
      <Section title="Fotografias e ilustrações" defaultOpen={false}>
        <MediaGallery items={d.media} />
      </Section>
      <Section title={`Fontes (${d.citations.length})`}>
        <Provenance d={d} />
        <div className="mt-2">
          <Citations items={d.citations} />
        </div>
      </Section>
    </div>
  )
}

export function SourcePanel({ d }: { d: any }) {
  return (
    <div>
      <PanelHeader title={d.title} subtitle={[d.authors, d.year].filter(Boolean).join(' · ')}>
        <span className="wa-chip">{SOURCE_KINDS[d.kind] ?? d.kind}</span>
        {d.url && (
          <a href={d.url} target="_blank" rel="noreferrer noopener" className="wa-btn">
            Abrir <ExternalLink size={12} />
          </a>
        )}
      </PanelHeader>
      <Section title="Referência">
        <KeyValue label="Autoria">{d.authors}</KeyValue>
        <KeyValue label="Série">{d.series}</KeyValue>
        <KeyValue label="Editora">{d.publisher}</KeyValue>
        <KeyValue label="Local">{d.place}</KeyValue>
        <KeyValue label="Ano">{d.year}</KeyValue>
        <KeyValue label="ISBN">{d.isbn}</KeyValue>
        <KeyValue label="Licença">{d.license}</KeyValue>
        <KeyValue label="Acesso">{d.accessed_on ? formatDate(d.accessed_on) : null}</KeyValue>
        {d.reliability_note && <p className="mt-2 text-[12px] text-steel-300 italic">{d.reliability_note}</p>}
      </Section>
      <Section title={`Registros que citam esta fonte (${d.cited_by.length})`}>
        <ul className="space-y-0.5 text-[12.5px]">
          {d.cited_by.map((c: any, i: number) => (
            <li key={i}>
              <span className="text-[10.5px] text-steel-400 uppercase">{entityLabel(c.entity.type)}</span>{' '}
              <EntityLink type={c.entity.type} slug={c.entity.slug}>{c.entity.name}</EntityLink>
              {c.pages && <span className="text-steel-400">, p. {c.pages}</span>}
            </li>
          ))}
        </ul>
      </Section>
    </div>
  )
}
