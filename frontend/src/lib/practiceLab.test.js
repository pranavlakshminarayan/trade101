import { describe, it, expect, beforeEach } from 'vitest'
import { getPortfolio, resetPortfolio, buy, sell, STARTING_CASH } from './practiceLab.js'

describe('practiceLab', () => {
  beforeEach(() => localStorage.clear())

  it('starts with STARTING_CASH and no positions', () => {
    const p = getPortfolio()
    expect(p.cash).toBe(STARTING_CASH)
    expect(p.positions).toEqual({})
    expect(p.closed).toEqual([])
  })

  it('buy() deducts exact cost and opens a position at that price', () => {
    const res = buy({ ticker: 'aapl', name: 'Apple Inc.', qty: 10, price: 150 })
    expect(res.ok).toBe(true)
    expect(res.state.cash).toBe(STARTING_CASH - 1500)
    expect(res.state.positions.AAPL).toMatchObject({ ticker: 'AAPL', qty: 10, avgCost: 150 })
  })

  it('buy() rejects a trade costing more than available cash', () => {
    const res = buy({ ticker: 'AAPL', qty: 1_000_000, price: 150 })
    expect(res.ok).toBe(false)
    expect(res.error).toMatch(/more than your/)
  })

  it('buy() rejects an invalid quantity', () => {
    expect(buy({ ticker: 'AAPL', qty: 0, price: 150 }).ok).toBe(false)
    expect(buy({ ticker: 'AAPL', qty: -5, price: 150 }).ok).toBe(false)
  })

  it('a second buy averages the cost basis correctly', () => {
    buy({ ticker: 'AAPL', qty: 10, price: 100 })   // cost 1000
    const res = buy({ ticker: 'AAPL', qty: 10, price: 200 })  // cost 2000
    // (1000 + 2000) / 20 = 150
    expect(res.state.positions.AAPL.qty).toBe(20)
    expect(res.state.positions.AAPL.avgCost).toBe(150)
  })

  it('sell() realizes P&L against average cost and credits proceeds exactly', () => {
    buy({ ticker: 'AAPL', qty: 10, price: 100 })
    const res = sell({ ticker: 'AAPL', qty: 5, price: 120 })
    expect(res.ok).toBe(true)
    // sold 5 @ 120 = 600 proceeds, cost basis 5*100=500, P&L = 100
    expect(res.state.cash).toBe(STARTING_CASH - 1000 + 600)
    expect(res.state.positions.AAPL.qty).toBe(5)
    const journal = res.state.closed[0]
    expect(journal.realizedPnl).toBe(100)
    expect(journal.realizedPct).toBeCloseTo(20)
  })

  it('selling the entire position closes it out (removes the position entry)', () => {
    buy({ ticker: 'AAPL', qty: 10, price: 100 })
    const res = sell({ ticker: 'AAPL', qty: 10, price: 110 })
    expect(res.state.positions.AAPL).toBeUndefined()
  })

  it('sell() rejects selling more than is held', () => {
    buy({ ticker: 'AAPL', qty: 5, price: 100 })
    const res = sell({ ticker: 'AAPL', qty: 10, price: 100 })
    expect(res.ok).toBe(false)
    expect(res.error).toMatch(/only hold/)
  })

  it('sell() rejects a ticker with no open position', () => {
    const res = sell({ ticker: 'MSFT', qty: 1, price: 100 })
    expect(res.ok).toBe(false)
    expect(res.error).toMatch(/don't hold/)
  })

  it('resetPortfolio wipes back to the starting state', () => {
    buy({ ticker: 'AAPL', qty: 10, price: 100 })
    const state = resetPortfolio()
    expect(state.cash).toBe(STARTING_CASH)
    expect(state.positions).toEqual({})
  })
})
