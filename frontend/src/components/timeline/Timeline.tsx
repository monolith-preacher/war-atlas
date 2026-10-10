import { ChevronLeft, ChevronRight, Pause, Play, SkipBack, SkipForward } from 'lucide-react'
import { useEffect, useMemo, useRef } from 'react'
import { useReplay, useTimeline } from '../../hooks/queries'
import { addDays, clamp, daysBetween, formatDate, type Granularity, isValidISO, parseISO, step, toISO } from '../../lib/dates'
import { useExplorer } from '../../store/explorer'

const SPEEDS: { value: number; label: string }[] = [
  { value: 0, label: 'Evento a evento' },
  { value: 1, label: '1 dia/s' },
  { value: 7, label: '1 semana/s' },
  { value: 30, label: '1 mês/s' },
  { value: 120, label: '4 meses/s' },
]

export function Timeline() {
  const conflict = useExplorer((s) => s.conflict)
  const date = useExplorer((s) => s.date)
  const setDate = useExplorer((s) => s.setDate)
  const granularity = useExplorer((s) => s.granularity)
  const setGranularity = useExplorer((s) => s.setGranularity)
  const playing = useExplorer((s) => s.playing)
  const setPlaying = useExplorer((s) => s.setPlaying)
  const speed = useExplorer((s) => s.speed)
  const setSpeed = useExplorer((s) => s.setSpeed)
  const replay = useExplorer((s) => s.replay)
  const select = useExplorer((s) => s.select)

  const tl = useTimeline(conflict)
  const rp = useReplay(replay?.scope ?? null, replay?.slug ?? null)

  const range = useMemo(() => {
    if (replay && rp.data) return { min: rp.data.scope.start_date, max: rp.data.scope.end_date }
    if (tl.data) return { min: tl.data.conflict.start_date, max: tl.data.conflict.end_date }
    return null
  }, [replay, rp.data, tl.data])

  const eventDates = useMemo(() => {
    const src = replay && rp.data ? rp.data.steps.map((s) => s.date) : (tl.data?.events ?? []).map((e) => e.start_date)
    return [...new Set(src)].sort()
  }, [replay, rp.data, tl.data])

  // ---- playback (documented dates only in "event by event" mode; continuous days otherwise)
  const acc = useRef(0)
  useEffect(() => {
    if (!playing || !range) return
    const tickMs = speed === 0 ? 1800 : 100
    const id = window.setInterval(() => {
      const cur = useExplorer.getState().date ?? range.min
      let next: string | undefined
      if (speed === 0) {
        next = eventDates.find((d) => d > cur)
      } else {
        acc.current += speed / 10
        const whole = Math.floor(acc.current)
        if (whole < 1) return
        acc.current -= whole
        next = addDays(cur, whole)
      }
      if (!next || next > range.max) {
        setDate(range.max)
        setPlaying(false)
        return
      }
      setDate(next)
    }, tickMs)
    return () => window.clearInterval(id)
  }, [playing, speed, range, eventDates, setDate, setPlaying])

  if (!range || !date) return null
  const total = Math.max(1, daysBetween(range.min, range.max))
  const pos = (d: string) => (daysBetween(range.min, clamp(d, range.min, range.max)) / total) * 100
  const go = (d: string) => setDate(clamp(d, range.min, range.max))
  const prevEvent = [...eventDates].reverse().find((d) => d < date)
  const nextEvent = eventDates.find((d) => d > date)

  const years: string[] = []
  for (let y = parseISO(range.min).getUTCFullYear(); y <= parseISO(range.max).getUTCFullYear(); y++) years.push(`${y}-01-01`)
  const months: string[] = []
  if (total < 800) {
    let m = toISO(new Date(Date.UTC(parseISO(range.min).getUTCFullYear(), parseISO(range.min).getUTCMonth() + 1, 1)))
    while (m <= range.max) {
      months.push(m)
      m = step(m, 'month', 1)
    }
  }
  const battles = (tl.data?.battles ?? []).filter((b) => b.start_date && !b.parent_id)
  const events = replay && rp.data ? rp.data.steps.flatMap((s) => s.events.map((e) => ({ ...e, start_date: s.date }))) : tl.data?.events ?? []
  const todaysEvents = events.filter((e) => e.start_date === date)

  return (
    <div className="wa-panel border-x-0 border-b-0 px-3 pt-2 pb-2.5 select-none">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <div className="flex items-center">
          <button className="wa-icon-btn" onClick={() => prevEvent && go(prevEvent)} disabled={!prevEvent} title="Evento anterior" aria-label="Evento anterior">
            <SkipBack size={16} />
          </button>
          <button className="wa-icon-btn" onClick={() => go(step(date, granularity, -1))} disabled={date <= range.min} title={`Recuar 1 ${labelFor(granularity)}`} aria-label="Recuar">
            <ChevronLeft size={18} />
          </button>
          <button
            className="mx-1 inline-flex size-9 items-center justify-center rounded-full bg-brass-500 text-ink-950 hover:bg-brass-400"
            onClick={() => {
              if (!playing && date >= range.max) setDate(range.min)
              setPlaying(!playing)
            }}
            title={playing ? 'Pausar' : 'Reproduzir cronologicamente'}
            aria-label={playing ? 'Pausar' : 'Reproduzir'}
          >
            {playing ? <Pause size={16} /> : <Play size={16} className="ml-0.5" />}
          </button>
          <button className="wa-icon-btn" onClick={() => go(step(date, granularity, 1))} disabled={date >= range.max} title={`Avançar 1 ${labelFor(granularity)}`} aria-label="Avançar">
            <ChevronRight size={18} />
          </button>
          <button className="wa-icon-btn" onClick={() => nextEvent && go(nextEvent)} disabled={!nextEvent} title="Próximo evento" aria-label="Próximo evento">
            <SkipForward size={16} />
          </button>
        </div>

        <div className="min-w-[180px]">
          <div className="wa-heading text-[19px] leading-tight">{formatDate(date, granularity === 'year' ? 'year' : granularity === 'month' ? 'month' : 'day', 'long')}</div>
          <div className="text-[11px] text-steel-400">
            {todaysEvents.length ? `${todaysEvents.length} evento(s) documentado(s) nesta data` : 'Nenhum evento cadastrado nesta data'}
          </div>
        </div>

        <div className="ml-auto flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-1.5 text-[11.5px] text-steel-400">
            Passo
            <select className="wa-input w-auto py-1" value={granularity} onChange={(e) => setGranularity(e.target.value as Granularity)}>
              <option value="day">Dia</option>
              <option value="month">Mês</option>
              <option value="year">Ano</option>
            </select>
          </label>
          <label className="flex items-center gap-1.5 text-[11.5px] text-steel-400">
            Velocidade
            <select className="wa-input w-auto py-1" value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
              {SPEEDS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          <input
            type="date"
            className="wa-input w-auto py-1 font-mono"
            min={range.min}
            max={range.max}
            value={date}
            onChange={(e) => isValidISO(e.target.value) && go(e.target.value)}
            aria-label="Selecionar data"
          />
        </div>
      </div>

      {/* track */}
      <div className="relative mt-2 h-14">
        <svg className="absolute inset-0 h-full w-full overflow-visible" preserveAspectRatio="none" aria-hidden>
          {months.map((m) => (
            <line key={m} x1={`${pos(m)}%`} x2={`${pos(m)}%`} y1="34" y2="40" stroke="#343d46" />
          ))}
          {years.map((y) =>
            y >= range.min ? <line key={y} x1={`${pos(y)}%`} x2={`${pos(y)}%`} y1="28" y2="44" stroke="#5c6772" /> : null,
          )}
          <line x1="0" x2="100%" y1="40" y2="40" stroke="#343d46" />
          {battles.map((b, i) => (
            <rect
              key={b.id}
              x={`${pos(b.start_date!)}%`}
              width={`${Math.max(0.35, pos(b.end_date ?? b.start_date!) - pos(b.start_date!))}%`}
              y={4 + (i % 2) * 7}
              height="5"
              rx="2"
              fill={b.start_date! <= date && (b.end_date ?? b.start_date!) >= date ? '#d9604f' : '#7a3a33'}
            >
              <title>{b.name}</title>
            </rect>
          ))}
          {events.map((e) => (
            <circle key={`${e.id}`} cx={`${pos(e.start_date)}%`} cy="23" r={1.2 + e.importance * 0.55} fill={e.start_date === date ? '#f0d48a' : '#c9a96a'} opacity={e.start_date <= date ? 0.95 : 0.4}>
              <title>{`${formatDate(e.start_date)} — ${e.title}`}</title>
            </circle>
          ))}
        </svg>
        {years.map((y) =>
          y >= range.min ? (
            <span key={y} className="absolute top-[44px] -translate-x-1/2 font-mono text-[10px] text-steel-400" style={{ left: `${pos(y)}%` }}>
              {y.slice(0, 4)}
            </span>
          ) : null,
        )}
        <div className="pointer-events-none absolute top-0 bottom-3 w-px bg-brass-400 shadow-[0_0_8px_#c9a96a]" style={{ left: `${pos(date)}%` }}>
          <span className="absolute -top-0.5 -left-[5px] size-[11px] rotate-45 border border-ink-950 bg-brass-400" />
        </div>
        <input
          type="range"
          min={0}
          max={total}
          value={daysBetween(range.min, date)}
          onChange={(e) => go(addDays(range.min, Number(e.target.value)))}
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
          aria-label="Linha do tempo"
          aria-valuetext={formatDate(date, 'day', 'long')}
        />
      </div>
      {todaysEvents.length > 0 && (
        <div className="mt-1 flex gap-2 overflow-x-auto pb-0.5">
          {todaysEvents.map((e) => (
            <button key={e.id} className="wa-chip shrink-0 hover:border-brass-600 hover:text-parchment" onClick={() => select({ type: 'event', slug: e.slug })}>
              <span className="size-1.5 rotate-45 bg-brass-500" />
              {e.time_of_day && <span className="font-mono text-steel-400">{e.time_of_day.length < 7 ? e.time_of_day : ''}</span>}
              {e.title}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function labelFor(g: Granularity) {
  return g === 'day' ? 'dia' : g === 'month' ? 'mês' : 'ano'
}
