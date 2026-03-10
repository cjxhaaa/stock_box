from __future__ import annotations

from app.schemas import ResearchResponse, SourceLink


def to_markdown(report: ResearchResponse) -> str:
    lines: list[str] = [
        f"# {report.company_name} {report.symbol}",
        "",
        f"- 市场: {report.market}",
        f"- 赛道: {report.sector}",
        f"- 风险等级: {report.risk_level}",
        f"- 风险分: {report.risk_score}",
        f"- 置信度: {round(report.confidence * 100)}%",
        f"- 数据状态: {'实时数据' if report.using_live_data else '演示数据'}",
        "",
        "## 核心判断",
        "",
        report.thesis,
        "",
        f"- 交易风格: {report.overview.trading_style}",
        f"- 当前叙事: {report.overview.dominant_narrative}",
        f"- 多头场景: {report.overview.bull_case}",
        f"- 空头场景: {report.overview.bear_case}",
        f"- 关键问题: {report.overview.key_question}",
        "",
        "## 数据就绪状态",
        "",
    ]

    for item in report.data_readiness:
        lines.append(f"- {item.label}: {item.status}，{item.detail}")

    lines.extend(["", "## 阶段化脉络", ""])
    for stage in report.narrative_stages:
        lines.extend(
            [
                f"### {stage.title} ({stage.date_range})",
                "",
                f"- 状态: {stage.status}",
                f"- 概要: {stage.summary}",
                f"- 驱动: {stage.driver}",
                f"- 依据: {_join_links(stage.links)}",
                "",
            ]
        )

    lines.extend(["## 关键涨跌日", ""])
    for item in report.timeline:
        lines.extend(
            [
                f"### {item.date} | {item.move} | {item.change_pct:+.2f}%",
                "",
                f"- 梯队: {item.ladder_position}",
                f"- 概要: {item.summary}",
                f"- 解读: {item.interpretation}",
                f"- 催化: {item.catalyst}",
                f"- 证据:",
            ]
        )
        for evidence in item.evidence:
            lines.append(
                f"  - {evidence.role} / {evidence.source} / {evidence.signal} / {round(evidence.score * 100)}分: "
                f"{evidence.summary} ({_join_links(evidence.links)})"
            )
        lines.append("")

    lines.extend(["## 风险项", ""])
    for risk in report.risks:
        watch = "重点跟踪" if risk.watch else "常规跟踪"
        lines.append(f"- {risk.title}: {risk.level} / {risk.score}分 / {watch}。{risk.detail}")

    lines.extend(["", "## 可比标的", ""])
    for item in report.comparables:
        lines.append(
            f"- {item.name} {item.symbol}: {item.reason} {item.edge} "
            f"(质量 {item.quality_score} / 波动 {item.volatility_score})"
        )

    lines.extend(["", "## 公告与披露", ""])
    for item in report.filings_digest:
        lines.append(
            f"- {item.published_at} {item.title} [{item.category} / {item.signal}]: "
            f"{item.summary} ({_join_links(item.links)})"
        )

    lines.extend(["", "## 事件簇", ""])
    for item in report.event_clusters:
        lines.append(
            f"- {item.published_at} {item.topic} [{item.direction} / {' / '.join(item.source_kinds)}]: "
            f"{item.summary} ({_join_links(item.links)})"
        )

    lines.extend(["", "## 新闻影响", ""])
    for item in report.news_digest:
        lines.append(f"- {item.headline} [{item.topic} / {item.category}]: {item.impact} ({_join_links(item.links)})")

    lines.extend(["", "## 社区热议", ""])
    for item in report.forum_digest:
        lines.append(
            f"- {item.published_at} {item.title} [{item.topic} / {item.platform} / {item.heat}]: "
            f"{item.summary} ({_join_links(item.links)})"
        )

    if report.retail_sentiment is not None:
        lines.extend(
            [
                "",
                "## 散户情绪",
                "",
                f"- 看多: {round(report.retail_sentiment.bullish_ratio * 100)}%",
                f"- 看空: {round(report.retail_sentiment.bearish_ratio * 100)}%",
                f"- 中性: {round(report.retail_sentiment.neutrality_ratio * 100)}%",
                f"- 总结: {report.retail_sentiment.summary}",
                f"- 关键词: {' / '.join(report.retail_sentiment.keywords)}",
                f"- 依据: {_join_links(report.retail_sentiment.links)}" if report.retail_sentiment.links else "- 依据: 无",
            ]
        )

    lines.extend(["", "## 统一依据入口", ""])
    for link in report.source_links:
        lines.append(f"- [{link.label}]({link.url}) - {link.note}")

    lines.extend(["", "## 免责声明", "", report.disclaimer])
    return "\n".join(lines)


def _join_links(links: list[SourceLink]) -> str:
    return " / ".join(f"[{link.label}]({link.url})" for link in links)
