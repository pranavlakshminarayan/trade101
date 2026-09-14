"""
Chart-pattern detection — deterministic, from price extrema and trendlines.

Two families are detected, and ONLY the ones actually present on the given
timeframe are returned (nothing is invented to fill space):

  Reversal shapes (from swing highs/lows):
    Triple/Double Top, Triple/Double Bottom, Head & Shoulders (+ inverse)
  Trendline shapes (from fitted support/resistance lines):
    Ascending / Descending / Symmetrical Triangle, Rising / Falling Wedge,
    Ascending / Descending Channel

Each result carries the points to mark, any lines to draw, and a plain-English
"what it is · why it's read this way · what traders watch · caveat" note for the
magnifier. Heuristic and noisy by nature — a LOW-to-MODERATE-confidence LEARNING
AID, never a signal. When nothing clean is present, returns [].
"""
from __future__ import annotations

import numpy as np
from scipy.signal import argrelextrema

TOL = 0.04       # "similar level" tolerance (4%) for reversal shapes
FLAT = 0.03      # a trendline is "flat" if it moves <3% across the window
CONVERGE = 0.72  # lines converge if the end gap is <72% of the start gap
PARALLEL = 0.28  # lines are parallel if start/end gap differ by <28%

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


def _sim(closes, a, b, tol=TOL):
    return abs(closes[a] - closes[b]) / ((closes[a] + closes[b]) / 2) <= tol


def _mk(name, direction, idxs, labels, closes, times, neckline=None, lines=None):
    pts = [{"time": int(times[i]), "price": round(float(closes[i]), 2), "label": lab}
           for i, lab in zip(idxs, labels)]
    p = {"name": name, "direction": direction, "confidence": "low–moderate",
         "points": pts, "explanation": EXPL.get(name, "")}
    if neckline:
        p["neckline"] = [{"time": int(times[i]), "price": round(float(closes[i]), 2)} for i in neckline]
    if lines:
        p["lines"] = lines
    return p


def _reversals(c, times, peaks, troughs) -> list[dict]:
    out = []
    if len(peaks) >= 3:
        a, b, mid = peaks[-3], peaks[-2], peaks[-1]
        if _sim(c, a, b) and _sim(c, b, mid):
            out.append(_mk("Triple Top", "bearish", [a, b, mid],
                           ["Peak 1", "Peak 2", "Peak 3"], c, times))
        elif c[b] > c[a] and c[b] > c[mid] and _sim(c, a, mid):
            neck = [t for t in troughs if a < t < mid][:2]
            out.append(_mk("Head & Shoulders", "bearish", [a, b, mid],
                           ["Left shoulder", "Head", "Right shoulder"], c, times,
                           neckline=neck if len(neck) == 2 else None))
        elif _sim(c, b, mid) and c[a] > c[b]:
            out.append(_mk("Double Top", "bearish", [b, mid],
                           ["Peak 1", "Peak 2"], c, times))

    if len(troughs) >= 3:
        a, b, mid = troughs[-3], troughs[-2], troughs[-1]
        if _sim(c, a, b) and _sim(c, b, mid):
            out.append(_mk("Triple Bottom", "bullish", [a, b, mid],
                           ["Trough 1", "Trough 2", "Trough 3"], c, times))
        elif c[b] < c[a] and c[b] < c[mid] and _sim(c, a, mid):
            neck = [t for t in peaks if a < t < mid][:2]
            out.append(_mk("Inverse Head & Shoulders", "bullish", [a, b, mid],
                           ["Left shoulder", "Head", "Right shoulder"], c, times,
                           neckline=neck if len(neck) == 2 else None))
        elif _sim(c, b, mid) and c[a] < c[b]:
            out.append(_mk("Double Bottom", "bullish", [b, mid],
                           ["Trough 1", "Trough 2"], c, times))
    return out


def _fit(idxs, c):
    """Least-squares slope/intercept of price over the index domain."""
    xs = np.asarray(idxs, dtype=float)
    ys = c[idxs]
    m, b = np.polyfit(xs, ys, 1)
    return float(m), float(b)


def _trendlines(c, times, peaks, troughs) -> list[dict]:
    """Triangles / wedges / channels from fitted support & resistance lines."""
    n = len(c)
    # Need at least two of each to define two lines; use the most recent few.
    hp = peaks[-4:] if len(peaks) >= 2 else []
    lp = troughs[-4:] if len(troughs) >= 2 else []
    if len(hp) < 2 or len(lp) < 2:
        return []

    x0 = min(hp[0], lp[0])
    x1 = max(hp[-1], lp[-1])
    if x1 - x0 < max(10, n * 0.15):   # window too short to be meaningful
        return []

    mr, br = _fit(hp, c)   # resistance (through the highs)
    ms, bs = _fit(lp, c)   # support (through the lows)
    res0, res1 = mr * x0 + br, mr * x1 + br
    sup0, sup1 = ms * x0 + bs, ms * x1 + bs
    avg = float(np.mean(c[x0:x1 + 1])) or 1.0

    gap0, gap1 = res0 - sup0, res1 - sup1
    if gap1 <= 0 or gap0 <= 0:        # crossed / inverted lines → not a clean shape
        return []

    frac_r = (res1 - res0) / avg      # fractional move of each line across window
    frac_s = (sup1 - sup0) / avg
    r_dir = "up" if frac_r > FLAT else "down" if frac_r < -FLAT else "flat"
    s_dir = "up" if frac_s > FLAT else "down" if frac_s < -FLAT else "flat"
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
        return []

    lines = [
        [{"time": int(times[x0]), "price": round(res0, 2)},
         {"time": int(times[x1]), "price": round(res1, 2)}],
        [{"time": int(times[x0]), "price": round(sup0, 2)},
         {"time": int(times[x1]), "price": round(sup1, 2)}],
    ]
    idxs = sorted(set(hp) | set(lp))
    labels = ["" for _ in idxs]
    p = _mk(name, direction, idxs, labels, c, times, lines=lines)
    return [p]


def detect(closes: list[float], times: list[int]) -> list[dict]:
    """Return the pattern(s) actually present — reversal and/or trendline shapes,
    from the most recent price action. Empty when nothing clean is found."""
    c = np.asarray(closes, dtype=float)
    n = len(c)
    if n < 30:
        return []
    order = max(3, n // 40)  # extrema window scales with data length
    peaks = list(argrelextrema(c, np.greater, order=order)[0])
    troughs = list(argrelextrema(c, np.less, order=order)[0])

    out = _reversals(c, times, peaks, troughs)
    out += _trendlines(c, times, peaks, troughs)
    return out
