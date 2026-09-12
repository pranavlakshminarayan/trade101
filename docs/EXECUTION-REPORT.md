# Trade101 — Execution Report & Testing Guide

**What this is:** everything built in the session of 2026-09-11, what to test, and
what I could *not* verify here. Written so you can sit down cold and check the work.

**Branch:** `claude/trading-idea-handover-dfe84a`
**Tests:** 128 backend (`pytest -q`) + 11 frontend (`npm test`), ~7s total, no network required.

---

## The one thing to read first

**I could not test any of this against live market data.** This session ran in a
cloud container whose egress proxy blocks Yahoo Finance, Finnhub and SEC EDGAR.
Every test uses stubbed data.

So: the logic, the maths, the degradation paths and the wording guarantees are
verified. **The live provider integrations are not.** That is the first thing to
check when you run it, and it is why the testing plan below starts there.

---

## What was built, phase by phase

The external review (ChatGPT + Gemini) reordered the roadmap: trust and coherence
first, features after. I followed that ordering. Each phase was built, tested and
committed separately — six commits, each with its own tests passing before the next
began.

### Phase 1.5 — Trust & coherence  (commits `0e435ad`, `c03c271`, `b0ee8b4`)

The evidence pipeline, which is the backbone everything else hangs off.

| Built | Why |
|---|---|
| `services/evidence.py` — relevance filter + citation verifier | Two deterministic gates around the *single* analysis call. Before: only headlines actually about this company reach the model. After: every claim must resolve to something we supplied, or it is withheld. |
| Claim-level citations | Each AI claim renders its source — news and filings link out, indicators show the exact value they rest on. |
| `services/cache.py` | One TTL cache behind all provider calls, per-kind lifetimes, entries carry their fetch time. `TRADE101_CACHE_URL` is the Redis seam. |
| Shared as-of spine | `marketdata.freshness()` + `components/AsOf.jsx`. Chart, metrics, patterns and AI read render the same timestamp from the same object. |
| Stale vs. closed | A closed market and a broken feed look identical on a chart. They are now named differently. |
| Graceful degradation | Provider outage → **503 with a retry**, not a 500 stack trace. Unknown ticker stays a non-retryable 404. |
| Per-purpose spend ledger | `GET /usage` — see the section below. |
| SQLite storage | The `services/storage.py` the original plan called for at M4 but never got built. |

### Phase 2 — Learning engine  (commit `923d90e`)

| Built | Why |
|---|---|
| **Guided Study** — observe → predict → reveal → challenge → revisit | Your read is saved **before** the AI's is rendered. Once you've read a confident paragraph you can't un-read it. |
| **Retrospective replay** | A hidden window of the stock's own history. `setup` and `reveal` are separate endpoints so the future is never in the browser. |
| **Learning journal** | Hypothesis + evidence, not trades. Saving a lean with no reasoning is a 400. |
| **Fundamentals** | Earnings/surprise, revenue, margins, cash flow, valuation, filing links. |

### Phase 2.5 — Style lenses  (commit `5718aca`)

Five lenses — trend, swing, mean-reversion, long-term, event-driven — each declaring
what it weighs, **what it's blind to**, evidence in this data against its own reading,
and how it fails. Entirely deterministic: costs nothing, can't hallucinate.

No day-trading lens, and the panel says why.

### Phase 3 — Research workspace  (commit `cda4ee2`)

Comparison (rebased to 100, **no ranking**), watchlist (alerts as information events),
practice lab (hypothetical, behind its own tab), light mode + accessibility.

### Phase 4 — Ecosystem graph  (commit `f0e7aa5`)

Typed edges with source, confidence and materiality. Fund holdings at high confidence
with real weights; peers at *low* confidence, labelled a sector grouping.
Supplier/customer/partner/investor are **left empty and said to be empty** — we have no
licensed source, and "no source" is reported rather than "none exist".

---

## Your API keys — what changed and why

You asked for separate keys to track spend per use. The review pushed back
("do not add separate keys merely to improve sourcing"). Both are satisfied:

- **Nothing was removed.** `TRADE101_RESEARCH_KEY`, `TRADE101_ECOSYSTEM_KEY` and
  `TRADE101_ORCHESTRATOR_KEY` still work. Each falls back to
  `TRADE101_ANALYSIS_KEY` when unset, so **one key is a fully supported setup.**
- **`GET /usage` gives you the breakdown regardless.** Every Claude call is
  recorded against the *feature* that made it, plus tokens, cost and ticker.

  Separate keys are like separate credit cards — the Anthropic Console shows card
  statements. The ledger is an itemised receipt. One card, still itemised:

  ```
  TOTAL: 2 calls, $3.88
    analysis         1 call   $3.0000
    news_inference   1 call   $0.8800
  byKey: [('TRADE101_ANALYSIS_KEY', '$3.8800')]   ← the Console's view
  ```

Pricing is from the published Anthropic rates (Sonnet 5 $2/$10 per MTok), captured
2026-06-24. A model with no known rate is **counted but never priced** — same
"never fabricate a number" rule as the rest of the app.

---

## How to run it

```bash
# backend (from backend/)
.venv/Scripts/python.exe -m uvicorn app:app --reload --port 8000

# frontend (from frontend/)
npm.cmd run dev
```

Open http://127.0.0.1:5173.

```bash
cd backend && .venv/Scripts/python.exe -m pytest -q   # 128 backend tests
cd frontend && npm.cmd test                           # 11 frontend tests
```

**Before the first run:**
- `pip install -r requirements.txt` — no new Python packages, but the venv here was rebuilt.
- `npm.cmd install` — **new dev dependencies** for the frontend tests (vitest, jsdom,
  @testing-library/react + user-event + jest-dom). Dev-only; they do not ship in the build.

---

## Seeing it without live data

This container cannot reach Yahoo/Finnhub/SEC, so I stubbed the providers and drove
the real UI with a headless browser. Both tools are committed, so you can do the same
— useful for checking a UI change without spending a Claude key or waiting on markets:

```bash
# terminal 1 — the real backend, providers stubbed with fixture data
cd backend && .venv/Scripts/python.exe tools/stub_server.py

# terminal 2
cd frontend && npm.cmd run dev

# terminal 3 — drives the app and writes frontend/screenshots/
cd frontend && npx playwright install chromium   # first time only
node scripts/screenshot.mjs
```

`tools/stub_server.py` stubs **only** the outbound providers — the endpoints, evidence
gates, lenses and freshness logic are all the real code path. Its fixture deliberately
includes two irrelevant headlines (a Ford recall, a multi-stock round-up) and one
un-sourceable claim, so you can watch the relevance filter drop 2 of 4 and the citation
verifier withhold 1 of 5.

---

## Testing plan — in priority order

### 🔴 Priority 1 — the live integrations I could not verify

Everything below was written against stubs. **Test these first.**

1. **`/research/NVDA`** — does real Yahoo data still flow? I changed
   `marketdata.get()` to wrap fetches in `ProviderError`, and added
   `get_with_meta()`. If anything broke in the market-data path, this is where.
2. **`/fundamentals/NVDA`** — **most likely to need adjustment.** I'm reading
   `t.income_stmt`, `t.cashflow` and `t.earnings_dates` and matching row labels
   (`Total Revenue`, `Net Income`, `Free Cash Flow`…). Yahoo's exact row names
   vary. If a figure shows "not reported" that you know exists, the label list in
   `services/fundamentals.py` needs a new entry. **Check a non-US symbol too**
   (`RELIANCE.NS`, `005930.KS`) — coverage is patchy and should degrade, not crash.
3. **`/graph/SPY`** — ETF holdings via `funds_data.top_holdings`. Do real weights
   appear, and do they look right? Then `/graph/NVDA` — peers should show as
   *low confidence*, and the "not shown" block should list supplier/customer.
4. **`/lenses/NVDA`** — the long-term lens needs real fundamentals. Does it read
   "unknown" when it shouldn't?
5. **`/analyze/NVDA`** — ⚠️ **this spends your Claude key.** Test it *once*. Check:
   does each evidence point carry a citation chip? Does anything appear under
   "claims withheld"? If lots of claims are withheld, the model isn't using
   catalog ids and the prompt needs tuning.

### 🟠 Priority 2 — the learning flows

6. **The curtain.** Open any stock. The AI read should be collapsed, the header
   strip should show **no lean chip**, and the News panel should open on **Feed**.
   Click "Reveal Trade101's read" — everything appears, including the lean chip.
   Then search a different stock: it must be collapsed again.
7. **Guided Study** (◎ button, or "Walk me through it first" on the curtain). Walk
   all five steps. The critical check: **is the AI's read genuinely hidden until
   after you commit?** Then open the Journal — your entry should be there with your
   lean *and* the AI's recorded separately.
8. **Replay** (⟲ button). Check the chart shows no future bars before you commit.
   Open devtools → Network: the `/replay/NVDA` response must contain **no**
   `outcome` key. Commit a read, reveal, confirm the one-sample caveat appears.
   Hit "Different window" — the cut should move.
9. **Journal** — add a reflection, reload, confirm it persists.

### 🟡 Priority 3 — the workspace

10. **Comparison** — add two companies with very different price levels
   (e.g. NVDA and a ₹ stock). Both lines must start at 100. Check the
   comparability warnings fire for different sectors/currencies.
11. **Watchlist** — add a level just above the current price, then one just below.
    Reload. Does the crossing event appear, and is the wording neutral?
12. **Practice lab** — open a position, confirm every figure says "hypothetical".
13. **Light mode** — the switch cycles System → Light → Dark. Check every screen in
    light mode; I built the palette but never saw it rendered.
14. **Keyboard** — Tab through a research page. Every control should show a focus
    ring. Try the skip link (Tab from page load on the welcome screen).
15. **Phone width** — resize to ~400px.

### 🟢 Priority 4 — the failure states

16. **Kill the backend**, then search. You should get the exact uvicorn command
    and a "Try again" button.
17. **Bad ticker** (`ZZZZZZ`) — a 404 with no retry button.
18. **Unplug the network**, then search — a 503 with a retry button, *not* a
    stack trace.

---

## Audit against the review's own Definition of Done

The review defined done for a "Trust & Learning" release as six things a learner
should be able to do. Checked honestly:

| # | Definition of Done | Status | Where |
|---|---|---|---|
| 1 | See exactly what timeframe and data timestamp every conclusion refers to | ✅ | `AsOf.jsx` renders from one shared `meta`; an integration test asserts chart, patterns and lenses agree |
| 2 | See only relevant company, sector, supply-chain or macro evidence | ✅ | `evidence.select()` — and it shows you what it dropped, and why |
| 3 | Open a citation and understand why it supports a displayed statement | ✅ | Every claim renders resolved citations; indicators show the exact value they rest on |
| 4 | See uncertainty when source coverage is poor | ✅ | `Coverage.jsx` — ok / thin / none, with the confidence instruction spelled out |
| 5 | **Form their own interpretation before seeing the AI synthesis** | ✅ | The AI read is **collapsed behind a reveal on every stock**. Guided Study is the stronger opt-in path. |
| 6 | Leave with a saved learning note, not a trading instruction | ✅ | Journal stores hypothesis + evidence; a lean with no reasoning is rejected |

### On item 5 — how the curtain works

Pranav chose option 2, and it shipped. Every stock now opens with the AI momentum read
collapsed, offering two ways forward: **"Walk me through it first"** (Guided Study, the
stronger path) or **"Reveal Trade101's read"** (one click).

Two things leak the synthesis if you only collapse the obvious panel, and both are closed:

- **The header strip** rendered the AI's lean chip — the conclusion, in three words,
  above the fold. Now hidden until reveal.
- **The News panel** opened on its "What it means" tab, which is AI inference rather
  than news. It now opens on the **Feed** — raw sourced headlines. Evidence is free;
  synthesis costs a deliberate click, and the inference tab says plainly that it is
  Trade101's reading rather than the news.

What stays visible behind the curtain, deliberately: the **as-of timestamp** and the
**source coverage**. Neither is a conclusion, and both are what you need to calibrate
*before* deciding how much to trust anything — hiding them would make the exercise
harder rather than more honest.

The copy matters here too. The curtain says the read is ready and that *"nothing is
being withheld from you — this is only about the order you see things in, which is the
one thing you cannot undo."* A locked-door treatment would read as the app
withholding, which it isn't.

Reset behaviour: the curtain re-closes on every new stock, and on every re-fetch of the
analysis. It does not remember that you revealed the last one.

---

## Known gaps and honest limits

- **Live data untested** (above). This is the big one.
- **`Ecosystem.jsx` and `Graph.jsx` both render.** The old peer panel is still
  there alongside the new sourced graph. I left it so you can compare them —
  tell me and I'll remove the old one.
- **No relationship data source.** Supplier/customer edges need a licensed
  dataset. `TRADE101_RELATIONSHIP_PROVIDER` is the slot; it's `none` today and
  the UI says so.
- **Practice lab is deliberately minimal.** The review called it optional and
  warned against making it prominent. It's behind its own tab with the
  disclaimer leading.
- **Frontend tests now exist, but only for the curtain.** Vitest + React Testing
  Library are set up (`npm test`), with 11 tests covering the reveal invariant and
  the news-panel default — the one frontend behaviour where a regression would be
  invisible, since the panel would simply look normal. The other 20-odd components
  are still verified only by a clean production build.
- **`/analyze` still uses one bounded call**, per the review. The other named
  keys are wired but unused until more agents exist — deliberately.

---

## Bugs found and fixed along the way

Worth knowing these existed, because two were silent:

1. **MACD and Bollinger were uncitable.** `evidence.build_catalog()` skipped
   dict-valued indicators, so the model had no id for them — any claim about MACD
   was being *dropped by the verifier* as untraceable. Nested values now flatten
   to `ind:macd.signal`.
2. **`watchlist.last_seen` was declared TEXT** while storing a price. SQLite type
   affinity coerced it to a string, so every level-crossing comparison would have
   raised a `TypeError` at runtime. Now `REAL`, with defensive coercion.
3. **StudyMode's MACD prompt never appeared** — destructured flat from a nested object.
4. **A provider outage returned a 500 stack trace.** Now a 503 that explains itself.
5. **Light mode failed contrast in eight places.** Found by rendering the app, not by
   any test: I had hardcoded dark-theme text colours (`#BFD6E2`, `#AFC4D2`, …) instead
   of theme tokens, so the not-advice notice and several panels were near-illegible
   pale-on-pale in light mode. All now use `var(--ink)` / `var(--muted)` / `var(--amber)`
   and follow the theme. This is exactly what a production build cannot catch.
6. Dead `<a href="#">` reference link; `datetime.utcnow()` deprecation; two stale
   module docstrings.

**Still open (cosmetic):** there is no `favicon.ico`, so every page load logs one 404 in
the browser console. It belongs with the "real logo" backlog item.

---

## Where things live

```
backend/services/
  evidence.py       relevance filter + citation verifier   ← the trust backbone
  lenses.py         the five style lenses (deterministic)
  relationships.py  typed ecosystem graph
  fundamentals.py   statements, earnings, valuation
  replay.py         hidden-window exercise
  compare.py        rebased multi-company comparison
  watchlist.py      information events, never prompts
  usage.py          per-purpose spend ledger
  storage.py        SQLite: history, journal, watchlist, practice, ledger
  cache.py          TTL cache behind every provider call

frontend/src/components/
  AsOf.jsx  Coverage.jsx  Lenses.jsx  StudyMode.jsx  Replay.jsx
  Journal.jsx  Fundamentals.jsx  Compare.jsx  Watchlist.jsx  Practice.jsx  Graph.jsx
```

New endpoints: `/usage` `/history` `/cache` `/fundamentals` `/replay` `/replay/reveal`
`/journal` `/lenses` `/compare` `/watchlist` `/practice` `/graph`

---

## The guardrails, still intact

Every phase was built against these, and there are tests enforcing them:

- Numbers are exact — deterministic code, never model output.
- Every AI claim resolves to real evidence, or it is withheld and shown as withheld.
- No buy/sell/hold anywhere — an integration test scans every learner-facing
  endpoint for advice language.
- Comparison produces no ranking — a test scans for ranking vocabulary.
- Watchlist alerts are information, never prompts — a test scans for prompting words.
- Absent data is reported as absent, never inferred.
