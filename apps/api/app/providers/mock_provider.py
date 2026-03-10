from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from random import Random

from app.catalog import CATALOG, StockProfile, get_profile, search_profiles
from app.data.evidence_seed import seeded_sources
from app.providers.models import DailyBar
from app.schemas import DataReadinessItem, SourceLink


@dataclass(frozen=True)
class MarketSnapshot:
    regime: str
    risk_appetite: str
    dominant_themes: tuple[str, ...]
    commentary: str


class MockResearchProvider:
    provider_name = "mock"
    provider_mode = "mock"
    degraded_reason: str | None = None

    def search_stocks(self, query: str, limit: int = 8) -> list[StockProfile]:
        return search_profiles(query, limit)

    def get_stock_profile(self, symbol: str) -> StockProfile:
        profile = get_profile(symbol)
        if profile is not None:
            return profile

        normalized = symbol.strip().upper() or "UNKNOWN"
        return StockProfile(
            symbol=normalized,
            name=f"{normalized} 调研标的",
            market="A股",
            sector="多因子待识别",
            concepts=("公告驱动", "题材博弈", "市场风格"),
            archetype="generalist",
            quality_score=68,
            volatility_score=61,
            peers=tuple(item.symbol for item in CATALOG[:3]),
        )

    def related_profiles(self, profile: StockProfile) -> list[StockProfile]:
        related: list[StockProfile] = []
        for symbol in profile.peers:
            match = get_profile(symbol)
            if match is not None:
                related.append(match)
        return related

    def market_snapshot(self, profile: StockProfile) -> MarketSnapshot:
        rng = self._rng(profile.symbol, "market")
        regimes = (
            "题材轮动加快，主线集中度中等",
            "指数震荡，市场偏向结构性机会",
            "风险偏好回升，高弹性方向更占优",
            "防御资产相对占优，追高胜率一般",
        )
        risk_appetites = ("偏进攻", "中性偏进攻", "中性", "中性偏防御")
        theme_pool = tuple(profile.concepts) + ("业绩验证", "监管预期", "资金切换")
        dominant_themes = tuple(rng.sample(theme_pool, k=3))
        commentary = (
            f"当前与 {profile.name} 相关的市场叙事主要围绕 "
            f"{' / '.join(dominant_themes)} 展开，短线表现更依赖风格与消息密度。"
        )
        return MarketSnapshot(
            regime=rng.choice(regimes),
            risk_appetite=rng.choice(risk_appetites),
            dominant_themes=dominant_themes,
            commentary=commentary,
        )

    def build_source_links(self, profile: StockProfile) -> list[SourceLink]:
        links = self.reference_bundle(profile)
        return [links["market"], links["filing"], links["forum"], links["ths"], links["community"], links["irm"]]

    def data_readiness(self) -> list[DataReadinessItem]:
        return [
            DataReadinessItem(
                key="market",
                label="行情与板块",
                status="mock",
                detail="当前使用本地规则和静态样本，尚未接入实时行情与板块异动。",
            ),
            DataReadinessItem(
                key="filings",
                label="公告与财报",
                status="missing",
                detail="链接已准备，但还没有自动抓取公告、问询函和财报原文。",
            ),
            DataReadinessItem(
                key="news",
                label="新闻聚合",
                status="mock",
                detail="当前由 mock provider 生成主题摘要，尚未接入多源新闻召回。",
            ),
            DataReadinessItem(
                key="forum",
                label="股吧与社区",
                status="mock",
                detail="当前情绪结果为规则模拟值，尚未直连东方财富、同花顺、雪球原帖。",
            ),
            DataReadinessItem(
                key="llm",
                label="报告生成",
                status="ready",
                detail="当前结构化报告和 Markdown 导出链路已可用，后续可替换为真实证据编排。",
            ),
        ]

    def reference_bundle(self, profile: StockProfile) -> dict[str, SourceLink]:
        return self._source_link_map(profile)

    def news_pool(self, profile: StockProfile) -> list[dict[str, object]]:
        links = self.reference_bundle(profile)
        concept = profile.concepts[0]
        sector = profile.sector.split(" / ")[0]
        return [
            {
                "headline": f"{concept} 讨论热度抬升",
                "category": "热门话题",
                "impact": f"如果市场主线继续聚焦 {concept}，{profile.name} 容易获得增量关注。",
                "links": [links["community"], links["forum"]],
            },
            {
                "headline": f"{sector} 相关政策预期升温",
                "category": "政策",
                "impact": f"政策催化会提高 {profile.sector} 的阶段性估值弹性。",
                "links": [links["market"], links["filing"]],
            },
            {
                "headline": f"{profile.name} 所处产业链景气验证",
                "category": "产业链",
                "impact": "若订单、价格或出货数据改善，将强化基本面支撑。",
                "links": [links["filing"], links["market"]],
            },
            {
                "headline": "监管持续关注异常波动标的",
                "category": "监管",
                "impact": "高位纯情绪驱动个股的接力风险会被放大。",
                "links": [links["filing"], links["market"]],
            },
        ]

    def disclosure_pool(self, profile: StockProfile) -> list[dict[str, object]]:
        links = self.reference_bundle(profile)
        return [
            {
                "title": f"{profile.name} 年报与业绩说明入口",
                "category": "定期报告",
                "published_at": "2026-03-09",
                "signal": "跟踪业绩兑现与利润率变化",
                "summary": "当前 mock provider 仅提供公告入口，正式接入后会替换为公告级摘要与原文链接。",
                "links": [links["filing"]],
            },
            {
                "title": f"{profile.name} 股东和交易结构观察",
                "category": "股权变动",
                "published_at": "2026-03-09",
                "signal": "跟踪减持、质押和重要股东动作",
                "summary": "暴雷与交易风险评估会重点吸收股东减持、质押、问询函等公告信号。",
                "links": [links["filing"], links["market"]],
            },
        ]

    def community_pool(self, profile: StockProfile) -> list[dict[str, object]]:
        links = self.reference_bundle(profile)
        return [
            {
                "title": f"{profile.name} 股吧热议主线仍围绕 {profile.concepts[0]}",
                "platform": "东方财富",
                "published_at": "2026-03-09 14:30",
                "heat": "高热度",
                "summary": "高频讨论集中在主线延续、板块龙头扩散和高位兑现节奏。",
                "links": [links["forum"]],
            },
            {
                "title": f"{profile.name} 同花顺资金与资讯标签偏向 {profile.concepts[0]}",
                "platform": "同花顺",
                "published_at": "2026-03-09 10:20",
                "heat": "中高热度",
                "summary": "舆论重心更多是资金流、订单兑现和景气验证，而不是纯题材空转。",
                "links": [links["ths"]],
            },
            {
                "title": f"{profile.name} 雪球观点分歧聚焦估值与持续性",
                "platform": "雪球",
                "published_at": "2026-03-09 09:40",
                "heat": "观察样本",
                "summary": "用于补充长文本观点入口，当前不作为稳定抓取源。",
                "links": [links["community"]],
            },
        ]

    def forum_snapshot(self, profile: StockProfile) -> dict[str, object]:
        rng = self._rng(profile.symbol, "forum")
        bullish = round(0.34 + rng.random() * 0.28, 2)
        bearish = round(0.14 + rng.random() * 0.22, 2)
        neutrality = round(max(0.0, 1 - bullish - bearish), 2)
        tags = list(rng.sample(list(profile.concepts) + ["低吸", "反包", "趋势", "减持"], k=4))
        links = self.reference_bundle(profile)
        return {
            "bullish_ratio": bullish,
            "bearish_ratio": bearish,
            "neutrality_ratio": neutrality,
            "keywords": tags,
            "links": [links["forum"], links["ths"], links["community"]],
        }

    def get_price_history(self, profile: StockProfile, window_days: int) -> list[DailyBar]:
        rng = self._rng(profile.symbol, f"price:{window_days}")
        price = 100.0 + rng.random() * 40
        bars: list[DailyBar] = []
        for offset in range(min(window_days, 90)):
            pct_change = round(rng.uniform(-6.5, 6.5), 2)
            open_price = round(price, 2)
            close_price = round(max(1.0, price * (1 + pct_change / 100)), 2)
            high = round(max(open_price, close_price) * (1 + rng.uniform(0.0, 0.03)), 2)
            low = round(min(open_price, close_price) * (1 - rng.uniform(0.0, 0.03)), 2)
            amount = float(round(rng.uniform(2.5e8, 5.5e9), 2))
            turnover = round(rng.uniform(1.0, 9.0), 2)
            bars.append(
                DailyBar(
                    trade_date=f"2025-01-{(offset % 28) + 1:02d}",
                    open=open_price,
                    close=close_price,
                    high=high,
                    low=low,
                    amount=amount,
                    turnover_rate=turnover,
                    pct_change=pct_change,
                )
            )
            price = close_price
        return bars

    def _rng(self, symbol: str, salt: str) -> Random:
        seed = int(sha256(f"{symbol}:{salt}".encode("utf-8")).hexdigest()[:8], 16)
        return Random(seed)

    def _source_link_map(self, profile: StockProfile) -> dict[str, SourceLink]:
        sources = seeded_sources(profile.symbol, profile.name)
        return {
            "market": sources["market_quote"],
            "filing": sources["cninfo_profile"],
            "forum": sources["eastmoney_forum"],
            "ths": sources["ths_stock"],
            "community": sources["xueqiu_stock"],
            "irm": sources["cninfo_irm"],
            "theme": sources["theme_reference"],
            "stage_build": sources.get("stage_build", sources["theme_reference"]),
            "stage_diverge": sources.get("stage_diverge", sources["cninfo_profile"]),
        }
