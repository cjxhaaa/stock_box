from __future__ import annotations

from app.schemas import SourceLink


def seeded_sources(symbol: str, company_name: str) -> dict[str, SourceLink]:
    normalized = symbol.strip().upper()
    code, exchange = normalized.split(".")
    eastmoney_exchange = exchange.lower()
    xueqiu_code = f"{exchange}{code}"

    base = {
        "market_quote": SourceLink(
            id=f"{normalized}:market_quote",
            label=f"{company_name} 东方财富行情页",
            url=f"https://quote.eastmoney.com/{eastmoney_exchange}{code}.html",
            domain="quote.eastmoney.com",
            kind="market",
            publishedAt=None,
            note="行情、成交、盘口和板块入口。",
        ),
        "cninfo_profile": SourceLink(
            id=f"{normalized}:cninfo_profile",
            label=f"{company_name} 巨潮资讯公司页",
            url=f"https://www.cninfo.com.cn/new/snapshot/companyDetailCn?code={code}",
            domain="www.cninfo.com.cn",
            kind="filing",
            publishedAt=None,
            note="公告、财报和监管披露入口。",
        ),
        "eastmoney_forum": SourceLink(
            id=f"{normalized}:eastmoney_forum",
            label=f"{company_name} 东方财富股吧",
            url=f"https://guba.eastmoney.com/list,{code}.html",
            domain="guba.eastmoney.com",
            kind="forum",
            publishedAt=None,
            note="散户讨论、热帖与情绪入口。",
        ),
        "ths_stock": SourceLink(
            id=f"{normalized}:ths_stock",
            label=f"{company_name} 同花顺个股页",
            url=f"https://stockpage.10jqka.com.cn/{code}/",
            domain="stockpage.10jqka.com.cn",
            kind="community",
            publishedAt=None,
            note="查看同花顺个股资讯、讨论和资金标签入口。",
        ),
        "xueqiu_stock": SourceLink(
            id=f"{normalized}:xueqiu_stock",
            label=f"{company_name} 雪球个股页",
            url=f"https://xueqiu.com/S/{xueqiu_code}",
            domain="xueqiu.com",
            kind="community",
            publishedAt=None,
            note="观点、讨论和资讯聚合入口。",
        ),
        "cninfo_irm": SourceLink(
            id=f"{normalized}:cninfo_irm",
            label=f"{company_name} 互动易入口",
            url=f"https://irm.cninfo.com.cn/ircs/company/companyDetails?stockcode={code}",
            domain="irm.cninfo.com.cn",
            kind="forum",
            publishedAt=None,
            note="查看互动易问答与投资者关注问题入口。",
        ),
        "theme_reference": SourceLink(
            id=f"{normalized}:theme_reference",
            label=f"{company_name} 题材参考入口",
            url=f"https://quote.eastmoney.com/{eastmoney_exchange}{code}.html",
            domain="quote.eastmoney.com",
            kind="theme",
            publishedAt="2026-03-09",
            note="当前版本用作题材脉络和板块映射的参考入口。",
        ),
    }

    specific = _symbol_specific(normalized, company_name)
    return {**base, **specific}


def _symbol_specific(symbol: str, company_name: str) -> dict[str, SourceLink]:
    if symbol == "300308.SZ":
        return {
            "stage_build": SourceLink(
                id=f"{symbol}:stage_build",
                label=f"{company_name} 算力主线观察入口",
                url="https://xueqiu.com/S/SZ300308",
                domain="xueqiu.com",
                kind="narrative",
                publishedAt="2025-04-18",
                note="用于观察算力主线、讨论热度和观点变化。",
            ),
            "stage_diverge": SourceLink(
                id=f"{symbol}:stage_diverge",
                label=f"{company_name} 公告与验证入口",
                url="https://www.cninfo.com.cn/new/snapshot/companyDetailCn?code=300308",
                domain="www.cninfo.com.cn",
                kind="filing",
                publishedAt="2025-09-03",
                note="用于核对公告、业绩与监管披露。",
            ),
        }

    if symbol == "600036.SH":
        return {
            "stage_build": SourceLink(
                id=f"{symbol}:stage_build",
                label=f"{company_name} 银行板块观察入口",
                url="https://quote.eastmoney.com/sh600036.html",
                domain="quote.eastmoney.com",
                kind="narrative",
                publishedAt="2025-05-09",
                note="用于观察银行板块风格切换和个股表现。",
            ),
            "stage_diverge": SourceLink(
                id=f"{symbol}:stage_diverge",
                label=f"{company_name} 银行社区讨论入口",
                url="https://xueqiu.com/S/SH600036",
                domain="xueqiu.com",
                kind="community",
                publishedAt="2025-09-16",
                note="用于观察分红、估值与风格分歧。",
            ),
        }

    return {}
