from __future__ import annotations

from app.config import AppSettings
from app.providers.mock_provider import MockResearchProvider
from app.schemas import DataReadinessItem


class TushareResearchProvider(MockResearchProvider):
    provider_name = "tushare"
    provider_mode = "tushare"
    degraded_reason: str | None = None

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        if not settings.tushare_token:
            raise RuntimeError("TUSHARE_TOKEN is not configured")

        try:
            import tushare  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError("tushare package is not installed") from exc

        self.client = tushare.pro_api(settings.tushare_token)

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
                        detail="已配置 Tushare provider，后续可接入真实行情、板块和财务数据。",
                    )
                )
            else:
                rewritten.append(item)
        return rewritten
