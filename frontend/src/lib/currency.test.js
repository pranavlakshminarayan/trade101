import { describe, it, expect } from 'vitest'
import { currencySymbol } from './currency.js'

describe('currencySymbol', () => {
  it('maps known currency codes to their display symbol', () => {
    expect(currencySymbol('USD')).toBe('$')
    expect(currencySymbol('JPY')).toBe('¥')
    expect(currencySymbol('INR')).toBe('₹')
    expect(currencySymbol('EUR')).toBe('€')
    expect(currencySymbol('HKD')).toBe('HK$')
  })

  it('falls back to the currency code itself for an unmapped currency, never blank', () => {
    expect(currencySymbol('AED')).toBe('AED ')
  })

  it('returns an empty string for a missing/falsy code rather than "undefined"', () => {
    expect(currencySymbol(null)).toBe('')
    expect(currencySymbol(undefined)).toBe('')
    expect(currencySymbol('')).toBe('')
  })
})
