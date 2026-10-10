/** Date helpers working on ISO 'YYYY-MM-DD' strings in UTC (no timezone drift). */

export type Granularity = 'day' | 'month' | 'year'

const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const MONTHS_FULL = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']

export function parseISO(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d))
}

export function toISO(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export function isValidISO(s: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(s) && toISO(parseISO(s)) === s
}

export function addDays(iso: string, n: number): string {
  const d = parseISO(iso)
  d.setUTCDate(d.getUTCDate() + n)
  return toISO(d)
}

export function addMonths(iso: string, n: number): string {
  const d = parseISO(iso)
  const day = d.getUTCDate()
  d.setUTCDate(1)
  d.setUTCMonth(d.getUTCMonth() + n)
  const last = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0)).getUTCDate()
  d.setUTCDate(Math.min(day, last))
  return toISO(d)
}

export function step(iso: string, g: Granularity, n: number): string {
  if (g === 'day') return addDays(iso, n)
  if (g === 'month') return addMonths(iso, n)
  return addMonths(iso, 12 * n)
}

export function clamp(iso: string, min: string, max: string): string {
  return iso < min ? min : iso > max ? max : iso
}

export function daysBetween(a: string, b: string): number {
  return Math.round((parseISO(b).getTime() - parseISO(a).getTime()) / 86_400_000)
}

/** Formats a date honouring its documented precision. */
export function formatDate(iso: string | null | undefined, precision: string | null = 'day', style: 'short' | 'long' = 'short'): string {
  if (!iso) return '—'
  const d = parseISO(iso)
  const y = d.getUTCFullYear()
  const m = d.getUTCMonth()
  const day = d.getUTCDate()
  const months = style === 'long' ? MONTHS_FULL : MONTHS
  switch (precision) {
    case 'year':
      return String(y)
    case 'month':
      return `${months[m]} ${y}`
    case 'circa':
      return `c. ${day} ${months[m]} ${y}`
    default:
      return style === 'long' ? `${day} de ${months[m]} de ${y}` : `${day} ${months[m]} ${y}`
  }
}

export function formatRange(
  from: string | null | undefined,
  to: string | null | undefined,
  fromPrecision: string | null = 'day',
  toPrecision: string | null = 'day',
): string {
  if (!from && !to) return 'Período não documentado'
  if (from && to && from === to) return formatDate(from, fromPrecision)
  const a = from ? formatDate(from, fromPrecision) : 'início não documentado'
  const b = to ? formatDate(to, toPrecision) : 'fim não documentado'
  return `${a} – ${b}`
}

export function yearOf(iso: string): number {
  return Number(iso.slice(0, 4))
}
