# Trade101 — Backlog & Future Features

A running list so we don't lose ideas. Add freely; we pull from here after the MVP.

**North-star principle (applies to every phase):** Trade101 must **extract data and make sense of it** — interpret, connect, and *teach understanding* — not just display labels. Reading a number is something you could do by hand; the app's job is to help you *understand* what the data means, together.

---

## MVP (Phase 1) — complete
- [x] M0 Scaffold · [x] M1 real-time core · [x] M2 frontend (welcome + research view + live chart + click-to-learn)
- [x] **M3 AI narration** — momentum read + news Feed + "What it means" inference (sense-making, sourced). News via **Finnhub (free) + SEC EDGAR**.
- [x] M4 patterns (magnifier) + ecosystem + index/beta + references + history
- [x] M5 resilience + tests + the "surprise-ticker" true test

**Verification run (2026-09-12), surprise ticker `7974.T` (Nintendo, Tokyo):** name search
resolved 4 listings across markets; `/research` returned 244 live bars + exact indicators;
`/patterns` correctly returned none (nothing clean); `/ecosystem` returned sector/industry/
market cap; `/analyze` produced a sourced, mixed-lean momentum read with no buy/sell language
and honestly reported that no news was available rather than inventing any; unknown ticker →
404 with a helpful message; with the key removed the app degraded to chart + indicators.
18 backend tests pass; frontend builds clean.

---

## Phase 2 — depth
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
