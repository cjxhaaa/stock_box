from __future__ import annotations

from dataclasses import dataclass

from app.config import AppSettings
from app.providers.akshare_provider import AkshareResearchProvider
from app.providers.base import ResearchProvider
from app.providers.mock_provider import MockResearchProvider
from app.providers.tushare_provider import TushareResearchProvider


@dataclass(frozen=True)
class ProviderSelection:
    provider: ResearchProvider
    requested_mode: str
    active_mode: str
    degraded: bool
    reason: str | None


def build_provider(settings: AppSettings) -> ProviderSelection:
    requested = settings.provider_mode

    if requested == "akshare":
        try:
            provider = AkshareResearchProvider(settings)
            return ProviderSelection(
                provider=provider,
                requested_mode=requested,
                active_mode=provider.provider_mode,
                degraded=False,
                reason=None,
            )
        except RuntimeError as exc:
            provider = MockResearchProvider()
            provider.degraded_reason = str(exc)
            return ProviderSelection(
                provider=provider,
                requested_mode=requested,
                active_mode=provider.provider_mode,
                degraded=True,
                reason=str(exc),
            )

    if requested == "tushare":
        try:
            provider = TushareResearchProvider(settings)
            return ProviderSelection(
                provider=provider,
                requested_mode=requested,
                active_mode=provider.provider_mode,
                degraded=False,
                reason=None,
            )
        except RuntimeError as exc:
            provider = MockResearchProvider()
            provider.degraded_reason = str(exc)
            return ProviderSelection(
                provider=provider,
                requested_mode=requested,
                active_mode=provider.provider_mode,
                degraded=True,
                reason=str(exc),
            )

    provider = MockResearchProvider()
    return ProviderSelection(
        provider=provider,
        requested_mode=requested,
        active_mode=provider.provider_mode,
        degraded=False,
        reason=None,
    )
