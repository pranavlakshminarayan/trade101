import { describe, it, expect } from 'vitest'
import { metricValue, metricLabel, factFor, lessonFor, METRICS } from './lessons.js'

const IND = {
  price: 150, rsi14: 65.4321, sma50: 148.1, sma200: null,
  above_sma50: true, above_sma200: null,
  macd: { macd: 1.234, signal: 0.9, hist: 0.334 },
  bollinger: { upper: 155, middle: 150, lower: 145 },
  volume_vs_20d_pct: 12.5,
}

describe('metricValue', () => {
  it('returns the exact indicator value for each metric, never recomputing it', () => {
    expect(metricValue('RSI', IND)).toBe(65.4321)
    expect(metricValue('SMA50', IND)).toBe(148.1)
    expect(metricValue('Bollinger', IND)).toBe('mid 150')
    expect(metricValue('Volume', IND)).toBe('+12.5%')
  })

  it('renders a null/missing figure as "—", never as "null" or 0', () => {
    expect(metricValue('SMA200', IND)).toBe('—')
    expect(metricValue('SMA200', {})).toBe('—')
    expect(metricValue('MACD', {})).toBe('—')
  })

  it('prefixes a positive MACD/volume figure with "+" but not a negative one', () => {
    expect(metricValue('MACD', { macd: { macd: 1.5 } })).toBe('+1.5')
    expect(metricValue('MACD', { macd: { macd: -1.5 } })).toBe('-1.5')
    expect(metricValue('Volume', { volume_vs_20d_pct: -8 })).toBe('-8%')
  })

  it('METRICS lists exactly the six metrics the app supports', () => {
    expect(METRICS).toEqual(['RSI', 'MACD', 'SMA50', 'SMA200', 'Bollinger', 'Volume'])
  })
})

describe('metricLabel', () => {
  it('has a human label for every metric in METRICS', () => {
    for (const m of METRICS) expect(metricLabel(m)).toBeTruthy()
  })
})

describe('factFor', () => {
  it('never treats a null SMA200 as "below" (docs/AUDIT.md C2 guardrail)', () => {
    // above_sma200 is null (unknown), not false - factFor must say "not
    // available", never claim the price is below an average that doesn't exist.
    const fact = factFor('SMA200', IND, 'AAPL')
    expect(fact).toMatch(/not enough history/i)
    expect(fact).not.toMatch(/below/i)
  })

  it('states above/below correctly when the average IS available', () => {
    expect(factFor('SMA50', IND, 'AAPL')).toMatch(/above the 50-day average/)
    const belowInd = { ...IND, above_sma50: false }
    expect(factFor('SMA50', belowInd, 'AAPL')).toMatch(/below the 50-day average/)
  })

  it('labels RSI zones correctly at the boundaries', () => {
    expect(factFor('RSI', { rsi14: 70 }, 'X')).toMatch(/overbought/)
    expect(factFor('RSI', { rsi14: 30 }, 'X')).toMatch(/oversold/)
    expect(factFor('RSI', { rsi14: 50 }, 'X')).toMatch(/neutral/)
  })
})

describe('lessonFor', () => {
  it('returns non-empty teaching text for every metric', () => {
    for (const m of METRICS) expect(lessonFor(m, IND, 'AAPL').length).toBeGreaterThan(20)
  })
})
