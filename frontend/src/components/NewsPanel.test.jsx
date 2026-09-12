import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import NewsPanel from './NewsPanel.jsx'

// The news panel is the OTHER place the AI's synthesis could slip past the
// curtain: "What it means" is inference, not news. So the panel opens on the
// sourced headlines, and the inference costs a deliberate click.

const AI = {
  available: true,
  coverage: { level: 'ok', news: 2, filings: 1, note: '2 relevant article(s).' },
  evidenceFilter: { considered: 6, kept: 2, dropped: 4, droppedExamples: [] },
  news: {
    feed: [
      { headline: 'A_REAL_HEADLINE', source: 'Reuters', url: 'https://example.com/a',
        datetime: '2026-09-10', relevanceWhy: 'names the company; in the headline' },
    ],
    inference: { summary: 'THE_INFERENCE_TEXT about what this may mean.', claims: [] },
  },
}

describe('NewsPanel', () => {
  it('opens on the sourced feed, not on the AI inference', () => {
    render(<NewsPanel ai={AI} loading={false} ticker="NVDA" revealed={false} />)

    expect(screen.getByText('A_REAL_HEADLINE')).toBeInTheDocument()
    expect(screen.queryByText(/THE_INFERENCE_TEXT/)).not.toBeInTheDocument()
  })

  it('shows why each kept article survived the relevance filter', () => {
    render(<NewsPanel ai={AI} loading={false} ticker="NVDA" revealed={false} />)
    expect(screen.getByText(/names the company; in the headline/)).toBeInTheDocument()
  })

  it('reaches the inference on a deliberate click, flagged as inference', async () => {
    render(<NewsPanel ai={AI} loading={false} ticker="NVDA" revealed={false} />)

    await userEvent.click(screen.getByRole('button', { name: /What it means/ }))
    expect(screen.getByText(/THE_INFERENCE_TEXT/)).toBeInTheDocument()
    // ...and it says plainly that this is Trade101's reading, not the news.
    expect(screen.getByText(/not the news itself/)).toBeInTheDocument()
  })

  it('an empty feed after filtering says so, rather than implying no news exists', () => {
    const ai = { ...AI, news: { feed: [], note: null },
                 evidenceFilter: { considered: 7, kept: 0, dropped: 7, droppedExamples: [] } }
    render(<NewsPanel ai={ai} loading={false} ticker="NVDA" revealed={false} />)
    expect(screen.getByText(/Screened 7 recent headline/)).toBeInTheDocument()
    expect(screen.getByText(/none were specifically about NVDA/)).toBeInTheDocument()
  })
})
