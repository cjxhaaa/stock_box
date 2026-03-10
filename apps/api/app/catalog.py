from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockProfile:
    symbol: str
    name: str
    market: str
    sector: str
    concepts: tuple[str, ...]
    archetype: str
    quality_score: int
    volatility_score: int
    peers: tuple[str, ...]


CATALOG: tuple[StockProfile, ...] = (
    StockProfile(
        symbol="600519.SH",
        name="贵州茅台",
        market="沪市主板",
        sector="白酒 / 核心消费",
        concepts=("高端消费", "机构抱团", "品牌护城河"),
        archetype="quality_compounder",
        quality_score=93,
        volatility_score=26,
        peers=("000858.SZ", "600809.SH", "000596.SZ"),
    ),
    StockProfile(
        symbol="300308.SZ",
        name="中际旭创",
        market="创业板",
        sector="光模块 / AI 算力",
        concepts=("AI 算力", "CPO", "高速光模块"),
        archetype="high_beta_growth",
        quality_score=82,
        volatility_score=78,
        peers=("300502.SZ", "603083.SH", "002281.SZ"),
    ),
    StockProfile(
        symbol="002594.SZ",
        name="比亚迪",
        market="深市主板",
        sector="新能源车 / 智能驾驶",
        concepts=("整车", "动力电池", "出海"),
        archetype="platform_leader",
        quality_score=88,
        volatility_score=62,
        peers=("601633.SH", "300750.SZ", "603799.SH"),
    ),
    StockProfile(
        symbol="600036.SH",
        name="招商银行",
        market="沪市主板",
        sector="银行 / 高股息",
        concepts=("高股息", "机构重仓", "低波防御"),
        archetype="defensive_income",
        quality_score=86,
        volatility_score=24,
        peers=("000001.SZ", "601398.SH", "601288.SH"),
    ),
    StockProfile(
        symbol="300750.SZ",
        name="宁德时代",
        market="创业板",
        sector="锂电 / 新能源制造",
        concepts=("动力电池", "储能", "全球化"),
        archetype="platform_leader",
        quality_score=90,
        volatility_score=55,
        peers=("002594.SZ", "300014.SZ", "002460.SZ"),
    ),
    StockProfile(
        symbol="603259.SH",
        name="药明康德",
        market="沪市主板",
        sector="CXO / 医药服务",
        concepts=("医药外包", "全球订单", "创新药链"),
        archetype="policy_sensitive_quality",
        quality_score=80,
        volatility_score=52,
        peers=("300347.SZ", "688271.SH", "300759.SZ"),
    ),
    StockProfile(
        symbol="000977.SZ",
        name="浪潮信息",
        market="深市主板",
        sector="服务器 / AI 算力",
        concepts=("服务器", "国产算力", "AI 基建"),
        archetype="high_beta_growth",
        quality_score=76,
        volatility_score=74,
        peers=("300308.SZ", "603019.SH", "603986.SH"),
    ),
    StockProfile(
        symbol="601899.SH",
        name="紫金矿业",
        market="沪市主板",
        sector="有色 / 资源",
        concepts=("黄金", "铜", "全球资源"),
        archetype="cyclical_resource",
        quality_score=79,
        volatility_score=58,
        peers=("600547.SH", "603993.SH", "601600.SH"),
    ),
    StockProfile(
        symbol="000001.SZ",
        name="平安银行",
        market="深市主板",
        sector="银行 / 高股息",
        concepts=("高股息", "零售银行", "低波防御"),
        archetype="defensive_income",
        quality_score=76,
        volatility_score=28,
        peers=("600036.SH", "601398.SH", "601166.SH"),
    ),
)


def get_profile(symbol: str) -> StockProfile | None:
    normalized = symbol.strip().upper()
    return next((item for item in CATALOG if item.symbol == normalized), None)


def search_profiles(query: str, limit: int = 8) -> list[StockProfile]:
    needle = query.strip().upper()
    if not needle:
        return list(CATALOG[:limit])

    exact: list[StockProfile] = []
    partial: list[StockProfile] = []

    for item in CATALOG:
        haystack = f"{item.symbol} {item.name} {' '.join(item.concepts)}".upper()
        if item.symbol == needle or item.name.upper() == needle:
            exact.append(item)
        elif needle in haystack:
            partial.append(item)

    return (exact + partial)[:limit]
