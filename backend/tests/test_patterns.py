"""Pattern-detector tests on synthetic price series (pure, no network)."""
import numpy as np

from services import patterns


def _wave(levels, base, seg=25):
    """base → level1 → base → level2 → … → base, with single, strict extrema
    at each level (endpoint=False avoids duplicate values at the joins that
    argrelextrema would otherwise skip)."""
    pts = [base]
    for lv in levels:
        pts += [lv, base]
    parts = [np.linspace(pts[i], pts[i + 1], seg, endpoint=False) for i in range(len(pts) - 1)]
    parts.append(np.array([pts[-1]]))
    return np.concatenate(parts)


def test_triple_top_detected():
    x = _wave([110, 110, 110], base=102)          # three equal peaks
    pats = patterns.detect(x.tolist(), x.tolist(), list(range(len(x))))
    assert any("Top" in p["name"] for p in pats)
    top = next(p for p in pats if "Top" in p["name"])
    assert top["direction"] == "bearish"
    assert top["explanation"]
    assert top["confidence"] in ("low", "moderate")  # a real label, never a fixed string


def test_head_and_shoulders_or_top():
    x = _wave([108, 114, 108], base=102)          # higher middle peak (head)
    pats = patterns.detect(x.tolist(), x.tolist(), list(range(len(x))))
    names = [p["name"] for p in pats]
    assert any(n in ("Head & Shoulders", "Triple Top", "Double Top") for n in names)


def test_triple_bottom_detected():
    x = _wave([100, 100, 100], base=108)          # three equal troughs
    pats = patterns.detect(x.tolist(), x.tolist(), list(range(len(x))))
    assert any("Bottom" in p["name"] and p["direction"] == "bullish" for p in pats)


def test_double_top_with_a_lower_prior_peak_is_still_detected():
    # Regression for docs/AUDIT.md H6: the OLD double-top branch required an
    # unrelated third, earlier peak to be HIGHER than the two matching ones —
    # rejecting the textbook case (a double top forming after an uptrend has
    # a LOWER prior peak). Build exactly that: a rising peak, then two equal
    # peaks at a new, higher level — a real double top with no third peak
    # anywhere near that level.
    base = np.linspace(90, 102, 40, endpoint=False)          # uptrend into the first peak
    x = np.concatenate([base, _wave([130, 130], base=118, seg=25)])
    pats = patterns.detect(x.tolist(), x.tolist(), list(range(len(x))))
    tops = [p for p in pats if p["name"] == "Double Top"]
    assert tops, "a double top with a lower prior peak must still be detected"


def test_pattern_earlier_in_the_window_is_found_not_just_the_tail():
    # Regression for H6: the OLD detector only ever looked at the LAST 3
    # swings. Put a clean double top early, then unrelated noise after it —
    # the old code would see only the noise and report nothing.
    top = _wave([120, 120], base=104, seg=25)
    noise = np.linspace(104, 110, 120)                        # plain drift, no shape
    x = np.concatenate([top, noise])
    pats = patterns.detect(x.tolist(), x.tolist(), list(range(len(x))))
    assert any(p["name"] == "Double Top" for p in pats)


def _zig(seq, seg=20):
    parts = [np.linspace(seq[i], seq[i + 1], seg, endpoint=False) for i in range(len(seq) - 1)]
    parts.append(np.array([seq[-1]]))
    return np.concatenate(parts)


def test_ascending_triangle_detected():
    # flat resistance ~110, rising support 100 -> 103 -> 106
    x = _zig([96, 110, 100, 110, 103, 110, 106, 110, 108])
    pats = patterns.detect(x.tolist(), x.tolist(), list(range(len(x))))
    tri = next((p for p in pats if p["name"] == "Ascending Triangle"), None)
    assert tri is not None
    assert tri["direction"] == "bullish"
    assert tri["lines"] and len(tri["lines"]) == 2   # support + resistance drawn
    assert tri["explanation"]
    assert tri["confidence"] in ("low", "moderate")


def test_descending_channel_detected():
    # parallel falling rails
    x = _zig([120, 128, 112, 120, 104, 112, 96, 104, 90])
    pats = patterns.detect(x.tolist(), x.tolist(), list(range(len(x))))
    ch = next((p for p in pats if p["name"] == "Descending Channel"), None)
    assert ch is not None
    assert ch["lines"] and len(ch["lines"]) == 2


def test_no_pattern_on_pure_trend():
    x = np.linspace(100, 200, 150)
    assert patterns.detect(x.tolist(), x.tolist(), list(range(150))) == []


def test_short_series_returns_empty():
    assert patterns.detect([1, 2, 3], [1, 2, 3], [0, 1, 2]) == []


def test_mismatched_high_low_length_returns_empty():
    assert patterns.detect(list(range(40)), list(range(35)), list(range(40))) == []


def test_low_volatility_intraday_series_still_finds_patterns():
    # Regression (user-reported): patterns worked on 1Y but returned NOTHING
    # on shorter/intraday timeframes. Root cause was the OLD fixed 4%/2%
    # tolerance/min-dip, tuned for daily/yearly swings, never firing on a
    # series whose total range is only ~1-2% (typical for 15-min bars over a
    # few days) — every real double top on that scale got rejected as "no
    # real dip between the peaks". Build a double top with peaks just ~0.4%
    # apart and a ~0.15% separating dip — proportionally identical to the
    # 4%-tolerance/2%-min-dip version, just 10x smaller in absolute terms.
    x = _wave([101.00, 101.00], base=100.50, seg=25)
    pats = patterns.detect(x.tolist(), x.tolist(), list(range(len(x))))
    assert any(p["name"] == "Double Top" for p in pats), \
        "a proportionally-clean double top must be found regardless of the series' absolute scale"


def test_patterns_are_sorted_most_recent_first():
    # Regression (user-reported): on the 1Y timeframe, the pattern shown by
    # default (index 0) was often many months old even when a much more
    # recent, equally clean pattern existed later in the same series — the
    # full-series scan (H6) found both but never sorted them, so the UI's
    # default selection (patSel = 0) surfaced whichever was found first
    # (earliest in time), not the most relevant one.
    old_top = _wave([120, 120], base=104, seg=25)                    # early in the series
    gap = np.linspace(104, 108, 60)                                   # unrelated drift
    recent_bottom = _wave([90, 90], base=104, seg=25)                 # late in the series
    x = np.concatenate([old_top, gap, recent_bottom])
    pats = patterns.detect(x.tolist(), x.tolist(), list(range(len(x))))
    names = [p["name"] for p in pats]
    assert "Double Top" in names and "Double Bottom" in names
    # the most recent pattern (the bottom, which starts after old_top+gap)
    # must be first in the returned list.
    assert pats[0]["name"] == "Double Bottom"
    top_time = max(pt["time"] for p in pats if p["name"] == "Double Top" for pt in p["points"])
    bottom_time = max(pt["time"] for p in pats if p["name"] == "Double Bottom" for pt in p["points"])
    assert bottom_time > top_time
