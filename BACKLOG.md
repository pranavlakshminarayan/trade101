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

## Phase 1.5 — Trust & coherence  ← **current**
External review (ChatGPT + Gemini, Sept 2026) recommended this land BEFORE the
feature work below; the phases after it are renumbered accordingly.
- [x] Evidence relevance filter — only articles actually about the company reach the model.
- [x] Claim-level citations — every claim resolves to a real catalog entry, or is withheld.
- [x] Evidence tests — the sourcing contract is now enforced by tests, not by prompt wording.
- [x] Shared timeframe / as-of labels across chart, metrics, patterns and AI read.
- [x] Provider coverage badges + stale-data states (closed market vs. feed behind).
- [x] Cache abstraction + response caching (Redis seam via `TRADE101_CACHE_URL`).
- [x] Visible not-advice notice beside the momentum narrative, not only in the footer.
- [x] API keys confirmed backend-only (no `VITE_` vars, no secrets in the bundle).
- [x] Graceful degradation hardened — provider outage is a 503 with a retry, never a 500.
- [ ] **Form your own read before the AI's** — the last Definition-of-Done item; belongs
      with Guided Study Mode below.
- [ ] **Saved learning note** — ditto.

## Phase 2 — Learning engine ✅
- [x] **Guided Study Mode** — observe → predict → reveal → challenge → revisit.
- [x] **Learning journal** — hypothesis + evidence, never a virtual trade.
- [x] **Retrospective replay** — separate setup/reveal endpoints so the future never reaches the browser.
- [x] **Company fundamentals** — earnings, results vs estimates, revenue, margins, cash flow, valuation, filing links.
- [x] Short contextual prompts over tooltip overload.

## Phase 2.5 — Style lenses ✅ (not "styles to copy")
Trend · Swing · Mean-reversion · Long-term · Event-driven. Each must show what it
considers, what it ignores, conflicting evidence, and its failure modes.
**No day-trading lens** until a licensed real-time feed exists — delayed data would
create false precision.

## Phase 3 — Research workspace ✅
- [x] **Comparison** — two or more companies, normalized charts; never reduced to "which is better".
- [x] **Watchlist** — alerts phrased as information events, never trade prompts.
- [x] **Practice lab** — separate tab, explicitly hypothetical, reasoning required; never the primary action.
- [x] Light mode (3-state switch), focus rings, skip link, responsive to 400px.

## Phase 4 — Supply-chain & ecosystem intelligence ✅ (within what is sourceable)
- [x] **Sourced relationship graph** — every edge carries type, source, date, confidence, materiality.
- [x] Public/private distinguished by an explicit flag.
- [x] "A relationship is a research hypothesis, not proof of a price effect" carried everywhere.
- [x] ETF view shows verified holdings and real published weights.
- [ ] **Supplier/customer/partner/investor edges still have no source.** They are shown as
      explicitly unsourced rather than guessed. Needs a licensed dataset behind
      `TRADE101_RELATIONSHIP_PROVIDER` — the adapter slot exists.

## Still open
- **Ask-Claude chat** over the research bundle — the one Phase-2 item from the original
  plan that was never built (no endpoint, no UI seam). Starts from zero.
- Remove the old `Ecosystem` peer panel once the new `Graph` has been compared against it.
- Frontend tests (Vitest) — the backend has 128, the React side has none.
- Live-data verification of fundamentals/ETF holdings across non-US markets.

## Deferred — depth (was Phase 2)
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

## Architecture rules (from the review)
- **Provider abstraction for market data** — add adapters behind the interface; never a
  one-shot rewrite onto an institutional feed. Choose on exchange coverage, redistribution
  rights, history, real-time entitlement and cost.
- **No WebSockets** until a licensed real-time feed justifies them — a socket cannot make
  delayed data live. Polling + cached refreshes are right for a learning tool.
- **Graceful degradation everywhere** — each unavailable panel says what failed, what is
  still usable, and whether retrying helps.
- **One bounded analysis call** — do not add agents or keys to improve sourcing; fix the
  evidence pipeline first. Per-purpose spend is tracked in-app via `GET /usage`.

## Guardrails (never drop)
- Numbers are exact (deterministic code); every AI claim is sourced.
- The AI describes momentum + teaches understanding; it **never** says buy/sell or predicts profit.
- When a source is unreachable/paywalled, say so — never fabricate.
