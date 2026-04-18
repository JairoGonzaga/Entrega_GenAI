import { describe, expect, it } from 'vitest'
import { formatCurrency, formatDate, toNumberOrNull } from './utils'

describe('catalog utils', () => {
  it('converts numbers safely', () => {
    expect(toNumberOrNull('')).toBeNull()
    expect(toNumberOrNull('  ')).toBeNull()
    expect(toNumberOrNull('12.5')).toBe(12.5)
    expect(toNumberOrNull('abc')).toBeNull()
  })

  it('formats currency and date values', () => {
    expect(formatCurrency(null)).toBe('-')
    expect(formatCurrency(1500)).toContain('R$')
    expect(formatDate(null)).toBe('-')
    expect(formatDate('2026-04-14T00:00:00.000Z')).toMatch(/\d{2}\/\d{2}\/\d{4}/)
  })

})