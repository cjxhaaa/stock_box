from __future__ import annotations

from datetime import datetime
import re

from app.schemas import ForumDigestItem, SourceLink


def build_forum_digest(raw_items: list[dict[str, object]]) -> list[ForumDigestItem]:
    clusters: dict[str, list[dict[str, object]]] = {}
    for item in raw_items:
        links = [link for link in item.get("links", []) if isinstance(link, SourceLink)]
        if not links:
            continue
        title = str(item["title"])
        topic = _infer_topic(f"{title} {item['summary']}")
        dedupe_key = f"{topic}:{str(item['platform'])}:{_normalize_text(title)}"
        bucket = clusters.setdefault(topic, [])
        if any(entry["dedupe_key"] == dedupe_key for entry in bucket):
            continue
        bucket.append(
            {
                "title": title,
                "platform": str(item["platform"]),
                "published_at": str(item["published_at"]),
                "heat": str(item["heat"]),
                "summary": str(item["summary"]),
                "links": links,
                "dedupe_key": dedupe_key,
            }
        )

    digest: list[ForumDigestItem] = []
    for topic, entries in sorted(clusters.items(), key=lambda pair: _cluster_rank(pair[1]), reverse=True):
        representative = sorted(entries, key=lambda item: _published_sort_key(item["published_at"]), reverse=True)[0]
        merged_links = _dedupe_links([link for entry in entries for link in entry["links"]])[:3]
        platforms = " / ".join(sorted({entry["platform"] for entry in entries}))
        summary = representative["summary"]
        if len(entries) > 1:
            summary = f"{topic} 主题聚合了 {len(entries)} 条社区讨论。{summary}"
        digest.append(
            ForumDigestItem(
                title=representative["title"],
                platform=platforms,
                topic=topic,
                publishedAt=representative["published_at"],
                heat=representative["heat"],
                summary=summary,
                sourceIds=[link.id for link in merged_links],
                links=merged_links,
            )
        )
        if len(digest) >= 5:
            break
    return digest


def _normalize_text(value: str) -> str:
    normalized = re.sub(r"[：:，,。!！?？\s]+", "", value.lower())
    normalized = re.sub(r"\d{2,}", "#", normalized)
    return normalized


def _infer_topic(text: str) -> str:
    topic_rules = [
        ("订单与产能", ("订单", "产能", "利用率")),
        ("融资与资金", ("融资买入", "净流入", "资金", "成交额", "etf")),
        ("产品与题材", ("激光器", "cpo", "光模块", "英伟达", "算力")),
        ("业绩预期", ("业绩", "指引", "利润", "营收")),
        ("风险与分歧", ("回调", "分歧", "减持", "质押", "风险")),
    ]
    lowered = text.lower()
    for topic, keywords in topic_rules:
        if any(keyword.lower() in lowered for keyword in keywords):
            return topic
    return "社区观点"


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
