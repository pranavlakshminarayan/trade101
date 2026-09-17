import { describe, it, expect, beforeEach } from 'vitest'
import { getWatchlist, isWatched, addWatch, removeWatch, toggleWatch } from './watchlist.js'

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
