from __future__ import annotations

from app.catalog import StockProfile
from app.schemas import MarketPulse, ResearchOverview


def build_overview(profile: StockProfile, pulse: MarketPulse) -> ResearchOverview:
    leading_concept = profile.concepts[0]
    trading_style = {
        "high_beta_growth": "高弹性主线博弈",
        "defensive_income": "防御与轮动配置",
        "quality_compounder": "中长期机构持仓",
        "platform_leader": "产业龙头趋势交易",
        "cyclical_resource": "周期与商品驱动",
        "policy_sensitive_quality": "政策敏感型机构博弈",
        "generalist": "事件驱动观察",
    }.get(profile.archetype, "事件驱动观察")

    bull_case = f"{leading_concept} 继续维持热度，且 {profile.name} 能拿到更强的景气验证或资金承接。"
    bear_case = "若市场主线切换、监管趋严或业绩验证落空，股价可能从叙事定价回到估值定价。"

    return ResearchOverview(
        tradingStyle=trading_style,
        dominantNarrative=f"{profile.name} 当前更像“{leading_concept}”框架下的 {profile.sector} 代表标的。",
        bullCase=bull_case,
        bearCase=bear_case,
        keyQuestion=f"在当前 {pulse.regime} 的环境下，{profile.name} 能否持续留在主线视野内？",
    )

