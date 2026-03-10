from __future__ import annotations

from app.schemas import FilingDigestItem, SourceLink


def build_filings_digest(raw_items: list[dict[str, object]]) -> list[FilingDigestItem]:
    digest: list[FilingDigestItem] = []
    for item in raw_items[:4]:
        links = [link for link in item.get("links", []) if isinstance(link, SourceLink)]
        if not links:
            continue
        digest.append(
            FilingDigestItem(
                title=str(item["title"]),
                category=str(item["category"]),
                publishedAt=str(item["published_at"]),
                signal=str(item["signal"]),
                summary=str(item["summary"]),
                sourceIds=[link.id for link in links],
                links=links,
            )
        )
    return digest
