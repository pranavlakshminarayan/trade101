# Trade101 — Backlog & Future Features

A running list so we don't lose ideas. Add freely; we pull from here after the MVP.

**North-star principle (applies to every phase):** Trade101 must **extract data and make sense of it** — interpret, connect, and *teach understanding* — not just display labels. Reading a number is something you could do by hand; the app's job is to help you *understand* what the data means, together.

---

## MVP (Phase 1) — in progress
- [x] M0 Scaffold · [x] M1 real-time core · [x] M2 frontend (welcome + research view + live chart + click-to-learn)
- [ ] **M3 AI narration** — momentum read + news Feed + "What it means" inference (sense-making, sourced). News via **Finnhub (free) + SEC EDGAR**.
- [ ] M4 patterns (magnifier) + ecosystem + index/beta + references + history
- [ ] M5 resilience + tests + the "surprise-ticker" true test

---

## Known bugs / debt from Phase 1

Found in a live end-to-end run on **7974.T (Nintendo, Tokyo)**, 2026-09-12.
Most cleared in the flaw pass on 2026-09-14 — detail in `docs/HANDOVER.md` §4.2.

- [x] **Finnhub API key leaked into the browser.** Fixed: `services/news.py` no longer returns
  raw exceptions (hardcoded friendly errors), and `services/safe.py::redact_secrets` scrubs any
  credential from anything reaching `/analyze`. Regression tests in `tests/test_safe.py`.
  **User action still required: rotate the Finnhub key** (assume the old one is compromised).
- [x] **Raw provider errors were user-facing copy** — replaced with plain explanations.
- [x] **Ecosystem thin outside the US showed a blank** — `services/company.py` returns a
  `coverage` map explaining missing beta/peers; the panel renders it.
- [x] **`datetime.utcnow()` deprecated** — now timezone-aware.
- [ ] **Non-US listings get no news** (Finnhub free tier 403s on non-US symbols). Now degrades
  with a plain message, but the news half stays US-only until the Firecrawl work below lands.

---

## Phase 1.5 — Trust and coherence (insert before Phase 2 depth work)

From a product/technical review, 2026-09-10 — full detail in
`docs/trade101-phase-2-recommendations.md`. Rationale: don't add more features/markets until
the existing single-stock read is demonstrably trustworthy end to end.

- [x] **Evidence relevance filter** — `services/evidence.py` classifies each article
  (company / related-peer / sector / irrelevant) by deterministic keyword matching and drops
  irrelevant ones *before* the AI call. Wired into `agents/orchestrator.py`; the feed, the
  references list, and the AI payload now contain only admitted evidence. (2026-09-14)
- [x] **Claim-level citations** — each momentum-evidence point now carries a
  Fact / Interpretation / Unknown `type` (enforced in `agents/analysis.py::_citation_guard`)
  rendered as a badge next to the claim in `AiRead.jsx`, alongside the existing `[source]`.
  When no company-specific news exists the agent must withhold a company-catalyst claim. (2026-09-14)
- [x] **Evidence tests** — `tests/test_evidence.py` feeds unrelated/peer/company articles and
  asserts irrelevant ones are dropped and `has_company_news` is reported honestly. (2026-09-14)
- [x] Confirm API keys stay backend-only — verified no `VITE_`/key refs in `frontend/src`, no
  frontend `.env`; combined with the `services/safe.py` leak fix. (2026-09-14)
- [ ] **Timeframe integrity** — one shared label (timeframe, bar interval, data timestamp,
  adjusted/unadjusted) across chart, metrics, patterns, and AI read; recompute indicators for
  the selected timeframe rather than always describing daily figures as if they were the
  active one.
- [ ] **Coverage-truthfulness badges** — per company, show supported/limited/unavailable for
  price, company news, filings, fundamentals, instead of implying every market is covered
  equally. (Backend `company.get_profile` already returns a `coverage` map — extend it.)
- [~] **Cache abstraction** — frontend session cache done (`api.js`: research/analyze/ecosystem/
  patterns; `/analyze` runs once per ticker per session, fixing tab-switch reloads + key waste).
  Backend-side caching (in-memory/SQLite for shared market bars/profiles/analysis) still to do.
- [ ] Visible "educational, not financial advice" notice near the momentum narrative itself,
  not only in the footer.

**Also shipped 2026-09-14 (user-reported fixes, see `docs/DEVELOPMENT-LOG.md`):**
- [x] Expanded pattern library (triangles/wedges/channels + reversals; only relevant shapes shown).
- [x] Non-US company name display (longName, not the ticker ID).
- [x] Non-US news via keyless Yahoo Finance fallback (Finnhub free tier is US-only) — this lands
  early part of the Phase 2 "non-US sourcing" goal without Firecrawl.
- [x] **Prompt caching on the Claude API** (`agents/llm.py`) — system prompt sent as a
  `cache_control` block; prefix expanded to ~1306 tok so it clears Sonnet 5's 1024 minimum and
  actually fires. Cuts repeated input cost across tickers/sessions.

---

## Phase 2 — depth
- **Deploy a shareable/public URL.** Currently local-only (`http://127.0.0.1:5173`); after the
  full execution, host the React frontend + FastAPI backend (e.g. Vercel + Render/Fly) so Pranav
  can check it from any device. Keep API keys backend-only.
- **Deeper search / scrape for non-US markets.** US data is easy/free (Wall Street sources, etc.); other countries (China, Japan, Korea, HK, Singapore, India) are harder → **Firecrawl or an alternative** to scrape/extract where clean APIs don't exist. Pluggable provider slot already designed for this.
- **Broader web sourcing** — add **Exa** (wide semantic search) and premium sources where accessible/legal (the WSJ / Bloomberg / JP Morgan / investment-bank-report depth). Always sourced.
- **"Ask Claude" chat** — conversational Q&A and discussion over the current research bundle (button already reserved in the UI).
- **Richer pattern library + step-by-step teaching replay** — beyond triple-top/bottom + head-and-shoulders; the magnifier walks through "peak 1 → peak 2 → peak 3 is a lower high → weakening," teaching the read.
- **Ecosystem depth** — fuller supply-chain graph (node-graph visualization), not just a chain.
- **Real logo** — generate from the data-cube spec (via OpenRouter image gen) and replace the placeholder mark.
- **Palette / visual polish** — tune the dark fintech colors (parked for now; "good enough for MVP").
- **TradingView widget option** — embed the exact TV chart look as an alternative to Lightweight-Charts.

## Phase 3 — surface & scale
- **Comparison tab** — two stocks side-by-side on the same metrics.
- **Full History tab** — saved searches with 2-line summaries, revisit past research.
- **Desktop packaging** — Tauri/Electron so it feels like a native app (Moomoo-style).
- **More markets fully supported** — all seven target markets with tuned data + news adapters.

---

## Ideas parked / to revisit
- Real-time (vs ~15-min delayed) data — would need a paid feed / broker API. Fine as delayed for learning.
- Alerts / watchlist.
- Export a research bundle (PDF/notes) for study.
- "Explain like I'm new" vs "pro" depth toggle on lessons.
- Backtesting a pattern's historical hit-rate (as a *learning* stat, with heavy caveats — never a signal).
- Multi-language / currency niceties for non-US markets.

## Guardrails (never drop)
- Numbers are exact (deterministic code); every AI claim is sourced.
- The AI describes momentum + teaches understanding; it **never** says buy/sell or predicts profit.
- When a source is unreachable/paywalled, say so — never fabricate.
