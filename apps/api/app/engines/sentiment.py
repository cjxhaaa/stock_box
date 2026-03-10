from __future__ import annotations

from app.catalog import StockProfile
from app.schemas import SentimentSnapshot, SourceLink


def build_sentiment(profile: StockProfile, forum_snapshot: dict[str, object]) -> SentimentSnapshot:
    bullish = float(forum_snapshot["bullish_ratio"])
    bearish = float(forum_snapshot["bearish_ratio"])
    neutral = float(forum_snapshot["neutrality_ratio"])
    keywords = [str(item) for item in forum_snapshot["keywords"]]
    links = [link for link in forum_snapshot.get("links", []) if isinstance(link, SourceLink)]

    if bullish >= 0.55:
        summary = "散户情绪明显偏多，一致性较高，适合重点防范高位接力后的兑现风险。"
    elif bearish >= 0.33:
        summary = "讨论区分歧较大，负面观点抬升，通常意味着资金对持续性存在担忧。"
    else:
        summary = f"围绕 {profile.name} 的讨论偏中性，更多是在交易主线持续性而非单纯情绪宣泄。"

    return SentimentSnapshot(
        bullishRatio=bullish,
        bearishRatio=bearish,
        neutralityRatio=neutral,
        summary=summary,
        keywords=keywords,
        sourceIds=[link.id for link in links],
        links=links,
    )
