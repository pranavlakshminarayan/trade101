import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Metrics from './Metrics.jsx'

const IND = {
  price: 150, rsi14: 65.4, sma50: 148, sma200: null,
  above_sma50: true, above_sma200: null,
  macd: { macd: 1.2, signal: 0.9, hist: 0.3 },
  bollinger: { upper: 155, middle: 150, lower: 145 },
  volume_vs_20d_pct: 12.5,
}

describe('<Metrics>', () => {
  it('renders all six metric tiles with their exact values', () => {
    render(<Metrics indicators={IND} ticker="AAPL" />)
    expect(screen.getByText('RSI (14)')).toBeInTheDocument()
    expect(screen.getByText('65.4')).toBeInTheDocument()
    expect(screen.getByText('SMA 200')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()  // sma200 is null
  })

  it('clicking a metric opens its fact + lesson panel', () => {
    render(<Metrics indicators={IND} ticker="AAPL" />)
    fireEvent.click(screen.getByText('RSI (14)'))
    expect(screen.getByText(/RSI\(14\) is 65.4/)).toBeInTheDocument()
  })

  it('clicking the same metric again closes the panel', () => {
    render(<Metrics indicators={IND} ticker="AAPL" />)
    const tile = screen.getByText('RSI (14)')
    fireEvent.click(tile)
    expect(screen.queryByText(/RSI\(14\) is 65.4/)).toBeInTheDocument()
    fireEvent.click(tile)
    expect(screen.queryByText(/RSI\(14\) is 65.4/)).not.toBeInTheDocument()
  })

  it('pressing Escape closes an open panel', () => {
    render(<Metrics indicators={IND} ticker="AAPL" />)
    fireEvent.click(screen.getByText('SMA 50'))
    expect(screen.getByText(/above the 50-day average/)).toBeInTheDocument()
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.queryByText(/above the 50-day average/)).not.toBeInTheDocument()
  })

  it('never shows "below" for a null (unavailable) SMA200 - docs/AUDIT.md C2 guardrail', () => {
    render(<Metrics indicators={IND} ticker="AAPL" />)
    fireEvent.click(screen.getByText('SMA 200'))
    expect(screen.getByText(/not enough history/i)).toBeInTheDocument()
  })
})
