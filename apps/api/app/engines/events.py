from __future__ import annotations

from datetime import datetime

from app.schemas import EventCluster, FilingDigestItem, ForumDigestItem, NewsDigestItem, SourceLink


def build_event_clusters(
    filings_digest: list[FilingDigestItem],
    news_digest: list[NewsDigestItem],
    forum_digest: list[ForumDigestItem],
) -> list[EventCluster]:
    raw_items = [
        *_filing_items(filings_digest),
        *_news_items(news_digest),
        *_forum_items(forum_digest),
    ]
    raw_items.sort(key=lambda item: (_parse_date(item["published_at"]), item["topic"]))

    grouped: list[dict[str, object]] = []
    for item in raw_items:
        matched = None
        for cluster in grouped:
            if cluster["topic"] != item["topic"]:
                continue
            gap = abs((_parse_date(str(cluster["published_at"])) - _parse_date(item["published_at"])).days)
            if gap <= 7:
                matched = cluster
                break
        if matched is None:
            grouped.append(
                {
                    "topic": item["topic"],
                    "published_at": item["published_at"],
                    "items": [item],
                }
            )
        else:
            matched["items"].append(item)
            if _parse_date(item["published_at"]) > _parse_date(str(matched["published_at"])):
                matched["published_at"] = item["published_at"]

    clusters: list[EventCluster] = []
    for index, cluster in enumerate(sorted(grouped, key=lambda item: _cluster_sort_key(item), reverse=True)[:4]):
        items = cluster["items"]
        links = _dedupe_links([link for item in items for link in item["links"]])[:4]
        source_kinds = sorted({str(item["kind"]) for item in items})
        summary_bits = [str(item["headline"]) for item in items[:2]]
        summary = f"{cluster['topic']} 事件簇汇总了 {len(items)} 条跨源线索，核心包括 {'；'.join(summary_bits)}。"
        direction = _cluster_direction(items)
        clusters.append(
            EventCluster(
                id=f"event:{index}:{cluster['topic']}",
                topic=str(cluster["topic"]),
                publishedAt=str(cluster["published_at"]),
                direction=direction,
                summary=summary,
                sourceKinds=source_kinds,
                sourceIds=[link.id for link in links],
                links=links,
            )
        )
    return clusters


def _filing_items(items: list[FilingDigestItem]) -> list[dict[str, object]]:
    return [
        {
            "topic": item.category,
            "published_at": item.published_at,
            "headline": item.title,
            "summary": item.summary,
            "kind": "filing",
            "links": item.links,
            "direction": _direction_from_text(f"{item.signal} {item.summary}"),
        }
        for item in items
    ]


def _news_items(items: list[NewsDigestItem]) -> list[dict[str, object]]:
    return [
        {
            "topic": item.topic,
            "published_at": item.links[0].published_at or "",
            "headline": item.headline,
            "summary": item.impact,
            "kind": "news",
            "links": item.links,
            "direction": _direction_from_text(f"{item.topic} {item.impact}"),
        }
        for item in items
        if item.links
    ]


def _forum_items(items: list[ForumDigestItem]) -> list[dict[str, object]]:
    return [
        {
            "topic": item.topic,
            "published_at": item.published_at,
            "headline": item.title,
            "summary": item.summary,
            "kind": "forum",
            "links": item.links,
            "direction": _direction_from_text(f"{item.topic} {item.summary}"),
        }
        for item in items
    ]


def _cluster_sort_key(cluster: dict[str, object]) -> tuple[int, datetime]:
    items = cluster["items"]
    return (len(items), _parse_date(str(cluster["published_at"])))


def _cluster_direction(items: list[dict[str, object]]) -> str:
    positive = sum(1 for item in items if item["direction"] == "positive")
    negative = sum(1 for item in items if item["direction"] == "negative")
    if positive and negative:
        return "mixed"
    if positive:
        return "positive"
    if negative:
        return "negative"
    return "neutral"


def _direction_from_text(text: str) -> str:
    positive_keywords = ("订单", "增长", "回购", "增持", "景气", "净流入", "融资买入", "饱满")
    negative_keywords = ("减持", "质押", "风险", "问询", "处罚", "回调", "分歧", "未发布")
    positive = sum(1 for item in positive_keywords if item in text)
    negative = sum(1 for item in negative_keywords if item in text)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def _parse_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value[:19].replace(" ", "T"))
    except ValueError:
        return datetime.min


def _dedupe_links(links: list[SourceLink]) -> list[SourceLink]:
    merged: dict[str, SourceLink] = {}
    for link in links:
        merged[link.id] = link
    return list(merged.values())
