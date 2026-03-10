from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.providers.factory import build_provider
from app.schemas import (
    CompareRequest,
    CompareResponse,
    ReportSnapshotSummary,
    ResearchRequest,
    ResearchResponse,
    StockLookupResult,
    SystemStatus,
)
from app.services.report_formatter import to_markdown
from app.services.research_orchestrator import ResearchOrchestrator
from app.services.snapshot_store import SnapshotStore

settings = get_settings()
provider_selection = build_provider(settings)
snapshot_store = SnapshotStore(settings.db_path)

app = FastAPI(
    title="Stock Box API",
    version="0.1.0",
    description="API for a cross-platform A-share research agent.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = ResearchOrchestrator(provider_selection.provider)


def resolve_report(request: ResearchRequest) -> ResearchResponse:
    max_age = request.max_snapshot_age_minutes or settings.snapshot_ttl_minutes
    if not request.force_refresh:
        cached = snapshot_store.fresh_for_symbol(
            request.symbol,
            max_age,
            include_retail_sentiment=request.include_retail_sentiment,
        )
        if cached is not None:
            return cached.model_copy(update={"from_cache": True})

    report = orchestrator.generate_report(request)
    snapshot_store.save_report(report)
    return report


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/system/status", response_model=SystemStatus)
def system_status() -> SystemStatus:
    return SystemStatus(
        environment=settings.environment,
        requestedProvider=provider_selection.requested_mode,
        activeProvider=provider_selection.active_mode,
        degraded=provider_selection.degraded,
        reason=provider_selection.reason,
        capabilities=provider_selection.provider.data_readiness(),
    )


@app.get("/api/v1/research/recent", response_model=list[ReportSnapshotSummary])
def recent_research(limit: int = 10) -> list[ReportSnapshotSummary]:
    return snapshot_store.list_recent(limit)


@app.get("/api/v1/research/latest/{symbol}", response_model=ResearchResponse)
def latest_research(symbol: str) -> ResearchResponse:
    report = snapshot_store.latest_for_symbol(symbol)
    if report is None:
        return resolve_report(ResearchRequest(symbol=symbol))
    return report.model_copy(update={"from_cache": True})


@app.get("/api/v1/stocks/search", response_model=list[StockLookupResult])
def search_stocks(q: str = "", limit: int = 8) -> list[StockLookupResult]:
    safe_limit = max(1, min(limit, 20))
    return orchestrator.search_stocks(q, safe_limit)


@app.post("/api/v1/research/report", response_model=ResearchResponse)
def generate_report(request: ResearchRequest) -> ResearchResponse:
    return resolve_report(request)


@app.post("/api/v1/research/report/markdown", response_class=PlainTextResponse)
def generate_report_markdown(request: ResearchRequest) -> str:
    report = resolve_report(request)
    return to_markdown(report)


@app.post("/api/v1/research/compare", response_model=CompareResponse)
def compare_reports(request: CompareRequest) -> CompareResponse:
    primary = resolve_report(
        ResearchRequest(
            symbol=request.symbol,
            includeRetailSentiment=request.include_retail_sentiment,
            forceRefresh=request.force_refresh,
        )
    )
    peer_symbols = request.peer_symbols or [item.symbol for item in primary.comparables[:3]]
    peer_reports: list[ResearchResponse] = []
    for symbol in peer_symbols:
        if symbol == primary.symbol:
            continue
        peer_reports.append(
            resolve_report(
                ResearchRequest(
                    symbol=symbol,
                    includeRetailSentiment=request.include_retail_sentiment,
                    forceRefresh=request.force_refresh,
                )
            )
        )

    return CompareResponse(
        primarySymbol=primary.symbol,
        rows=orchestrator.compare_rows([primary, *peer_reports], primary.symbol),
    )
