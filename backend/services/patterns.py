"""
Chart-pattern detection — deterministic, from price extrema and trendlines.

Rewritten for docs/AUDIT.md finding H6, which found three structural defects
in the original version:
  1. Only the LAST 3 swing highs/lows were ever examined, so an otherwise
     clean pattern earlier in the window was invisible.
  2. At most one reversal + one trendline shape could ever be returned, and
     the double-top branch required an unrelated third peak to be strictly
     HIGHER than the two matching peaks — which rejects the textbook case
     (a double top forming at the end of an uptrend has a LOWER prior peak),
     so a real double top often produced nothing at all.
  3. Extrema were found on Close, not High/Low — under-detecting shapes and
     misplacing the marked points relative to the actual wicks.

This version scans the WHOLE series for every matching shape (not just the
tail), builds extrema from High (peaks) and Low (troughs), requires a real
separating move between levels (not just any two similarly-priced closes),
and computes a genuine confidence label from how tightly each match's levels
agree — never a fixed string. Overlapping matches are deduplicated greedily
(a Head & Shoulders consumes its three peaks so they can't also be reported
as a separate Double Top).

Two families are detected, and ONLY the ones actually present are returned
(nothing is invented to fill space):

  Reversal shapes (from swing highs/lows):
    Triple/Double Top, Triple/Double Bottom, Head & Shoulders (+ inverse)
  Trendline shapes (from fitted support/resistance lines):
    Ascending / Descending / Symmetrical Triangle, Rising / Falling Wedge,
    Ascending / Descending Channel

Each result carries the points to mark, any lines to draw, a confidence
label, and a plain-English "what it is · why it's read this way · what
traders watch · caveat" note for the magnifier. Heuristic and noisy by
nature — a LOW-to-MODERATE-confidence LEARNING AID, never a signal.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import argrelextrema

# Fixed fallbacks (used only if volatility can't be measured, e.g. a flat
# series) — the REAL values used are derived per-series by _scale(), below.
# A fixed 4%/2%/3% was tuned for daily/yearly swings and simply never fires
# on an intraday chart where the whole window might only move 1-2% total —
# that under-detection on short timeframes is a real bug (user-reported),
# not a design choice: patterns must scale with the series' own volatility.
TOL = 0.04        # "similar level" tolerance for reversal shapes
MIN_DIP = 0.02    # the extremum between two levels must clear this fraction
                   # of the level itself, or it's noise, not a real separating
                   # move (two pushes to the same level, not one wobble)
FLAT = 0.03       # a trendline is "flat" if it moves less than this across the window
CONVERGE = 0.72   # lines converge if the end gap is <72% of the start gap
PARALLEL = 0.28   # lines are parallel if start/end gap differ by <28% (scale-free, unchanged)

# what it is · momentum read · what traders watch · caveat — descriptive, never advice.
EXPL = {
    "Triple Top": "Three peaks at roughly the same level with dips between. A topping / exhaustion shape — buyers tried three times to clear the same ceiling and failed, so upward momentum reads as fading. Chartists watch for a break BELOW the connecting 'neckline' (the dip lows) as confirmation sellers have taken over. A tendency, not a rule — read alongside volume and trend.",
    "Double Top": "Two peaks at a similar level — no higher high. It hints the up-move is stalling at resistance. A break below the dip between the peaks is the usual sign momentum has turned. Weaker and less reliable than a triple top; confirm with volume.",
    "Head & Shoulders": "A higher middle peak (head) between two lower, similar peaks (shoulders) — a classic end-of-uptrend reversal where each push loses steam. The 'neckline' runs under the two dips; a decisive close below it is the textbook confirmation the trend may flip down. High-profile but frequently gives false signals.",
    "Triple Bottom": "Three troughs at roughly the same level — sellers tried three times to break lower and failed, a basing / accumulation shape hinting downward momentum is drying up. Traders watch for a break ABOVE the bounce highs as confirmation buyers are taking control. A tendency, not a guarantee.",
    "Double Bottom": "Two troughs at a similar level — no lower low, a sign selling pressure may be easing. A move above the bounce high between the troughs is the usual confirmation momentum is turning up. Less reliable than a triple bottom; look for rising volume on the breakout.",
    "Inverse Head & Shoulders": "A lower middle trough (head) between two higher, similar troughs (shoulders) — the mirror of head & shoulders and a classic bottoming shape after a downtrend. A close above the neckline (the two bounce highs) is the watched trigger a recovery may be starting. Well-known but false-signal-prone.",
    "Ascending Triangle": "A flat resistance ceiling with rising support beneath it — higher lows pressing price into the same top. Often read as a bullish continuation: buyers keep stepping in higher while sellers hold one line, and a break ABOVE the ceiling is the watched trigger. Works best mid-uptrend; a break the other way negates it.",
    "Descending Triangle": "A flat support floor with falling resistance above — lower highs pressing price down onto the same bottom. Often read as a bearish continuation: a break BELOW the floor is the watched trigger. Read with the prevailing trend; it can resolve upward, so it's a lean, not a verdict.",
    "Symmetrical Triangle": "Lower highs and higher lows converging to a point — the market is coiling as buyers and sellers reach balance. Direction-neutral by itself: traders wait for the breakout (up or down) and treat THAT as the signal, ideally with a volume expansion. The apex just marks when a move often resolves, not which way.",
    "Rising Wedge": "Both support and resistance slope up but converge, with support rising faster — gains are getting shallower even as price grinds higher. Typically read as a bearish exhaustion shape (in up- or down-trends), with a break below support the watched trigger. Notorious for false breaks; confirm with volume/momentum.",
    "Falling Wedge": "Both lines slope down but converge, with resistance falling faster — declines are getting shallower as selling tires. Typically read as a bullish shape, with a break above resistance the watched trigger. Like all wedges it fails often; pair with volume and the broader trend.",
    "Ascending Channel": "Parallel rising support and resistance — an orderly uptrend where price ricochets between two upward-sloping rails. The read is a healthy trend while it holds; traders watch the rails for where momentum has recently turned, and a decisive break below support is the usual 'trend may be ending' cue. Channels bend and break — describe it, don't extrapolate it.",
    "Descending Channel": "Parallel falling support and resistance — an orderly downtrend between two downward-sloping rails. The read is sustained selling pressure while it holds; a decisive break above resistance is the watched cue the downtrend may be easing. A description of current structure, not a forecast.",
}


def _scale(highs, lows) -> tuple[float, float, float]:
    """Derive (tol, min_dip, flat) from THIS series' own bar-to-bar volatility
    instead of a fixed percentage. A median per-bar move of 0.08% (typical for
    5 days of 15-min bars) needs a tolerance an order of magnitude tighter
    than a median move of 0.8% (typical for a year of daily bars) — a single
    fixed threshold can't serve both, which is why patterns used to go missing
    on every timeframe shorter than about a month."""
    mid = (highs + lows) / 2
    with np.errstate(divide="ignore", invalid="ignore"):
        rets = np.abs(np.diff(mid) / mid[:-1])
    rets = rets[np.isfinite(rets)]
    vol = float(np.median(rets)) if len(rets) else 0.005
    tol = float(np.clip(vol * 6, 0.008, 0.06))
    min_dip = float(np.clip(vol * 3, 0.004, 0.03))
    flat = float(np.clip(vol * 5, 0.006, 0.05))
    return tol, min_dip, flat


def _sim(vals, a, b, tol=TOL):
    return abs(vals[a] - vals[b]) / ((vals[a] + vals[b]) / 2) <= tol


def _has_real_dip(vals, i, j, want_min, min_frac=MIN_DIP):
    """Between bar-index i and j, is there a genuine trough (want_min=True —
    used between two peaks) or peak (want_min=False — between two troughs)
    that actually separates them, not just noise? True if the extremum in
    between clears min_frac of the edge level."""
    if j <= i + 1:
        return False
    seg = vals[i + 1:j]
    if len(seg) == 0:
        return False
    edge = min(vals[i], vals[j]) if want_min else max(vals[i], vals[j])
    extreme = seg.min() if want_min else seg.max()
    return (abs(edge - extreme) / edge) >= min_frac if edge else False


def _confidence(vals, idxs, tol=TOL):
    """A real fit score, not a fixed string: 'moderate' when the matched
    levels sit well inside the tolerance that defines the shape at all,
    'low' otherwise. Capped at 'moderate' on purpose — this stays a LEARNING
    AID, never confident enough to read as 'high'/a signal."""
    diffs = [abs(vals[idxs[i]] - vals[idxs[i + 1]]) / ((vals[idxs[i]] + vals[idxs[i + 1]]) / 2)
             for i in range(len(idxs) - 1)]
    worst = max(diffs) if diffs else 0.0
    return "moderate" if (worst / tol if tol else 1) <= 0.5 else "low"


def _mk(name, direction, idxs, labels, vals, times, confidence, neckline=None, neck_vals=None, lines=None):
    pts = [{"time": int(times[i]), "price": round(float(vals[i]), 2), "label": lab}
           for i, lab in zip(idxs, labels)]
    p = {"name": name, "direction": direction, "confidence": confidence,
         "points": pts, "explanation": EXPL.get(name, "")}
    if neckline:
        nv = neck_vals if neck_vals is not None else vals
        p["neckline"] = [{"time": int(times[i]), "price": round(float(nv[i]), 2)} for i in neckline]
    if lines:
        p["lines"] = lines
    return p


def _reversals(highs, lows, times, peaks, troughs, tol, min_dip) -> list[dict]:
    """Full-series scan: every consecutive triple, then every consecutive
    pair, of peaks/troughs — not just the most recent window. Triples/H&S
    are checked first and claim their peaks/troughs so a Double Top can't
    also be reported from the same two of a Triple Top's three peaks."""
    out: list[dict] = []
    used_p: set[int] = set()
    used_t: set[int] = set()

    for i in range(len(peaks) - 2):
        a, b, mid = peaks[i], peaks[i + 1], peaks[i + 2]
        if a in used_p or b in used_p or mid in used_p:
            continue
        if not (_has_real_dip(lows, a, b, True, min_dip) and _has_real_dip(lows, b, mid, True, min_dip)):
            continue
        if _sim(highs, a, b, tol) and _sim(highs, b, mid, tol):
            out.append(_mk("Triple Top", "bearish", [a, b, mid],
                           ["Peak 1", "Peak 2", "Peak 3"], highs, times,
                           _confidence(highs, [a, b, mid], tol)))
            used_p |= {a, b, mid}
        elif highs[b] > highs[a] and highs[b] > highs[mid] and _sim(highs, a, mid, tol):
            neck = [t for t in troughs if a < t < mid]
            neck2 = [neck[0], neck[-1]] if len(neck) >= 2 else None
            out.append(_mk("Head & Shoulders", "bearish", [a, b, mid],
                           ["Left shoulder", "Head", "Right shoulder"], highs, times,
                           _confidence(highs, [a, mid], tol), neckline=neck2, neck_vals=lows))
            used_p |= {a, b, mid}

    for i in range(len(troughs) - 2):
        a, b, mid = troughs[i], troughs[i + 1], troughs[i + 2]
        if a in used_t or b in used_t or mid in used_t:
            continue
        if not (_has_real_dip(highs, a, b, False, min_dip) and _has_real_dip(highs, b, mid, False, min_dip)):
            continue
        if _sim(lows, a, b, tol) and _sim(lows, b, mid, tol):
            out.append(_mk("Triple Bottom", "bullish", [a, b, mid],
                           ["Trough 1", "Trough 2", "Trough 3"], lows, times,
                           _confidence(lows, [a, b, mid], tol)))
            used_t |= {a, b, mid}
        elif lows[b] < lows[a] and lows[b] < lows[mid] and _sim(lows, a, mid, tol):
            neck = [p for p in peaks if a < p < mid]
            neck2 = [neck[0], neck[-1]] if len(neck) >= 2 else None
            out.append(_mk("Inverse Head & Shoulders", "bullish", [a, b, mid],
                           ["Left shoulder", "Head", "Right shoulder"], lows, times,
                           _confidence(lows, [a, mid], tol), neckline=neck2, neck_vals=highs))
            used_t |= {a, b, mid}

    # Double Top/Bottom — on peaks/troughs a triple/H&S above didn't already claim.
    # Fixed from the original: no longer requires an unrelated third peak to be
    # higher than the two matching ones (that rejected the textbook case of a
    # double top with a LOWER prior peak) — just two similar levels with a real
    # separating move between them.
    for i in range(len(peaks) - 1):
        a, b = peaks[i], peaks[i + 1]
        if a in used_p or b in used_p:
            continue
        if _sim(highs, a, b, tol) and _has_real_dip(lows, a, b, True, min_dip):
            out.append(_mk("Double Top", "bearish", [a, b], ["Peak 1", "Peak 2"],
                           highs, times, _confidence(highs, [a, b], tol)))
            used_p |= {a, b}
    for i in range(len(troughs) - 1):
        a, b = troughs[i], troughs[i + 1]
        if a in used_t or b in used_t:
            continue
        if _sim(lows, a, b, tol) and _has_real_dip(highs, a, b, False, min_dip):
            out.append(_mk("Double Bottom", "bullish", [a, b], ["Trough 1", "Trough 2"],
                           lows, times, _confidence(lows, [a, b], tol)))
            used_t |= {a, b}

    return out


def _fit(idxs, vals):
    """Least-squares slope/intercept of price over the index domain."""
    xs = np.asarray(idxs, dtype=float)
    ys = vals[idxs]
    m, b = np.polyfit(xs, ys, 1)
    return float(m), float(b)


def _fit_trendline_window(highs, lows, times, hp, lp, n, flat) -> dict | None:
    """Try fitting one triangle/wedge/channel to this specific (hp, lp) window
    of peak/trough indices. None if the lines don't form a clean shape."""
    x0 = min(hp[0], lp[0])
    x1 = max(hp[-1], lp[-1])
    if x1 - x0 < max(8, n * 0.08):   # window too short to be meaningful
        return None

    mr, br = _fit(hp, highs)   # resistance (through the highs)
    ms, bs = _fit(lp, lows)    # support (through the lows)
    res0, res1 = mr * x0 + br, mr * x1 + br
    sup0, sup1 = ms * x0 + bs, ms * x1 + bs
    avg = float(np.mean((highs[x0:x1 + 1] + lows[x0:x1 + 1]) / 2)) or 1.0

    gap0, gap1 = res0 - sup0, res1 - sup1
    if gap1 <= 0 or gap0 <= 0:        # crossed / inverted lines → not a clean shape
        return None

    frac_r = (res1 - res0) / avg      # fractional move of each line across window
    frac_s = (sup1 - sup0) / avg
    r_dir = "up" if frac_r > flat else "down" if frac_r < -flat else "flat"
    s_dir = "up" if frac_s > flat else "down" if frac_s < -flat else "flat"
    converging = gap1 < gap0 * CONVERGE
    parallel = abs(gap1 - gap0) / gap0 < PARALLEL

    name = direction = None
    if converging:
        if r_dir == "flat" and s_dir == "up":
            name, direction = "Ascending Triangle", "bullish"
        elif r_dir == "down" and s_dir == "flat":
            name, direction = "Descending Triangle", "bearish"
        elif r_dir == "down" and s_dir == "up":
            name, direction = "Symmetrical Triangle", "neutral"
        elif r_dir == "up" and s_dir == "up":
            name, direction = "Rising Wedge", "bearish"
        elif r_dir == "down" and s_dir == "down":
            name, direction = "Falling Wedge", "bullish"
    elif parallel:
        if r_dir == "up" and s_dir == "up":
            name, direction = "Ascending Channel", "bullish"
        elif r_dir == "down" and s_dir == "down":
            name, direction = "Descending Channel", "bearish"

    if not name:
        return None

    # Confidence from how well the touches actually sit on their fitted line.
    r_err = max(abs(highs[i] - (mr * i + br)) / avg for i in hp)
    s_err = max(abs(lows[i] - (ms * i + bs)) / avg for i in lp)
    confidence = "moderate" if max(r_err, s_err) <= flat else "low"

    lines = [
        [{"time": int(times[x0]), "price": round(res0, 2)},
         {"time": int(times[x1]), "price": round(res1, 2)}],
        [{"time": int(times[x0]), "price": round(sup0, 2)},
         {"time": int(times[x1]), "price": round(sup1, 2)}],
    ]
    idxs = sorted(set(hp) | set(lp))
    labels = ["" for _ in idxs]
    return _mk(name, direction, idxs, labels, highs, times, confidence, lines=lines)


def _trendlines(highs, lows, times, peaks, troughs, flat) -> list[dict]:
    """Triangles / wedges / channels from fitted support & resistance lines —
    resistance through the HIGHS, support through the LOWS (previously both
    were fit on Close, which touches neither rail precisely).

    Tries the most recent (smallest) window of peaks/troughs FIRST, widening
    only if that finds nothing. Fixed from a real bug (user-reported: a
    clearly visible falling wedge on NKE's 1D chart wasn't detected) — the
    original version only ever fit ONE window, the last 4 peaks + last 4
    troughs, which on a volatile day can span nearly the whole session and
    average a real, tight recent wedge into a flat, undetectable line. This
    mirrors `_reversals()`'s existing full-series-scan approach, just for
    trendline shapes instead of swing-point shapes."""
    n = len(highs)
    if len(peaks) < 2 or len(troughs) < 2:
        return []

    max_k = min(max(len(peaks), len(troughs)), 6)
    for k in range(2, max_k + 1):
        hp = peaks[-k:]
        lp = troughs[-k:]
        if len(hp) < 2 or len(lp) < 2:
            continue
        match = _fit_trendline_window(highs, lows, times, hp, lp, n, flat)
        if match:
            return [match]

    # Still-forming patterns near the very end of the series have no chance
    # of showing up above: argrelextrema needs `order` bars on BOTH sides to
    # confirm a local peak/trough, so a shape still actively developing in
    # the last few bars has no confirmed extrema to fit through at all
    # (user-reported: a visually obvious falling wedge on NKE's 1D chart, in
    # its final ~15 bars, wasn't detected — that window contained zero
    # confirmed peaks/troughs). Fall back to fitting resistance/support
    # directly through EVERY bar in a trailing window (no extrema
    # requirement) — a straightforward regression trendline, same as the
    # extrema-based fit but over raw recent bars instead of confirmed swings.
    for frac in (0.18, 0.24, 0.32, 0.4):
        width = max(10, int(n * frac))
        if width >= n:
            continue
        idxs = list(range(n - width, n))
        match = _fit_trendline_window(highs, lows, times, idxs, idxs, n, flat)
        if match:
            return [match]
    return []


def detect(highs: list[float], lows: list[float], times: list[int]) -> list[dict]:
    """Return every pattern actually present — reversal and/or trendline
    shapes, scanned across the WHOLE series (docs/AUDIT.md H6 — previously
    only the most recent 3 swings were ever examined). Empty when nothing
    clean is found; never invents a shape to fill space.

    Sorted MOST-RECENT-FIRST (by each match's latest point) — a full-series
    scan can find a real pattern from months ago alongside one from last
    week, and the UI selects index 0 by default, so an unsorted list meant
    the oldest match (not the most relevant one) was often what showed."""
    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)
    n = len(h)
    # Lowered from 30: with the volatility-scaled tolerances above, 20 bars is
    # enough to find real reversal patterns (verified: AAPL's 1-month/daily
    # view, 22 bars, found a genuine Double Top once this floor stopped
    # blocking it) — the OLD fixed threshold made the "1M" timeframe tab
    # return nothing at all, always, regardless of the actual data.
    if n < 20 or len(l) != n:
        return []
    order = max(3, n // 40)  # extrema window scales with data length
    peaks = list(argrelextrema(h, np.greater, order=order)[0])
    troughs = list(argrelextrema(l, np.less, order=order)[0])
    tol, min_dip, flat = _scale(h, l)

    out = _reversals(h, l, times, peaks, troughs, tol, min_dip)
    out += _trendlines(h, l, times, peaks, troughs, flat)
    out.sort(key=lambda p: max(pt["time"] for pt in p["points"]), reverse=True)
    return out
