from typing import Literal

from pydantic import BaseModel, Field


PriceMove = Literal["up", "down", "flat"]
RiskLevel = Literal["low", "medium", "high"]
EvidenceRole = Literal["main", "support", "counter"]


class CamelModel(BaseModel):
    model_config = {"populate_by_name": True}


class ResearchRequest(CamelModel):
    symbol: str = Field(..., description="Stock code, e.g. 000001.SZ")
    company_name: str | None = Field(default=None, alias="companyName")
    analysis_window_days: int = Field(default=365, alias="analysisWindowDays", ge=30, le=730)
    include_retail_sentiment: bool = Field(default=True, alias="includeRetailSentiment")
    force_refresh: bool = Field(default=False, alias="forceRefresh")
    max_snapshot_age_minutes: int | None = Field(default=None, alias="maxSnapshotAgeMinutes", ge=1, le=1440)


class StockLookupResult(CamelModel):
    symbol: str
    name: str
    market: str
    sector: str
    concepts: list[str]


class SourceLink(CamelModel):
    id: str
    label: str
    url: str
    domain: str
    kind: str
    published_at: str | None = Field(default=None, alias="publishedAt")
    note: str


class DataReadinessItem(CamelModel):
    key: str
    label: str
    status: Literal["ready", "mock", "missing"]
    detail: str


class SystemStatus(CamelModel):
    environment: str
    requested_provider: str = Field(alias="requestedProvider")
    active_provider: str = Field(alias="activeProvider")
    degraded: bool
    reason: str | None = None
    capabilities: list[DataReadinessItem]


class ReportSnapshotSummary(CamelModel):
    symbol: str
    company_name: str = Field(alias="companyName")
    market: str
    sector: str
    risk_level: RiskLevel = Field(alias="riskLevel")
    generated_at: str = Field(alias="generatedAt")
    thesis: str


class CompareRequest(CamelModel):
    symbol: str
    peer_symbols: list[str] | None = Field(default=None, alias="peerSymbols")
    include_retail_sentiment: bool = Field(default=False, alias="includeRetailSentiment")
    force_refresh: bool = Field(default=False, alias="forceRefresh")


class ComparisonRow(CamelModel):
    symbol: str
    company_name: str = Field(alias="companyName")
    sector: str
    risk_level: RiskLevel = Field(alias="riskLevel")
    risk_score: int = Field(alias="riskScore")
    confidence: float
    trading_style: str = Field(alias="tradingStyle")
    thesis: str
    relation: Literal["primary", "peer"]


class CompareResponse(CamelModel):
    primary_symbol: str = Field(alias="primarySymbol")
    rows: list[ComparisonRow]


class EvidenceLine(CamelModel):
    source: str
    signal: str
    summary: str
    role: EvidenceRole
    score: float
    source_ids: list[str] = Field(alias="sourceIds")
    links: list[SourceLink]


class NarrativeStage(CamelModel):
    title: str
    date_range: str = Field(alias="dateRange")
    status: Literal["build", "accelerate", "diverge", "cooldown"]
    summary: str
    driver: str
    source_ids: list[str] = Field(alias="sourceIds")
    links: list[SourceLink]


class TimelineEvent(CamelModel):
    date: str
    move: PriceMove
    change_pct: float = Field(alias="changePct")
    summary: str
    catalyst: str
    sector: str
    ladder_position: str = Field(alias="ladderPosition")
    interpretation: str
    confidence: float
    evidence: list[EvidenceLine]


class RiskItem(CamelModel):
    title: str
    level: RiskLevel
    score: int
    detail: str
    watch: bool


class ComparableStock(CamelModel):
    symbol: str
    name: str
    reason: str
    edge: str
    quality_score: int = Field(alias="qualityScore")
    volatility_score: int = Field(alias="volatilityScore")


class SentimentSnapshot(CamelModel):
    bullish_ratio: float = Field(alias="bullishRatio")
    bearish_ratio: float = Field(alias="bearishRatio")
    neutrality_ratio: float = Field(alias="neutralityRatio")
    summary: str
    keywords: list[str]
    source_ids: list[str] = Field(default_factory=list, alias="sourceIds")
    links: list[SourceLink] = Field(default_factory=list)


class NewsDigestItem(CamelModel):
    headline: str
    category: str
    topic: str
    impact: str
    source_ids: list[str] = Field(alias="sourceIds")
    links: list[SourceLink]


class FilingDigestItem(CamelModel):
    title: str
    category: str
    published_at: str = Field(alias="publishedAt")
    signal: str
    summary: str
    source_ids: list[str] = Field(alias="sourceIds")
    links: list[SourceLink]


class ForumDigestItem(CamelModel):
    title: str
    platform: str
    topic: str
    published_at: str = Field(alias="publishedAt")
    heat: str
    summary: str
    source_ids: list[str] = Field(alias="sourceIds")
    links: list[SourceLink]


class EventCluster(CamelModel):
    id: str
    topic: str
    published_at: str = Field(alias="publishedAt")
    direction: Literal["positive", "negative", "mixed", "neutral"]
    summary: str
    source_kinds: list[str] = Field(alias="sourceKinds")
    source_ids: list[str] = Field(alias="sourceIds")
    links: list[SourceLink]


class MarketPulse(CamelModel):
    regime: str
    risk_appetite: str = Field(alias="riskAppetite")
    dominant_themes: list[str] = Field(alias="dominantThemes")
    commentary: str


class ResearchOverview(CamelModel):
    trading_style: str = Field(alias="tradingStyle")
    dominant_narrative: str = Field(alias="dominantNarrative")
    bull_case: str = Field(alias="bullCase")
    bear_case: str = Field(alias="bearCase")
    key_question: str = Field(alias="keyQuestion")


class ResearchResponse(CamelModel):
    symbol: str
    company_name: str = Field(alias="companyName")
    market: str
    sector: str
    concept_tags: list[str] = Field(alias="conceptTags")
    source_links: list[SourceLink] = Field(alias="sourceLinks")
    sources: list[SourceLink]
    data_readiness: list[DataReadinessItem] = Field(alias="dataReadiness")
    narrative_stages: list[NarrativeStage] = Field(alias="narrativeStages")
    overview: ResearchOverview
    market_pulse: MarketPulse = Field(alias="marketPulse")
    thesis: str
    risk_level: RiskLevel = Field(alias="riskLevel")
    risk_score: int = Field(alias="riskScore")
    confidence: float
    provider: str
    from_cache: bool = Field(alias="fromCache")
    using_live_data: bool = Field(alias="usingLiveData")
    generated_at: str = Field(alias="generatedAt")
    timeline: list[TimelineEvent]
    risks: list[RiskItem]
    comparables: list[ComparableStock]
    filings_digest: list[FilingDigestItem] = Field(default_factory=list, alias="filingsDigest")
    forum_digest: list[ForumDigestItem] = Field(default_factory=list, alias="forumDigest")
    event_clusters: list[EventCluster] = Field(default_factory=list, alias="eventClusters")
    news_digest: list[NewsDigestItem] = Field(alias="newsDigest")
    retail_sentiment: SentimentSnapshot | None = Field(default=None, alias="retailSentiment")
    monitor_points: list[str] = Field(alias="monitorPoints")
    disclaimer: str
