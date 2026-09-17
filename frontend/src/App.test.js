import { describe, it, expect } from 'vitest'
import { looksLikeTicker, routeHash, parseRoute } from './App.jsx'

describe('looksLikeTicker (docs/AUDIT.md H1)', () => {
  it('accepts a genuinely ticker-shaped query: all-caps, no spaces', () => {
    expect(looksLikeTicker('AAPL')).toBe(true)
    expect(looksLikeTicker('7974.T')).toBe(true)
    expect(looksLikeTicker('005930.KS')).toBe(true)
  })

  it('rejects a company name, even one with no spaces, because it is not all-caps', () => {
    expect(looksLikeTicker('sony')).toBe(false)
    expect(looksLikeTicker('Toyota')).toBe(false)
  })

  it('rejects a multi-word company name even if capitalized', () => {
    expect(looksLikeTicker('Toyota Motor')).toBe(false)
  })

  it('rejects a query with no letters at all (not a real ticker shape)', () => {
    expect(looksLikeTicker('12345')).toBe(false)
  })

  // The actual regression this exists for: "Sony" (searched however the user
  // types it) must NOT silently auto-pick the NYSE ADR just because that ADR's
  // own ticker happens to spell "SONY" - only an EXPLICITLY typed, all-caps,
  // space-free query should skip the disambiguation picker.
  it('a lowercase company name whose ticker happens to equal the word does not look like a ticker', () => {
    expect(looksLikeTicker('sony')).toBe(false)
    expect(looksLikeTicker('Sony')).toBe(false)
  })
})

describe('routeHash', () => {
  it('a ticker route takes priority and is URL-encoded', () => {
    expect(routeHash({ ticker: 'AAPL' })).toBe('#AAPL')
    expect(routeHash({ ticker: '7974.T' })).toBe('#7974.T')
  })

  it('a non-home view with no ticker gets its own #/view route', () => {
    expect(routeHash({ view: 'watchlist' })).toBe('#/watchlist')
    expect(routeHash({ view: 'compare' })).toBe('#/compare')
  })

  it('home with no ticker is just "#"', () => {
    expect(routeHash({ view: 'home' })).toBe('#')
    expect(routeHash({})).toBe('#')
  })
})

describe('parseRoute', () => {
  const setHash = (h) => { window.location.hash = h }

  it('parses a bare ticker hash', () => {
    setHash('#AAPL')
    expect(parseRoute()).toEqual({ view: 'home', ticker: 'AAPL' })
  })

  it('parses a /view hash with no ticker', () => {
    setHash('#/watchlist')
    expect(parseRoute()).toEqual({ view: 'watchlist', ticker: null })
  })

  it('an empty hash means home with no ticker', () => {
    setHash('')
    expect(parseRoute()).toEqual({ view: 'home', ticker: null })
  })

  it('round-trips through routeHash for a ticker', () => {
    setHash(routeHash({ ticker: '005930.KS' }))
    expect(parseRoute()).toEqual({ view: 'home', ticker: '005930.KS' })
  })
})
