import { describe, it, expect, beforeEach } from 'vitest'
import { getHistory, addHistory, clearHistory, timeAgo } from './history.js'

describe('history', () => {
  beforeEach(() => localStorage.clear())

  it('starts empty', () => {
    expect(getHistory()).toEqual([])
  })

  it('adds an entry to the front, stamped with `when`', () => {
    const next = addHistory({ ticker: 'AAPL', name: 'Apple Inc.', lean: 'bullish', summary: 'x' })
    expect(next).toHaveLength(1)
    expect(next[0].ticker).toBe('AAPL')
    expect(typeof next[0].when).toBe('number')
  })

  it('re-researching the same ticker moves it to the front instead of duplicating', () => {
    addHistory({ ticker: 'AAPL', name: 'Apple Inc.' })
    addHistory({ ticker: 'NVDA', name: 'NVIDIA Corp' })
    const next = addHistory({ ticker: 'AAPL', name: 'Apple Inc. (updated)' })
    expect(next).toHaveLength(2)
    expect(next[0].ticker).toBe('AAPL')
    expect(next[0].name).toBe('Apple Inc. (updated)')
  })

  it('caps history at 50 entries', () => {
    for (let i = 0; i < 55; i++) addHistory({ ticker: `T${i}` })
    expect(getHistory()).toHaveLength(50)
  })

  it('clearHistory empties the list', () => {
    addHistory({ ticker: 'AAPL' })
    clearHistory()
    expect(getHistory()).toEqual([])
  })

  it('degrades to an empty list if localStorage holds invalid JSON', () => {
    localStorage.setItem('trade101_history', 'not json')
    expect(getHistory()).toEqual([])
  })
})

describe('timeAgo', () => {
  it('formats recent timestamps in relative units', () => {
    const now = Date.now()
    expect(timeAgo(now)).toBe('just now')
    expect(timeAgo(now - 5 * 60 * 1000)).toBe('5m ago')
    expect(timeAgo(now - 3 * 60 * 60 * 1000)).toBe('3h ago')
    expect(timeAgo(now - 2 * 24 * 60 * 60 * 1000)).toBe('2d ago')
  })

  it('falls back to a calendar date once a week has passed', () => {
    const weekAgo = Date.now() - 10 * 24 * 60 * 60 * 1000
    expect(timeAgo(weekAgo)).toBe(new Date(weekAgo).toLocaleDateString())
  })
})
