"""
Watchlist — companies you are following, and what changed since you looked.

The single rule this module exists to enforce: an alert is an INFORMATION
EVENT, never a prompt to act. "Price crossed the level you marked" and "a new
filing was published" are facts the learner asked to be told. "Time to buy" is
not something this app says, and phrasing is how that promise is kept or broken
at the moment it matters most — when something has just moved.

So every event here carries a neutral verb, and none carries a recommendation,
an urgency cue, or a direction to act.
"""
from __future__ import annotations

from services import marketdata, storage


def _crossing_event(w: dict, price: float) -> dict | None:
    """Did price cross the level the learner asked to be told about?"""
    # Coerce explicitly: a value round-tripped through a differently-typed
    # column would otherwise compare as a string and silently never fire.
    try:
        level = float(w["level"]) if w.get("level") is not None else None
        prev = float(w["last_seen"]) if w.get("last_seen") is not None else None
        price = float(price)
    except (TypeError, ValueError):
        return None
    if level is None or prev is None:
        return None
    if prev < level <= price:
        direction = "up through"
    elif prev > level >= price:
        direction = "down through"
    else:
        return None
    return {
        "kind": "level_crossed",
        # Neutral verb, no recommendation, no urgency.
        "text": f"Price moved {direction} {level}, the level you marked "
                f"(now {round(price, 2)}, was {round(prev, 2)} when last checked).",
        "context": "This is the level you asked to be told about — it is information, "
                   "not a signal. Nothing about a price crossing a number you chose "
                   "makes it a good or bad moment for anything.",
    }


def status(refresh: bool = True) -> dict:
    """Every watched company, its latest price, and what changed since last look."""
    items, errors = [], []
    for w in storage.watch_list():
        entry = {
            "ticker": w["ticker"], "name": w.get("name"), "note": w.get("note"),
            "level": w.get("level"), "addedAt": w.get("added_at"),
            "lastSeen": w.get("last_seen"), "price": None, "changePercent": None,
            "events": [], "asOf": None, "stale": None, "coverage": None,
        }
        if not refresh:
            items.append(entry)
            continue
        try:
            data = marketdata.get(w["ticker"], period="1mo")
        except marketdata.ProviderError as e:
            entry["error"] = str(e)
            errors.append(w["ticker"])
            items.append(entry)
            continue
        if data is None:
            entry["error"] = f"No market data found for {w['ticker']}."
            errors.append(w["ticker"])
            items.append(entry)
            continue

        hist, quote = data
        price = quote.get("price")
        fresh = marketdata.freshness(hist, "1d")
        entry.update({"price": price, "changePercent": quote.get("changePercent"),
                      "asOf": fresh["asOf"], "stale": fresh["stale"]})

        if price is not None:
            ev = _crossing_event(w, float(price))
            if ev:
                entry["events"].append(ev)
            storage.watch_record_price(w["ticker"], float(price))

        if fresh["stale"]:
            entry["events"].append({
                "kind": "stale_data",
                "text": f"The newest bar for {w['ticker']} is older than expected.",
                "context": fresh["note"],
            })
        items.append(entry)

    return {
        "items": items,
        "errors": errors,
        "note": "Everything here is an information event — something happened that you "
                "asked to be told about. None of it is a prompt to act, and a level you "
                "chose being crossed says nothing about whether anything should be done.",
    }
