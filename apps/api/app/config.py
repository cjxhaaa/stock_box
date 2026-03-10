from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    provider_mode: str
    tushare_token: str | None
    environment: str
    db_path: str
    snapshot_ttl_minutes: int


def get_settings() -> AppSettings:
    return AppSettings(
        provider_mode=os.getenv("STOCKBOX_PROVIDER_MODE", "mock").strip().lower() or "mock",
        tushare_token=os.getenv("TUSHARE_TOKEN"),
        environment=os.getenv("STOCKBOX_ENV", "development").strip().lower() or "development",
        db_path=os.getenv("STOCKBOX_DB_PATH", "/home/cjxh/stock-box/apps/api/data/stock_box.db"),
        snapshot_ttl_minutes=max(1, int(os.getenv("STOCKBOX_SNAPSHOT_TTL_MINUTES", "240"))),
    )
