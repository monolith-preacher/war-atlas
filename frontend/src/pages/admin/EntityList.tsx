import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Badge, CertaintyBadge, ErrorState, Loading } from '../../components/common/ui'
import { api } from '../../lib/api'
import { STATUS_LABELS, STATUS_TONES, useEntityMeta } from './adminApi'

interface ListResponse {
  total: number
  page: number
  page_size: number
  items: { id: number; title: string; slug: string | null; status: string | null; certainty: string | null; updated_at: string | null }[]
}

export function EntityList() {
  const { entity } = useParams()
  const [params] = useSearchParams()
  const { entity: meta } = useEntityMeta(entity)
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const filterField = params.get('filter_field') ?? undefined
  const filterValue = params.get('filter_value') ?? undefined
  const list = useQuery({
    queryKey: ['admin-list', entity, q, status, page, filterField, filterValue],
    queryFn: () => api.get<ListResponse>(`/admin/${entity}`, { q, status, page, page_size: 50, filter_field: filterField, filter_value: filterValue }),
    placeholderData: keepPreviousData,
  })
  if (!meta) return <Loading />
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1
  return (
    <div className="p-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="wa-heading text-2xl">{meta.label_plural}</h1>
        <span className="font-mono text-[12px] text-steel-400">{list.data?.total ?? '…'} registros</span>
        <Link to={`/admin/e/${entity}/novo${params.toString() ? `?${params}` : ''}`} className="wa-btn wa-btn-primary ml-auto">
          <Plus size={14} /> Novo
        </Link>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <input className="wa-input max-w-sm" placeholder="Filtrar por nome…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} />
        {meta.has_status && (
          <select className="wa-input w-auto" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
            <option value="">Todos os status</option>
            {Object.entries(STATUS_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        )}
        {filterField && <span className="wa-chip">filtro: {filterField} = {filterValue}</span>}
      </div>
      {list.isError && <ErrorState error={list.error} />}
      {list.isLoading && <Loading />}
      {list.data && (
        <table className="mt-4 w-full text-[13px]">
          <thead>
            <tr className="text-left text-[11px] text-steel-400 uppercase">
              <th className="py-2">Registro</th>
              <th>Status</th>
              <th>Certeza</th>
              <th className="text-right">Atualizado</th>
            </tr>
          </thead>
          <tbody>
            {list.data.items.map((r) => (
              <tr key={r.id} className="border-t border-ink-700 hover:bg-ink-850">
                <td className="py-2">
                  <Link className="wa-link" to={`/admin/e/${entity}/${r.id}`}>{r.title}</Link>
                  {r.slug && <span className="ml-2 font-mono text-[11px] text-steel-400">{r.slug}</span>}
                </td>
                <td>{r.status && <Badge tone={STATUS_TONES[r.status]}>{STATUS_LABELS[r.status]}</Badge>}</td>
                <td><CertaintyBadge value={r.certainty} /></td>
                <td className="text-right font-mono text-[11px] text-steel-400">{r.updated_at?.slice(0, 16).replace('T', ' ')}</td>
              </tr>
            ))}
            {list.data.items.length === 0 && (
              <tr><td colSpan={4} className="py-6 text-center text-steel-400">Nenhum registro.</td></tr>
            )}
          </tbody>
        </table>
      )}
      {pages > 1 && (
        <div className="mt-3 flex items-center gap-2 text-[12px]">
          <button className="wa-btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</button>
          <span>{page} / {pages}</span>
          <button className="wa-btn" disabled={page >= pages} onClick={() => setPage(page + 1)}>Próxima</button>
        </div>
      )}
    </div>
  )
}
