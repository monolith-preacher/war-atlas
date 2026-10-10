/* eslint-disable @typescript-eslint/no-explicit-any */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, EmptyState, ErrorState, Loading } from '../../components/common/ui'
import { api, ApiError } from '../../lib/api'
import { useAuth } from '../../store/auth'
import { isReviewer } from './adminApi'

export function ReviewQueue() {
  const q = useQuery({ queryKey: ['review-queue'], queryFn: () => api.get<any[]>('/admin/review-queue') })
  return (
    <div className="p-6">
      <h1 className="wa-heading text-2xl">Fila de revisão</h1>
      <p className="text-[13px] text-steel-400">Registros enviados para revisão por editores. Revisores verificam fontes e publicam.</p>
      {q.isLoading && <Loading />}
      {q.isError && <ErrorState error={q.error} />}
      {q.data?.length === 0 && <EmptyState title="Nada aguardando revisão" />}
      <ul className="mt-4 space-y-2">
        {q.data?.map((i) => (
          <li key={`${i.entity}-${i.id}`} className="wa-panel flex items-center justify-between rounded-md px-3 py-2">
            <span>
              <span className="wa-chip mr-2">{i.entity}</span>
              <Link className="wa-link" to={`/admin/e/${i.entity}/${i.id}`}>{i.title}</Link>
              {i.review_note && <span className="ml-2 text-[12px] text-steel-400 italic">{i.review_note}</span>}
            </span>
            <span className="font-mono text-[11px] text-steel-400">{i.updated_at.slice(0, 16).replace('T', ' ')}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

const IMPORT_TYPES = ['person', 'battle', 'campaign', 'unit', 'polity', 'place', 'equipment', 'conflict']

export function ImportsPage() {
  const qc = useQueryClient()
  const role = useAuth((s) => s.user?.role)
  const [qid, setQid] = useState('')
  const [type, setType] = useState('person')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [batchType, setBatchType] = useState('place')
  const [batchSource, setBatchSource] = useState('')
  const [batchJson, setBatchJson] = useState('')
  const [overrides, setOverrides] = useState<Record<number, string>>({})
  const list = useQuery({ queryKey: ['imports'], queryFn: () => api.get<any[]>('/admin/imports/records', { status: 'pending' }) })
  const refresh = () => qc.invalidateQueries({ queryKey: ['imports'] })

  const importWikidata = async (e: React.FormEvent) => {
    e.preventDefault()
    setMsg(null)
    try {
      await api.post('/admin/imports/wikidata', { qid, entity_type: type })
      setMsg({ ok: true, text: `${qid} colocado em preparação.` })
      setQid('')
      refresh()
    } catch (err) {
      setMsg({ ok: false, text: err instanceof ApiError ? `${err.message} ${err.details ? String(err.details) : ''}` : 'Falha.' })
    }
  }

  const importBatch = async (e: React.FormEvent) => {
    e.preventDefault()
    setMsg(null)
    let records: unknown
    try {
      records = JSON.parse(batchJson)
    } catch {
      setMsg({ ok: false, text: 'JSON inválido.' })
      return
    }
    try {
      const r: any = await api.post('/admin/imports/batch', { entity_type: batchType, source_name: batchSource, records })
      setMsg({ ok: true, text: `Lote #${r.batch_id}: ${r.records} registros em preparação.` })
      setBatchJson('')
      refresh()
    } catch (err) {
      setMsg({ ok: false, text: err instanceof ApiError ? err.message : 'Falha.' })
    }
  }

  const decide = async (id: number, action: 'approve' | 'reject') => {
    setMsg(null)
    let ov = {}
    if (overrides[id]) {
      try { ov = JSON.parse(overrides[id]) } catch { setMsg({ ok: false, text: 'Campos complementares: JSON inválido.' }); return }
    }
    try {
      const r: any = await api.post(`/admin/imports/records/${id}/${action}`, { overrides: ov })
      setMsg({ ok: true, text: action === 'approve' ? `Criado como rascunho: ${r.entity} #${r.id}.` : 'Rejeitado.' })
      refresh()
    } catch (err) {
      if (err instanceof ApiError && Array.isArray(err.details)) setMsg({ ok: false, text: `${err.message} ${(err.details as any[]).map((d) => `${d.field}: ${d.message}`).join('; ')}` })
      else setMsg({ ok: false, text: err instanceof ApiError ? err.message : 'Falha.' })
    }
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="wa-heading text-2xl">Importações (área de preparação)</h1>
        <p className="text-[13px] text-steel-400">
          Dados externos nunca entram diretamente no acervo: ficam em preparação, são revisados e, se aprovados, viram rascunhos sujeitos ao fluxo normal de publicação.
        </p>
      </div>
      {msg && <p className={`text-[13px] ${msg.ok ? 'text-ok' : 'text-alert'}`} role="status">{msg.text}</p>}
      <div className="grid gap-4 lg:grid-cols-2">
        <form onSubmit={importWikidata} className="wa-panel space-y-2 rounded-md p-4">
          <p className="wa-heading">Wikidata (CC0)</p>
          <div className="flex gap-2">
            <input className="wa-input" placeholder="QID, ex.: Q132568" value={qid} onChange={(e) => setQid(e.target.value)} pattern="[Qq]\d+" required />
            <select className="wa-input w-auto" value={type} onChange={(e) => setType(e.target.value)}>
              {IMPORT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <button className="wa-btn wa-btn-primary">Buscar</button>
          </div>
          <p className="text-[11.5px] text-steel-400">Mapeia rótulo, datas (somente com precisão de dia) e coordenadas. Datas de precisão menor geram avisos.</p>
        </form>
        <form onSubmit={importBatch} className="wa-panel space-y-2 rounded-md p-4">
          <p className="wa-heading">Lote JSON</p>
          <div className="flex gap-2">
            <select className="wa-input w-auto" value={batchType} onChange={(e) => setBatchType(e.target.value)}>
              {IMPORT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input className="wa-input" placeholder="Nome da origem (ex.: planilha-cmh)" value={batchSource} onChange={(e) => setBatchSource(e.target.value)} required minLength={2} />
          </div>
          <textarea className="wa-input min-h-24 font-mono text-[11.5px]" placeholder='[{"external_id": "x1", "name": "...", "geom": [2.35, 48.85]}]' value={batchJson} onChange={(e) => setBatchJson(e.target.value)} required />
          <button className="wa-btn wa-btn-primary">Enviar para preparação</button>
        </form>
      </div>
      <div>
        <p className="wa-label mb-2">Pendentes ({list.data?.length ?? 0})</p>
        {list.isLoading && <Loading />}
        {list.data?.length === 0 && <EmptyState title="Nenhum registro pendente" />}
        <div className="space-y-3">
          {list.data?.map((r) => (
            <div key={r.id} className="wa-panel rounded-md p-3 text-[12.5px]">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="warn">pendente</Badge>
                <span className="wa-chip">{r.entity_type}</span>
                <b className="text-parchment">{r.proposed?.name ?? r.external_id}</b>
                {r.external_url ? <a className="wa-link" href={r.external_url} target="_blank" rel="noreferrer">{r.external_id}</a> : <span>{r.external_id}</span>}
                <span className="text-steel-400">· {r.external_source} · licença {r.license ?? 'não informada'}</span>
              </div>
              <pre className="mt-2 max-h-40 overflow-auto rounded bg-ink-950 p-2 text-[11px] text-steel-300">{JSON.stringify(r.proposed, null, 1)}</pre>
              {r.warnings?.length > 0 && (
                <ul className="mt-1 list-disc pl-5 text-[11.5px] text-warn">
                  {r.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
                </ul>
              )}
              {isReviewer(role) ? (
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <input
                    className="wa-input max-w-md font-mono text-[11.5px]"
                    placeholder='Campos complementares obrigatórios, ex.: {"conflict_id": 2}'
                    value={overrides[r.id] ?? ''}
                    onChange={(e) => setOverrides({ ...overrides, [r.id]: e.target.value })}
                  />
                  <button className="wa-btn wa-btn-primary" onClick={() => decide(r.id, 'approve')}>Aprovar como rascunho</button>
                  <button className="wa-btn" onClick={() => decide(r.id, 'reject')}>Rejeitar</button>
                </div>
              ) : (
                <p className="mt-2 text-[11.5px] text-steel-400">Aguardando um revisor.</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export function RevisionsPage() {
  const q = useQuery({ queryKey: ['revisions-all'], queryFn: () => api.get<any[]>('/admin/revisions', { limit: 200 }) })
  return (
    <div className="p-6">
      <h1 className="wa-heading text-2xl">Histórico de alterações</h1>
      {q.isLoading && <Loading />}
      {q.data?.length === 0 && <EmptyState title="Nenhuma alteração registrada ainda">Os dados iniciais são carregados por script e não geram revisões.</EmptyState>}
      <table className="mt-4 w-full text-[12.5px]">
        <tbody>
          {q.data?.map((r) => (
            <tr key={r.id} className="border-t border-ink-700 align-top">
              <td className="py-1.5 pr-3 font-mono text-[11px] whitespace-nowrap text-steel-400">{r.created_at.slice(0, 19).replace('T', ' ')}</td>
              <td className="pr-3">{r.user ?? '—'}</td>
              <td className="pr-3"><span className="wa-chip">{r.action}</span></td>
              <td className="pr-3"><Link className="wa-link" to={`/admin/e/${r.entity_type}/${r.entity_id}`}>{r.entity_type} #{r.entity_id}</Link></td>
              <td className="text-steel-400">
                {r.comment && <i>{r.comment} · </i>}
                <span className="font-mono text-[11px]">{r.changes ? Object.keys(r.changes).join(', ') : ''}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function IntegrityPage() {
  const q = useQuery({ queryKey: ['integrity'], queryFn: () => api.get<Record<string, { id: number; slug: string }[]>>('/admin/integrity/report') })
  return (
    <div className="p-6">
      <h1 className="wa-heading text-2xl">Verificações de integridade</h1>
      <p className="text-[13px] text-steel-400">Registros publicados sem fonte e unidades sem nenhuma subordinação documentada.</p>
      {q.isLoading && <Loading />}
      {q.isError && <ErrorState error={q.error} />}
      {q.data && Object.keys(q.data).every((k) => q.data![k].length === 0) && <EmptyState title="Nenhum problema encontrado" />}
      {q.data &&
        Object.entries(q.data).map(([k, rows]) =>
          rows.length ? (
            <div key={k} className="mt-4">
              <p className="wa-label mb-1">{k.replace(/_/g, ' ')} ({rows.length})</p>
              <ul className="ml-4 list-disc text-[12.5px]">
                {rows.map((r) => {
                  const ent = k.startsWith('units') ? 'unit' : k.split('_published')[0]
                  return <li key={r.id}><Link className="wa-link" to={`/admin/e/${ent}/${r.id}`}>{r.slug}</Link></li>
                })}
              </ul>
            </div>
          ) : null,
        )}
    </div>
  )
}
