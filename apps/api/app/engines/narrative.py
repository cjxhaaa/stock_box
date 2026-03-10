from __future__ import annotations

from app.catalog import StockProfile
from app.schemas import NarrativeStage, SourceLink


def build_narrative_stages(
    profile: StockProfile,
    timeline_ranges: list[str],
    reference_bundle: dict[str, SourceLink],
) -> list[NarrativeStage]:
    concept = profile.concepts[0]
    secondary_concept = profile.concepts[1] if len(profile.concepts) > 1 else profile.concepts[0]

    ranges = (timeline_ranges + ["近一年初期", "中期", "后期", "当前"])[:4]
    return [
        NarrativeStage(
            title="预热建仓",
            dateRange=ranges[0],
            status="build",
            summary=f"{profile.name} 的交易叙事开始从基本面观察转向 {concept} 主题预期，市场先做认知建立。",
            driver=f"{concept} 相关话题升温，资金开始把它纳入观察名单。",
            sourceIds=[reference_bundle["stage_build"].id, reference_bundle["community"].id],
            links=[reference_bundle["stage_build"], reference_bundle["community"]],
        ),
        NarrativeStage(
            title="主升扩散",
            dateRange=ranges[1],
            status="accelerate",
            summary=f"当主线确认后，{profile.name} 更容易从板块共振中获得弹性，股价进入加速段。",
            driver=f"板块龙头打开高度，{secondary_concept} 与成交放大共同强化交易预期。",
            sourceIds=[reference_bundle["market"].id, reference_bundle["forum"].id],
            links=[reference_bundle["market"], reference_bundle["forum"]],
        ),
        NarrativeStage(
            title="高位分歧",
            dateRange=ranges[2],
            status="diverge",
            summary="随着预期抬高，市场开始重新审视业绩兑现、估值承受力和监管约束。",
            driver="新增催化边际减弱后，分歧会先在高位成交和社区讨论里出现。",
            sourceIds=[reference_bundle["stage_diverge"].id, reference_bundle["forum"].id],
            links=[reference_bundle["stage_diverge"], reference_bundle["forum"]],
        ),
        NarrativeStage(
            title="退潮或再定价",
            dateRange=ranges[3],
            status="cooldown",
            summary=f"{profile.name} 后续是继续留在主线，还是转入估值回摆，取决于真实数据验证与市场风格。",
            driver="景气验证、政策变化和主线切换会决定它最终是二波还是冷却。",
            sourceIds=[reference_bundle["filing"].id, reference_bundle["community"].id],
            links=[reference_bundle["filing"], reference_bundle["community"]],
        ),
    ]
