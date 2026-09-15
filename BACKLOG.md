# Trade Craft (né Trade101) — Backlog & Future Features

A running list so we don't lose ideas. Add freely; we pull from here after the MVP.

**North-star principle (applies to every phase):** Trade Craft must **extract data and make sense of it** — interpret, connect, and *teach understanding* — not just display labels. Reading a number is something you could do by hand; the app's job is to help you *understand* what the data means, together.

---

## MVP (Phase 1) — DONE
- [x] M0 Scaffold · [x] M1 real-time core · [x] M2 frontend (welcome + research view + live chart + click-to-learn)
- [x] **M3 AI narration** — momentum read + news Feed + "What it means" inference (sense-making, sourced). News via **Finnhub (free) + SEC EDGAR**.
- [x] M4 patterns (magnifier) + ecosystem + index/beta + references + history
- [x] M5 resilience + tests + the "surprise-ticker" true test

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
- [x] **Cache abstraction** — frontend session cache (`api.js`) + backend TTL cache
  (`services/cache.py`, memoises `orchestrator.gather`) + Claude prompt caching (`llm.py`).
  (SQLite/Redis still optional if this ever goes multi-process.)
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
- [~] **Deploy a shareable URL.** Single-service config is DONE — see the "Deploy" section below
  for the full status (both deploy paths ready, repo private, going live is the only remaining
  step). Keep API keys backend-only (already true).
- **Deeper search / scrape for non-US markets.**
  - [x] Free tier (2026-09-14): Yahoo news fallback + company-name fix + **computed beta vs the
    regional index** (`company.py`) so non-US listings get a real beta.
  - [ ] Paid tier (deferred to **after full deployment**, user's call): **Firecrawl or an
    alternative** for deeper regional news/scrape + non-US peers, behind the pluggable provider
    slot (`TRADE101_NEWS_PROVIDER`). Needs an API key + costs per scrape.
- **Broader web sourcing** — add **Exa** (wide semantic search) and premium sources where accessible/legal (the WSJ / Bloomberg / JP Morgan / investment-bank-report depth). Always sourced.
- [x] **"Ask Claude" chat** — DONE 2026-09-14. `POST /ask/{ticker}` + `agents/chat.py` +
  `components/AskClaude.jsx`; grounded in the same exact data + filtered evidence as `/analyze`,
  never advice, prompt-cached context so multi-turn stays cheap.
- **Richer pattern library + step-by-step teaching replay** — beyond triple-top/bottom + head-and-shoulders; the magnifier walks through "peak 1 → peak 2 → peak 3 is a lower high → weakening," teaching the read.
- [~] **Ecosystem depth** — DONE (v1, 2026-09-14): peers now render as a **radial node graph**
  (company at centre, peers on a ring, each clickable) instead of flat chips (`Ecosystem.jsx`
  `EcoGraph`). Fuller sourced supply-chain graph (edge types, private/public) is still future.
- [x] **Real logo** — DONE. Superseded by the 2026-09-15 rebrand: `Logo.jsx` is now the
  **Trade Craft** growth-spiral mark (green→teal ribbon + arrow + bar chart + $/€/¥ nodes).
- [x] **Palette / visual polish** — DONE 2026-09-15: deep-navy theme + cream/near-white text
  (`styles.css` `:root`), part of the Trade Craft rebrand.
- **TradingView widget option** — embed the exact TV chart look as an alternative to Lightweight-Charts.

## Phase 3 — surface & scale
- [x] **Comparison tab** — DONE 2026-09-14/15. Two stocks side by side: normalized price chart
  (rebased to 100) + metrics table (RSI/MACD/SMA/Bollinger/volume/beta/sector/mktcap).
  Deterministic (no AI call); "describes differences, never which to buy". `Compare.jsx` +
  `ComparisonChart.jsx`. Fixed after initial ship: pickers now use the same disambiguation
  picker as the main search (blind first-match had broken on "samsung"), and a latent
  `/research` 500 on some non-US symbols (bad NaN OHLC bar) was fixed at the `marketdata.py`
  source. See `docs/HANDOVER.md` §10.
- [x] **Full History tab** — DONE (MVP): saved searches with 2-line summaries, revisit past research.
- [x] **Watchlist** — DONE 2026-09-15. Track companies (`lib/watchlist.js` + `Watchlist.jsx`,
  ☆ Watch toggle on the research header); live quotes via `/research`, framed as tracking /
  information — no positions, P&L, or signals.
- **Desktop packaging** — Tauri/Electron so it feels like a native app (Moomoo-style). **Parked
  2026-09-15**: the user's actual near-term goal turned out to be a shareable *link*, which a
  desktop app doesn't produce — the web deploy (below) covers that instead, more efficiently
  (no Rust toolchain or PyInstaller currently installed for either packaging path). Revisit if a
  native installed app is wanted later. See `docs/HANDOVER.md` §13.
- **More markets fully supported** — all seven target markets with tuned data + news adapters.
- **Optional simulated practice lab** — kept SEPARATE from the main learning flow (delayed/
  hypothetical, reflection-focused), per `docs/trade101-phase-2-recommendations.md` Phase 3.
- **Accessibility / keyboard nav / responsive polish.**

---

## Ideas parked / to revisit
- Real-time (vs ~15-min delayed) data — would need a paid feed / broker API. Fine as delayed for learning.
- Alerts (info-event style: earnings filed, price crossed a chosen level) — watchlist itself is DONE.
- Export a research bundle (PDF/notes) for study.
- "Explain like I'm new" vs "pro" depth toggle on lessons.
- Backtesting a pattern's historical hit-rate (as a *learning* stat, with heavy caveats — never a signal).
- Multi-language / currency niceties for non-US markets.

## Deploy (single-service) — 2026-09-15

- [x] App is single-service: FastAPI serves the built React app (`app.py` mounts `frontend/dist`;
  `api.js` uses same-origin in prod).
- [x] Two deploy paths ready, both free: `render.yaml` (**no Docker** — Render native Python
  runtime; recommended) and `Dockerfile` + `.dockerignore` (container, for hosts that want one).
  Both documented in `docs/DEPLOY.md`. Native build verified locally (fresh `npm install && npm
  run build` succeeds; backend serves the rebuilt `dist/`).
- [x] GitHub repo set **private**.
- [ ] Go live: connect the repo to a host (Render/Fly, needs Pranav's account) → get the URL →
  add it to the repo About/README. (Deferred host signup is the user's step.)

## ⚠️ Pre-share checklist (BLOCKER before distributing the URL — do this right after "Go live" above)

The repo is private and the deploy URL is **personal-use only** until this is done. **Remind
Pranav at the END of Phase 3 execution** (his explicit request) — only after this can the link
be shared:

- [ ] **Guard the paid endpoints.** `/analyze` and `/ask` spend the owner's Claude key with no
  auth or rate-limit; a public visitor could run up the bill. Add before sharing:
  a shared password/access-token gate on the app, and/or rate-limiting or a per-day cap on
  `/analyze` + `/ask`, and/or a spend cap on the Claude key in the Anthropic console.

## Guardrails (never drop)
- Numbers are exact (deterministic code); every AI claim is sourced.
- The AI describes momentum + teaches understanding; it **never** says buy/sell or predicts profit.
- When a source is unreachable/paywalled, say so — never fabricate.
