from __future__ import annotations

from datetime import date, datetime, timedelta
from hashlib import sha256
from random import Random

from app.catalog import StockProfile
from app.providers.models import DailyBar
from app.schemas import EventCluster, FilingDigestItem, ForumDigestItem, NewsDigestItem, EvidenceLine, SourceLink, TimelineEvent


UP_CATALYSTS = (
    "板块龙头打开高度，带动资金向同题材扩散",
    "公告或产业信息强化景气叙事，推动估值抬升",
    "市场风险偏好回暖，资金重新偏向高弹性方向",
    "机构与游资共振，短期形成加速段",
)

DOWN_CATALYSTS = (
    "高位分歧放大，前期获利盘集中兑现",
    "主线切换导致题材关注度下降",
    "监管或风险提示提高短线接力难度",
    "基本面验证低于市场预期，情绪回落",
)

LADDERS = ("龙一", "龙二", "中军", "跟风前排", "跟风后排", "修复补涨")


def build_timeline(
    profile: StockProfile,
    window_days: int,
    reference_bundle: dict[str, SourceLink],
    filings_digest: list[FilingDigestItem] | None = None,
    news_digest: list[NewsDigestItem] | None = None,
    forum_digest: list[ForumDigestItem] | None = None,
    event_clusters: list[EventCluster] | None = None,
    price_history: list[DailyBar] | None = None,
) -> list[TimelineEvent]:
    if price_history:
        real_timeline = _timeline_from_history(
            profile,
            reference_bundle,
            price_history,
            filings_digest=filings_digest,
            news_digest=news_digest,
            forum_digest=forum_digest,
            event_clusters=event_clusters,
        )
        if real_timeline:
            return real_timeline

    rng = _rng(profile.symbol, "timeline")
    today = date.today()
    anchors = [24, 72, 138, 224, 315]
    timeline: list[TimelineEvent] = []

    for index, anchor in enumerate(anchors, start=1):
        move = "up" if index in {1, 3, 5} else "down"
        event_date = today - timedelta(days=min(window_days - 1, anchor + rng.randint(-6, 6)))
        change_pct = round((rng.uniform(3.2, 10.1) if move == "up" else -rng.uniform(2.9, 8.4)), 2)
        catalyst = rng.choice(UP_CATALYSTS if move == "up" else DOWN_CATALYSTS)
        ladder_position = _ladder_for_profile(profile, rng)
        evidence = _evidence_stack(
            profile,
            move,
            catalyst,
            rng,
            reference_bundle,
            matched_filing=None,
            matched_news=None,
            matched_forum=None,
        )
        interpretation = (
            f"{profile.name} 在该阶段更像是 {profile.concepts[0]} 方向的 {ladder_position}，"
            f"交易主导因素是{'题材扩散' if move == 'up' else '高位分歧'}。"
        )
        timeline.append(
            TimelineEvent(
                date=event_date.isoformat(),
                move=move,
                changePct=change_pct,
                summary=f"{event_date.isoformat()} 前后，{profile.name} 出现显著{'上攻' if move == 'up' else '回撤'}。",
                catalyst=catalyst,
                sector=profile.sector,
                ladderPosition=ladder_position,
                interpretation=interpretation,
                confidence=round(0.52 + rng.random() * 0.28, 2),
                evidence=evidence,
            )
        )

    timeline.sort(key=lambda item: item.date)
    return timeline


def _timeline_from_history(
    profile: StockProfile,
    reference_bundle: dict[str, SourceLink],
    price_history: list[DailyBar],
    filings_digest: list[FilingDigestItem] | None = None,
    news_digest: list[NewsDigestItem] | None = None,
    forum_digest: list[ForumDigestItem] | None = None,
    event_clusters: list[EventCluster] | None = None,
) -> list[TimelineEvent]:
    candidates = _select_timeline_candidates(price_history)
    if not candidates:
        return []

    timeline: list[TimelineEvent] = []
    rng = _rng(profile.symbol, "timeline-real")

    for bar in sorted(candidates, key=lambda item: item.trade_date):
        move = "up" if bar.pct_change > 0 else "down"
        matched_event = _best_digest_item(profile, bar.trade_date, event_clusters or [], move)
        matched_filing = _best_digest_item(profile, bar.trade_date, filings_digest or [], move)
        matched_news = _best_digest_item(profile, bar.trade_date, news_digest or [], move)
        matched_forum = _best_digest_item(profile, bar.trade_date, forum_digest or [], move)
        catalyst = _pick_catalyst(
            move,
            matched_event=matched_event,
            matched_filing=matched_filing,
            matched_news=matched_news,
            matched_forum=matched_forum,
            rng=rng,
        )
        ladder_position = _ladder_for_profile(profile, rng)
        summary = (
            f"{bar.trade_date} 当日振幅 {((bar.high - bar.low) / max(bar.open, 0.01)) * 100:.2f}%，"
            f"成交额约 {bar.amount / 1e8:.2f} 亿元。"
        )
        interpretation = _build_interpretation(
            bar,
            move,
            matched_event=matched_event,
            matched_filing=matched_filing,
            matched_news=matched_news,
            matched_forum=matched_forum,
        )
        evidence = _evidence_stack(
            profile,
            move,
            catalyst,
            rng,
            reference_bundle,
            target_date=bar.trade_date,
            matched_event=matched_event,
            matched_filing=matched_filing,
            matched_news=matched_news,
            matched_forum=matched_forum,
        )
        timeline.append(
            TimelineEvent(
                date=bar.trade_date,
                move=move,
                changePct=round(bar.pct_change, 2),
                summary=summary,
                catalyst=catalyst,
                sector=profile.sector,
                ladderPosition=ladder_position,
                interpretation=interpretation,
                confidence=min(0.92, round(0.58 + abs(bar.pct_change) / 20, 2)),
                evidence=evidence,
            )
        )
    return timeline


def _evidence_stack(
    profile: StockProfile,
    move: str,
    catalyst: str,
    rng: Random,
    reference_bundle: dict[str, SourceLink],
    target_date: str | None = None,
    matched_event=None,
    matched_filing=None,
    matched_news=None,
    matched_forum=None,
) -> list[EvidenceLine]:
    price_signal = "放量上涨" if move == "up" else "放量回撤"
    forum_signal = "讨论热度抬升" if move == "up" else "分歧显著增大"
    lines = [
        EvidenceLine(
            source="market",
            signal=price_signal,
            summary=f"{profile.sector} 在对应阶段与个股方向形成同步共振。",
            role="support",
            score=0.72,
            sourceIds=[reference_bundle["market"].id],
            links=[reference_bundle["market"]],
        ),
    ]
    if matched_event is not None:
        lines.append(
            EvidenceLine(
                source="event",
                signal=matched_event.topic,
                summary=matched_event.summary,
                role="main" if matched_event.direction != "neutral" else "support",
                score=_evidence_score(
                    profile,
                    move,
                    matched_event.topic,
                    matched_event.summary,
                    published_at=matched_event.published_at,
                    target_date=target_date,
                    base=0.84,
                ),
                sourceIds=matched_event.source_ids,
                links=matched_event.links,
            )
        )
    if matched_filing is not None:
        filing_signal = matched_filing.signal
        filing_summary = matched_filing.summary
        filing_role = _evidence_role(move, filing_signal, filing_summary)
        if matched_event is not None and filing_role == "main":
            filing_role = "support"
        lines.append(
            EvidenceLine(
                source="filing",
                signal=filing_signal,
                summary=filing_summary,
                role=filing_role,
                score=_evidence_score(
                    profile,
                    move,
                    filing_signal,
                    filing_summary,
                    published_at=matched_filing.published_at,
                    target_date=target_date,
                    base=0.82,
                ),
                sourceIds=matched_filing.source_ids,
                links=matched_filing.links,
            )
        )
    else:
        lines.append(
            EvidenceLine(
                source="news",
                signal="催化映射",
                summary=catalyst,
                role="main",
                score=0.68,
                sourceIds=[reference_bundle["filing"].id, reference_bundle["theme"].id],
                links=[reference_bundle["filing"], reference_bundle["community"]],
            )
        )

    if matched_news is not None:
        news_signal = matched_news.topic
        news_summary = f"{matched_news.category}: {matched_news.impact}"
        news_role = _evidence_role(move, news_signal, news_summary)
        if matched_event is not None and news_role == "main":
            news_role = "support"
        lines.append(
            EvidenceLine(
                source="news",
                signal=news_signal,
                summary=news_summary,
                role=news_role,
                score=_evidence_score(
                    profile,
                    move,
                    news_signal,
                    news_summary,
                    published_at=_item_published_at(matched_news),
                    target_date=target_date,
                    base=0.74,
                ),
                sourceIds=matched_news.source_ids,
                links=matched_news.links,
            )
        )

    if matched_forum is not None:
        forum_signal = matched_forum.topic
        forum_summary = f"{matched_forum.platform} / {matched_forum.heat}: {matched_forum.summary}"
        forum_role = _evidence_role(move, forum_signal, forum_summary)
        if matched_event is not None and forum_role == "main":
            forum_role = "support"
        lines.append(
            EvidenceLine(
                source="forum",
                signal=forum_signal,
                summary=forum_summary,
                role=forum_role,
                score=_evidence_score(
                    profile,
                    move,
                    forum_signal,
                    forum_summary,
                    published_at=matched_forum.published_at,
                    target_date=target_date,
                    base=0.68,
                ),
                sourceIds=matched_forum.source_ids,
                links=matched_forum.links,
            )
        )
    else:
        lines.append(
            EvidenceLine(
                source="forum",
                signal=forum_signal,
                summary=f"散户讨论关键词集中在 {rng.choice(profile.concepts)} 与 {rng.choice(['业绩', '龙头', '低吸', '监管'])}。",
                role="support",
                score=0.58,
                sourceIds=[reference_bundle["forum"].id, reference_bundle["community"].id],
                links=[reference_bundle["forum"], reference_bundle["community"]],
            )
        )
    return _rank_evidence(lines)[:4]


def _ladder_for_profile(profile: StockProfile, rng: Random) -> str:
    if profile.archetype in {"platform_leader", "quality_compounder"}:
        return rng.choice(LADDERS[:3])
    if profile.archetype in {"high_beta_growth", "cyclical_resource"}:
        return rng.choice(LADDERS)
    return rng.choice(LADDERS[2:])


def _rng(symbol: str, salt: str) -> Random:
    seed = int(sha256(f"{symbol}:{salt}".encode("utf-8")).hexdigest()[:8], 16)
    return Random(seed)


def _select_timeline_candidates(price_history: list[DailyBar]) -> list[DailyBar]:
    if not price_history:
        return []

    sorted_history = sorted(price_history, key=lambda item: item.trade_date)
    bucket_count = min(5, len(sorted_history))
    if bucket_count == 0:
        return []

    bucket_size = max(1, len(sorted_history) // bucket_count)
    selected: list[DailyBar] = []

    for index in range(bucket_count):
        start = index * bucket_size
        end = len(sorted_history) if index == bucket_count - 1 else min(len(sorted_history), (index + 1) * bucket_size)
        bucket = sorted_history[start:end]
        if not bucket:
            continue
        selected.append(max(bucket, key=lambda item: abs(item.pct_change)))

    deduped: dict[str, DailyBar] = {}
    for item in selected:
        deduped[item.trade_date] = item
    return list(deduped.values())


def _best_digest_item(profile: StockProfile, target_date: str, items: list, move: str) -> object | None:
    if not items:
        return None
    try:
        target = datetime.fromisoformat(target_date[:10]).date()
    except ValueError:
        return None

    ranked: list[tuple[float, object]] = []
    for item in items:
        published = _item_published_at(item)
        if not published:
            continue
        try:
            item_date = datetime.fromisoformat(str(published)[:10]).date()
        except ValueError:
            continue
        if item_date > target + timedelta(days=2):
            continue
        gap = abs((target - item_date).days)
        if gap > 45:
            continue
        text = _item_signal_text(item)
        score = _match_score(profile, move, text, target_date=target.isoformat(), published_at=str(published))
        ranked.append((score, item))

    if not ranked:
        return None
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return ranked[0][1]


def _pick_catalyst(move: str, matched_event, matched_filing, matched_news, matched_forum, rng: Random) -> str:
    candidates: list[tuple[float, str]] = []
    for item, base in ((matched_event, 0.92), (matched_filing, 0.88), (matched_news, 0.8), (matched_forum, 0.7)):
        if item is None:
            continue
        signal = getattr(item, "signal", None) or getattr(item, "category", None) or getattr(item, "title", None)
        summary = getattr(item, "summary", None) or getattr(item, "impact", None) or getattr(item, "headline", None)
        if not signal and not summary:
            continue
        score = _evidence_score(
            profile=None,
            move=move,
            signal=str(signal or ""),
            summary=str(summary or ""),
            published_at=_item_published_at(item),
            target_date=None,
            base=base,
        )
        text = getattr(item, "title", None) or getattr(item, "headline", None) or summary or signal
        candidates.append((score, str(text)))
    if candidates:
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        return candidates[0][1]
    return rng.choice(UP_CATALYSTS if move == "up" else DOWN_CATALYSTS)


def _build_interpretation(bar: DailyBar, move: str, matched_event, matched_filing, matched_news, matched_forum) -> str:
    base = (
        f"真实日线数据显示该日涨跌幅 {bar.pct_change:+.2f}%，换手率 {bar.turnover_rate:.2f}%，"
        f"{'更像主线强化' if move == 'up' else '更像高位分歧或兑现'}。"
    )
    contexts: list[str] = []
    if matched_event is not None:
        contexts.append(f"跨源事件簇聚焦“{matched_event.topic}”")
    if matched_filing is not None:
        contexts.append(f"附近公告信号为“{matched_filing.signal}”")
    if matched_news is not None:
        contexts.append(f"新闻侧聚焦“{matched_news.headline}”")
    if matched_forum is not None:
        contexts.append(f"社区热议集中在“{matched_forum.title}”")
    if not contexts:
        return base
    return f"{base} {'；'.join(contexts)}。"


UP_KEYWORDS = ("订单", "增长", "中标", "合作", "回购", "增持", "景气", "突破", "龙头", "净流入", "融资买入")
DOWN_KEYWORDS = ("减持", "质押", "问询", "处罚", "立案", "风险", "异常波动", "回撤", "下滑", "分歧", "兑现")


def _evidence_role(move: str, signal: str, summary: str) -> str:
    score = _direction_bias(move, signal, summary)
    if score >= 1:
        return "main"
    if score <= -1:
        return "counter"
    return "support"


def _evidence_score(
    profile: StockProfile | None,
    move: str,
    signal: str,
    summary: str,
    published_at: str | None,
    target_date: str | None,
    base: float,
) -> float:
    relevance = _relevance_bonus(profile, signal, summary)
    time_bonus = _time_bonus(published_at, target_date)
    score = base + _direction_bias(move, signal, summary) * 0.08 + relevance + time_bonus
    return round(max(0.4, min(0.96, score)), 2)


def _direction_bias(move: str, signal: str, summary: str) -> int:
    text = f"{signal} {summary}"
    up_hits = sum(1 for keyword in UP_KEYWORDS if keyword in text)
    down_hits = sum(1 for keyword in DOWN_KEYWORDS if keyword in text)
    raw = up_hits - down_hits
    if move == "down":
        raw = -raw
    if raw >= 2:
        return 2
    if raw <= -2:
        return -2
    if raw > 0:
        return 1
    if raw < 0:
        return -1
    return 0


def _rank_evidence(lines: list[EvidenceLine]) -> list[EvidenceLine]:
    role_rank = {"main": 0, "support": 1, "counter": 2}
    return sorted(lines, key=lambda item: (role_rank[item.role], -item.score))


def _item_published_at(item) -> str | None:
    return getattr(item, "published_at", None) or getattr(item, "publishedAt", None)


def _item_signal_text(item) -> str:
    parts = [
        getattr(item, "topic", None),
        getattr(item, "title", None),
        getattr(item, "headline", None),
        getattr(item, "signal", None),
        getattr(item, "category", None),
        getattr(item, "summary", None),
        getattr(item, "impact", None),
    ]
    return " ".join(str(part) for part in parts if part)


def _match_score(profile: StockProfile, move: str, text: str, target_date: str, published_at: str) -> float:
    return _evidence_score(
        profile=profile,
        move=move,
        signal=text,
        summary=text,
        published_at=published_at,
        target_date=target_date,
        base=0.62,
    )


def _relevance_bonus(profile: StockProfile | None, signal: str, summary: str) -> float:
    if profile is None:
        return 0.0
    text = f"{signal} {summary}"
    tokens = [profile.name, profile.symbol.split(".")[0], *profile.concepts]
    sector_tokens = [part.strip() for part in profile.sector.replace("/", " ").split() if part.strip()]
    matches = sum(1 for token in [*tokens, *sector_tokens] if token and token in text)
    if matches >= 3:
        return 0.08
    if matches == 2:
        return 0.05
    if matches == 1:
        return 0.02
    return 0.0


def _time_bonus(published_at: str | None, target_date: str | None) -> float:
    if not published_at or not target_date:
        return 0.0
    try:
        item_date = datetime.fromisoformat(str(published_at)[:10]).date()
        ref_date = datetime.fromisoformat(str(target_date)[:10]).date()
    except ValueError:
        return 0.0
    gap = abs((ref_date - item_date).days)
    if gap <= 3:
        return 0.05
    if gap <= 10:
        return 0.03
    if gap <= 30:
        return 0.01
    return -0.02
