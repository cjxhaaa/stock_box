from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import lru_cache
import json
import re
from urllib.parse import urlparse

import pandas as pd
import requests

from app.catalog import CATALOG, StockProfile, get_profile
from app.config import AppSettings
from app.providers.mock_provider import MarketSnapshot, MockResearchProvider
from app.providers.models import DailyBar
from app.schemas import DataReadinessItem


class AkshareResearchProvider(MockResearchProvider):
    provider_name = "akshare"
    provider_mode = "akshare"
    degraded_reason: str | None = None

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        import akshare as ak  # type: ignore

        self.ak = ak

    def search_stocks(self, query: str, limit: int = 8) -> list[StockProfile]:
        matches = super().search_stocks(query, limit)
        if matches:
            return matches

        listing = self._listing_cache()
        needle = query.strip().upper()
        if not needle:
            return self._profiles_from_listing(listing.head(limit))

        filtered = listing[
            listing["code"].astype(str).str.upper().str.contains(needle, na=False)
            | listing["name"].astype(str).str.upper().str.contains(needle, na=False)
        ].head(limit)
        return self._profiles_from_listing(filtered)

    def get_stock_profile(self, symbol: str) -> StockProfile:
        normalized = symbol.strip().upper()
        fallback = super().get_stock_profile(normalized)
        code = normalized.split(".")[0]
        try:
            profile_df = self.ak.stock_profile_cninfo(symbol=code)
        except Exception:
            return fallback

        row = profile_df.iloc[0].to_dict()
        concepts = _split_concepts(str(row.get("入选指数", "")))
        sector = self._industry_board_for_symbol(code) or str(row.get("所属行业", "") or fallback.sector)
        market = str(row.get("所属市场", "") or fallback.market)
        peers = _peer_candidates(sector, normalized) or list(fallback.peers)

        return StockProfile(
            symbol=normalized,
            name=str(row.get("A股简称", "") or fallback.name),
            market=market,
            sector=sector,
            concepts=tuple(concepts or fallback.concepts),
            archetype=fallback.archetype,
            quality_score=fallback.quality_score,
            volatility_score=fallback.volatility_score,
            peers=tuple(peers or fallback.peers),
        )

    def related_profiles(self, profile: StockProfile) -> list[StockProfile]:
        peers = super().related_profiles(profile)
        code = profile.symbol.split(".")[0]
        board_name = self._industry_board_for_symbol(code)
        if not board_name:
            return peers or self._fallback_related_profiles(profile)

        try:
            cons_df = self.ak.stock_board_industry_cons_em(symbol=board_name)
        except Exception:
            return peers or self._fallback_related_profiles(profile)

        seen = {item.symbol for item in peers}
        results = list(peers)
        for _, row in cons_df.head(12).iterrows():
            peer_code = str(row["代码"]).zfill(6)
            peer_symbol = _normalize_symbol(peer_code)
            if peer_symbol == profile.symbol or peer_symbol in seen:
                continue
            fallback = get_profile(peer_symbol) or super().get_stock_profile(peer_symbol)
            results.append(fallback)
            seen.add(peer_symbol)
            if len(results) >= 3:
                break
        return results or self._fallback_related_profiles(profile)

    def market_snapshot(self, profile: StockProfile) -> MarketSnapshot:
        bars = self.get_price_history(profile, 60)
        if len(bars) < 5:
            return super().market_snapshot(profile)

        recent = bars[-10:]
        avg_pct = sum(item.pct_change for item in recent) / len(recent)
        avg_turnover = sum(item.turnover_rate for item in recent) / len(recent)
        volatility = sum(abs(item.pct_change) for item in recent) / len(recent)

        if avg_pct > 1.5:
            regime = "真实日线显示强势上行，市场偏向趋势强化"
            appetite = "偏进攻"
        elif avg_pct < -1.5:
            regime = "真实日线显示回撤压力，市场更关注防守与兑现"
            appetite = "中性偏防御"
        else:
            regime = "真实日线显示震荡，市场仍以结构性轮动为主"
            appetite = "中性"

        dominant = list(profile.concepts[:2]) + ["真实行情"]
        commentary = (
            f"最近 10 个交易日平均涨跌幅 {avg_pct:.2f}%，平均换手率 {avg_turnover:.2f}%，"
            f"平均绝对波动 {volatility:.2f}%。"
        )
        return MarketSnapshot(
            regime=regime,
            risk_appetite=appetite,
            dominant_themes=tuple(dominant),
            commentary=commentary,
        )

    def data_readiness(self) -> list[DataReadinessItem]:
        items = super().data_readiness()
        rewritten: list[DataReadinessItem] = []
        for item in items:
            if item.key == "market":
                rewritten.append(
                    DataReadinessItem(
                        key=item.key,
                        label=item.label,
                        status="ready",
                        detail="已接入 AkShare 个股信息与日线数据，可用于真实价格驱动分析。",
                    )
                )
            elif item.key == "filings":
                rewritten.append(
                    DataReadinessItem(
                        key=item.key,
                        label=item.label,
                        status="ready",
                        detail="已接入巨潮资讯公告列表，可下钻到公告明细页和 PDF 原文。",
                    )
                )
            elif item.key == "news":
                rewritten.append(
                    DataReadinessItem(
                        key=item.key,
                        label=item.label,
                        status="ready",
                        detail="已接入东方财富个股新闻流，可生成真实新闻来源链接。",
                    )
                )
            elif item.key == "forum":
                rewritten.append(
                    DataReadinessItem(
                        key=item.key,
                        label=item.label,
                        status="ready",
                        detail="已接入东方财富股吧热帖、同花顺个股资讯和互动易问答；雪球仍保留为入口源。",
                    )
                )
            else:
                rewritten.append(item)
        return rewritten

    def get_price_history(self, profile: StockProfile, window_days: int) -> list[DailyBar]:
        code = profile.symbol.split(".")[0]
        end_date = date.today()
        start_date = end_date - timedelta(days=max(window_days * 2, 120))
        analysis_start = end_date - timedelta(days=max(window_days - 1, 1))
        try:
            df = self.ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="",
            )
        except Exception:
            return super().get_price_history(profile, window_days)

        if df.empty:
            return super().get_price_history(profile, window_days)

        df = df.copy()
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
        filtered = df[df["日期"].dt.date >= analysis_start]
        trimmed = filtered if not filtered.empty else df.tail(min(window_days, len(df)))
        bars: list[DailyBar] = []
        for _, row in trimmed.iterrows():
            bars.append(
                DailyBar(
                    trade_date=row["日期"].date().isoformat(),
                    open=float(row["开盘"]),
                    close=float(row["收盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    amount=float(row["成交额"]),
                    turnover_rate=float(row["换手率"]),
                    pct_change=float(row["涨跌幅"]),
                )
            )
        return bars

    @lru_cache(maxsize=1)
    def _listing_cache(self) -> pd.DataFrame:
        return self.ak.stock_info_a_code_name()

    @lru_cache(maxsize=1)
    def _industry_board_snapshot(self) -> pd.DataFrame:
        return self.ak.stock_board_industry_name_em()

    @lru_cache(maxsize=128)
    def _industry_board_members(self, board_name: str) -> pd.DataFrame:
        return self.ak.stock_board_industry_cons_em(symbol=board_name)

    def _industry_board_for_symbol(self, code: str) -> str | None:
        try:
            boards = self._industry_board_snapshot()
        except Exception:
            return None

        candidates = self._candidate_board_names(code, boards)
        for board_name in candidates:
            try:
                cons_df = self._industry_board_members(board_name)
            except Exception:
                continue
            if cons_df["代码"].astype(str).str.zfill(6).eq(code).any():
                return board_name
        return None

    def _candidate_board_names(self, code: str, boards: pd.DataFrame) -> list[str]:
        board_names = [str(item) for item in boards["板块名称"].astype(str).tolist()]
        normalized_symbol = _normalize_symbol(code)
        fallback = get_profile(normalized_symbol)
        candidates: list[str] = []

        if fallback is not None:
            sector_parts = [part.strip() for part in fallback.sector.split("/") if part.strip()]
            concept_parts = list(fallback.concepts)
            for board_name in board_names:
                if any(part in board_name or board_name in part for part in sector_parts + concept_parts):
                    candidates.append(board_name)

        if not candidates:
            candidates = board_names[:40]

        seen: set[str] = set()
        ordered: list[str] = []
        for name in candidates + board_names[:20]:
            if name not in seen:
                ordered.append(name)
                seen.add(name)
        return ordered

    def _profiles_from_listing(self, frame: pd.DataFrame) -> list[StockProfile]:
        profiles: list[StockProfile] = []
        for _, row in frame.iterrows():
            code = str(row["code"]).zfill(6)
            symbol = _normalize_symbol(code)
            fallback = super().get_stock_profile(symbol)
            profiles.append(
                StockProfile(
                    symbol=symbol,
                    name=str(row["name"]),
                    market=fallback.market,
                    sector=fallback.sector,
                    concepts=fallback.concepts,
                    archetype=fallback.archetype,
                    quality_score=fallback.quality_score,
                    volatility_score=fallback.volatility_score,
                    peers=fallback.peers,
                )
            )
        return profiles

    def news_pool(self, profile: StockProfile) -> list[dict[str, object]]:
        code = profile.symbol.split(".")[0]
        try:
            df = self.ak.stock_news_em(symbol=code)
        except Exception:
            return super().news_pool(profile)

        if df.empty:
            return super().news_pool(profile)

        items: list[dict[str, object]] = []
        for index, row in df.head(6).iterrows():
            url = str(row.get("新闻链接", "")).strip()
            if not url:
                continue
            title = str(row.get("新闻标题", "")).strip() or f"{profile.name} 新闻"
            published_at = str(row.get("发布时间", "")).strip() or None
            source_name = str(row.get("文章来源", "")).strip() or "财经媒体"
            summary = str(row.get("新闻内容", "")).strip()
            items.append(
                {
                    "headline": title,
                    "category": source_name,
                    "impact": summary[:120] or f"{profile.name} 的相关新闻流更新。",
                    "links": [
                        self._news_source_link(
                            symbol=profile.symbol,
                            index=index,
                            title=title,
                            url=url,
                            source_name=source_name,
                            published_at=published_at,
                        )
                    ],
                }
            )

        return items or super().news_pool(profile)

    def disclosure_pool(self, profile: StockProfile) -> list[dict[str, object]]:
        code = profile.symbol.split(".")[0]
        rows = self._announcement_rows(code)
        if not rows:
            return super().disclosure_pool(profile)

        items: list[dict[str, object]] = []
        for index, row in enumerate(rows[:4]):
            title = str(row.get("announcementTitle", "")).strip()
            if not title:
                continue
            published_at = _format_announcement_time(row.get("announcementTime"))
            detail_url = self._announcement_detail_url(row)
            pdf_url = self._announcement_pdf_url(row)
            category, signal = _classify_announcement(title)
            links = [
                self._source_link(
                    id=f"{profile.symbol}:filing:{index}:detail",
                    label=title,
                    url=detail_url,
                    domain="www.cninfo.com.cn",
                    kind="filing",
                    published_at=published_at,
                    note=f"{category} · 公告明细页",
                )
            ]
            if pdf_url:
                links.append(
                    self._source_link(
                        id=f"{profile.symbol}:filing:{index}:pdf",
                        label=f"{title} PDF",
                        url=pdf_url,
                        domain="static.cninfo.com.cn",
                        kind="filing",
                        published_at=published_at,
                        note="公告 PDF 原文",
                    )
                )
            items.append(
                {
                    "title": title,
                    "category": category,
                    "published_at": published_at,
                    "signal": signal,
                    "summary": _filing_summary(title, signal, profile.name),
                    "links": links,
                }
            )
        return items or super().disclosure_pool(profile)

    def community_pool(self, profile: StockProfile) -> list[dict[str, object]]:
        code = profile.symbol.split(".")[0]
        items: list[dict[str, object]] = []
        items.extend(self._eastmoney_forum_items(profile.symbol, code))
        items.extend(self._ths_community_items(profile.symbol, code, profile.name))
        if not items:
            return super().community_pool(profile)
        return items[:5]

    def forum_snapshot(self, profile: StockProfile) -> dict[str, object]:
        code = profile.symbol.split(".")[0]
        community_items = self.community_pool(profile)
        try:
            df = self.ak.stock_irm_cninfo(symbol=code)
        except Exception:
            df = pd.DataFrame()

        questions = " ".join(df["问题"].astype(str).head(12).tolist()) if not df.empty else ""
        discussion_titles = " ".join(str(item["title"]) for item in community_items[:5])
        combined_text = f"{questions} {discussion_titles}".strip()
        if not combined_text:
            return super().forum_snapshot(profile)

        keywords = _extract_keywords(combined_text, list(profile.concepts))
        positive_hits = _count_hits(combined_text, ["订单", "回购", "增持", "饱满", "增长", "景气", "突破", "龙头"])
        negative_hits = _count_hits(combined_text, ["减持", "质押", "风险", "问询", "处罚", "下滑", "回撤", "分歧"])
        total = min(len(df), 12) if not df.empty else len(community_items)
        bullish = round(min(0.68, 0.33 + positive_hits * 0.04), 2)
        bearish = round(min(0.45, 0.16 + negative_hits * 0.05), 2)
        if bullish + bearish > 0.9:
            bearish = round(0.9 - bullish, 2)
        neutrality = round(max(0.0, 1 - bullish - bearish), 2)
        links = self.reference_bundle(profile)
        community_links = [link for item in community_items for link in item["links"][:1]]
        return {
            "bullish_ratio": bullish,
            "bearish_ratio": bearish,
            "neutrality_ratio": neutrality,
            "keywords": keywords[:4] or list(profile.concepts[:4]),
            "question_count": total,
            "links": _dedupe_links([links["irm"], *community_links, links["forum"], links["ths"], links["community"]]),
        }

    def _fallback_related_profiles(self, profile: StockProfile) -> list[StockProfile]:
        scored: list[tuple[int, StockProfile]] = []
        concept_set = set(profile.concepts)
        for item in CATALOG:
            if item.symbol == profile.symbol:
                continue
            score = len(concept_set.intersection(item.concepts))
            if item.archetype == profile.archetype:
                score += 2
            if profile.sector and item.sector and profile.sector[:4] == item.sector[:4]:
                score += 1
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for score, item in scored[:3] if score > 0]

    @lru_cache(maxsize=128)
    def _announcement_rows(self, code: str) -> list[dict[str, object]]:
        try:
            from akshare.stock_feature import stock_disclosure_cninfo as disclosure_module
        except Exception:
            return []

        get_stock_json = getattr(disclosure_module, "__get_stock_json", None)
        if get_stock_json is None:
            return []

        org_id = get_stock_json("沪深京").get(code)
        if not org_id:
            return []

        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        payload = {
            "pageNum": "1",
            "pageSize": "30",
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": f"{code},{org_id}",
            "searchkey": "",
            "secid": "",
            "category": "",
            "trade": "",
            "seDate": f"{start_date.isoformat()}~{end_date.isoformat()}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        }
        try:
            response = requests.post(
                "http://www.cninfo.com.cn/new/hisAnnouncement/query",
                data=payload,
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            payload_json = response.json()
        except Exception:
            return []

        total = int(payload_json.get("totalAnnouncement", 0) or 0)
        page_size = int(payload["pageSize"])
        total_pages = max(1, min(6, (total + page_size - 1) // page_size))
        merged_rows: list[dict[str, object]] = []
        first_page = payload_json.get("announcements", [])
        if isinstance(first_page, list):
            merged_rows.extend(row for row in first_page if isinstance(row, dict))

        for page in range(2, total_pages + 1):
            payload["pageNum"] = str(page)
            try:
                page_response = requests.post(
                    "http://www.cninfo.com.cn/new/hisAnnouncement/query",
                    data=payload,
                    headers=headers,
                    timeout=20,
                )
                page_response.raise_for_status()
                page_json = page_response.json()
            except Exception:
                break
            page_rows = page_json.get("announcements", [])
            if not isinstance(page_rows, list):
                break
            merged_rows.extend(row for row in page_rows if isinstance(row, dict))

        return merged_rows

    @lru_cache(maxsize=128)
    def _eastmoney_forum_items(self, symbol: str, code: str) -> list[dict[str, object]]:
        try:
            response = requests.get(
                f"https://guba.eastmoney.com/list,{code}.html",
                headers=_request_headers("https://guba.eastmoney.com/"),
                timeout=20,
            )
            response.raise_for_status()
        except Exception:
            return []

        marker = "var article_list="
        index = response.text.find(marker)
        if index == -1:
            return []

        try:
            payload, _ = json.JSONDecoder().raw_decode(response.text[index + len(marker):])
        except json.JSONDecodeError:
            return []

        rows = payload.get("re", [])
        if not isinstance(rows, list):
            return []

        items: list[dict[str, object]] = []
        for index, row in enumerate(rows[:3]):
            if not isinstance(row, dict):
                continue
            title = str(row.get("post_title", "")).strip()
            post_id = str(row.get("post_id", "")).strip()
            if not title or not post_id:
                continue
            clicks = int(row.get("post_click_count", 0) or 0)
            comments = int(row.get("post_comment_count", 0) or 0)
            published_at = str(row.get("post_publish_time", "")).strip() or str(row.get("post_last_time", "")).strip()
            url = f"https://guba.eastmoney.com/news,{code},{post_id}.html"
            items.append(
                {
                    "title": title,
                    "platform": "东方财富股吧",
                    "published_at": published_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "heat": f"阅读 {clicks} / 评论 {comments}",
                    "summary": "热帖标题能反映短线资金关注点和散户叙事焦点。",
                    "links": [
                        self._source_link(
                            id=f"{symbol}:forum:eastmoney:{index}",
                            label=title,
                            url=url,
                            domain="guba.eastmoney.com",
                            kind="forum",
                            published_at=published_at or None,
                            note=f"东方财富股吧热帖，阅读 {clicks} / 评论 {comments}",
                        )
                    ],
                }
            )
        return items

    @lru_cache(maxsize=128)
    def _ths_community_items(self, symbol: str, code: str, company_name: str) -> list[dict[str, object]]:
        try:
            response = requests.get(
                f"https://stockpage.10jqka.com.cn/{code}/",
                headers=_request_headers(f"https://stockpage.10jqka.com.cn/{code}/"),
                timeout=20,
            )
            response.raise_for_status()
        except Exception:
            return []

        matches = re.findall(
            r'<span class="news_title fl"><a href="([^"]+)" target="_blank">(.*?)</a></span>\s*'
            r'<span class="news_date"><em>(.*?)</em></span>',
            response.text,
            flags=re.S,
        )
        filtered = [
            item for item in matches
            if company_name in _strip_html(item[1]) or code in _strip_html(item[1])
        ]
        if not filtered:
            filtered = list(matches[:3])

        items: list[dict[str, object]] = []
        for index, (url, raw_title, raw_date) in enumerate(filtered[:3]):
            title = _strip_html(raw_title)
            published_at = _normalize_partial_datetime(raw_date)
            items.append(
                {
                    "title": title,
                    "platform": "同花顺",
                    "published_at": published_at,
                    "heat": "资讯热度",
                    "summary": "同花顺个股页会把资金、公告和公司问答聚合到高频资讯流里。",
                    "links": [
                        self._source_link(
                            id=f"{symbol}:forum:ths:{index}",
                            label=title,
                            url=url.replace("http://", "https://"),
                            domain=urlparse(url).netloc or "stock.10jqka.com.cn",
                            kind="community",
                            published_at=published_at,
                            note="同花顺个股页资讯条目",
                        )
                    ],
                }
            )
        return items

    @staticmethod
    def _announcement_detail_url(row: dict[str, object]) -> str:
        code = str(row.get("secCode", "")).strip()
        announcement_id = str(row.get("announcementId", "")).strip()
        org_id = str(row.get("orgId", "")).strip()
        announcement_time = _format_announcement_time(row.get("announcementTime"))
        return (
            "https://www.cninfo.com.cn/new/disclosure/detail"
            f"?stockCode={code}&announcementId={announcement_id}&orgId={org_id}"
            f"&announcementTime={announcement_time}"
        )

    @staticmethod
    def _announcement_pdf_url(row: dict[str, object]) -> str | None:
        adjunct_url = str(row.get("adjunctUrl", "")).strip()
        if not adjunct_url:
            return None
        return f"https://static.cninfo.com.cn/{adjunct_url}"

    def _news_source_link(
        self,
        symbol: str,
        index: int,
        title: str,
        url: str,
        source_name: str,
        published_at: str | None,
    ):
        domain = urlparse(url).netloc or "finance.eastmoney.com"
        return self._source_link(
            id=f"{symbol}:news:{index}",
            label=title,
            url=url,
            domain=domain,
            kind="news",
            published_at=published_at,
            note=f"来源: {source_name}",
        )

    @staticmethod
    def _source_link(
        id: str,
        label: str,
        url: str,
        domain: str,
        kind: str,
        published_at: str | None,
        note: str,
    ):
        from app.schemas import SourceLink

        return SourceLink(
            id=id,
            label=label,
            url=url,
            domain=domain,
            kind=kind,
            publishedAt=published_at,
            note=note,
        )


def _normalize_symbol(code: str) -> str:
    if code.startswith(("600", "601", "603", "605", "688")):
        return f"{code}.SH"
    return f"{code}.SZ"


def _split_concepts(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()][:4]


def _peer_candidates(sector: str, symbol: str) -> list[str]:
    peers = [item.symbol for item in CATALOG if sector and sector.split("、")[0] in item.sector and item.symbol != symbol]
    return peers[:3]


def _extract_keywords(text: str, concept_fallback: list[str]) -> list[str]:
    candidates = [
        "订单",
        "产能",
        "业绩",
        "毛利率",
        "CPO",
        "800G",
        "1.6T",
        "出货",
        "客户",
        "激光器",
    ]
    found = [item for item in candidates if item.lower() in text.lower()]
    return found or concept_fallback


def _count_hits(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _format_announcement_time(raw_value: object) -> str:
    if raw_value is None:
        return date.today().isoformat()
    try:
        return datetime.fromtimestamp(int(raw_value) / 1000).date().isoformat()
    except Exception:
        text = str(raw_value).strip()
        return text[:10] if text else date.today().isoformat()


def _classify_announcement(title: str) -> tuple[str, str]:
    mapping = [
        (("问询", "监管", "处罚", "立案", "关注函"), ("监管事项", "监管问询或处罚进展")),
        (("减持", "质押", "回购", "解除质押", "股东"), ("股权变动", "股东资金安排与筹码变化")),
        (("年报", "半年报", "季报", "业绩预告", "快报"), ("定期报告", "业绩兑现与预期差")),
        (("订单", "合同", "中标", "合作"), ("经营进展", "经营催化与订单兑现")),
        (("可转债", "增发", "融资"), ("融资事项", "融资节奏与摊薄影响")),
        (("风险提示", "异常波动", "澄清"), ("风险提示", "短线交易风险提示")),
    ]
    for keywords, result in mapping:
        if any(keyword in title for keyword in keywords):
            return result
    return "日常公告", "常规经营与治理披露"


def _filing_summary(title: str, signal: str, company_name: str) -> str:
    return f"{company_name} 最近公告涉及“{title}”，当前更值得关注 {signal} 对交易节奏和风险定价的影响。"


def _request_headers(referer: str) -> dict[str, str]:
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": referer,
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
    }


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).strip()


def _normalize_partial_datetime(value: str) -> str:
    text = _strip_html(value)
    match = re.fullmatch(r"(\d{2})-(\d{2})\s+(\d{2}:\d{2})", text)
    if not match:
        return text or datetime.now().strftime("%Y-%m-%d %H:%M")
    month, day, hm = match.groups()
    year = date.today().year
    return f"{year}-{month}-{day} {hm}"


def _dedupe_links(links):
    merged = {}
    for link in links:
        merged[link.id] = link
    return list(merged.values())
