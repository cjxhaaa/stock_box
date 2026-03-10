from __future__ import annotations

from datetime import datetime, timezone

from app.engines.events import build_event_clusters
from app.engines.filings import build_filings_digest
from app.engines.forum import build_forum_digest
from app.engines.market import build_market_pulse
from app.engines.narrative import build_narrative_stages
from app.engines.news import build_news_digest
from app.engines.overview import build_overview
from app.engines.peers import build_comparables
from app.engines.risk import build_risks
from app.engines.sentiment import build_sentiment
from app.engines.timeline import build_timeline
from app.providers.base import ResearchProvider
from app.schemas import ComparisonRow, ResearchRequest, ResearchResponse, StockLookupResult


class ResearchOrchestrator:
    def __init__(self, provider: ResearchProvider) -> None:
        self.provider = provider

    def search_stocks(self, query: str, limit: int = 8) -> list[StockLookupResult]:
        return [
            StockLookupResult(
                symbol=item.symbol,
                name=item.name,
                market=item.market,
                sector=item.sector,
                concepts=list(item.concepts),
            )
            for item in self.provider.search_stocks(query, limit)
        ]

    def generate_report(self, request: ResearchRequest) -> ResearchResponse:
        profile = self.provider.get_stock_profile(request.symbol)
        reference_bundle = self.provider.reference_bundle(profile)
        sources = list({item.id: item for item in reference_bundle.values()}.values())
        data_readiness = self.provider.data_readiness()
        market_snapshot = self.provider.market_snapshot(profile)
        related_profiles = self.provider.related_profiles(profile)
        price_history = self.provider.get_price_history(profile, request.analysis_window_days)
        filings_digest = build_filings_digest(self.provider.disclosure_pool(profile))
        news_digest = build_news_digest(profile, self.provider.news_pool(profile))
        forum_digest = build_forum_digest(self.provider.community_pool(profile))
        event_clusters = build_event_clusters(filings_digest, news_digest, forum_digest)
        market_pulse = build_market_pulse(market_snapshot)
        overview = build_overview(profile, market_pulse)
        timeline = build_timeline(
            profile,
            request.analysis_window_days,
            reference_bundle,
            filings_digest=filings_digest,
            news_digest=news_digest,
            forum_digest=forum_digest,
            event_clusters=event_clusters,
            price_history=price_history,
        )
        timeline_ranges = _timeline_ranges(timeline)
        narrative_stages = build_narrative_stages(
            profile,
            timeline_ranges,
            reference_bundle,
        )
        risk_score, risk_level, risks, monitor_points = build_risks(profile, filings_digest, event_clusters)
        comparables = build_comparables(profile, related_profiles)
        retail_sentiment = None
        if request.include_retail_sentiment:
            retail_sentiment = build_sentiment(profile, self.provider.forum_snapshot(profile))

        thesis = (
            f"{profile.name} 当前更适合放在“{profile.concepts[0]} + {profile.sector}”框架里观察。"
            f" 在 {market_pulse.regime} 的环境下，短线关键不只是涨跌本身，而是它是否仍处在主线梯队内并拿到持续催化。"
        )
        sources = _merge_sources(
            sources,
            [link for item in narrative_stages for link in item.links],
            [link for item in timeline for evidence in item.evidence for link in evidence.links],
            [link for item in filings_digest for link in item.links],
            [link for item in forum_digest for link in item.links],
            [link for item in event_clusters for link in item.links],
            [link for item in news_digest for link in item.links],
            retail_sentiment.links if retail_sentiment is not None else [],
            self.provider.build_source_links(profile),
        )

        return ResearchResponse(
            symbol=profile.symbol,
            companyName=request.company_name or profile.name,
            market=profile.market,
            sector=profile.sector,
            conceptTags=list(profile.concepts),
            sourceLinks=self.provider.build_source_links(profile),
            sources=sources,
            dataReadiness=data_readiness,
            narrativeStages=narrative_stages,
            overview=overview,
            marketPulse=market_pulse,
            thesis=thesis,
            riskLevel=risk_level,
            riskScore=risk_score,
            confidence=round(0.61 + (profile.quality_score - profile.volatility_score) / 300, 2),
            provider=getattr(self.provider, "provider_name", "unknown"),
            fromCache=False,
            usingLiveData=getattr(self.provider, "provider_mode", "mock") != "mock",
            generatedAt=datetime.now(timezone.utc).isoformat(),
            timeline=timeline,
            risks=risks,
            comparables=comparables,
            filingsDigest=filings_digest,
            forumDigest=forum_digest,
            eventClusters=event_clusters,
            newsDigest=news_digest,
            retailSentiment=retail_sentiment,
            monitorPoints=monitor_points,
            disclaimer=(
                f"当前结果由 {getattr(self.provider, 'provider_name', 'unknown')} provider 生成，不构成投资建议。"
                "后续接入更完整的公告、新闻和论坛证据后，字段结构保持不变。"
            ),
        )

    def compare_rows(self, reports: list[ResearchResponse], primary_symbol: str) -> list[ComparisonRow]:
        rows: list[ComparisonRow] = []
        normalized_primary = primary_symbol.strip().upper()
        for report in reports:
            rows.append(
                ComparisonRow(
                    symbol=report.symbol,
                    companyName=report.company_name,
                    sector=report.sector,
                    riskLevel=report.risk_level,
                    riskScore=report.risk_score,
                    confidence=report.confidence,
                    tradingStyle=report.overview.trading_style,
                    thesis=report.thesis,
                    relation="primary" if report.symbol == normalized_primary else "peer",
                )
            )
        return rows


def _merge_sources(*groups):
    merged = {}
    for group in groups:
        for item in group:
            merged[item.id] = item
    return list(merged.values())


def _timeline_ranges(timeline) -> list[str]:
    if len(timeline) < 2:
        return []
    return [f"{timeline[index].date} - {timeline[index + 1].date}" for index in range(len(timeline) - 1)]
