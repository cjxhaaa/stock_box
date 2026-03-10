# 系统架构

## 1. 产品目标

这个 Agent 不是普通问答机器人，而是一个面向 A 股短中周期研究的“研究协作系统”。输入一只股票后，系统需要生成一份带证据链的研究结果：

- 一年内的关键行情阶段
- 每次大涨大跌的潜在驱动
- 题材归属与梯队位置
- 暴雷风险和基本面风险
- 同类可比标的
- 最新新闻与市场热度影响
- 散户情绪和短线博弈可能性

## 2. 总体架构

```text
Tauri Client / Android App
        |
        v
API Gateway / Auth / Rate Limit
        |
        v
Research Orchestrator
  |- Market Data Connectors
  |- News Aggregator
  |- Forum Collector
  |- Event Attribution Engine
  |- Risk Engine
  |- Peer Comparison Engine
  |- LLM Report Composer
        |
        v
Storage Layer
  |- OLTP: PostgreSQL
  |- Time Series: Timescale / ClickHouse
  |- Cache / Queue: Redis
  |- Full Text / Vector: OpenSearch / pgvector
  |- Object Storage: raw pages, announcements, snapshots
```

## 3. 核心模块

### 3.1 行情与板块数据层

职责：

- 获取日线、分钟线、成交额、换手率、涨跌停、龙虎榜、资金流向
- 获取概念板块、行业板块、热榜和板块成分变化
- 将个股在某个交易日映射到当日主线题材和梯队位置

建议来源：

- Tushare: 行情、财务、题材、资金流、龙虎榜
- AkShare: 公共数据补充
- 交易所公告和上市公司公告原文

### 3.2 新闻聚合层

目标不是只抓财经新闻，而是抓一切可能影响题材预期的热门信息：

- 财经快讯
- 公司公告
- 监管通报
- 行业政策
- 宏观新闻
- 社会议题
- 国际新闻
- 科技热点

这里要做两件事：

1. `entity linking`，把新闻映射到公司、行业、概念、供应链
2. `market relevance scoring`，判断一条热门内容对 A 股博弈是否有影响

### 3.3 股吧与论坛情绪层

覆盖对象：

- 东方财富股吧
- 同花顺社区/热榜相关评论
- 雪球讨论

输出不是“看多/看空”这么简单，而是：

- 多空占比
- 情绪斜率
- 一致性过高风险
- 散户关注点迁移
- 是否出现典型高位接力叙事

### 3.4 事件归因引擎

这是产品核心。

对过去一年中显著涨跌日做事件归因时，不能只看一条新闻，而要合并多信号：

- 当日价格与成交异常
- 板块强度和市场风格
- 新闻、公告、政策与社媒讨论
- 同类股票共振
- 资金面和游资活跃度

归因结果建议采用“证据栈”形式：

- 主因
- 次因
- 反证
- 置信度

### 3.5 风险引擎

暴雷风险需要拆成多维评分，而不是单个标签：

- 财务风险：现金流恶化、应收异常、审计意见、连续亏损
- 经营风险：订单依赖、客户集中、行业下行
- 治理风险：高质押、高减持、关联交易、违规担保
- 监管风险：问询函、立案、处罚、异常波动监管
- 市场风险：纯题材驱动、成交脆弱、情绪退潮、筹码松动

建议最终输出：

- `risk_level`
- `risk_score`
- `risk_items`
- `watch_list`

### 3.6 可比标的引擎

不能只按行业找可比，需要多维相似度：

- 同概念
- 同产业链位置
- 同市值区间
- 同弹性
- 同财务质量
- 同交易风格

然后输出：

- 更强势标的
- 更稳健标的
- 更低估标的
- 替代性最强标的

## 4. Agent 工作流

```text
输入股票
-> 标准化证券代码
-> 拉取基础数据与最近一年行情
-> 检测显著涨跌日
-> 为每个关键日检索相关新闻/公告/板块/评论
-> 归因并计算置信度
-> 计算风险项
-> 计算可比标的
-> 汇总最新市场上下文
-> 生成研究报告
```

## 5. 数据表建议

### `security_master`

- symbol
- ts_code
- name
- exchange
- industry
- concept_tags
- listing_date

### `market_daily`

- symbol
- trade_date
- open
- close
- high
- low
- volume
- amount
- turnover_rate
- limit_status

### `news_events`

- id
- published_at
- title
- source
- category
- content
- linked_symbols
- linked_concepts
- popularity_score
- market_relevance_score

### `forum_posts`

- id
- platform
- symbol
- posted_at
- author
- title
- content
- likes
- replies
- sentiment
- emotion_tags

### `research_snapshots`

- symbol
- generated_at
- report_json
- confidence
- live_data

## 6. 模型层建议

### 规则引擎负责

- 日期窗口筛选
- 涨跌异常识别
- 风险硬指标判断
- 板块梯队规则

### 机器学习/NLP 负责

- 新闻主题分类
- 舆情情绪分类
- 热点向市场影响映射
- 文本聚类去重

### LLM 负责

- 多源证据归纳
- 因果链文字表达
- 不确定性说明
- 生成用户可读报告

结论不要直接由 LLM 幻觉产出，LLM 只负责“解释已检索证据”。

## 7. 跨端交付建议

优先顺序：

1. Web/Tauri Desktop
2. Android
3. macOS 原生打包细化
4. iOS 视团队资源决定

原因是 Android 和桌面端的投研使用场景最接近，且 Tauri 2 已经支持移动端扩展能力。iOS 也支持，但需要 macOS 环境进行构建。

## 8. 当前仓库范围

当前仓库已经实现了“骨架 + 演示链路 + 可替换 provider 的模块化后端”，包括：

- 股票搜索接口
- 研究编排器
- 时间线、风险、可比、市场脉搏、新闻、情绪等独立引擎
- 一页式研究工作台 UI

但仍不包含：

- 真正的行情抓取
- 大规模新闻聚合
- 股吧爬虫
- 向量检索
- 模型推理服务
- 登录、订阅和权限系统

这些是下一阶段要接入的能力。
