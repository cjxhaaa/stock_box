from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.schemas import ReportSnapshotSummary, ResearchResponse


class SnapshotStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def save_report(self, report: ResearchResponse) -> None:
        payload = report.model_dump(by_alias=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                insert into research_snapshots (
                    symbol,
                    company_name,
                    market,
                    sector,
                    risk_level,
                    include_retail_sentiment,
                    generated_at,
                    thesis,
                    report_json
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.symbol,
                    report.company_name,
                    report.market,
                    report.sector,
                    report.risk_level,
                    1 if report.retail_sentiment is not None else 0,
                    report.generated_at,
                    report.thesis,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
            connection.commit()

    def list_recent(self, limit: int = 10) -> list[ReportSnapshotSummary]:
        safe_limit = max(1, min(limit, 50))
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                select symbol, company_name, market, sector, risk_level, generated_at, thesis
                from research_snapshots
                order by generated_at desc, id desc
                limit ?
                """,
                (safe_limit,),
            ).fetchall()

        return [
            ReportSnapshotSummary(
                symbol=row[0],
                companyName=row[1],
                market=row[2],
                sector=row[3],
                riskLevel=row[4],
                generatedAt=row[5],
                thesis=row[6],
            )
            for row in rows
        ]

    def latest_for_symbol(self, symbol: str, include_retail_sentiment: bool | None = None) -> ResearchResponse | None:
        normalized = symbol.strip().upper()
        query = """
            select report_json
            from research_snapshots
            where symbol = ?
        """
        params: list[object] = [normalized]
        if include_retail_sentiment is not None:
            query += " and include_retail_sentiment = ?"
            params.append(1 if include_retail_sentiment else 0)
        query += """
            order by generated_at desc, id desc
        """
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(query, params).fetchall()

        for row in rows:
            payload = json.loads(row[0])
            payload.setdefault("provider", "mock")
            payload.setdefault("fromCache", False)
            payload.setdefault("usingLiveData", False)
            payload.setdefault("filingsDigest", [])
            payload.setdefault("forumDigest", [])
            payload.setdefault("eventClusters", [])
            for item in payload.get("newsDigest", []):
                item.setdefault("topic", "公司动态")
            for item in payload.get("forumDigest", []):
                item.setdefault("topic", "社区观点")
            for timeline_item in payload.get("timeline", []):
                for evidence in timeline_item.get("evidence", []):
                    evidence.setdefault("role", "support")
                    evidence.setdefault("score", 0.5)
            if isinstance(payload.get("retailSentiment"), dict):
                payload["retailSentiment"].setdefault("sourceIds", [])
                payload["retailSentiment"].setdefault("links", [])
            if include_retail_sentiment is not None:
                has_sentiment = payload.get("retailSentiment") is not None
                if has_sentiment != include_retail_sentiment:
                    continue
            return ResearchResponse.model_validate(payload)

        return None

    def fresh_for_symbol(
        self,
        symbol: str,
        max_age_minutes: int,
        include_retail_sentiment: bool | None = None,
    ) -> ResearchResponse | None:
        latest = self.latest_for_symbol(symbol, include_retail_sentiment=include_retail_sentiment)
        if latest is None:
            return None

        generated_at = datetime.fromisoformat(latest.generated_at.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        if generated_at >= cutoff:
            return latest
        return None

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                create table if not exists research_snapshots (
                    id integer primary key autoincrement,
                    symbol text not null,
                    company_name text not null,
                    market text not null,
                    sector text not null,
                    risk_level text not null,
                    include_retail_sentiment integer not null default 0,
                    generated_at text not null,
                    thesis text not null,
                    report_json text not null
                )
                """
            )
            columns = [row[1] for row in connection.execute("pragma table_info(research_snapshots)").fetchall()]
            if "include_retail_sentiment" not in columns:
                connection.execute(
                    "alter table research_snapshots add column include_retail_sentiment integer not null default 0"
                )
            connection.execute(
                """
                create index if not exists idx_research_snapshots_symbol_generated_at
                on research_snapshots(symbol, include_retail_sentiment, generated_at desc)
                """
            )
            connection.commit()
