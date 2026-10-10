/** Small shared presentational components. */
import clsx from 'clsx'
import { AlertTriangle, CircleHelp, Info, Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { ApiError } from '../../lib/api'
import { formatRange } from '../../lib/dates'
import { CERTAINTY, PRECISION_LABELS } from '../../lib/labels'
import type { Temporal } from '../../lib/types'

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={clsx('animate-spin text-brass-500', className)} size={18} aria-hidden />
}

export function Loading({ label = 'Carregando…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 p-4 text-steel-400" role="status">
      <Spinner /> <span>{label}</span>
    </div>
  )
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const msg = error instanceof ApiError ? error.message : 'Ocorreu um erro inesperado.'
  return (
    <div className="m-3 rounded-md border border-alert/40 bg-alert/10 p-3 text-sm text-parchment" role="alert">
      <div className="flex items-start gap-2">
        <AlertTriangle size={16} className="mt-0.5 shrink-0 text-alert" />
        <div className="flex-1">
          <p>{msg}</p>
          {onRetry && (
            <button className="wa-btn mt-2" onClick={onRetry}>
              Tentar novamente
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/** Explicit "no data" marker: absence of data is not absence of history. */
export function Undocumented({ children = 'Não documentado no acervo atual' }: { children?: ReactNode }) {
  return <span className="text-steel-400 italic">{children}</span>
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="m-3 rounded-md border border-dashed border-ink-600 p-4 text-center text-sm">
      <p className="wa-heading text-base">{title}</p>
      {children && <div className="mt-1 text-steel-400">{children}</div>}
    </div>
  )
}

export function Section({ title, children, right, defaultOpen = true }: { title: string; children: ReactNode; right?: ReactNode; defaultOpen?: boolean }) {
  return (
    <details open={defaultOpen} className="group border-t border-ink-700 first:border-t-0">
      <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-2.5 select-none hover:bg-ink-800/60">
        <span className="wa-label group-open:text-brass-400">{title}</span>
        <span className="flex items-center gap-2 text-steel-400">
          {right}
          <span className="text-xs transition-transform group-open:rotate-90">›</span>
        </span>
      </summary>
      <div className="px-4 pt-1 pb-3">{children}</div>
    </details>
  )
}

const TONES: Record<string, string> = {
  ok: 'border-ok/50 text-ok bg-ok/10',
  info: 'border-info/50 text-info bg-info/10',
  warn: 'border-warn/50 text-warn bg-warn/10',
  danger: 'border-alert/50 text-alert bg-alert/10',
  neutral: 'border-ink-500 text-steel-300 bg-ink-800',
}

export function Badge({ tone = 'neutral', children, title }: { tone?: string; children: ReactNode; title?: string }) {
  return (
    <span title={title} className={clsx('inline-flex items-center gap-1 rounded border px-1.5 py-px text-[10.5px] font-medium tracking-wide uppercase', TONES[tone])}>
      {children}
    </span>
  )
}

export function CertaintyBadge({ value }: { value?: string | null }) {
  if (!value) return null
  const c = CERTAINTY[value]
  if (!c) return null
  return (
    <Badge tone={c.tone} title={c.description}>
      {c.tone === 'warn' || c.tone === 'danger' ? <AlertTriangle size={10} /> : <Info size={10} />}
      {c.label}
    </Badge>
  )
}

/** Date interval with precision hints ("atestada", "ano"...). */
export function Period({ t, className }: { t: Partial<Temporal>; className?: string }) {
  const text = formatRange(t.valid_from ?? null, t.valid_to ?? null, t.valid_from_precision ?? 'day', t.valid_to_precision ?? 'day')
  const notes: string[] = []
  if (t.valid_from_precision && t.valid_from_precision !== 'day') notes.push(`início: ${PRECISION_LABELS[t.valid_from_precision]}`)
  if (t.valid_to_precision && t.valid_to_precision !== 'day') notes.push(`fim: ${PRECISION_LABELS[t.valid_to_precision]}`)
  const attested = t.valid_from_precision === 'attested' || t.valid_to_precision === 'attested'
  return (
    <span className={clsx('font-mono text-[11.5px] text-steel-300', className)} title={notes.join(' · ') || undefined}>
      {text}
      {attested && (
        <span className="ml-1 text-warn" aria-label="limites atestados">
          ≈
        </span>
      )}
    </span>
  )
}

export function HelpTip({ text }: { text: string }) {
  return (
    <span title={text} className="inline-flex cursor-help text-steel-400 hover:text-brass-400">
      <CircleHelp size={13} />
    </span>
  )
}

export function KeyValue({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[minmax(110px,38%)_1fr] gap-2 py-1 text-[13px]">
      <dt className="text-steel-400">{label}</dt>
      <dd className="text-steel-200">{children ?? <Undocumented />}</dd>
    </div>
  )
}

export function PlannedFeature({ phase, children }: { phase: number; children: ReactNode }) {
  return (
    <div className="rounded-md border border-ink-600 bg-ink-800/60 p-3 text-[12.5px] text-steel-400">
      <Badge tone="info">Fase {phase}</Badge> <span className="ml-1">{children}</span>
    </div>
  )
}
