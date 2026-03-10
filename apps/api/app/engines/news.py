from __future__ import annotations

from datetime import datetime
import re

from app.catalog import StockProfile
from app.schemas import NewsDigestItem, SourceLink


def build_news_digest(profile: StockProfile, raw_items: list[dict[str, object]]) -> list[NewsDigestItem]:
    clusters: dict[str, list[dict[str, object]]] = {}
    for item in raw_items:
        headline = str(item["headline"])
        links = [link for link in item["links"] if isinstance(link, SourceLink)]
        if not links:
            continue
        topic = _infer_topic(f"{headline} {item['impact']}")
        dedupe_key = f"{topic}:{_normalize_text(headline)}"
        bucket = clusters.setdefault(topic, [])
        if any(entry["dedupe_key"] == dedupe_key for entry in bucket):
            continue
        bucket.append(
            {
                "headline": headline,
                "category": str(item["category"]),
                "impact": str(item["impact"]),
                "links": links,
                "published_at": links[0].published_at,
                "dedupe_key": dedupe_key,
            }
        )

    digest: list[NewsDigestItem] = []
    for topic, entries in sorted(clusters.items(), key=lambda pair: _cluster_rank(pair[1]), reverse=True):
        representative = sorted(entries, key=lambda item: _published_sort_key(item["published_at"]), reverse=True)[0]
        merged_links = _dedupe_links([link for entry in entries for link in entry["links"]])[:3]
        impact = representative["impact"]
        if len(entries) > 1:
            impact = f"{topic} 主题聚合了 {len(entries)} 条近端资讯。{impact}"
        digest.append(
            NewsDigestItem(
                headline=representative["headline"],
                category=representative["category"],
                topic=topic,
                impact=impact,
                sourceIds=[link.id for link in merged_links],
                links=merged_links,
            )
        )
        if len(digest) >= 3:
            break
    return digest


def _normalize_text(value: str) -> str:
    normalized = re.sub(r"[：:，,。!！?？\s]+", "", value.lower())
    normalized = re.sub(r"\d{2,}", "#", normalized)
    return normalized


def _infer_topic(text: str) -> str:
    topic_rules = [
        ("订单与产能", ("订单", "产能", "出货", "利用率")),
        ("业绩预期", ("业绩", "快报", "预告", "营收", "利润", "指引")),
        ("资金热度", ("成交额", "净流入", "融资买入", "etf", "资金")),
        ("算力链产品", ("cpo", "光模块", "激光器", "算力")),
        ("监管与风险", ("问询", "风险", "监管", "处罚", "异常波动")),
    ]
    lowered = text.lower()
    for topic, keywords in topic_rules:
        if any(keyword.lower() in lowered for keyword in keywords):
            return topic
    return "公司动态"


def _published_sort_key(value: str | None) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value[:19].replace(" ", "T"))
    except ValueError:
        return datetime.min


def _cluster_rank(entries: list[dict[str, object]]) -> tuple[int, datetime]:
    latest = max((_published_sort_key(entry["published_at"]) for entry in entries), default=datetime.min)
    return (len(entries), latest)


def _dedupe_links(links: list[SourceLink]) -> list[SourceLink]:
    merged: dict[str, SourceLink] = {}
    for link in links:
        merged[link.id] = link
    return list(merged.values())
