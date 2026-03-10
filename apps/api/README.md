# API

当前 API 提供演示级研究接口：

- `GET /health`
- `GET /api/v1/system/status`
- `GET /api/v1/stocks/search`
- `GET /api/v1/research/recent`
- `GET /api/v1/research/latest/{symbol}`
- `POST /api/v1/research/report`
- `POST /api/v1/research/compare`
- `POST /api/v1/research/report/markdown`

现阶段返回的是基于本地规则引擎和 mock provider 的结构化报告，目的是先把前后端链路、字段设计和页面展示稳定下来。后续只需要替换 provider 和各分析引擎的数据来源，不需要改前端页面协议。

## 启动

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## 当前结构

- `app/catalog.py`: 本地股票目录
- `app/config.py`: 运行模式与 provider 配置
- `app/providers/mock_provider.py`: 可替换的数据提供者
- `app/providers/factory.py`: provider 选择与降级逻辑
- `app/data/evidence_seed.py`: 本地来源记录与证据种子
- `app/engines/*`: 时间线、风险、可比、情绪、市场脉搏等引擎
- `app/services/research_orchestrator.py`: 研究编排入口
- `app/services/report_formatter.py`: Markdown 导出器
- `app/services/snapshot_store.py`: SQLite 研究快照存储
- `tests/test_api.py`: 搜索与报告结构测试

## 缓存与刷新

- `POST /api/v1/research/report` 默认优先读取最近快照
- 可通过 `forceRefresh=true` 强制重新生成
- 可通过 `maxSnapshotAgeMinutes` 控制快照有效期
- 快照会区分是否包含 `retailSentiment`

## Provider 模式

- 默认 `mock`
- 设置 `STOCKBOX_PROVIDER_MODE=akshare` 可启用真实个股信息、行业映射与日线数据
- 设置 `STOCKBOX_PROVIDER_MODE=tushare` 且安装 `tushare`、配置 `TUSHARE_TOKEN` 后，可切换到真实 provider 骨架
- 如果请求真实 provider 但依赖或 token 缺失，会自动降级到 `mock`，并在 `/api/v1/system/status` 返回降级原因
