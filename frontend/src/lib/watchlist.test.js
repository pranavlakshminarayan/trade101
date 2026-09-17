import { describe, it, expect, beforeEach } from 'vitest'
import { getWatchlist, isWatched, addWatch, removeWatch, toggleWatch, setNote } from './watchlist.js'

describe('watchlist', () => {
  beforeEach(() => localStorage.clear())

  it('starts empty and unwatched', () => {
    expect(getWatchlist()).toEqual([])
    expect(isWatched('AAPL')).toBe(false)
  })

  it('addWatch adds a ticker, case-insensitively checkable', () => {
    addWatch({ ticker: 'AAPL', name: 'Apple Inc.' })
    expect(isWatched('aapl')).toBe(true)
    expect(isWatched('AAPL')).toBe(true)
  })

  it('adding the same ticker twice does not duplicate it', () => {
    addWatch({ ticker: 'AAPL', name: 'Apple Inc.' })
    addWatch({ ticker: 'AAPL', name: 'Apple Inc.' })
    expect(getWatchlist()).toHaveLength(1)
  })

  it('removeWatch drops a ticker', () => {
    addWatch({ ticker: 'AAPL' })
    removeWatch('AAPL')
    expect(isWatched('AAPL')).toBe(false)
  })

  it('toggleWatch adds when unwatched, removes when watched', () => {
    toggleWatch({ ticker: 'NVDA' })
    expect(isWatched('NVDA')).toBe(true)
    toggleWatch({ ticker: 'NVDA' })
    expect(isWatched('NVDA')).toBe(false)
  })

  it('caps the list at 60 entries', () => {
    for (let i = 0; i < 65; i++) addWatch({ ticker: `T${i}` })
    expect(getWatchlist()).toHaveLength(60)
  })
})

describe('watchlist notes (docs/AUDIT.md §9)', () => {
  beforeEach(() => localStorage.clear())

  it('a fresh watch starts with an empty note', () => {
    addWatch({ ticker: 'AAPL' })
    expect(getWatchlist()[0].note).toBe('')
  })

  it('setNote attaches a study note to the right entry only', () => {
    addWatch({ ticker: 'AAPL' })
    addWatch({ ticker: 'NVDA' })
    setNote('AAPL', 'Watching for a pullback to the 50-day.')
    const list = getWatchlist()
    expect(list.find((e) => e.ticker === 'AAPL').note).toBe('Watching for a pullback to the 50-day.')
    expect(list.find((e) => e.ticker === 'NVDA').note).toBe('')
  })

  it('calling addWatch again for an already-tracked ticker does not wipe its note', () => {
    addWatch({ ticker: 'AAPL' })
    setNote('AAPL', 'Studying the earnings reaction.')
    addWatch({ ticker: 'AAPL', name: 'Apple Inc. (refreshed)' })
    expect(getWatchlist()[0].note).toBe('Studying the earnings reaction.')
  })

  it('removing a ticker and re-watching it starts with a blank note (the old one is gone)', () => {
    addWatch({ ticker: 'AAPL' })
    setNote('AAPL', 'Studying the earnings reaction.')
    removeWatch('AAPL')
    addWatch({ ticker: 'AAPL' })
    expect(getWatchlist()[0].note).toBe('')
  })
})
