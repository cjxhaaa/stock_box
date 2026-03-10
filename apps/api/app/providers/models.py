from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DailyBar:
    trade_date: str
    open: float
    close: float
    high: float
    low: float
    amount: float
    turnover_rate: float
    pct_change: float
