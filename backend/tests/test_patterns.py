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
    pats = patterns.detect(x.tolist(), list(range(len(x))))
    assert any("Top" in p["name"] for p in pats)
    top = next(p for p in pats if "Top" in p["name"])
    assert top["direction"] == "bearish"
    assert top["explanation"]


def test_head_and_shoulders_or_top():
    x = _wave([108, 114, 108], base=102)          # higher middle peak (head)
    pats = patterns.detect(x.tolist(), list(range(len(x))))
    names = [p["name"] for p in pats]
    assert any(n in ("Head & Shoulders", "Triple Top", "Double Top") for n in names)


def test_triple_bottom_detected():
    x = _wave([100, 100, 100], base=108)          # three equal troughs
    pats = patterns.detect(x.tolist(), list(range(len(x))))
    assert any("Bottom" in p["name"] and p["direction"] == "bullish" for p in pats)


def _zig(seq, seg=20):
    parts = [np.linspace(seq[i], seq[i + 1], seg, endpoint=False) for i in range(len(seq) - 1)]
    parts.append(np.array([seq[-1]]))
    return np.concatenate(parts)


def test_ascending_triangle_detected():
    # flat resistance ~110, rising support 100 -> 103 -> 106
    x = _zig([96, 110, 100, 110, 103, 110, 106, 110, 108])
    pats = patterns.detect(x.tolist(), list(range(len(x))))
    tri = next((p for p in pats if p["name"] == "Ascending Triangle"), None)
    assert tri is not None
    assert tri["direction"] == "bullish"
    assert tri["lines"] and len(tri["lines"]) == 2   # support + resistance drawn
    assert tri["explanation"]


def test_descending_channel_detected():
    # parallel falling rails
    x = _zig([120, 128, 112, 120, 104, 112, 96, 104, 90])
    pats = patterns.detect(x.tolist(), list(range(len(x))))
    ch = next((p for p in pats if p["name"] == "Descending Channel"), None)
    assert ch is not None
    assert ch["lines"] and len(ch["lines"]) == 2


def test_no_pattern_on_pure_trend():
    x = np.linspace(100, 200, 150)
    assert patterns.detect(x.tolist(), list(range(150))) == []


def test_short_series_returns_empty():
    assert patterns.detect([1, 2, 3], [0, 1, 2]) == []
