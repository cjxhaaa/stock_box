from __future__ import annotations

from app.providers.mock_provider import MarketSnapshot
from app.schemas import MarketPulse


def build_market_pulse(snapshot: MarketSnapshot) -> MarketPulse:
    return MarketPulse(
        regime=snapshot.regime,
        riskAppetite=snapshot.risk_appetite,
        dominantThemes=list(snapshot.dominant_themes),
        commentary=snapshot.commentary,
    )

