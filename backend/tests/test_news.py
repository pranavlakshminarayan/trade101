"""Google News RSS fallback (services.news._google_news) — the "more markets"
fix so non-US listings get real, keyless news beyond Yahoo/Finnhub."""
from datetime import datetime, timezone

from services import news

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<item>
  <title>Nintendo announces new console - Example News</title>
  <link>https://example.com/nintendo-console</link>
  <pubDate>{recent}</pubDate>
  <source url="https://example.com">Example News</source>
</item>
<item>
  <title>Old story with no date match</title>
  <link>https://example.com/old</link>
  <pubDate>{old}</pubDate>
  <source url="https://example.com">Example News</source>
</item>
</channel></rss>"""


class Resp:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


def test_google_news_parses_items_and_strips_source_suffix(monkeypatch):
    recent = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    old = "Mon, 01 Jan 2001 00:00:00 GMT"
    xml = SAMPLE_RSS.format(recent=recent, old=old).encode()
    monkeypatch.setattr(news.httpx, "get", lambda *a, **k: Resp(xml))

    items, note = news._google_news("7974.T", "Nintendo Co., Ltd.")
    assert note is None
    assert len(items) == 1  # the old-dated item falls outside the 30-day window
    assert items[0]["headline"] == "Nintendo announces new console"
    assert items[0]["source"] == "Example News"
    assert items[0]["url"] == "https://example.com/nintendo-console"


def test_google_news_degrades_on_provider_error(monkeypatch):
    def boom(*a, **k):
        raise Exception("network down")

    monkeypatch.setattr(news.httpx, "get", boom)
    items, note = news._google_news("7974.T", "Nintendo Co., Ltd.")
    assert items == []
    assert note  # friendly message, not a crash


def test_get_news_falls_back_to_google_then_yahoo(monkeypatch):
    monkeypatch.delenv("TRADE101_NEWS_KEY", raising=False)  # Finnhub returns nothing
    monkeypatch.setattr(news, "_google_news", lambda *a, **k: ([], "no google results"))
    monkeypatch.setattr(news, "_yahoo_news", lambda *a, **k: ([{"headline": "Yahoo item"}], None))

    items, note = news.get_news("7974.T", name="Nintendo Co., Ltd.")
    assert items == [{"headline": "Yahoo item"}]
