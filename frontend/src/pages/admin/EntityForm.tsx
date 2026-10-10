/* eslint-disable @typescript-eslint/no-explicit-any */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Save, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Badge, ErrorState, Loading } from '../../components/common/ui'
import { api, ApiError } from '../../lib/api'
import { useAuth } from '../../store/auth'
import { type FieldMeta, isReviewer, STATUS_LABELS, STATUS_TONES, useEntityMeta } from './adminApi'

interface RecordResponse {
  entity: string
  title: string
  values: Record<string, any>
  ref_titles: Record<string, string | null>
  related: { entity: string; field: string; items: { id: number; title: string }[] }[]
  citations: { id: number; source: { id: number; title: string; slug: string }; field: string | null; pages: string | null; note: string | null }[]
  figures: any[]
}

const READONLY = new Set(['id', 'created_at', 'updated_at', 'reviewed_at', 'status'])

function RefSelect({ field, value, title, onChange }: { field: FieldMeta; value: any; title?: string | null; onChange: (v: number | null, title?: string) => void }) {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const box = useRef<HTMLDivElement>(null)
  const results = useQuery({
    queryKey: ['lookup', field.ref, q],
    queryFn: () => api.get<{ id: number; title: string; status: string | null }[]>(`/admin/lookup/${field.ref}`, { q }),
    enabled: open && !!field.ref,
  })
  useEffect(() => {
    const h = (e: MouseEvent) => box.current && !box.current.contains(e.target as Node) && setOpen(false)
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])
  return (
    <div ref={box} className="relative">
      <div className="flex gap-1">
        <input
          className="wa-input"
          value={open ? q : value ? `${title ?? ''} (#${value})` : ''}
          placeholder={`Buscar ${field.ref ?? ''}…`}
          onFocus={() => { setOpen(true); setQ('') }}
          onChange={(e) => setQ(e.target.value)}
        />
        {value && (
          <button type="button" className="wa-btn" onClick={() => onChange(null)} title="Limpar">×</button>
        )}
      </div>
      {open && (
        <div className="wa-panel absolute z-20 mt-1 max-h-60 w-full overflow-y-auto rounded-md">
          {results.isLoading && <p className="p-2 text-[12px] text-steel-400">Buscando…</p>}
          {results.data?.map((r) => (
            <button
              type="button"
              key={r.id}
              className="block w-full px-2 py-1.5 text-left text-[12.5px] hover:bg-ink-700"
              onClick={() => { onChange(r.id, r.title); setOpen(false) }}
            >
              {r.title} <span className="text-[11px] text-steel-400">#{r.id}{r.status ? ` · ${STATUS_LABELS[r.status] ?? r.status}` : ''}</span>
            </button>
          ))}
          {results.data?.length === 0 && <p className="p-2 text-[12px] text-steel-400">Nada encontrado.</p>}
        </div>
      )}
    </div>
  )
}

function FieldInput({ f, value, title, onChange }: { f: FieldMeta; value: any; title?: string | null; onChange: (v: any, title?: string) => void }) {
  const [text, setText] = useState(() => (f.type === 'json' || f.type === 'geometry') && value != null ? JSON.stringify(value, null, 1) : '')
  const [parseError, setParseError] = useState<string | null>(null)
  switch (f.type) {
    case 'textarea':
      return <textarea className="wa-input min-h-24" value={value ?? ''} onChange={(e) => onChange(e.target.value)} />
    case 'date':
      return <input type="date" className="wa-input w-auto font-mono" value={value ?? ''} onChange={(e) => onChange(e.target.value || null)} />
    case 'int':
    case 'float':
      return <input type="number" step={f.type === 'float' ? 'any' : 1} className="wa-input w-40" value={value ?? ''} onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))} />
    case 'bool':
      return <input type="checkbox" checked={!!value} onChange={(e) => onChange(e.target.checked)} />
    case 'enum':
      return (
        <select className="wa-input w-auto" value={value ?? ''} onChange={(e) => onChange(e.target.value || null)}>
          <option value="">—</option>
          {f.options?.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      )
    case 'ref':
      return <RefSelect field={f} value={value} title={title} onChange={onChange} />
    case 'json':
    case 'geometry':
      return (
        <div>
          <textarea
            className="wa-input min-h-20 font-mono text-[11.5px]"
            value={text}
            placeholder={f.type === 'geometry' ? '[longitude, latitude]  ou  {"type": "LineString", "coordinates": [...]}' : '[ ... ]'}
            onChange={(e) => {
              setText(e.target.value)
              if (!e.target.value.trim()) { setParseError(null); onChange(null); return }
              try { onChange(JSON.parse(e.target.value)); setParseError(null) } catch { setParseError('JSON inválido') }
            }}
          />
          {parseError && <p className="text-[11px] text-alert">{parseError}</p>}
          {f.type === 'geometry' && <p className="text-[11px] text-steel-400">Tipo esperado: {f.geometry_type ?? 'qualquer'} · SRID 4326 (WGS84). Declare o significado da geometria no campo correspondente.</p>}
        </div>
      )
    default:
      return <input className="wa-input" value={value ?? ''} onChange={(e) => onChange(e.target.value)} />
  }
}

export function EntityForm() {
  const { entity, id } = useParams()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const role = useAuth((s) => s.user?.role)
  const { entity: meta } = useEntityMeta(entity)
  const isNew = !id
  const record = useQuery({ queryKey: ['admin-record', entity, id], queryFn: () => api.get<RecordResponse>(`/admin/${entity}/${id}`), enabled: !isNew })
  const [values, setValues] = useState<Record<string, any>>({})
  const [titles, setTitles] = useState<Record<string, string | null>>({})
  const [dirty, setDirty] = useState<Set<string>>(new Set())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [message, setMessage] = useState<{ tone: string; text: string } | null>(null)
  const [duplicates, setDuplicates] = useState<any[] | null>(null)
  const [comment, setComment] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (record.data) {
      setValues(record.data.values)
      setTitles(record.data.ref_titles)
      setDirty(new Set())
    } else if (isNew) {
      const init: Record<string, any> = {}
      params.forEach((v, k) => {
        if (k !== 'filter_field' && k !== 'filter_value') init[k] = /^\d+$/.test(v) && k.endsWith('_id') ? Number(v) : v
      })
      const ff = params.get('filter_field'), fv = params.get('filter_value')
      if (ff && fv) init[ff] = Number(fv)
      setValues(init)
      setDirty(new Set(Object.keys(init)))
    }
  }, [record.data, isNew]) // eslint-disable-line react-hooks/exhaustive-deps

  const fields = useMemo(() => (meta?.fields ?? []).filter((f) => !READONLY.has(f.name)), [meta])
  if (!meta) return <Loading />
  if (!isNew && record.isLoading) return <Loading />
  if (record.isError) return <ErrorState error={record.error} />
  const status = values.status as string | undefined
  const locked = !isNew && (status === 'published' || status === 'archived') && !isReviewer(role)

  const save = async (confirmDuplicate = false) => {
    setBusy(true)
    setErrors({})
    setMessage(null)
    const payloadValues = isNew ? Object.fromEntries(Object.entries(values).filter(([k]) => !READONLY.has(k))) : Object.fromEntries([...dirty].map((k) => [k, values[k]]))
    try {
      const body = { values: payloadValues, comment: comment || undefined, confirm_duplicate: confirmDuplicate }
      const r: any = isNew ? await api.post(`/admin/${entity}`, body) : await api.patch(`/admin/${entity}/${id}`, body)
      setDuplicates(null)
      qc.invalidateQueries({ queryKey: ['admin-list', entity] })
      qc.invalidateQueries({ queryKey: ['admin-record', entity] })
      setComment('')
      if (isNew) navigate(`/admin/e/${entity}/${r.id}`, { replace: true })
      else setMessage({ tone: 'ok', text: r.changed?.length ? `Salvo (${r.changed.join(', ')}).` : 'Nenhuma alteração.' })
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.code === 'possible_duplicate') setDuplicates(e.details as any[])
        else if (e.code === 'validation_error' && Array.isArray(e.details)) {
          setErrors(Object.fromEntries((e.details as any[]).map((d) => [d.field, d.message])))
          setMessage({ tone: 'danger', text: e.message })
        } else setMessage({ tone: 'danger', text: e.message })
      }
    } finally {
      setBusy(false)
    }
  }

  const changeStatus = async (target: string) => {
    setMessage(null)
    try {
      await api.post(`/admin/${entity}/${id}/status`, { status: target, note: comment || undefined })
      qc.invalidateQueries({ queryKey: ['admin-record', entity, id] })
      qc.invalidateQueries({ queryKey: ['admin-list', entity] })
      setMessage({ tone: 'ok', text: `Status alterado para ${STATUS_LABELS[target]}.` })
    } catch (e) {
      if (e instanceof ApiError) setMessage({ tone: 'danger', text: e.message })
    }
  }

  const remove = async () => {
    if (!confirm('Remover este registro? A ação fica registrada no histórico.')) return
    try {
      await api.del(`/admin/${entity}/${id}`)
      qc.invalidateQueries({ queryKey: ['admin-list', entity] })
      navigate(`/admin/e/${entity}`)
    } catch (e) {
      if (e instanceof ApiError) setMessage({ tone: 'danger', text: e.message })
    }
  }

  return (
    <div className="grid gap-6 p-6 xl:grid-cols-[1fr_360px]">
      <div>
        <p className="text-[12px] text-steel-400">
          <Link className="wa-link" to={`/admin/e/${entity}`}>{meta.label_plural}</Link> / {isNew ? 'novo' : `#${id}`}
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="wa-heading text-2xl">{isNew ? `Novo: ${meta.label}` : record.data?.title}</h1>
          {status && <Badge tone={STATUS_TONES[status]}>{STATUS_LABELS[status]}</Badge>}
        </div>
        {locked && (
          <p className="mt-2 flex items-center gap-2 rounded border border-warn/40 bg-warn/10 p-2 text-[12.5px] text-warn">
            <AlertTriangle size={14} /> Registro publicado: somente revisores podem editá-lo.
          </p>
        )}
        <form className="mt-4 space-y-3" onSubmit={(e) => { e.preventDefault(); save() }}>
          {fields.map((f) => (
            <label key={f.name} className="grid gap-1 sm:grid-cols-[200px_1fr] sm:gap-3">
              <span className="pt-1.5 text-[12.5px] text-steel-300">
                {f.label}
                {f.required && <span className="text-alert"> *</span>}
                <span className="block font-mono text-[10.5px] text-steel-400">{f.name}</span>
              </span>
              <span>
                <fieldset disabled={locked}>
                  <FieldInput
                    key={`${f.name}-${record.dataUpdatedAt}`}
                    f={f}
                    value={values[f.name]}
                    title={titles[f.name]}
                    onChange={(v, t) => {
                      setValues((s) => ({ ...s, [f.name]: v }))
                      if (t !== undefined) setTitles((s) => ({ ...s, [f.name]: t }))
                      setDirty((d) => new Set(d).add(f.name))
                    }}
                  />
                </fieldset>
                {errors[f.name] && <span className="text-[11.5px] text-alert">{errors[f.name]}</span>}
              </span>
            </label>
          ))}
          <label className="grid gap-1 sm:grid-cols-[200px_1fr] sm:gap-3">
            <span className="pt-1.5 text-[12.5px] text-steel-300">Comentário da alteração</span>
            <input className="wa-input" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Opcional — fica registrado no histórico" />
          </label>
          {message && <p className={`text-[12.5px] ${message.tone === 'ok' ? 'text-ok' : 'text-alert'}`} role="status">{message.text}</p>}
          {duplicates && (
            <div className="rounded-md border border-warn/50 bg-warn/10 p-3 text-[12.5px]">
              <p className="text-warn">Possíveis duplicados encontrados:</p>
              <ul className="my-1 list-disc pl-5">
                {duplicates.map((d) => (
                  <li key={d.id}><Link className="wa-link" to={`/admin/e/${entity}/${d.id}`}>{d.title}</Link> {d.wikidata_id && <span className="text-steel-400">({d.wikidata_id})</span>}</li>
                ))}
              </ul>
              <button type="button" className="wa-btn" onClick={() => save(true)}>Não é duplicado — salvar mesmo assim</button>
            </div>
          )}
          <div className="flex flex-wrap gap-2 pt-2">
            <button className="wa-btn wa-btn-primary" disabled={busy || locked}><Save size={14} /> {isNew ? 'Criar rascunho' : 'Salvar'}</button>
            {!isNew && (isReviewer(role) || status === 'draft' || !status) && (
              <button type="button" className="wa-btn" onClick={remove}><Trash2 size={14} /> Remover</button>
            )}
          </div>
        </form>
      </div>

      {!isNew && record.data && (
        <aside className="space-y-4">
          {meta.has_status && (
            <div className="wa-panel rounded-md p-3">
              <p className="wa-label mb-2">Fluxo de publicação</p>
              <div className="flex flex-wrap gap-2">
                {status === 'draft' && <button className="wa-btn" onClick={() => changeStatus('in_review')}>Enviar para revisão</button>}
                {isReviewer(role) && status !== 'published' && <button className="wa-btn wa-btn-primary" onClick={() => changeStatus('published')}>Publicar</button>}
                {isReviewer(role) && status === 'published' && <button className="wa-btn" onClick={() => changeStatus('in_review')}>Despublicar (revisão)</button>}
                {isReviewer(role) && status !== 'archived' && <button className="wa-btn" onClick={() => changeStatus('archived')}>Arquivar</button>}
                {status === 'in_review' && <button className="wa-btn" onClick={() => changeStatus('draft')}>Devolver a rascunho</button>}
              </div>
              <p className="mt-2 text-[11px] text-steel-400">Publicar registros históricos principais exige ao menos uma citação. O comentário acima é salvo como nota de revisão.</p>
            </div>
          )}
          <div className="wa-panel rounded-md p-3">
            <div className="mb-2 flex items-center justify-between">
              <p className="wa-label">Fontes ({record.data.citations.length})</p>
              <Link className="wa-link text-[12px]" to={`/admin/e/citation/novo?entity_type=${entity}&entity_id=${id}`}>+ citação</Link>
            </div>
            {record.data.citations.length === 0 && <p className="text-[12px] text-warn">Sem citações.</p>}
            <ul className="space-y-1 text-[12px]">
              {record.data.citations.map((c) => (
                <li key={c.id}>
                  <Link className="wa-link" to={`/admin/e/citation/${c.id}`}>{c.source.title}</Link>
                  {c.pages && `, p. ${c.pages}`} {c.field && <span className="font-mono text-steel-400">[{c.field}]</span>}
                </li>
              ))}
            </ul>
            <Link className="wa-link mt-2 block text-[12px]" to={`/admin/e/figure/novo?entity_type=${entity}&entity_id=${id}`}>+ número/estatística ({record.data.figures.length})</Link>
          </div>
          <div className="wa-panel rounded-md p-3">
            <p className="wa-label mb-2">Relações</p>
            {record.data.related.length === 0 && <p className="text-[12px] text-steel-400">Nenhuma relação.</p>}
            {record.data.related.map((g) => (
              <div key={`${g.entity}-${g.field}`} className="mb-2">
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-steel-300">{g.entity} <span className="font-mono text-steel-400">({g.field})</span></span>
                  <Link className="wa-link" to={`/admin/e/${g.entity}/novo?${g.field}=${id}`}>+ adicionar</Link>
                </div>
                <ul className="ml-2 text-[12px]">
                  {g.items.slice(0, 12).map((it) => <li key={it.id}><Link className="wa-link" to={`/admin/e/${g.entity}/${it.id}`}>{it.title}</Link></li>)}
                  {g.items.length > 12 && <li><Link className="wa-link" to={`/admin/e/${g.entity}?filter_field=${g.field}&filter_value=${id}`}>ver todos ({g.items.length})</Link></li>}
                </ul>
              </div>
            ))}
          </div>
          <RevisionList entity={entity!} id={id!} />
        </aside>
      )}
    </div>
  )
}

function RevisionList({ entity, id }: { entity: string; id: string }) {
  const revs = useQuery({ queryKey: ['revisions', entity, id], queryFn: () => api.get<any[]>('/admin/revisions', { entity, entity_id: id, limit: 20 }) })
  return (
    <div className="wa-panel rounded-md p-3">
      <p className="wa-label mb-2">Histórico</p>
      {revs.data?.length === 0 && <p className="text-[12px] text-steel-400">Sem alterações registradas (ex.: dados iniciais carregados por script).</p>}
      <ul className="space-y-1 text-[11.5px]">
        {revs.data?.map((r) => (
          <li key={r.id}>
            <span className="font-mono text-steel-400">{r.created_at.slice(0, 16).replace('T', ' ')}</span> {r.action} · {r.user ?? '—'}
            {r.comment && <span className="block text-steel-400 italic">{r.comment}</span>}
          </li>
        ))}
      </ul>
    </div>
  )
}
