from __future__ import annotations

from app.catalog import StockProfile
from app.schemas import ComparableStock


def build_comparables(profile: StockProfile, related: list[StockProfile]) -> list[ComparableStock]:
    comparables: list[ComparableStock] = []
    for item in related[:3]:
        overlap = " / ".join(item.concepts[:2])
        edge = (
            "题材纯度更高" if item.volatility_score > profile.volatility_score
            else "波动更低，更适合稳健替代"
        )
        comparables.append(
            ComparableStock(
                symbol=item.symbol,
                name=item.name,
                reason=f"与当前标的共享相近赛道，核心共性是 {overlap}。",
                edge=edge,
                qualityScore=item.quality_score,
                volatilityScore=item.volatility_score,
            )
        )
    return comparables

