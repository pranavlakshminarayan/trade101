"""
Chart-pattern detection — deterministic, from price extrema.

Detects the classic reversal shapes (head & shoulders, triple/double top &
bottom) and returns the points to draw + a plain-English "how it was identified"
note for the learning overlay. Heuristic and noisy by nature — surfaced as a
LOW-to-MODERATE-confidence LEARNING AID, never a signal.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import argrelextrema

TOL = 0.04  # "similar level" tolerance (4%)

# Rich, educational explanations: what it is · momentum inference · what traders
# typically do · caveat. Descriptive learning content — never advice.
EXPL = {
    "Triple Top": "Three peaks at roughly the same level with dips between. It's a topping / exhaustion shape — buyers tried three times to push past the same ceiling and failed, which usually reads as upward momentum fading. Textbook interpretation: chartists watch for a break BELOW the connecting 'neckline' (the dip lows) as confirmation that sellers have taken over, and many take profits or step aside near the resistance ceiling. It's a tendency, not a rule — these patterns fail often, so it's read alongside volume and trend.",
    "Double Top": "Two peaks at a similar level — the stock failed to make a higher high. It hints that the up-move is stalling at a resistance ceiling. Traders typically treat a break below the dip between the two peaks as the sign momentum has turned, and often lighten up near that ceiling. Weaker and less reliable than a triple top; confirm with volume.",
    "Head & Shoulders": "A higher middle peak (the head) between two lower, similar peaks (the shoulders) — one of the most-watched reversal shapes at the end of an uptrend. The read is that each successive push is losing steam. The 'neckline' runs under the two dips; a decisive close below it is the classic confirmation that the trend may be flipping down, and is where trend-followers commonly exit longs. High-profile but frequently gives false signals — treat as a heads-up, not a verdict.",
    "Triple Bottom": "Three troughs at roughly the same level — sellers tried three times to break lower and failed, a basing / accumulation shape that hints downward momentum is drying up. Traders watch for a break ABOVE the bounce highs as confirmation buyers are taking control, and it's often where bargain-hunters start accumulating. A tendency, not a guarantee — pair it with volume and the broader trend.",
    "Double Bottom": "Two troughs at a similar level — the stock refused to make a lower low, a sign selling pressure may be easing. A move above the bounce high between the two troughs is the usual confirmation that momentum is turning up. Less reliable than a triple bottom; look for rising volume on the breakout.",
    "Inverse Head & Shoulders": "A lower middle trough (head) between two higher, similar troughs (shoulders) — the mirror image of head & shoulders, and a classic BOTTOMING shape after a downtrend. It suggests sellers are progressively losing force. A close above the neckline (the two bounce highs) is the watched trigger that a recovery may be starting, and where accumulators often step in. Well-known but false-signal-prone — a signpost, not certainty.",
}


def _sim(closes, a, b, tol=TOL):
    return abs(closes[a] - closes[b]) / ((closes[a] + closes[b]) / 2) <= tol


def _mk(name, direction, idxs, labels, closes, times, neckline=None):
    pts = [{"time": int(times[i]), "price": round(float(closes[i]), 2), "label": lab}
           for i, lab in zip(idxs, labels)]
    p = {"name": name, "direction": direction, "confidence": "low–moderate",
         "points": pts, "explanation": EXPL.get(name, "")}
    if neckline:
        p["neckline"] = [{"time": int(times[i]), "price": round(float(closes[i]), 2)} for i in neckline]
    return p


def detect(closes: list[float], times: list[int]) -> list[dict]:
    """Return detected pattern(s) — at most one top-type and one bottom-type,
    from the most recent extrema."""
    c = np.asarray(closes, dtype=float)
    n = len(c)
    if n < 30:
        return []
    order = max(3, n // 40)  # extrema window scales with data length
    peaks = list(argrelextrema(c, np.greater, order=order)[0])
    troughs = list(argrelextrema(c, np.less, order=order)[0])
    out = []

    if len(peaks) >= 3:
        a, b, mid = peaks[-3], peaks[-2], peaks[-1]
        if _sim(c, a, b) and _sim(c, b, mid):
            out.append(_mk("Triple Top", "bearish", [a, b, mid],
                           ["Peak 1", "Peak 2", "Peak 3"], c, times))
        elif c[b] > c[a] and c[b] > c[mid] and _sim(c, a, mid):
            # trough indices between the peaks form the neckline
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
