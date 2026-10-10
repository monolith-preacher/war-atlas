import { BookOpen, ChevronDown, Menu, Settings, Shield } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useConflicts } from '../../hooks/queries'
import { MODES, type MapMode } from '../../lib/layers'
import { useExplorer } from '../../store/explorer'
import { SearchBox } from './SearchBox'

export function Logo() {
  return (
    <Link to="/" className="flex shrink-0 items-center gap-2" aria-label="War Atlas — início">
      <svg width="26" height="26" viewBox="0 0 64 64" aria-hidden>
        <circle cx="32" cy="32" r="22" fill="none" stroke="#c9a96a" strokeWidth="3" />
        <path d="M32 6v52M6 32h52" stroke="#c9a96a" strokeWidth="1.6" opacity=".55" />
        <path d="M32 16l6 16-6 16-6-16z" fill="#c9a96a" />
      </svg>
      <span className="wa-heading text-[19px] font-semibold tracking-[0.18em] uppercase">
        War <span className="text-brass-500">Atlas</span>
      </span>
    </Link>
  )
}

function usePopover() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const h = (e: MouseEvent) => ref.current && !ref.current.contains(e.target as Node) && setOpen(false)
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])
  return { open, setOpen, ref }
}

function ConflictSelector() {
  const conflicts = useConflicts()
  const conflict = useExplorer((s) => s.conflict)
  const setConflict = useExplorer((s) => s.setConflict)
  const pop = usePopover()
  const current = conflicts.data?.find((c) => c.slug === conflict)
  return (
    <div ref={pop.ref} className="relative">
      <button className="wa-btn min-w-[190px] justify-between" onClick={() => pop.setOpen(!pop.open)} aria-haspopup="listbox" aria-expanded={pop.open}>
        <span className="flex items-center gap-2">
          <span className="size-2 rounded-full" style={{ background: current?.color ?? '#5a6570' }} />
          <span className="truncate">{current ? current.name : 'Selecionar conflito'}</span>
        </span>
        <ChevronDown size={14} />
      </button>
      {pop.open && (
        <div className="wa-panel absolute top-full left-0 z-50 mt-1 w-72 animate-fade-in rounded-md p-1 shadow-xl" role="listbox">
          {conflicts.isLoading && <p className="p-2 text-[12px] text-steel-400">Carregando…</p>}
          {conflicts.data?.length === 0 && <p className="p-2 text-[12px] text-steel-400">Nenhum conflito publicado.</p>}
          {conflicts.data?.map((c) => (
            <button
              key={c.slug}
              role="option"
              aria-selected={c.slug === conflict}
              onClick={() => {
                setConflict(c.slug, c.start_date)
                pop.setOpen(false)
              }}
              className={`flex w-full flex-col rounded px-2.5 py-2 text-left hover:bg-ink-700 ${c.slug === conflict ? 'bg-ink-750' : ''}`}
            >
              <span className="flex items-center gap-2 text-parchment">
                <span className="size-2 rounded-full" style={{ background: c.color ?? '#5a6570' }} />
                {c.name}
              </span>
              <span className="pl-4 font-mono text-[11px] text-steel-400">
                {c.start_date.slice(0, 4)}–{c.end_date.slice(0, 4)} · {c.counts?.battles ?? 0} batalhas · {c.counts?.events ?? 0} eventos
              </span>
            </button>
          ))}
          <p className="border-t border-ink-700 p-2 text-[11px] text-steel-400">Novos conflitos podem ser cadastrados pelo painel administrativo.</p>
        </div>
      )}
    </div>
  )
}

function ModeSwitcher() {
  const mode = useExplorer((s) => s.mode)
  const setMode = useExplorer((s) => s.setMode)
  return (
    <div className="flex rounded-md border border-ink-600 bg-ink-850 p-0.5" role="radiogroup" aria-label="Modo de visualização">
      {(Object.keys(MODES) as MapMode[]).map((m) => (
        <button
          key={m}
          role="radio"
          aria-checked={mode === m}
          title={MODES[m].description}
          onClick={() => setMode(m)}
          className={`rounded px-2.5 py-1 text-[12px] transition-colors ${mode === m ? 'bg-olive-600 text-parchment' : 'text-steel-300 hover:text-parchment'}`}
        >
          {MODES[m].label}
        </button>
      ))}
    </div>
  )
}

function SettingsMenu() {
  const pop = usePopover()
  const s = useExplorer()
  return (
    <div ref={pop.ref} className="relative">
      <button className="wa-icon-btn" onClick={() => pop.setOpen(!pop.open)} aria-label="Configurações" title="Configurações">
        <Settings size={17} />
      </button>
      {pop.open && (
        <div className="wa-panel absolute top-full right-0 z-50 mt-1 w-72 animate-fade-in space-y-3 rounded-md p-3 text-[12.5px] shadow-xl">
          <p className="wa-label">Configurações</p>
          <label className="flex items-center justify-between gap-2">
            Janela de eventos recentes
            <select className="wa-input w-auto py-1" value={s.eventWindow} onChange={(e) => s.setEventWindow(Number(e.target.value))}>
              {[0, 1, 3, 7, 14, 30].map((n) => (
                <option key={n} value={n}>
                  {n === 0 ? 'só o dia' : `${n} dias`}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center justify-between gap-2">
            Reduzir animações
            <input type="checkbox" checked={s.reduceMotion} onChange={(e) => s.setReduceMotion(e.target.checked)} />
          </label>
          <label className="flex items-center justify-between gap-2">
            Halos de incerteza
            <input type="checkbox" checked={s.layers.uncertainty} onChange={() => s.toggleLayer('uncertainty')} />
          </label>
          <button className="wa-btn w-full justify-center" onClick={() => s.setMode(s.mode)}>
            Restaurar camadas do modo
          </button>
          <div className="space-y-1 border-t border-ink-700 pt-2">
            <Link to="/sobre" className="wa-link flex items-center gap-1.5">
              <BookOpen size={13} /> Metodologia, fontes e fases
            </Link>
            <Link to="/admin" className="wa-link flex items-center gap-1.5">
              <Shield size={13} /> Painel administrativo
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export function Header() {
  const setSidebar = useExplorer((s) => s.setSidebar)
  const sidebarOpen = useExplorer((s) => s.sidebarOpen)
  return (
    <header className="wa-panel relative z-30 flex flex-wrap items-center gap-x-4 gap-y-2 border-x-0 border-t-0 px-3 py-2">
      <button className="wa-icon-btn" onClick={() => setSidebar(!sidebarOpen)} aria-label="Alternar barra lateral" title="Barra lateral">
        <Menu size={18} />
      </button>
      <Logo />
      <ConflictSelector />
      <div className="order-last w-full flex-1 md:order-none md:w-auto">
        <SearchBox />
      </div>
      <div className="flex items-center gap-2">
        <div className="hidden lg:block">
          <ModeSwitcher />
        </div>
        <SettingsMenu />
      </div>
      <div className="w-full lg:hidden">
        <ModeSwitcher />
      </div>
    </header>
  )
}
