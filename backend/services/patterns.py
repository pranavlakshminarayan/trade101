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


def _sim(closes, a, b, tol=TOL):
    return abs(closes[a] - closes[b]) / ((closes[a] + closes[b]) / 2) <= tol


def _mk(name, direction, idxs, labels, closes, times, why, neckline=None):
    pts = [{"time": int(times[i]), "price": round(float(closes[i]), 2), "label": lab}
           for i, lab in zip(idxs, labels)]
    p = {"name": name, "direction": direction, "confidence": "low–moderate",
         "points": pts, "explanation": why}
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
                           ["Peak 1", "Peak 2", "Peak 3"], c, times,
                           "Three peaks at a similar level with pullbacks between — buyers repeatedly failed to break higher, a classic exhaustion/topping shape."))
        elif c[b] > c[a] and c[b] > c[mid] and _sim(c, a, mid):
            # trough indices between the peaks form the neckline
            neck = [t for t in troughs if a < t < mid][:2]
            out.append(_mk("Head & Shoulders", "bearish", [a, b, mid],
                           ["Left shoulder", "Head", "Right shoulder"], c, times,
                           "A higher middle peak (the head) flanked by two lower, similar peaks (the shoulders) — a well-known topping/reversal shape. A break below the neckline (under the two dips) is what chartists watch for.",
                           neckline=neck if len(neck) == 2 else None))
        elif _sim(c, b, mid) and c[a] > c[b]:
            out.append(_mk("Double Top", "bearish", [b, mid],
                           ["Peak 1", "Peak 2"], c, times,
                           "Two peaks at a similar level — a failure to make a higher high, often read as momentum stalling."))

    if len(troughs) >= 3:
        a, b, mid = troughs[-3], troughs[-2], troughs[-1]
        if _sim(c, a, b) and _sim(c, b, mid):
            out.append(_mk("Triple Bottom", "bullish", [a, b, mid],
                           ["Trough 1", "Trough 2", "Trough 3"], c, times,
                           "Three troughs at a similar level — sellers repeatedly failed to push lower, a basing/accumulation shape."))
        elif c[b] < c[a] and c[b] < c[mid] and _sim(c, a, mid):
            neck = [t for t in peaks if a < t < mid][:2]
            out.append(_mk("Inverse Head & Shoulders", "bullish", [a, b, mid],
                           ["Left shoulder", "Head", "Right shoulder"], c, times,
                           "A lower middle trough (the head) between two higher, similar troughs (the shoulders) — a classic bottoming/reversal shape; a break above the neckline is the watched trigger.",
                           neckline=neck if len(neck) == 2 else None))
        elif _sim(c, b, mid) and c[a] < c[b]:
            out.append(_mk("Double Bottom", "bullish", [b, mid],
                           ["Trough 1", "Trough 2"], c, times,
                           "Two troughs at a similar level — a failure to make a lower low, often read as selling pressure easing."))

    return out
