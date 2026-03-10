from fastapi.testclient import TestClient

from app.engines.forum import build_forum_digest
from app.engines.news import build_news_digest
from app.engines.timeline import _best_digest_item
from app.main import app
from app.schemas import SourceLink


client = TestClient(app)


def test_stock_search_returns_matches() -> None:
    response = client.get("/api/v1/stocks/search", params={"q": "AI", "limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert any(item["symbol"] == "300308.SZ" for item in payload)


def test_system_status_exposes_provider_mode() -> None:
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["activeProvider"] in {"mock", "tushare", "akshare"}
    assert payload["capabilities"]


def test_report_contains_links_and_narrative() -> None:
    response = client.post(
        "/api/v1/research/report",
        json={"symbol": "300308.SZ", "includeRetailSentiment": True, "forceRefresh": True},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["symbol"] == "300308.SZ"
    assert len(payload["narrativeStages"]) == 4
    assert payload["dataReadiness"]
    assert payload["sources"]
    assert payload["sourceLinks"][0]["url"].startswith("https://")
    assert payload["timeline"][0]["evidence"][0]["sourceIds"]
    assert payload["timeline"][0]["evidence"][0]["links"]
    assert payload["timeline"][0]["evidence"][0]["role"] in {"main", "support", "counter"}
    assert isinstance(payload["timeline"][0]["evidence"][0]["score"], float)
    assert payload["filingsDigest"]
    assert payload["filingsDigest"][0]["links"]
    assert payload["eventClusters"]
    assert payload["eventClusters"][0]["sourceKinds"]
    assert payload["forumDigest"]
    assert payload["forumDigest"][0]["topic"]
    assert payload["forumDigest"][0]["links"]
    assert payload["newsDigest"][0]["topic"]
    assert payload["newsDigest"][0]["sourceIds"]
    assert payload["newsDigest"][0]["links"]
    assert payload["retailSentiment"] is not None
    assert payload["retailSentiment"]["links"]
    assert payload["provider"]


def test_report_can_disable_retail_sentiment() -> None:
    response = client.post(
        "/api/v1/research/report",
        json={"symbol": "600036.SH", "includeRetailSentiment": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["retailSentiment"] is None


def test_report_markdown_export_contains_citations() -> None:
    response = client.post(
        "/api/v1/research/report/markdown",
        json={"symbol": "300308.SZ", "includeRetailSentiment": True},
    )
    assert response.status_code == 200
    body = response.text
    assert "# 中际旭创 300308.SZ" in body
    assert "## 数据就绪状态" in body
    assert "## 公告与披露" in body
    assert "## 事件簇" in body
    assert "## 社区热议" in body
    assert "main /" in body or "support /" in body or "counter /" in body
    assert "https://quote.eastmoney.com" in body


def test_recent_research_and_latest_snapshot() -> None:
    create_response = client.post(
        "/api/v1/research/report",
        json={"symbol": "600036.SH", "includeRetailSentiment": True, "forceRefresh": True},
    )
    assert create_response.status_code == 200

    recent_response = client.get("/api/v1/research/recent", params={"limit": 20})
    assert recent_response.status_code == 200
    recent_payload = recent_response.json()
    assert any(item["symbol"] == "600036.SH" for item in recent_payload)

    latest_response = client.get("/api/v1/research/latest/600036.SH")
    assert latest_response.status_code == 200
    latest_payload = latest_response.json()
    assert latest_payload["symbol"] == "600036.SH"


def test_report_cache_and_force_refresh() -> None:
    fresh_response = client.post(
        "/api/v1/research/report",
        json={"symbol": "002594.SZ", "forceRefresh": True},
    )
    assert fresh_response.status_code == 200
    fresh_payload = fresh_response.json()
    assert fresh_payload["fromCache"] is False

    cached_response = client.post(
        "/api/v1/research/report",
        json={"symbol": "002594.SZ"},
    )
    assert cached_response.status_code == 200
    cached_payload = cached_response.json()
    assert cached_payload["fromCache"] is True


def test_compare_endpoint_returns_primary_and_peers() -> None:
    response = client.post(
        "/api/v1/research/compare",
        json={"symbol": "300308.SZ", "peerSymbols": ["000977.SZ", "002594.SZ"]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["primarySymbol"] == "300308.SZ"
    assert any(item["relation"] == "primary" for item in payload["rows"])
    assert any(item["relation"] == "peer" for item in payload["rows"])


def test_news_digest_deduplicates_similar_titles() -> None:
    link = SourceLink(
        id="n1",
        label="新闻 1",
        url="https://example.com/1",
        domain="example.com",
        kind="news",
        publishedAt="2026-03-09",
        note="test",
    )
    digest = build_news_digest(
        profile=type("P", (), {"name": "中际旭创"})(),  # lightweight stand-in
        raw_items=[
            {"headline": "中际旭创：公司订单饱满 产能利用率充足", "category": "公司", "impact": "A", "links": [link]},
            {"headline": "中际旭创：公司订单饱满，产能利用率充足", "category": "公司", "impact": "B", "links": [link]},
            {"headline": "中际旭创：公司目前未发布任何业绩指引", "category": "公司", "impact": "C", "links": [link]},
        ],
    )
    assert len(digest) == 2
    assert all(item.topic for item in digest)


def test_forum_digest_deduplicates_similar_titles_per_platform() -> None:
    link = SourceLink(
        id="f1",
        label="帖子 1",
        url="https://example.com/f1",
        domain="example.com",
        kind="forum",
        publishedAt="2026-03-09",
        note="test",
    )
    digest = build_forum_digest(
        [
            {
                "title": "中际旭创：3月6日获融资买入14.50亿元",
                "platform": "同花顺",
                "published_at": "2026-03-09 09:04",
                "heat": "高",
                "summary": "A",
                "links": [link],
            },
            {
                "title": "中际旭创：3月6日获融资买入14.50 亿元",
                "platform": "同花顺",
                "published_at": "2026-03-09 09:05",
                "heat": "高",
                "summary": "B",
                "links": [link],
            },
            {
                "title": "中际旭创：公司订单饱满，产能利用率充足",
                "platform": "东方财富股吧",
                "published_at": "2026-03-08 21:54:49",
                "heat": "阅读 3597 / 评论 9",
                "summary": "C",
                "links": [link],
            },
        ]
    )
    assert len(digest) == 2
    assert all(item.topic for item in digest)


def test_report_event_clusters_are_present() -> None:
    response = client.post(
        "/api/v1/research/report",
        json={"symbol": "300308.SZ", "includeRetailSentiment": True, "forceRefresh": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["eventClusters"]
    assert payload["eventClusters"][0]["direction"] in {"positive", "negative", "mixed", "neutral"}
    assert any("事件簇" in item["title"] for item in payload["risks"])
    assert any("事件跟踪:" in item for item in payload["monitorPoints"])


def test_timeline_match_does_not_pick_future_event() -> None:
    profile = type("P", (), {"name": "中际旭创", "symbol": "300308.SZ", "concepts": ("AI 算力",), "sector": "光模块 / AI 算力"})()
    future_item = type(
        "E",
        (),
        {"topic": "股权变动", "summary": "未来公告", "published_at": "2026-03-07", "title": "未来事件"},
    )()
    assert _best_digest_item(profile, "2026-02-02", [future_item], "down") is None
