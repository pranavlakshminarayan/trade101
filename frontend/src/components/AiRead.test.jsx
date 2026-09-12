import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import AiRead from './AiRead.jsx'

// The curtain invariant: the AI's synthesis must not reach the screen until the
// learner asks for it. This is the one frontend behaviour where a regression
// would be invisible — the panel would simply look normal — so it is tested.

const AI = {
  available: true,
  asOf: '2026-09-11T00:00:00',
  timeframe: '1y',
  coverage: { level: 'ok', news: 4, filings: 2, note: '4 relevant article(s) informed this read.' },
  evidenceFilter: { considered: 9, kept: 4, dropped: 5, droppedExamples: [] },
  momentum: {
    lean: 'bullish',
    confidence: 'moderate',
    summary: 'THE_SYNTHESIS_SENTENCE — price is holding above both averages.',
    evidence: [{ point: 'RSI is mid-range', source: 'ind:rsi14',
                 citations: [{ id: 'ind:rsi14', kind: 'indicator', label: 'rsi14', detail: 'rsi14 = 56.2' }] }],
  },
  learning_note: 'A note that teaches the read.',
  meta: { unsupportedClaims: [] },
}

const META = { asOf: '2026-09-11T00:00:00', period: '1y', delayed: true }

describe('AiRead curtain', () => {
  it('hides the lean, the confidence and the summary before reveal', () => {
    render(<AiRead ai={AI} loading={false} meta={META} revealed={false}
                   onReveal={() => {}} onStudy={() => {}} />)

    expect(screen.queryByText(/THE_SYNTHESIS_SENTENCE/)).not.toBeInTheDocument()
    expect(screen.queryByText('bullish')).not.toBeInTheDocument()
    expect(screen.queryByText(/confidence: moderate/)).not.toBeInTheDocument()
    expect(screen.queryByText(/RSI is mid-range/)).not.toBeInTheDocument()
  })

  it('still shows the as-of and the source coverage, which are not synthesis', () => {
    render(<AiRead ai={AI} loading={false} meta={META} revealed={false}
                   onReveal={() => {}} onStudy={() => {}} />)

    // Calibrating on evidence quality is what the learner needs BEFORE deciding.
    expect(screen.getByText(/Sourced/)).toBeInTheDocument()
    expect(screen.getByText(/4 relevant article/)).toBeInTheDocument()
    expect(screen.getByText(/as of/)).toBeInTheDocument()
  })

  it('says the read is ready rather than implying it is withheld', () => {
    render(<AiRead ai={AI} loading={false} meta={META} revealed={false}
                   onReveal={() => {}} onStudy={() => {}} />)
    expect(screen.getByText(/nothing is being withheld from you/)).toBeInTheDocument()
  })

  it('offers both the reveal and the stronger study path', async () => {
    const onReveal = vi.fn()
    const onStudy = vi.fn()
    render(<AiRead ai={AI} loading={false} meta={META} revealed={false}
                   onReveal={onReveal} onStudy={onStudy} />)

    await userEvent.click(screen.getByRole('button', { name: /Reveal Trade101's read/ }))
    expect(onReveal).toHaveBeenCalledOnce()

    await userEvent.click(screen.getByRole('button', { name: /Walk me through it first/ }))
    expect(onStudy).toHaveBeenCalledOnce()
  })

  it('shows the full read, its citations and the not-advice notice once revealed', () => {
    render(<AiRead ai={AI} loading={false} meta={META} revealed={true}
                   onReveal={() => {}} onStudy={() => {}} />)

    expect(screen.getByText(/THE_SYNTHESIS_SENTENCE/)).toBeInTheDocument()
    expect(screen.getByText('bullish')).toBeInTheDocument()
    expect(screen.getByText(/confidence: moderate/)).toBeInTheDocument()
    expect(screen.getByText(/RSI is mid-range/)).toBeInTheDocument()
    expect(screen.getByText(/rsi14 = 56.2/)).toBeInTheDocument()
    expect(screen.getByText(/it is not advice/)).toBeInTheDocument()
    expect(screen.queryByText(/Reveal Trade101's read/)).not.toBeInTheDocument()
  })

  it('shows withheld claims once revealed, rather than dropping them silently', () => {
    const ai = { ...AI, meta: { unsupportedClaims: [
      { point: 'A bank raised targets', reason: "cites 'Bloomberg terminal', which was not in the evidence supplied" },
    ] } }
    render(<AiRead ai={ai} loading={false} meta={META} revealed={true}
                   onReveal={() => {}} onStudy={() => {}} />)
    expect(screen.getByText(/1 claim withheld/)).toBeInTheDocument()
  })

  it('an unavailable read says the deterministic panels are unaffected', () => {
    render(<AiRead ai={{ available: false, reason: 'No key set.' }} loading={false}
                   meta={META} revealed={false} onReveal={() => {}} onStudy={() => {}} />)
    expect(screen.getByText(/No key set./)).toBeInTheDocument()
    expect(screen.getByText(/remain exact/)).toBeInTheDocument()
  })
})
