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

## Audit — Wave 0: critical, do first (from `docs/AUDIT.md`, 2026-09-16) — ✅ DONE 2026-09-16

- [x] **C3 — Phase 3 work was stranded off `master`.** Turned out to already be merged via PR #2
  in a parallel session; this session's `master` (one commit behind) merged up to match. Verified
  on `master`: `services/access.py`, Google-News fallback, `lib/currency.js`, Practice Lab,
  accessibility fixes.
- [x] **C1 — Market cap was rendered as USD for every listing.** `company.get_profile` now
  returns `marketCapCurrency`; `Ecosystem.jsx` + `Compare.jsx` format with `currencySymbol()`.
  Verified: 7974.T → `¥9.36T`, not `$9.36T`.
- [x] **C2 — `above_sma50/200` reported `false` when the average was unknown.** Now tri-state
  (`True|False|None`); both agent prompts explicitly told `null` ≠ false. Regression test added.
- [x] **C4 — `/analyze` + `/ask` unauthenticated/uncapped on `master`** — resolved by the C3 merge.
- [x] **M8** — news items with no URL now render as a non-link block, not `href="#"`.
- [x] **M9** — `components/ErrorBoundary.jsx` wraps `<App/>`; a render crash now shows a
  recoverable message instead of a white screen.

## Audit — Wave 1: the four flaws the user named — ✅ DONE 2026-09-17 (H5 deferred to Wave 3)

- [x] **H1 — Search silently auto-picked on a name/ticker collision.** Fixed: `App.jsx`'s
  `looksLikeTicker()` only skips the picker for a genuinely ticker-shaped, unambiguous query —
  "Sony" now opens the picker with `6758.T` correctly ranked above the NYSE ADR. Same fix in
  `Compare.jsx`. Verified live.
- [x] **H2 — Candidate ranking favoured ADR/OTC/CDR over the primary listing.** Fixed:
  `services/search.py::resolve()` scores and sorts by listing quality (home/major exchange
  first; OTC/CDR/Pref/Secondary demoted + badged with a tooltip). 4 new tests in
  `tests/test_search.py`. Verified: "nintendo" now ranks `7974.T` above `NTDOY`.
- [x] **H3 — News was gated behind the paid AI call.** Fixed: new `GET /news/{ticker}` (no
  Claude call, no access-token/daily-cap gate), `NewsPanel.jsx`'s Feed tab loads from it
  independently of `/analyze` and is now the default tab. 4 new tests in
  `tests/test_news_endpoint.py`. Verified live: headlines rendered while the AI panel was still
  loading.
- [x] **H4 — The chart was destroyed and rebuilt on every parent render.** Fixed: `PriceChart.jsx`
  rewritten into three independent effects (chart lifecycle / price data / pattern overlay);
  `Research.jsx` memoizes the arrays passed in. View only re-fits on a genuinely new dataset, so
  zoom/pan survive the 7-min auto-refresh. Verified live.
- [x] **H5 — No indicators were drawn on the chart.** Fixed 2026-09-17 (Wave 3, first item —
  the UI/UX redesign proposal itself is separate and still pending review). Upgraded
  `lightweight-charts` v4.2 → **v5** (its multi-pane support is the whole point — v4 has none).
  Backend: `indicators.compute_indicator_series()` returns full time-aligned SMA/Bollinger/RSI/
  MACD arrays (the existing `compute_indicators()` only ever returned the latest snapshot value,
  useless for plotting a line); wired into `/research`'s new `indicatorSeries` field. Frontend:
  `PriceChart.jsx` overlays SMA50/SMA200 + Bollinger Bands on the price pane, RSI + MACD each in
  their own pane below (RSI with 30/70 overbought/oversold reference lines, fixed 0-100 scale),
  and a crosshair-driven OHLC + change% + volume legend. All four togglable from the chart header
  (SMA on by default, others off so the chart isn't busy for a first-time user). 3 new backend
  tests (`test_indicators.py`). Verified live: SMA/Bollinger overlays render correctly on price; RSI's live value
  (46.89) matches the Metrics panel's snapshot (46.8876) exactly; crosshair legend confirmed via
  a real hover event.
- [x] **User caught a real bug in H5's first pass, fixed same day:** SMA200 was cut short on 1Y
  and vanished entirely on 5D/1D. Root cause: SMA200 needs 200 bars of lookback before it
  produces a single point, but the backend fetched ONLY the display window (e.g. exactly 5 days
  for the "5D" tab) — no room for that lookback. Fixed: `app.py::_fetch_with_lookback` fetches
  more history than it displays (e.g. "60d" of 15-min bars for "5D" — verified empirically that
  "3mo" is silently REJECTED for 30m/15m/5m intervals, intraday history is capped at 60 days
  regardless of the period token used), computes indicators on the full fetch, trims back to the
  original display width. 3 new tests. Verified live: SMA200 now spans every timeframe fully.
- [x] **H6 — Pattern detection was structurally limited.** Fixed: `services/patterns.py`
  rewritten — full-series scan (not just the last 3 swings), all non-overlapping matches
  returned, detection on High/Low (not Close), double top/bottom no longer requires an unrelated
  higher prior peak, confidence is a real fit-based label. **Two more regressions caught by the
  user after the first pass, both fixed 2026-09-17:** the fixed 4%/2%/3% tolerances never fired
  on intraday timeframes (5D/1D always returned 0 patterns) — now derived per-series from the
  series' own volatility (`_scale()`); results weren't sorted, so a months-old match could
  outrank an equally clean recent one (UI shows index 0 by default) — now sorted most-recent-
  first. 6 total regression tests. Verified live on NVDA across all 5 timeframes and confirmed
  the default tab is the most recent pattern.
- [x] **H7 — Not shareable as written.** Fixed: `Welcome.jsx` greeting de-personalized;
  `news.py`'s SEC contact now reads `TRADE101_SEC_CONTACT` (falls back to a placeholder) instead
  of a hardcoded email in committed source.
- [x] **H8 — Currency symbols covered only INR + USD.** Already fixed by the Phase 3 merge
  (`lib/currency.js`) before this wave started — confirmed still in place.

## Audit — Wave 2: cost/reliability, then deploy — ✅ FULLY DONE 2026-09-17

- [x] **M2 — No backend cache of the analysis result.** Fixed: `orchestrator.analyze()` now
  caches its finished result for 20 min per ticker; a raised exception is never cached (retried
  on the next request, not stuck for the TTL). Verified live: two `/analyze/AMD` calls → one
  real ~30s Claude call then a 4ms cache hit, one `[llm]` log line for both. 3 new tests.
- [x] **M11 — No timeout on the Anthropic client.** Fixed: `agents/llm.py` sets `timeout=` on
  client construction (90s analysis, 45s chat) — a hung request now degrades gracefully instead
  of occupying a worker indefinitely. 3 new tests.
- [x] **Deploy to Render.** Live: https://trade-craft-qdsw.onrender.com (2026-09-17). Verified
  via `/health` (`{"status":"ok",...}`) and a real page load showing the BYOK key gate. Free-tier
  idle-sleep applies (~15 min idle → sleeps, ~30-60s cold-start on next hit).

## Audit — Wave 3: UI/UX redesign — ✅ DONE 2026-09-17, merged to `master` (commit `897514c`)

- [x] **H5 — chart indicator overlays.** Done (see "Known bugs" in `CLAUDE.md` for detail).
- [x] **Layout, icon system, evidence panel, accessibility/mobile pass.** Reviewed live across
  two feedback rounds on real tickers (including a thin-coverage edge case, TECA.F) and approved.
  Full detail in `CLAUDE.md` → "Known bugs" → the Wave 3 "Fixed" entry; full narrative (including
  a pattern-scan fix that was reverted after user feedback) in `docs/HANDOVER.md` §21. Summary:
  fixed two-zone layout, new SVG icon set (`Icons.jsx`), a redesigned evidence "receipts" panel,
  a mobile media query for the Welcome rail, dead CSS removed, logo→home navigation, a chart
  autofit bug fixed, a per-timeframe Metrics bug fixed, news-coverage recency window widened.
  Also renamed the Ask-Claude widget to **Ask TC-Buddy** with a candlestick icon.
- [x] **M1 — frontend session cache never expired.** Found while chasing a stale-SMA200 report:
  `api.js`'s `research`/`ecosystem`/`patterns`/`news` caches had no TTL. Added a 5-min TTL
  matching the backend's own cache; `analyze` (the paid call) deliberately stays session-long.
- [ ] **Not yet done**: full type scale / 8pt spacing system. Not pursued further this wave.

---

## Audit — Wave 4: depth — ✅ DONE 2026-09-17

From `docs/AUDIT.md` §10 item 14-17. Working through in order per the audit's own sequencing.

- [x] **M5 — fundamentals + earnings dates.** Done 2026-09-17. `services/company.py::
  _fundamentals()` — P/E (trailing+forward), EPS, revenue growth, profit margin, dividend
  yield, debt/equity, next earnings date, all straight from yfinance's `.info`/`.calendar`
  (nothing computed). Wired into `/ecosystem/{ticker}`'s response; rendered in `Ecosystem.jsx`.
  Degrades honestly (a genuinely thin listing gets a coverage note, not fabricated numbers).
  6 new backend tests.
- [x] **Bonus fix (user-reported mid-wave): non-US peers were completely empty.** Finnhub's
  free peers endpoint is US-listed-only, so every non-US stock (verified: RELIANCE.NS) showed
  no ecosystem graph at all — previously deferred to a paid Firecrawl/Exa tier. Found a free,
  keyless alternative: Yahoo Finance's own public "people also watch" endpoint
  (`_yahoo_related()`), used as a fallback when Finnhub has nothing. This is a DIFFERENT signal
  (co-viewed by other investors, not same-industry competitors) — tracked via a new
  `peersSource` field and labeled differently in the UI ("Related companies (commonly viewed
  together)... not necessarily direct competitors") so it's never presented as if it were the
  same kind of data Finnhub returns. 5 new backend tests. Verified live: RELIANCE.NS now shows
  a real 5-node graph (HDFCBANK/TCS/ICICIBANK/SBIN/LT) with the honest caveat.
- [x] **M3 — sharper evidence matching.** Done 2026-09-17. `services/evidence.py::classify()`
  no longer trusts a bare common-English-word match alone (e.g. "Apple cider vinegar" no longer
  matches Apple Inc. on the word "apple"). A small curated `_AMBIGUOUS_NAME_WORDS` set flags
  company names that double as ordinary words; for those, a match now requires a secondary
  corroborating signal (the ticker itself, or ordinary market/business vocabulary nearby via
  `_FINANCE_CONTEXT`) before being classified "company". Non-ambiguous names (the vast majority
  — Nvidia, Reliance, Toshiba, ...) are completely unaffected, so recall isn't hurt on the common
  case. 4 new tests.
- [x] **Bonus fix (user-reported mid-wave): trendline patterns missed still-forming shapes.**
  `services/patterns.py::_trendlines()` only ever fit ONE window — the last 4 confirmed peaks +
  last 4 confirmed troughs — which for a pattern still actively forming at the very end of the
  series (no bars after it yet to confirm a local extremum there) meant NO fit was ever
  attempted through it at all. Verified live: a clearly visible falling wedge in NKE's final
  ~15 bars on the 1D chart wasn't detected. Fixed with two changes: (1) try progressively
  smaller/more-recent extrema windows first instead of only the largest one, and (2) when no
  extrema-based window matches, fall back to fitting resistance/support directly through every
  raw bar in a trailing window (no extrema-confirmation requirement) — same fit logic, just not
  gated on argrelextrema having already confirmed a swing point. 1 new regression test.
- [x] **M10 — frontend tests + symbol-resolution tests.** Done 2026-09-17. Backend
  symbol-resolution tests already existed (`tests/test_search.py`, from Wave 1's H2 fix) — the
  real gap was frontend tests: **zero existed**. Set up Vitest + Testing Library (Vitest v2, to
  stay compatible with the project's Vite 5 — Vitest 5 requires Vite 6+). `npm test` (or `npm run
  test`) runs the suite. 53 tests across: `lib/currency.js`, `lib/history.js`, `lib/watchlist.js`,
  `lib/practiceLab.js` (buy/sell math — cost basis, P&L, insufficient-cash/oversell rejection),
  `lessons.js` (metric formatting + the C2 null-vs-false guardrail), `App.jsx`'s `looksLikeTicker`/
  `routeHash`/`parseRoute` (extracted to module scope + exported so they're directly testable —
  the H1 disambiguation-skip logic, previously untested anywhere), and one component test
  (`Metrics.jsx`, via Testing Library) to prove the render/interaction path works end to end.
- [x] **Glossary + watchlist notes.** Done 2026-09-17.
  - **Glossary**: new `lib/glossary.js` (static reference terms, grouped: Indicators / Chart
    patterns / Company-fundamentals) + `components/Glossary.jsx` (new nav tab, search box that
    filters term + definition text). Distinct from `lessons.js`, which teaches a metric IN
    CONTEXT of the current stock's own numbers — this is a plain, stock-independent lookup.
  - **Watchlist notes**: `lib/watchlist.js::setNote()` — a one-line "why I'm watching this" field
    per entry, editable inline in `Watchlist.jsx` (save on blur), preserved across a plain
    re-`addWatch` (not wiped by a refresh) but cleared if the entry is actually removed and
    re-added. Stays inside the "describes, never advises" guardrail — a note, not a
    position/target/signal.
  - 3 new tests (watchlist notes). Verified live.

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
- [x] **Non-US listings get no news** (Finnhub free tier 403s on non-US symbols) — resolved
  across several later fixes: Google News RSS fallback searches by company name (2026-09-15),
  then widened to a 90-day window + an honest "little findable coverage" note when a listing
  genuinely has almost nothing (Wave 3, 2026-09-17). No longer US-only.

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
**Feature-complete as of 2026-09-15.** Non-US peers were gapped until 2026-09-17 (see Wave 4
below — a free Yahoo fallback closed this); desktop packaging remains deliberately parked, not
planned.
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
  - [x] **Non-US peers (Ecosystem tab) fixed 2026-09-17** — a free substitute WAS found:
    Yahoo Finance's keyless "people also watch" endpoint, used as a fallback when Finnhub (US-only
    free tier) has nothing. Different signal (co-viewed, not same-industry) — labeled as such.
    See "Audit — Wave 4" below for detail. The paid Firecrawl/Exa tier remains a future option for
    TRUE same-industry peers on non-US listings, but is no longer the only path to a populated
    ecosystem graph.
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
- [x] Go live: deployed to Render — https://trade-craft-qdsw.onrender.com (2026-09-17). Added
  to README.

## ✅ Pre-share checklist — DONE 2026-09-17, superseded by BYOK

**The old shared-token/cap model this section originally described is gone.** `/analyze` and
`/ask` used to spend the owner's Claude key with an optional shared token + daily cap
(`services/access.py`) guarding them. Redesigned entirely instead of extended: every visitor now
supplies their OWN Anthropic API key (BYOK — see `CLAUDE.md`'s "Known bugs" → the 2026-09-17 BYOK
entry, and `docs/DEPLOY.md`), stored only in their own browser. **There is no user action
required before sharing a live link any more** — no token to set, no cap to configure, zero cost
risk to the owner by design. `services/access.py`, `lib/access.js`, and `tests/test_access.py`
were deleted outright (replaced by `tests/test_byok.py`), not kept as dead code alongside the
new system.

## Guardrails (never drop)
- Numbers are exact (deterministic code); every AI claim is sourced.
- The AI describes momentum + teaches understanding; it **never** says buy/sell or predicts profit.
- When a source is unreachable/paywalled, say so — never fabricate.
