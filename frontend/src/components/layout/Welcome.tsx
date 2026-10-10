import { ArrowRight, BookOpen, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useConflicts } from '../../hooks/queries'
import { formatRange } from '../../lib/dates'
import { useExplorer } from '../../store/explorer'
import { ErrorState, Loading } from '../common/ui'
import { Logo } from './Header'

const SUGGESTIONS: Record<string, { label: string; type: 'battle' | 'campaign'; slug: string; date: string; center: [number, number]; zoom: number }[]> = {
  'primeira-guerra-mundial': [{ label: 'Batalha do Somme (1916)', type: 'battle', slug: 'batalha-do-somme', date: '1916-07-01', center: [2.72, 50.03], zoom: 10 }],
  'segunda-guerra-mundial': [{ label: 'Campanha da Normandia (1944)', type: 'campaign', slug: 'campanha-da-normandia', date: '1944-06-06', center: [-0.6, 49.25], zoom: 8.6 }],
}

export function Welcome() {
  const conflicts = useConflicts()
  const setConflict = useExplorer((s) => s.setConflict)
  const select = useExplorer((s) => s.select)
  const fly = useExplorer((s) => s.fly)
  const setMode = useExplorer((s) => s.setMode)
  return (
    <div className="wa-grid-bg absolute inset-0 z-40 flex animate-fade-in items-center justify-center overflow-y-auto bg-ink-950/85 p-4 backdrop-blur-sm">
      <div className="w-full max-w-3xl">
        <div className="mb-6 flex flex-col items-center text-center">
          <Logo />
          <h1 className="wa-heading mt-4 text-3xl sm:text-4xl">Explore a história militar num mapa vivo</h1>
          <p className="mt-2 max-w-xl text-[14px] text-steel-300">
            Conflitos, batalhas, unidades, comandantes e equipamentos ligados no espaço e no tempo — com fontes identificáveis e as incertezas sinalizadas.
          </p>
        </div>
        {conflicts.isLoading && <Loading label="Conectando à API…" />}
        {conflicts.isError && <ErrorState error={conflicts.error} onRetry={() => conflicts.refetch()} />}
        {conflicts.data?.length === 0 && <p className="text-center text-steel-300">Nenhum conflito publicado ainda. Carregue os dados iniciais (veja o README).</p>}
        <div className="grid gap-4 sm:grid-cols-2">
          {conflicts.data?.map((c) => (
            <div key={c.slug} className="wa-panel group rounded-lg p-5 transition-colors hover:border-brass-600">
              <div className="flex items-center gap-2">
                <span className="size-2.5 rounded-full" style={{ background: c.color ?? '#777' }} />
                <span className="font-mono text-[12px] text-steel-400">{formatRange(c.start_date, c.end_date)}</span>
              </div>
              <h2 className="wa-heading mt-2 text-2xl">{c.name}</h2>
              <p className="mt-2 text-[13px] leading-relaxed text-steel-300">{c.summary}</p>
              <p className="mt-3 font-mono text-[11px] text-steel-400">
                {c.counts?.theaters} teatros · {c.counts?.battles} batalhas · {c.counts?.events} eventos cadastrados
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button className="wa-btn wa-btn-primary" onClick={() => setConflict(c.slug, c.start_date)}>
                  Explorar <ArrowRight size={14} />
                </button>
                {(SUGGESTIONS[c.slug] ?? []).map((s) => (
                  <button
                    key={s.slug}
                    className="wa-btn"
                    onClick={() => {
                      setConflict(c.slug, s.date)
                      setMode('military')
                      select({ type: s.type, slug: s.slug })
                      setTimeout(() => fly(s.center, s.zoom), 1700)
                    }}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 flex flex-col items-center gap-2 text-center text-[12px] text-steel-400">
          <p className="flex items-center gap-1.5">
            <ShieldCheck size={14} className="text-olive-400" /> Nenhum dado é inventado: ausência de registro é mostrada como tal, e reconstruções cartográficas são sinalizadas.
          </p>
          <Link to="/sobre" className="wa-link flex items-center gap-1">
            <BookOpen size={13} /> Metodologia, fontes e estado do projeto
          </Link>
        </div>
      </div>
    </div>
  )
}
