from __future__ import annotations

from app.catalog import StockProfile
from app.schemas import EventCluster, FilingDigestItem, RiskItem


def build_risks(
    profile: StockProfile,
    filings_digest: list[FilingDigestItem] | None = None,
    event_clusters: list[EventCluster] | None = None,
) -> tuple[int, str, list[RiskItem], list[str]]:
    items: list[RiskItem] = []
    filings_digest = filings_digest or []
    event_clusters = event_clusters or []

    if profile.volatility_score >= 70:
        items.append(
            RiskItem(
                title="高波动题材回撤风险",
                level="high",
                score=82,
                detail="这类标的容易受主线切换和高位分歧影响，回撤速度通常快于指数。",
                watch=True,
            )
        )
    else:
        items.append(
            RiskItem(
                title="相对收益受风格切换影响",
                level="medium",
                score=56,
                detail="当市场追逐更高弹性方向时，当前标的的相对收益可能阶段性落后。",
                watch=False,
            )
        )

    if profile.quality_score <= 78:
        items.append(
            RiskItem(
                title="基本面验证强度不足",
                level="medium",
                score=61,
                detail="需要跟踪订单、利润率和现金流质量，避免纯叙事交易失真。",
                watch=True,
            )
        )
    else:
        items.append(
            RiskItem(
                title="高预期透支风险",
                level="medium",
                score=52,
                detail="高质量龙头通常面临较高预期，若增速低于市场预期也会触发估值压缩。",
                watch=False,
            )
        )

    if profile.archetype in {"policy_sensitive_quality", "cyclical_resource"}:
        items.append(
            RiskItem(
                title="政策与外部变量扰动",
                level="medium",
                score=64,
                detail="政策节奏、国际关系或商品价格波动会显著影响交易情绪和估值锚。",
                watch=True,
            )
        )
    else:
        items.append(
            RiskItem(
                title="监管与异常波动监控",
                level="medium",
                score=58,
                detail="正式版本需结合问询函、立案、处罚和异常波动监管做更细颗粒度评分。",
                watch=True,
            )
        )

    flagged_filings = [item for item in filings_digest if item.category in {"风险提示", "股权变动", "监管事项"}]
    if flagged_filings:
        latest = flagged_filings[0]
        score = min(84, 62 + len(flagged_filings) * 5)
        level = "high" if latest.category == "监管事项" else "medium"
        items.append(
            RiskItem(
                title="近期公告出现重点观察信号",
                level=level,
                score=score,
                detail=f"最近公告“{latest.title}”提示需要重点跟踪 {latest.signal}，短线情绪与基本面预期都可能受影响。",
                watch=True,
            )
        )

    event_risks = _event_risk_items(event_clusters)
    items.extend(event_risks)

    average_score = round(sum(item.score for item in items) / len(items))
    if any(item.level == "high" for item in items):
        risk_level = "high"
    elif average_score >= 60:
        risk_level = "medium"
    else:
        risk_level = "low"

    watchlist = [
        "是否出现连续放量滞涨",
        "板块龙头高度是否被压制",
        "是否有新的问询函、减持或业绩低预期信号",
    ]
    for item in flagged_filings[:2]:
        watchlist.append(f"公告跟踪: {item.signal}")
    for item in event_clusters[:3]:
        if item.direction in {"negative", "mixed"}:
            watchlist.append(f"事件跟踪: {item.topic} / {item.direction}")
    return average_score, risk_level, items, watchlist


def _event_risk_items(event_clusters: list[EventCluster]) -> list[RiskItem]:
    items: list[RiskItem] = []
    seen_titles: set[str] = set()
    for event in event_clusters:
        if event.direction not in {"negative", "mixed"}:
            continue
        score = _event_risk_score(event)
        level = "high" if score >= 78 else "medium"
        title = f"事件簇触发{event.topic}风险复核"
        if title in seen_titles:
            continue
        items.append(
            RiskItem(
                title=title,
                level=level,
                score=score,
                detail=(
                    f"最近事件簇“{event.topic}”呈现 {event.direction} 方向，来源覆盖 {' / '.join(event.source_kinds)}，"
                    f"需要复核其对短线情绪、预期差和资金承接的影响。"
                ),
                watch=True,
            )
        )
        seen_titles.add(title)
        if len(items) >= 2:
            break
    return items


def _event_risk_score(event: EventCluster) -> int:
    topic_weights = {
        "股权变动": 82,
        "业绩预期": 78,
        "监管与风险": 84,
        "融资与资金": 72,
        "风险与分歧": 76,
    }
    base = topic_weights.get(event.topic, 68)
    if event.direction == "mixed":
        base -= 4
    if "filing" in event.source_kinds:
        base += 4
    if len(event.source_kinds) >= 2:
        base += 2
    return max(60, min(88, base))
