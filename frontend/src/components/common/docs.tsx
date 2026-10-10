/** Provenance components: entity links, citations, quantitative figures, media. */
import { BookOpen, ExternalLink, MapPin } from 'lucide-react'
import type { ReactNode } from 'react'
import { formatDate } from '../../lib/dates'
import { METRICS, SOURCE_KINDS } from '../../lib/labels'
import type { Citation, EntityType, Figure, MediaItem, Source } from '../../lib/types'
import { useExplorer } from '../../store/explorer'
import { CertaintyBadge, EmptyState, Undocumented } from './ui'

const SELECTABLE = new Set(['conflict', 'theater', 'campaign', 'battle', 'event', 'place', 'polity', 'unit', 'person', 'equipment', 'armed_force', 'source', 'map_feature'])

export function EntityLink({ type, slug, children, location, zoom }: { type: EntityType | string; slug?: string | null; children: ReactNode; location?: [number, number] | null; zoom?: number }) {
  const select = useExplorer((s) => s.select)
  const fly = useExplorer((s) => s.fly)
  if (!slug || !SELECTABLE.has(type)) return <span>{children}</span>
  return (
    <span className="inline-flex items-center gap-1">
      <button className="wa-link text-left" onClick={() => select({ type: type as EntityType, slug })}>
        {children}
      </button>
      {location && (
        <button className="text-steel-400 hover:text-brass-400" title="Centralizar no mapa" onClick={() => fly(location, zoom)}>
          <MapPin size={12} />
        </button>
      )}
    </span>
  )
}

export function sourceLabel(s: Source): string {
  const parts = [s.authors, s.title, s.series, s.publisher, s.place, s.year].filter(Boolean)
  return parts.join('. ')
}

export function SourceLine({ s, pages }: { s: Source; pages?: string | null }) {
  return (
    <span>
      {s.authors && <span className="text-steel-200">{s.authors}. </span>}
      <EntityLink type="source" slug={s.slug}>
        <em>{s.title}</em>
      </EntityLink>
      {s.series && <span className="text-steel-400">. {s.series}</span>}
      {(s.publisher || s.year) && <span className="text-steel-400">. {[s.place, s.publisher, s.year].filter(Boolean).join(', ')}</span>}
      {pages && <span className="text-steel-300">, p. {pages}</span>}
      {s.accessed_on && <span className="text-steel-400"> (acesso em {formatDate(s.accessed_on)})</span>}
      {s.url && (
        <a href={s.url} target="_blank" rel="noreferrer noopener" className="ml-1 inline-flex align-middle text-steel-400 hover:text-brass-400" title="Abrir fonte">
          <ExternalLink size={11} />
        </a>
      )}
      <span className="ml-1 text-[10.5px] text-steel-400 uppercase">[{SOURCE_KINDS[s.kind] ?? s.kind}]</span>
    </span>
  )
}

export function Citations({ items }: { items: Citation[] }) {
  if (!items?.length)
    return (
      <EmptyState title="Sem fonte associada">
        Este registro ainda não possui citação. Trate o conteúdo como não verificado.
      </EmptyState>
    )
  // group by source, keep field-specific notes
  const bySource = new Map<string, { s: Source; notes: Citation[] }>()
  for (const c of items) {
    const g = bySource.get(c.source.slug) ?? { s: c.source, notes: [] }
    g.notes.push(c)
    bySource.set(c.source.slug, g)
  }
  return (
    <ol className="space-y-2 text-[12.5px] leading-snug">
      {[...bySource.values()].map(({ s, notes }) => (
        <li key={s.slug} className="flex gap-2">
          <BookOpen size={13} className="mt-0.5 shrink-0 text-brass-600" />
          <div>
            <SourceLine s={s} pages={notes.find((n) => n.pages)?.pages} />
            {notes.some((n) => n.field || n.note) && (
              <ul className="mt-0.5 space-y-0.5 text-[11.5px] text-steel-400">
                {notes.filter((n) => n.field || n.note).map((n, i) => (
                  <li key={i}>
                    {n.field && <span className="font-mono text-steel-300">{n.field}</span>} {n.note}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </li>
      ))}
    </ol>
  )
}

function fmtNumber(n: number) {
  return n.toLocaleString('pt-BR')
}

export function figureValue(f: Figure): string {
  if (f.value_text) return f.value_text
  if (f.value_low != null && f.value_high != null && f.value_low !== f.value_high) return `${fmtNumber(f.value_low)}–${fmtNumber(f.value_high)}`
  if (f.value_low != null) return fmtNumber(f.value_low)
  if (f.value_high != null) return `até ${fmtNumber(f.value_high)}`
  return '—'
}

/** Quantitative claims grouped by metric; divergent figures are shown side by side with their sources. */
export function Figures({ items, sideNames }: { items?: Figure[]; sideNames?: Record<string, string> }) {
  if (!items?.length) return <Undocumented>Nenhum número documentado no acervo atual.</Undocumented>
  const groups = new Map<string, Figure[]>()
  for (const f of items) {
    const key = f.metric
    groups.set(key, [...(groups.get(key) ?? []), f])
  }
  return (
    <div className="space-y-3">
      {[...groups.entries()].map(([metric, figs]) => {
        const disputed = figs.some((f) => f.certainty === 'disputed')
        return (
          <div key={metric}>
            <div className="mb-1 flex items-center gap-2">
              <span className="text-[12px] font-semibold text-parchment">{METRICS[metric] ?? metric}</span>
              {disputed && <CertaintyBadge value="disputed" />}
            </div>
            <table className="w-full text-[12px]">
              <tbody>
                {figs.map((f) => (
                  <tr key={f.id} className="border-t border-ink-700/70 align-top">
                    <td className="w-[38%] py-1 pr-2 text-steel-300">
                      {f.polity?.name ?? (f.side ? sideNames?.[f.side] ?? `Lado ${f.side.toUpperCase()}` : 'Total')}
                      {f.scope_note && <div className="text-[11px] text-steel-400">{f.scope_note}</div>}
                    </td>
                    <td className="py-1 pr-2 font-mono text-parchment">{figureValue(f)}</td>
                    <td className="py-1 text-[11px] text-steel-400">
                      {f.source ? <SourceLine s={f.source} pages={f.pages} /> : <span className="text-alert">sem fonte</span>}
                      {f.notes && <div className="mt-0.5 italic">{f.notes}</div>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      })}
    </div>
  )
}

export function MediaGallery({ items }: { items?: MediaItem[] }) {
  if (!items?.length)
    return <Undocumented>Nenhuma imagem com licença verificada cadastrada. Imagens só são exibidas com autoria, licença e procedência registradas.</Undocumented>
  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map((m) => (
        <figure key={m.id} className="overflow-hidden rounded border border-ink-700">
          <img src={m.thumbnail_url ?? m.file_url} alt={m.title} className="aspect-video w-full object-cover" loading="lazy" />
          <figcaption className="p-1.5 text-[10.5px] text-steel-400">
            {m.caption ?? m.title}
            <div>
              {m.author} · {m.license}
            </div>
          </figcaption>
        </figure>
      ))}
    </div>
  )
}

export function Provenance({ d }: { d: { certainty?: string; provenance_note?: string | null; wikidata_id?: string | null } }) {
  if (!d.certainty && !d.provenance_note && !d.wikidata_id) return null
  return (
    <div className="space-y-1.5 text-[12px]">
      <div className="flex flex-wrap items-center gap-2">
        <CertaintyBadge value={d.certainty} />
        {d.wikidata_id && (
          <a className="wa-chip hover:border-brass-600" href={`https://www.wikidata.org/wiki/${d.wikidata_id}`} target="_blank" rel="noreferrer noopener">
            Wikidata {d.wikidata_id} <ExternalLink size={10} />
          </a>
        )}
      </div>
      {d.provenance_note && <p className="text-steel-400 italic">{d.provenance_note}</p>}
    </div>
  )
}
