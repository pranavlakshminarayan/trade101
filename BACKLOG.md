# Trade Craft (né Trade101) — Backlog & Future Features

A running list so we don't lose ideas. Add freely; we pull from here after the MVP.

> **📋 Full critical audit (2026-09-16): [`docs/AUDIT.md`](docs/AUDIT.md)** — adversarial review of
> the whole app (functional / logical / executional / UI-UX), 30+ ranked findings with a wave-by-wave
> fix order. The "Audit — Wave 0/1" sections below are pulled from it; the audit is the detail.

**North-star principle (applies to every phase):** Trade Craft must **extract data and make sense of it** — interpret, connect, and *teach understanding* — not just display labels. Reading a number is something you could do by hand; the app's job is to help you *understand* what the data means, together.

---

## MVP (Phase 1) — DONE
- [x] M0 Scaffold · [x] M1 real-time core · [x] M2 frontend (welcome + research view + live chart + click-to-learn)
- [x] **M3 AI narration** — momentum read + news Feed + "What it means" inference (sense-making, sourced). News via **Finnhub (free) + SEC EDGAR**.
- [x] M4 patterns (magnifier) + ecosystem + index/beta + references + history
- [x] M5 resilience + tests + the "surprise-ticker" true test

---

## Audit — Wave 0: critical, do first (from `docs/AUDIT.md`, 2026-09-16)

- [ ] **C3 — Phase 3 work is stranded off `master`.** Branch `claude/trading-idea-phase-3-297572`
  (commit `8d80ef9`, 24 files, +1256) holds the **pre-share access guard** (`services/access.py`),
  the Google-News fallback, `lib/currency.js`, the Practice Lab and accessibility fixes. It is
  **unmerged and unpushed** — local-worktree-only. Review, merge, push, then reconcile the status
  in `CLAUDE.md` + this file.
- [ ] **C1 — Market cap is rendered as USD for every listing.** `Ecosystem.jsx:4` hardcodes `$`, so
  Nintendo shows **`$9.36T`** (really ¥9.36T ≈ $63B) against Apple's `$4.81T`. Breaks the
  "numbers are exact" north star on screen. Format with the listing's own currency.
- [ ] **C2 — `above_sma50/200` reports `false` when the average is unknown**
  (`indicators.py:108`), and that false is sent to Claude as exact data. Make it tri-state
  (`True|False|None`) and teach the agent prompt to read `null` as unknown.
- [ ] **C4 — `/analyze` + `/ask` unauthenticated/uncapped on `master`** — resolved by the C3 merge.
- [ ] **M8** — news items with no URL render `href="#"`, which resets the hash route and kicks the
  user back to the home screen. **M9** — add a React error boundary.

## Audit — Wave 1: the four flaws the user named

- [ ] **H1 — Search silently auto-picks on a name/ticker collision.** `App.jsx:56` skips the picker
  when the query equals the top candidate's symbol, so **"Sony" opens the NYSE ADR** and never
  offers Tokyo (`6758.T`). Verified.
- [ ] **H2 — Candidate ranking favours ADR/OTC/CDR over the primary listing.** "nintendo" ranks
  `NTDOY` (OTC) above `7974.T`; "toyota" ranks `TM` above `7203.T`. Rank by listing class, group by
  country, badge `ADR`/`OTC`/`CDR`/`Pref`.
- [ ] **H3 — News is gated behind the paid AI call.** `NewsPanel` reads only from `/analyze`, so no
  Claude key / an AI error / the daily cap ⇒ **no headlines at all**, and the feed waits on the full
  model call. Add a free `GET /news/{ticker}` (gather() already computes it, TTL-cached).
- [ ] **H4 — The chart is destroyed and rebuilt on every parent render** — a new `[]` literal in the
  `patterns` prop (`Research.jsx:170`) invalidates the effect, so typing in the header search
  rebuilds the chart per keystroke and auto-refresh discards zoom/pan.
- [ ] **H5 — No indicators are drawn on the chart.** SMA/Bollinger/RSI/MACD are computed and
  explained but never plotted. Upgrade `lightweight-charts` v4.2 → **v5** for sub-panes, add
  overlays + a crosshair OHLC legend. (Not the TradingView embed — it can't draw our pattern overlays.)
- [ ] **H6 — Pattern detection is structurally limited.** Only the last 3 swings are examined; ≤1
  reversal + ≤1 trendline is ever returned; the double-top branch requires a *higher* prior peak so
  it rejects the textbook case; detection runs on closes, not highs/lows; confidence is a hardcoded
  string. Rewrite: full-series scan, all matches, real fit scores, grouped Reversal/Continuation/Trendline.
- [ ] **H7 — Not shareable as written:** `Welcome.jsx:26` hardcodes "Pranav"; `news.py:23` sends a
  personal email as the SEC User-Agent.
- [ ] **H8 — Currency symbols cover only INR + USD**, duplicated in three files (`lib/currency.js`
  on the unmerged branch fixes this).

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
**Feature-complete as of 2026-09-15**, except non-US peers (still gapped behind the deferred
paid Firecrawl/Exa tier) and desktop packaging (deliberately parked, not planned).
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
- **Accessibility / keyboard nav / responsive polish.**
  - [x] **2026-09-15 pass** — fixed 10 nav-tab links (`<a>` with no `href`, unreachable by
    keyboard/screen reader) → real `<button>`s with `aria-current="page"`; added a global
    `:focus-visible` ring; fixed one input (`.cmp-pick`) that removed its focus outline with no
    replacement; fixed a contrast bug where metric values were nearly invisible. Verified live
    with actual Tab-key navigation and screenshots (focus ring visible, tabs reachable).
  - [ ] Broader pass still open: full keyboard-trap review of modals (disambiguation picker,
    Ask-Claude panel), color-contrast audit beyond what this pass touched, responsive/mobile
    layout review.
- **More markets fully supported** — all seven target markets with tuned data + news adapters.
  - [x] **Currency display fixed** (2026-09-15) — non-US currencies (JPY/KRW/HKD/SGD/CNY/EUR/GBP/…)
    were rendering as a bare number with no symbol; three duplicated, USD/INR-only `sym()`
    helpers replaced with one shared `frontend/src/lib/currency.js`. Verified live on 7974.T.
  - [ ] Non-US peers (Ecosystem tab) — still gapped; Finnhub's peers endpoint is US-only free
    tier, and a real free substitute wasn't found. Real fix is the paid Firecrawl/Exa tier
    (already deferred to post-deploy elsewhere in this doc).
  - [x] **Non-US news broadened** (2026-09-15) — added a keyless Google News RSS fallback
    (`services/news.py::_google_news`, searches by company name) ahead of the Yahoo fallback,
    so non-US markets get real, diverse coverage instead of relying on Yahoo Finance's own feed
    alone. Verified live on 7974.T: MarketWatch, BeInCrypto, Britannica, nintendo.com, Anime
    News Network all appeared.
- [x] **Optional simulated practice lab** — DONE 2026-09-15. `lib/practiceLab.js` +
  `components/PracticeLab.jsx`: a simulated $100,000 USD-only portfolio + trade journal, its
  own top-level tab, kept SEPARATE from the main learning flow per
  `docs/trade101-phase-2-recommendations.md` Phase 3. Log a hypothetical buy/sell at the real
  live price with a reasoning note; selling realizes P&L against average cost and closes the
  journal entry. Zero Claude spend (deterministic, like Watchlist/Compare). Scoped to USD only
  for v1 — mixing currencies into one cash pool would need real FX data this app doesn't have.
  Verified live: bought 10 AAPL, sold 5, cash/P&L math exact, journal entry recorded correctly.

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

The repo is private and the deploy URL is **personal-use only** until this is done.

- [x] **Guard the paid endpoints — code done 2026-09-15.** `/analyze` and `/ask` spent the
  owner's Claude key with no auth or rate-limit; a public visitor could have run up the bill.
  Fixed: `services/access.py` gates both behind an optional shared access token
  (`TRADE101_ACCESS_TOKEN`) and a shared daily cap (`TRADE101_DAILY_CAP`, default 50/day). Both
  are no-ops until set, so this didn't change local dev at all. Tests in `tests/test_access.py`.
  - [ ] **User action still required before actually sharing a live link:** set
    `TRADE101_ACCESS_TOKEN` as an env var on the host (Render, per `docs/DEPLOY.md`), then share
    the URL once as `?token=<value>` — the frontend saves it locally after that. Optionally also
    set a spend cap on the Claude key in the Anthropic console as a last-resort backstop.

## Guardrails (never drop)
- Numbers are exact (deterministic code); every AI claim is sourced.
- The AI describes momentum + teaches understanding; it **never** says buy/sell or predicts profit.
- When a source is unreachable/paywalled, say so — never fabricate.
