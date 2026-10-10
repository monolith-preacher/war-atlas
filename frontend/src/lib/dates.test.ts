import { describe, expect, it } from 'vitest'
import { addDays, addMonths, clamp, daysBetween, formatDate, formatRange, isValidISO, step } from './dates'

describe('dates', () => {
  it('adds days across month and year boundaries', () => {
    expect(addDays('1916-06-30', 1)).toBe('1916-07-01')
    expect(addDays('1944-12-31', 1)).toBe('1945-01-01')
    expect(addDays('1916-03-01', -1)).toBe('1916-02-29') // leap year
  })
  it('adds months clamping to month end', () => {
    expect(addMonths('1944-01-31', 1)).toBe('1944-02-29')
    expect(step('1916-07-01', 'year', 1)).toBe('1917-07-01')
  })
  it('clamps to the conflict range', () => {
    expect(clamp('1913-01-01', '1914-07-28', '1918-11-11')).toBe('1914-07-28')
    expect(clamp('1919-01-01', '1914-07-28', '1918-11-11')).toBe('1918-11-11')
  })
  it('counts days', () => {
    expect(daysBetween('1944-06-06', '1944-08-30')).toBe(85)
  })
  it('formats honouring precision', () => {
    expect(formatDate('1916-07-01')).toBe('1 jul 1916')
    expect(formatDate('1916-01-01', 'year')).toBe('1916')
    expect(formatDate('1914-09-01', 'month')).toBe('set 1914')
    expect(formatRange(null, null)).toBe('Período não documentado')
    expect(formatRange('1916-07-01', null)).toBe('1 jul 1916 – fim não documentado')
  })
  it('validates ISO dates', () => {
    expect(isValidISO('1916-02-30')).toBe(false)
    expect(isValidISO('1916-02-29')).toBe(true)
  })
})
