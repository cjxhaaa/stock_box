# Stock Box

面向 A 股调研场景的跨端 AI Agent 软件骨架。目标是支持 Windows、macOS、Linux、Android，并围绕单只股票提供以下能力：

- 回溯过去一年内的炒作脉络，解释关键上涨/下跌日期
- 识别个股在对应题材中的梯队位置
- 识别暴雷风险、财务异常、监管风险和情绪退潮风险
- 自动扩散到同类个股，比较谁更强、更稳、更具赔率
- 聚合实时行情、热门新闻、公告、题材热度和股吧评论，生成研究结论

当前仓库提供的是第一阶段骨架：

- `apps/client`: Tauri 2 兼容的 React/Vite 前端
- `apps/api`: FastAPI 分析服务
- `packages/contracts`: 前后端共享数据模型
- `docs`: 架构说明、数据路线和落地节奏

## 为什么选这条技术路线

客户端选择 `Tauri 2 + React + TypeScript`，原因是它已经支持桌面和移动端能力扩展，适合用一套前端覆盖 Windows、macOS、Linux 和 Android。分析服务独立为 `Python + FastAPI`，原因是数据工程、NLP、RAG、舆情和量化特征计算在 Python 生态下更高效。

这意味着最终形态不是“把所有 AI 都塞进端上”，而是：

1. 跨端客户端负责交互、检索、展示、缓存和通知
2. 服务端负责行情接入、新闻抓取、论坛解析、事件归因和风控评分
3. 端上通过 Tauri 打包，服务端按模块扩展

## 当前已实现

- 一个共享的研究报告契约和股票搜索契约
- 一个可运行的 FastAPI 研究 API，包含搜索、状态、报告编排、研究快照、缓存复用、同类对比和 Markdown 导出
- 一个更接近投研工作台的研究页 UI，支持联想选股、最近研究、证据入口跳转、按来源类型归档、缓存状态展示、强制刷新、同类对比和 Markdown 导出
- 一套可替换 provider 的后端结构，支持 provider 路由、降级和状态暴露；当前 `akshare` 已接入真实个股信息、日线、公告列表和新闻流
- 阶段化炒作脉络和逐段证据入口
- 公告与披露摘要区，能下钻到巨潮公告明细页和 PDF 原文
- 社区热议区，当前能拉取东方财富股吧热帖、同花顺个股资讯，并把它们接入散户情绪判断
- 统一来源记录模型，支持来源明细视图、按类型归档和按模块引用来源 ID
- 散户情绪区已经挂接依据链接；当前真实文本主要来自股吧热帖、同花顺资讯和互动易问答，雪球仍保留为入口源
- `Tauri 2` 桌面壳骨架已经落入 `apps/client/src-tauri`，并补上根目录桌面开发脚本
- 基础自动化测试，覆盖搜索与报告结构
- 一套从数据源到事件归因再到风控和情绪分析的系统设计文档

## 本地开发

前端：

```bash
cd apps/client
pnpm install
pnpm dev
```

后端：

```bash
cd apps/api
uv sync
uv run uvicorn app.main:app --reload
```

测试：

```bash
cd apps/api
uv run pytest
```

默认前端读取 `http://127.0.0.1:8000`。

桌面模式：

```bash
pnpm desktop:doctor
pnpm dev:desktop
```

桌面打包（含 API sidecar，支持双击应用自动拉起后端）：

```bash
pnpm build:desktop
```

Windows 专用打包（建议在 Windows 主机执行）：

```bash
pnpm build:desktop:windows
```

桌面交付说明见 [docs/desktop-delivery.md](./docs/desktop-delivery.md)。

## 下一步优先级

1. 继续提高 `akshare` 的板块映射稳定性，把行业/概念映射做成可缓存的真实链路
2. 把“过去一年涨跌归因”进一步升级为基于真实价格异动、公告、新闻和社区热议的事件归因引擎
3. 把东方财富、同花顺从热帖/资讯级推进到原帖正文和评论级，并评估雪球反爬绕过或替代源
4. 把新闻和社区链接继续细化到帖子级、主题级和时间切片级
5. 接入 LLM，把结构化因子和文本证据统一成可追溯报告
6. 补上 Tauri 2 shell、桌面能力和 Android 打包配置

## 当前高不确定项

1. 东方财富、同花顺、雪球的评论抓取接口稳定性和使用边界需要单独核实，建议做平台适配层，不要把分析逻辑直接绑到网页结构上。
2. 实时新闻如果要覆盖财经外的热门事件，数据源很可能需要多家组合，且不同源的授权和延迟差异会直接影响归因精度。
3. Tauri 2 适合统一跨端壳层，但 Android/macOS 的最终打包链仍需要目标平台环境验证，当前仓库还没落这部分。

## 参考

- Tauri 2 官方站点: <https://tauri.app/>
- Tauri 2 依赖与跨平台说明: <https://v2.tauri.app/start/prerequisites/>
- Tushare 文档: <https://tushare.pro/document/2>
