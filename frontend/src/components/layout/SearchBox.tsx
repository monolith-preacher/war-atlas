import { Filter, MapPin, Search, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { type SearchFilters, useConflict, usePolities, useSearch } from '../../hooks/queries'
import { formatRange } from '../../lib/dates'
import { BRANCHES, ECHELONS, EQUIPMENT_CATEGORIES, entityLabel } from '../../lib/labels'
import type { SearchItem } from '../../lib/types'
import { useExplorer } from '../../store/explorer'
import { Spinner } from '../common/ui'

const TYPES = ['battle', 'campaign', 'event', 'unit', 'person', 'equipment', 'polity', 'place', 'theater', 'conflict']

function useDebounced<T>(value: T, ms = 250) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

export function SearchBox() {
  const conflict = useExplorer((s) => s.conflict)
  const select = useExplorer((s) => s.select)
  const fly = useExplorer((s) => s.fly)
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [onlyConflict, setOnlyConflict] = useState(true)
  const [types, setTypes] = useState<string[]>([])
  const [polity, setPolity] = useState('')
  const [theater, setTheater] = useState('')
  const [category, setCategory] = useState('')
  const [branch, setBranch] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [active, setActive] = useState(0)
  const box = useRef<HTMLDivElement>(null)
  const debounced = useDebounced(q)

  const conflictQ = useConflict(conflict)
  const polities = usePolities(onlyConflict ? conflict : null)
  const filters: SearchFilters = {
    types: types.length ? types.join(',') : undefined,
    conflict: onlyConflict ? conflict : undefined,
    polity: polity || undefined,
    theater: theater || undefined,
    category: category || undefined,
    branch: branch || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  }
  const search = useSearch(debounced, filters)
  const flat = useMemo(() => search.data?.groups.flatMap((g) => g.items) ?? [], [search.data])
  const activeFilters = [types.length, polity, theater, category, branch, dateFrom, dateTo].filter(Boolean).length

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        box.current?.querySelector('input')?.focus()
        setOpen(true)
      }
    }
    document.addEventListener('mousedown', onDoc)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDoc)
      document.removeEventListener('keydown', onKey)
    }
  }, [])

  const choose = (item: SearchItem, center = false) => {
    if (item.type === 'conflict') {
      useExplorer.getState().setConflict(item.slug, item.start_date)
    } else {
      select({ type: item.type, slug: item.slug })
    }
    if ((center || item.type !== 'conflict') && item.location) fly(item.location, item.type === 'place' || item.type === 'event' ? 11 : undefined)
    setOpen(false)
  }

  const categoryOptions = types.length === 1 && types[0] === 'unit' ? ECHELONS : EQUIPMENT_CATEGORIES

  return (
    <div ref={box} className="relative w-full max-w-xl">
      <div className="flex items-center gap-1 rounded-md border border-ink-600 bg-ink-850 pr-1 focus-within:border-brass-500">
        <Search size={15} className="ml-2.5 shrink-0 text-steel-400" />
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value)
            setOpen(true)
            setActive(0)
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') setActive((a) => Math.min(a + 1, flat.length - 1))
            if (e.key === 'ArrowUp') setActive((a) => Math.max(a - 1, 0))
            if (e.key === 'Enter' && flat[active]) choose(flat[active])
            if (e.key === 'Escape') setOpen(false)
          }}
          placeholder="Pesquisar batalhas, unidades, comandantes, equipamentos…  (Ctrl+K)"
          className="w-full bg-transparent px-2 py-1.5 text-[13px] text-parchment placeholder:text-steel-400 focus:outline-none"
          aria-label="Pesquisa global"
          role="combobox"
          aria-expanded={open}
        />
        {search.isFetching && <Spinner className="size-4" />}
        {q && (
          <button className="wa-icon-btn size-7" onClick={() => setQ('')} aria-label="Limpar">
            <X size={14} />
          </button>
        )}
        <button className={`wa-icon-btn size-7 ${activeFilters ? 'text-brass-400' : ''}`} onClick={() => { setShowFilters(!showFilters); setOpen(true) }} title="Filtros" aria-label="Filtros">
          <Filter size={14} />
          {activeFilters > 0 && <span className="absolute mt-[-14px] ml-[14px] text-[9px]">{activeFilters}</span>}
        </button>
      </div>

      {open && (showFilters || q.trim().length >= 2) && (
        <div className="wa-panel absolute top-full right-0 left-0 z-50 mt-1 max-h-[70vh] animate-fade-in overflow-y-auto rounded-md shadow-2xl">
          {showFilters && (
            <div className="space-y-2 border-b border-ink-700 p-3 text-[12px]">
              <div className="flex flex-wrap gap-1">
                {TYPES.map((t) => (
                  <button
                    key={t}
                    onClick={() => setTypes(types.includes(t) ? types.filter((x) => x !== t) : [...types, t])}
                    className={`wa-chip ${types.includes(t) ? 'border-brass-500 bg-brass-500/15 text-brass-300' : ''}`}
                  >
                    {entityLabel(t, true)}
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <label className="flex items-center gap-2 text-steel-300">
                  <input type="checkbox" checked={onlyConflict} onChange={(e) => setOnlyConflict(e.target.checked)} disabled={!conflict} /> Apenas o conflito atual
                </label>
                <select className="wa-input py-1" value={polity} onChange={(e) => setPolity(e.target.value)} aria-label="País">
                  <option value="">Qualquer país</option>
                  {(polities.data ?? []).map((p) => (
                    <option key={p.slug} value={p.slug}>
                      {p.name}
                    </option>
                  ))}
                </select>
                <select className="wa-input py-1" value={theater} onChange={(e) => setTheater(e.target.value)} aria-label="Teatro" disabled={!conflictQ.data}>
                  <option value="">Qualquer teatro</option>
                  {(conflictQ.data?.theaters ?? []).map((t) => (
                    <option key={t.slug} value={t.slug}>
                      {t.name}
                    </option>
                  ))}
                </select>
                <select className="wa-input py-1" value={branch} onChange={(e) => setBranch(e.target.value)} aria-label="Ramo militar">
                  <option value="">Qualquer ramo (unidades)</option>
                  {Object.entries(BRANCHES).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
                <select className="wa-input py-1" value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Categoria">
                  <option value="">{types.length === 1 && types[0] === 'unit' ? 'Qualquer escalão' : 'Qualquer categoria de equipamento'}</option>
                  {Object.entries(categoryOptions).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
                <div className="flex items-center gap-1">
                  <input type="date" className="wa-input py-1" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} aria-label="De" />
                  <input type="date" className="wa-input py-1" value={dateTo} onChange={(e) => setDateTo(e.target.value)} aria-label="Até" />
                </div>
              </div>
              {activeFilters > 0 && (
                <button className="wa-link text-[11.5px]" onClick={() => { setTypes([]); setPolity(''); setTheater(''); setCategory(''); setBranch(''); setDateFrom(''); setDateTo('') }}>
                  Limpar filtros
                </button>
              )}
            </div>
          )}
          {q.trim().length < 2 ? (
            <p className="p-3 text-[12px] text-steel-400">Digite ao menos 2 caracteres.</p>
          ) : search.isError ? (
            <p className="p-3 text-[12px] text-alert">Falha na pesquisa.</p>
          ) : search.data && search.data.total === 0 ? (
            <p className="p-3 text-[12px] text-steel-400">
              Nenhum registro cadastrado corresponde a “{search.data.query}”{activeFilters || onlyConflict ? ' com os filtros atuais' : ''}.
            </p>
          ) : (
            search.data?.groups.map((g) => (
              <div key={g.type} className="py-1">
                <div className="wa-label px-3 pt-1.5 pb-1">{entityLabel(g.type, true)}</div>
                {g.items.map((item) => {
                  const idx = flat.indexOf(item)
                  return (
                    <div key={`${item.type}-${item.id}`} className={`group flex items-center gap-2 px-3 py-1.5 ${idx === active ? 'bg-ink-700' : 'hover:bg-ink-800'}`} onMouseEnter={() => setActive(idx)}>
                      <button className="min-w-0 flex-1 text-left" onClick={() => choose(item)}>
                        <div className="truncate text-[13px] text-parchment">{item.title}</div>
                        <div className="truncate text-[11px] text-steel-400">
                          {[item.subtitle, item.start_date || item.end_date ? formatRange(item.start_date, item.end_date) : null].filter(Boolean).join(' · ')}
                        </div>
                      </button>
                      {item.location && (
                        <button className="wa-icon-btn size-7 opacity-60 group-hover:opacity-100" title="Centralizar no mapa" onClick={() => choose(item, true)}>
                          <MapPin size={14} />
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
