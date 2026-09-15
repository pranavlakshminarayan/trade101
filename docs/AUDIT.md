# Trade Craft — Critical Audit (2026-09-16)

An adversarial review of the whole app: product critic, systems analyst, solution-architect
reviewer and red-teamer in one pass. Written to be **useful, not kind**. Every finding below was
read in the source and, where marked ✅ **verified**, reproduced by running the code.

Scope: `backend/` (FastAPI, services, agents), `frontend/` (React), `docs/`, git history and
branch state. Reviewed at `master` @ `b3ae062`.

**Related docs:** [CLAUDE.md](../CLAUDE.md) (current state) · [BACKLOG.md](../BACKLOG.md) (work
queue) · [docs/HANDOVER.md](HANDOVER.md) (history) · [docs/DEVELOPMENT-LOG.md](DEVELOPMENT-LOG.md)
(phase journey).

---

## 0. Verdict

The architecture is genuinely good and the guardrails are real. The deterministic/AI split is the
right call, `services/evidence.py` is a better idea than most shipped fintech has, and the
"describes, never advises" rule is enforced in the prompts *and* in the UI copy. The bones are
sound.

**But the app is not finished, and three things are worse than "unfinished":**

1. **It prints a false number with total confidence.** Nintendo's market cap renders as
   **`$9.36T`** — larger than Apple's `$4.81T`. The real figure is ¥9.36T ≈ **$63B**. The app's
   north star is "numbers are exact"; this is the app breaking its own core promise on screen,
   silently, on every non-USD stock. (§1, C1)
2. **The deterministic layer feeds the AI a fact that isn't true.** When a stock has under 200
   days of history, `above_sma200` is sent to Claude as `false` rather than "unknown" — so the
   model can correctly-per-its-input state a stock is "below its 200-day average" when no such
   average exists. The anti-hallucination layer is manufacturing the hallucination. (§1, C2)
3. **A completed Phase 3 — including the pre-share security fix — exists only as an unmerged,
   unpushed commit in a local worktree.** One disk failure and it is gone. Meanwhile `CLAUDE.md`
   still lists that fix as outstanding, so the project's own memory is wrong. (§1, C3)

Everything else is fixable in a focused sequence. The good news: your instinct on all four things
you named (search, news, chart, patterns) was correct, and in three of the four the real defect is
**worse or different** than you thought — which is why they never quite got fixed.

---

## 1. Findings, ranked

Severity = user-visible harm × likelihood. **Effort** is my estimate for a focused session.

| # | Severity | Finding | Where | Effort |
|---|----------|---------|-------|--------|
| C1 | 🔴 Critical | Market cap always rendered as USD → false figures for every non-USD listing | `Ecosystem.jsx:4` | S |
| C2 | 🔴 Critical | `above_sma50/200` reports `false` for *unknown*, and that false reaches Claude | `indicators.py:108` | S |
| C3 | 🔴 Critical | Phase 3 (incl. the access guard) committed but never merged **or pushed** | branch `claude/trading-idea-phase-3-297572` | S |
| C4 | 🔴 Critical | `/analyze` + `/ask` unauthenticated and uncapped on `master` | `app.py:120,139` | S (fix exists, unmerged) |
| H1 | 🟠 High | Search silently auto-picks when the query equals a ticker → "Sony" opens the NYSE ADR | `App.jsx:56` | S |
| H2 | 🟠 High | Candidate ranking favours ADR/OTC/CDR over the primary listing; no grouping or labels | `search.py:35` | M |
| H3 | 🟠 High | News is gated behind the *paid AI call* — no key or AI error ⇒ no headlines at all | `NewsPanel.jsx:8` | M |
| H4 | 🟠 High | Chart destroyed + rebuilt on every parent render; typing in search rebuilds it per keystroke | `Research.jsx:170` | S |
| H5 | 🟠 High | No indicators drawn on the chart — SMA/Bollinger/RSI/MACD explained but never plotted | `PriceChart.jsx` | L |
| H6 | 🟠 High | Pattern detection only inspects the last 3 swings; ≤1 reversal + ≤1 trendline ever returned | `patterns.py:62` | L |
| H7 | 🟠 High | Hardcoded "Pranav" greeting + personal email in the SEC User-Agent | `Welcome.jsx:26`, `news.py:23` | S |
| H8 | 🟠 High | Currency symbol map covers only INR + USD; duplicated in three files | `Research.jsx:125` +2 | S |
| M1 | 🟡 Med | Frontend session cache never expires → stale prices shown as live | `api.js:10` | S |
| M2 | 🟡 Med | No backend cache of the *analysis result* → every reload is a fresh paid call | `orchestrator.py:50` | S |
| M3 | 🟡 Med | Evidence filter is bare token matching → "Apple cider" matches AAPL | `evidence.py:64` | M |
| M4 | 🟡 Med | `is_us = "." not in ticker` misclassifies `BRK.B` as non-US | `company.py:85` | S |
| M5 | 🟡 Med | Zero fundamentals (P/E, EPS, revenue, margin, dividend) anywhere in the app | product gap | L |
| M6 | 🟡 Med | `/ecosystem` makes 3+ serial network round-trips; panel is visibly slow | `company.py:75` | M |
| M7 | 🟡 Med | Watchlist fires N parallel `/research` calls on mount — Yahoo throttling risk | `Watchlist.jsx:19` | S |
| M8 | 🟡 Med | News items without a URL render `href="#"` → resets the hash route, kicks user home | `NewsPanel.jsx:34` | S |
| M9 | 🟡 Med | No React error boundary — one render throw white-screens the entire app | `App.jsx` | S |
| M10 | 🟡 Med | Zero frontend tests; backend tests don't cover symbol resolution at all | `frontend/`, `tests/` | M |
| M11 | 🟡 Med | No timeout on the Anthropic client; `effort="high"` + 4000 tok on every `/analyze` | `llm.py:49` | S |
| L1 | ⚪ Low | No mobile layout for the Welcome screen (fixed 230px rail, no media query) | `styles.css:24` | S |
| L2 | ⚪ Low | No `:focus-visible` anywhere; nav tabs are `<a>` with no `href` (unfocusable) | `styles.css`, `Research.jsx:206` | S |
| L3 | ⚪ Low | `--faint` small text is borderline on contrast against `--surface` | `styles.css:3` | S |
| L4 | ⚪ Low | ~8 dead CSS rulesets left from the pre-masonry layout | `styles.css:58,104,120` | S |
| L5 | ⚪ Low | Ask-Claude panel: no Esc-to-close, no focus trap, `role="dialog"` without `aria-modal` | `AskClaude.jsx:51` | S |
| L6 | ⚪ Low | `useLayoutEffect` with no dependency array — re-measures on every render | `Research.jsx:109` | S |
| L7 | ⚪ Low | News opens on the AI interpretation tab, not the actual headlines | `NewsPanel.jsx:6` | XS |
| L8 | ⚪ Low | Prices render without thousands separators; `…` always appended to summaries | `Research.jsx:229` | XS |

---

## 2. Data integrity — the guardrail is leaking

This is the most serious section, because these defects attack the app's *reason to exist*.

### C1 — Market cap is labelled `$` regardless of the actual currency ✅ verified

```js
// frontend/src/components/Ecosystem.jsx:4
function marketCap(v) {
  if (v >= 1e12) return '$' + (v / 1e12).toFixed(2) + 'T'   // ← hardcoded $
```

`marketCap` arrives from Yahoo **in the listing's own currency**. Verified output:

| Ticker | Real `marketCap` | Currency | App renders | Truth |
|--------|------------------|----------|-------------|-------|
| `7974.T` (Nintendo) | 9,359,025,242,112 | **JPY** | `$9.36T` | **≈ $63B** |
| `AAPL` | 4,811,409,326,080 | USD | `$4.81T` | $4.81T ✓ |

A learner comparing them concludes Nintendo is ~2× Apple. It is roughly 1/76th. This misfires on
every JPY, KRW, INR and HKD listing — i.e. most of the "any market" promise.

**Fix:** return `currency` from `company.get_profile` (it's already in the quote) and format with
`Intl.NumberFormat(locale, {style:'currency', currency, notation:'compact'})`. Optionally add a
converted USD figure — but only if you fetch a real FX rate and label it as converted.

### C2 — `above_sma200: false` conflates "below" with "unknown" ✅ verified

```python
# backend/services/indicators.py:108
"above_sma50":  (price is not None and sma50  is not None and price > sma50),
"above_sma200": (price is not None and sma200 is not None and price > sma200),
```

Verified on 6 months of AAPL data: `sma200 = None` but `above_sma200 = False`.

That `false` is serialized straight into the analysis payload (`analysis.py:98`). The system prompt
tells Claude the numbers are exact and must not be recomputed — so the model *correctly* reasons
from a flag that is a lie. The `unknown` label the prompt so carefully defines can never fire here,
because the data layer already decided.

**Fix:** emit `True | False | None`, and have the agent prompt treat `null` as explicitly unknown.
`lessons.js` already guards this properly in the UI — the bug is that the *agent* doesn't get the
same guard.

### M4 — `is_us` misclassifies dotted US tickers ✅ verified

```python
is_us = "." not in ticker   # BRK.B → False. It is very much US-listed.
```
Drives the coverage-explanation copy, so `BRK.B` is told the peers source "covers US-listed
symbols" — while being one. Use the exchange/country from the profile instead of string shape.

---

## 3. Search — two separate defects, not one

### H1 — The auto-pick ✅ verified (this is your Sony bug)

```js
// frontend/src/App.jsx:56
if (cands.length === 1 || cands[0].symbol.toUpperCase() === qn.toUpperCase()) {
  return doResearch(cands[0].symbol)     // picker never shown
}
```

That second clause exists to let a typed ticker (`AAPL`) skip the picker. But it fires whenever the
**company name happens to equal a ticker symbol** — and Sony's NYSE ADR is literally `SONY`.
Verified:

```
query 'sony' → SONY (NYSE) | 6758.T (Tokyo) | SFGYY | 8729.T | SONY.NE | SNEJF
  => auto-picks without asking: TRUE  → opens SONY, the US ADR
```

Same class of trap for any name-equals-ticker company. **Fix:** only skip the picker when the query
looks like a ticker *and* is unambiguous — e.g. skip only if exactly one candidate matches, or the
query contains no lowercase letters and no spaces. Safest: always show the picker when >1 candidate
exists, with the best match preselected and Enter accepting it.

### H2 — The ranking is wrong even when the picker *does* appear ✅ verified

```
'toyota'   → TM (NYSE)      before 7203.T (Tokyo)
'nintendo' → NTDOY (OTC!)   before 7974.T (Tokyo)
'samsung'  → 005930.KS ✓    then SSNLF (OTC), SMSN.IL, 005935.KS (preferred shares)
```

The top suggestion for Nintendo is an **OTC ADR** — thin, wide-spread, not the real company's
market. The list also mixes in CDRs, Frankfurt secondary lines and preferred share classes
(`005935.KS`) with no visual distinction. `services/search.py` passes Yahoo's order straight
through and only filters on `quoteType`.

**Fix:** rank and annotate. Score by `exchange` class (primary home listing > major foreign
listing > ADR > OTC/CDR), group in the picker by country with a flag/exchange label, and badge
non-primary lines as `ADR` / `OTC` / `CDR` / `Pref`. Add a "primary listing" hint. This turns the
picker from a disambiguation chore into the most educational moment in the app — *why* a company
has six tickers is exactly the kind of thing a beginning trader should learn.

---

## 4. News — the real flaw is architectural, not the provider

You said the news tab is "still flawed." The provider quality is part of it (and the unmerged
branch adds a Google News RSS fallback, §7), but the structural defect is this:

```js
// frontend/src/components/NewsPanel.jsx:8
const news = ai?.news || {}       // ai === the /analyze response
```

**News reaches the UI only through the paid AI endpoint.** Consequences:

- **No Claude key → no news.** The panel renders "AI narration unavailable" even though headlines
  are keyless, deterministic data that was already fetched.
- **Claude errors, refuses, or 429s → no news.** Deterministic data disappears because a
  probabilistic system failed.
- **Claude is slow → news is slow.** `/analyze` runs `effort="high"` with `max_tokens=4000` and
  adaptive thinking. Headlines are available in ~1s; the user stares at "Gathering the news feed…"
  for the entire model call.
- **Once the daily cap lands (C4 fix), the news tab dies with it.**

This violates the app's own architecture principle — deterministic data must never depend on the
judgment layer.

**Fix:** add `GET /news/{ticker}` returning the filtered feed + `sourcing` (free, no AI). The panel
loads it immediately; the "What it means" tab layers the AI inference on top when/if it arrives.
Same data, decoupled lifecycles. `orchestrator.gather()` already computes exactly this and is
already TTL-cached, so the endpoint is nearly free to add.

Secondary news defects: no date sorting (provider order is trusted blindly); undated Yahoo items
bypass the freshness cutoff (`news.py:73` — a `ValueError` keeps the item with `date_iso=None`); the
per-article `category` the backend computes is never shown in the feed; `href="#"` on URL-less items
breaks hash routing (M8); the panel opens on the AI tab rather than the headlines (L7).

---

## 5. The chart — why it doesn't feel "real"

You're right that it isn't a serious charting surface. Three reasons, in order of severity:

### H4 — It is destroyed and rebuilt constantly ✅ by inspection

```jsx
// Research.jsx:170 — new array identity on EVERY render
patterns={showPatterns && selPat ? [selPat] : []}
```
```jsx
// PriceChart.jsx:74
}, [ohlcv, type, patterns, showPatterns])   // ← `patterns` changes identity every render
// ...and the effect's cleanup is chart.remove()
```

Every parent re-render produces a new `[]`, so the effect tears the chart down and builds a new one.
`Research` re-renders on **every keystroke in the header search box** (`q` state lives there). So
typing "toyota" rebuilds the chart six times. The 7-minute auto-refresh does the same, discarding
any zoom/pan the user set. It feels janky because it *is* being rebuilt.

**Fix:** memoize the patterns array (`useMemo`), split the effect — create the chart once on mount,
update series data via `setData` on change — and keep the `timeScale` state across refreshes.

### H5 — Nothing is drawn but price

The app computes RSI, MACD, Bollinger Bands, SMA50, SMA200 — and **plots none of them**. It
*explains* them in prose beside a chart that doesn't show them. For a learning tool that's
backwards: the whole point is seeing the 50-day cross the 200-day, seeing price ride the upper
Bollinger band.

Also: `timeVisible: type === 'line'` (`PriceChart.jsx:19`) means intraday **candles** show no time
axis — on the 1D/5m view every bar is labelled by date only.

**Fix / library call:** stay on `lightweight-charts`, but **upgrade v4.2 → v5**, which adds
multi-pane support — that's what lets you put RSI and MACD in proper sub-panes beneath price like a
real terminal, instead of cramming them onto one axis. Then add: SMA50/200 overlays, Bollinger
envelope, volume in its own pane, a crosshair OHLC legend in the top-left, and toggles for each
overlay. That single change is most of what you mean by "more realistic." (I don't have access to
the other session's notes on this — if it recommended something specific, paste it and I'll
reconcile.)

I'd *not* embed the actual TradingView widget: it's a third-party iframe, it can't render your
deterministic pattern overlays, and it would undercut the thing that makes Trade Craft yours.

---

## 6. Patterns — the detector is structurally limited

You said patterns "could be organised better and more." The detector can only ever find very few,
by construction:

```python
# services/patterns.py:65
a, b, mid = peaks[-3], peaks[-2], peaks[-1]     # ONLY the last three swings
```

1. **Only the final 3 peaks and 3 troughs are examined.** A textbook double bottom in month 4 of a
   12-month chart is invisible.
2. **At most one reversal + one trendline shape is ever returned** — `_reversals` uses `elif`
   chains, `_trendlines` returns `[p]`. The tabbed pattern selector in the UI can therefore almost
   never show more than two tabs.
3. **The double-top branch rejects the textbook case.** `elif _sim(c, b, mid) and c[a] > c[b]`
   requires the *older* peak to be higher than the two matching peaks. A double top forming at the
   end of an uptrend has a **lower** prior peak — so it's skipped, and since the H&S branch also
   fails, **nothing is returned at all**.
4. **Detection runs on closing prices, not highs/lows.** Real chart patterns are built from
   intraday extremes; using closes systematically under-detects and misplaces the swing points
   drawn on the chart.
5. **Confidence is a hardcoded string** — `"low–moderate"` for every pattern, regardless of how
   well it actually fits. There's no quality score, so the UI can't sort or filter.

**Fix direction:** scan a sliding window across the whole series rather than only the tail; collect
*all* matches and rank by a real fit score (symmetry, level tolerance, duration, volume
confirmation); detect on `High`/`Low`; return a scored list the UI can group as
**Reversal / Continuation / Trendline**; keep the "none found" honesty. Add the missing common
shapes — Cup & Handle, Flag/Pennant, Rounding Bottom, Double/Triple variants at any position.

---

## 7. Cost, access and the unmerged branch

### C3 — Completed work is stranded ✅ verified

```
$ git log --oneline master..claude/trading-idea-phase-3-297572
8d80ef9 Complete Phase 3: Practice Lab, pre-share guard, more-markets and accessibility fixes
  24 files changed, 1256 insertions(+), 142 deletions(-)
$ git branch -r
origin/master, origin/claude/trading-idea-handover-dfe84a     # ← the Phase-3 branch is NOT here
```

That commit contains, already written and tested (`test_access.py`, `test_news.py` — 29 tests pass
on master, more on the branch):

- `backend/services/access.py` — **the pre-share fix**: `X-Access-Token` header + a UTC-daily cap,
  wired onto `/analyze` and `/ask` only, leaving the free endpoints open. Exactly right for your
  "just me + a few friends" target.
- `_google_news()` — keyless global news by **company name** rather than bare ticker. This is a
  genuine fix for non-US coverage.
- `frontend/src/lib/currency.js` — the fix for H8.
- `PracticeLab.jsx` + `lib/practiceLab.js` — the simulated practice lab.
- Accessibility and more-markets fixes.

It is unmerged, **unpushed**, and lives in a worktree under `.claude/`. It is one `rm -rf` or disk
failure from being lost. Simultaneously `CLAUDE.md` still carries the ⚠️ PRE-SHARE BUG banner as
outstanding and says Phase 3 is merely "started" — **the project's memory contradicts its own
git history.** By your own memory protocol, that's a bug in the memory.

**Fix, before anything else:** review that branch, merge it to `master`, push. Then correct the
status docs.

### C4 / M2 / M11 — remaining cost exposure after that merge

Even with the guard merged: there is **no backend cache of the analysis result**. `gather()` is
TTL-cached but `analysis.run()` is not — so every page reload, every new browser tab, every friend
opening the link spends a fresh `effort="high"` / 4000-token call. The frontend cache is per-tab
memory only. Add a TTL cache on the analysis output keyed by ticker (15–30 min is fine for a
learning tool), and the daily cap will last far longer. Also set an explicit client timeout on the
Anthropic SDK — a hung call currently occupies a worker indefinitely.

### H7 — Not shareable as written

`Welcome.jsx:26` greets **"Which stock shall we study, Pranav?"** and `news.py:23` sends your
personal email as the SEC User-Agent on every filings request. Before anyone else opens the link:
parameterise the greeting (or drop the name), and move the SEC contact to an env var.

---

## 8. UI/UX — the critique (redesign proposal follows separately, per your call)

You said the UI is "shit." It isn't — it's *coherent and competent but undesigned*. The specific
failures:

**1. No visual hierarchy.** Every panel is the identical `.card`: same background, same 1px hair
border, same 16px radius, same padding. Six identical boxes means the eye has no entry point — the
References list looks exactly as important as the chart. Nothing tells you where to start.

**2. The self-balancing masonry actively hurts.** `Research.jsx:109` measures block heights in a
`useLayoutEffect` (with no dependency array, so it re-measures on *every* render) and assigns each
block to the shorter column. The result: **panels move between columns as content loads.** The user
can never learn "news lives on the right," because sometimes it doesn't. Non-deterministic layout is
worse than an imperfect fixed one. It also re-runs layout work on every keystroke.

**3. Competing affordances at the top.** The research view has a logo, four nav tabs, a Watch
button, a "New search" button, *and* a second search input in the strip below — five controls
fighting for the same corner, none visually dominant.

**4. Typography has one voice.** Nearly everything is 12–14px at one weight; `--faint` is used for
both UI labels and body copy, so chrome and content read as the same thing. There's no scale, so
nothing can be emphasised without a coloured chip.

**5. Emoji as an icon system.** 🔍 📎 ⚖️ ★ 🕘 ✚ ✦ ▲ ▼ ■. Mixed metaphors, inconsistent weights,
OS-dependent rendering, and the single biggest "this is a prototype" tell in the whole app.

**6. Four accent colours competing.** Teal (brand/interactive), green/red (semantic up/down), amber
(patterns *and* the watch star). Amber doing double duty means the pattern highlight and the
watchlist state are visually the same signal.

**7. The most valuable thing is the least designed.** The Fact/Interpretation/Unknown evidence list
is genuinely novel — it's the app's actual differentiator — and it renders as a plain `<ul>` with
small badges, visually indistinguishable from a bullet list.

**8. No state design system.** Three different loading treatments (`.loading`, `.scraping`,
inline `Loading 1M…`), and errors appear as a fixed-position toast on Welcome but as inline
`.placeholder` text elsewhere.

**9. Accessibility is not wired.** No `:focus-visible` rule anywhere in 263 lines of CSS. Nav tabs
are `<a>` elements with no `href`, so they are **not keyboard-focusable at all**. The ecosystem
graph nodes are `<g onClick>` — invisible to keyboard and screen readers. `--faint` (#7C90A6) on
`--surface` (#0D1726) is borderline for small text.

**10. Mobile is unhandled on the entry screen.** `.welcome` is `grid-template-columns:230px 1fr`
with **no media query** — on a phone the nav rail consumes most of the viewport. `.top` doesn't
wrap either.

**11. Dead CSS.** `.row`, `.cockpit`, `.midrow`, `.snap`, `.refs`, `.eco-peers`, `.mkt`, `.phase`
are leftovers from the pre-masonry layout.

### Redesign direction (sketch — for your approval, not yet built)

- **Replace the masonry with a deterministic three-zone layout:** persistent left rail (nav +
  watchlist + recents) · a centre "spine" that is chart → AI read → metrics · a right column that is
  always news + evidence. Fixed positions, so the user builds a mental map.
- **Make the chart the hero:** full spine width, indicator overlays, RSI/MACD sub-panes, crosshair
  legend. It should look like the most important thing on the page, because it is.
- **A real design system:** a 6-step type scale, an 8pt spacing scale, one accent (teal) + semantic
  up/down only, amber reserved exclusively for pattern overlays, and a proper icon set (Lucide)
  replacing every emoji.
- **Elevate the evidence panel** into the signature component — a proper "receipts" card where
  Fact / Interpretation / Unknown are the primary visual structure.
- **One state system:** a single skeleton/loading component, a single inline error component, a
  single empty state.
- **Accessibility pass:** real `<button>`/`<a href>` semantics, a global `:focus-visible` ring, keyboard-reachable graph nodes, contrast lifted on small text.

---

## 9. Product gaps (things a user will ask for and not find)

- **No fundamentals at all.** P/E, EPS, revenue growth, margins, dividend yield, debt — none. The
  app teaches only technical analysis, which for a *beginning investor* is arguably the less useful
  half. This is the single biggest content gap.
- **No earnings dates** — the most consequential scheduled event for any stock.
- **Watchlist has no notes field.** The user studies a company, forms a view, and has nowhere to
  record it. A one-line "why I'm watching this" would make the list genuinely useful and stays well
  clear of the no-advice line.
- **History stores a summary but can't be searched or filtered.**
- **Comparison is limited to exactly two stocks** and has no AI commentary (a deliberate cost
  choice — worth revisiting now that caching exists).
- **No glossary.** Lessons are attached to metrics; a beginner meeting "beta" or "neckline" in prose
  has nowhere to look it up.

---

## 10. Recommended fix order

Sequenced so each wave leaves the app in a shippable state.

### Wave 0 — Stop the bleeding (do this first, ~1 session)
1. **C3** — review, merge and **push** `claude/trading-idea-phase-3-297572`. Reconcile `CLAUDE.md` /
   `BACKLOG.md` with reality afterwards.
2. **C1** — currency-correct market cap. It's printing false numbers right now.
3. **C2** — tri-state `above_sma*`; teach the agent prompt to read `null` as unknown.
4. **M8, M9** — `href="#"` routing bug + an error boundary.

### Wave 1 — The four things you named (~2 sessions)
5. **H1 + H2** — kill the auto-pick; rank and label candidates by listing type and country.
6. **H3** — free `GET /news/{ticker}`; decouple the news panel from `/analyze`.
7. **H4** — memoize patterns, stop rebuilding the chart, preserve zoom across refresh.
8. **H6** — rewrite the pattern scan: full-series window, all matches, real fit scores, grouped.

### Wave 2 — Make it shareable (~1 session)
9. **H7** — de-personalise the greeting; SEC contact to env.
10. **M2 + M11** — cache the analysis result; set an Anthropic client timeout.
11. Deploy to Render, set `TRADE101_ACCESS_TOKEN` + `TRADE101_DAILY_CAP`, verify the guard from a
    logged-out browser, then share the link.

### Wave 3 — The UI rebuild (~2–3 sessions, after you approve a direction)
12. Design system + three-zone layout + icon set + state system + accessibility pass.
13. **H5** — `lightweight-charts` v5, indicator overlays, RSI/MACD panes, crosshair legend.

### Wave 4 — Depth
14. **M5** — fundamentals + earnings dates. 15. **M3** — sharper evidence matching.
16. **M10** — frontend tests + symbol-resolution tests. 17. Glossary, watchlist notes.

---

## 11. What is genuinely good (don't refactor these)

Worth stating plainly, because a red-team read can make a project look worse than it is:

- **The deterministic/AI split is correct** and consistently enforced. Numbers are computed in
  Python and handed to the model; the model is told not to recompute. C2 is a leak *in* that
  design, not a failure *of* it.
- **`services/evidence.py`** — filtering evidence before the model sees it, and reporting the
  kept/dropped counts to the user, is better sourcing discipline than most shipped products have.
- **Fact / Interpretation / Unknown labelling** is a genuinely strong idea and the `_citation_guard`
  that prunes unsourced points is the right way to enforce it.
- **Graceful degradation** is thorough — every provider path returns `(items, note)` and the app
  survives every one of them failing.
- **`redact_secrets` + the tests around it** — a real fix for a real past incident, with regression
  coverage.
- **Prompt caching** is correctly implemented, with usage logging to prove it fires.
- **The documentation discipline** (CLAUDE.md / BACKLOG / HANDOVER / DEVELOPMENT-LOG) is unusually
  good. C3 is the exception that proves it matters.
