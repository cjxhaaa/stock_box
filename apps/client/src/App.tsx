import { FormEvent, useDeferredValue, useEffect, useState } from "react";
import type {
  CompareResponse,
  ReportSnapshotSummary,
  ResearchRequest,
  ResearchResponse,
  SourceLink,
  StockLookupResult,
  SystemStatus
} from "@stock-box/contracts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const fallbackQuickPicks: StockLookupResult[] = [
  {
    symbol: "300308.SZ",
    name: "中际旭创",
    market: "创业板",
    sector: "光模块 / AI 算力",
    concepts: ["AI 算力", "CPO", "高速光模块"]
  },
  {
    symbol: "002594.SZ",
    name: "比亚迪",
    market: "深市主板",
    sector: "新能源车 / 智能驾驶",
    concepts: ["整车", "动力电池", "出海"]
  },
  {
    symbol: "600036.SH",
    name: "招商银行",
    market: "沪市主板",
    sector: "银行 / 高股息",
    concepts: ["高股息", "机构重仓", "低波防御"]
  }
];

const demoSources: SourceLink[] = [
  {
    id: "300308.SZ:market_quote",
    label: "东方财富行情页",
    url: "https://quote.eastmoney.com/sz300308.html",
    domain: "quote.eastmoney.com",
    kind: "market",
    publishedAt: null,
    note: "查看行情、成交与板块入口"
  },
  {
    id: "300308.SZ:cninfo_profile",
    label: "巨潮资讯公司页",
    url: "https://www.cninfo.com.cn/new/snapshot/companyDetailCn?code=300308",
    domain: "www.cninfo.com.cn",
    kind: "filing",
    publishedAt: null,
    note: "查看公告、财报和监管披露"
  },
  {
    id: "300308.SZ:eastmoney_forum",
    label: "东方财富股吧",
    url: "https://guba.eastmoney.com/list,300308.html",
    domain: "guba.eastmoney.com",
    kind: "forum",
    publishedAt: null,
    note: "查看散户讨论和情绪变化"
  },
  {
    id: "300308.SZ:ths_stock",
    label: "同花顺个股页",
    url: "https://stockpage.10jqka.com.cn/300308/",
    domain: "stockpage.10jqka.com.cn",
    kind: "community",
    publishedAt: null,
    note: "查看同花顺个股资讯与讨论入口"
  },
  {
    id: "300308.SZ:xueqiu_stock",
    label: "雪球个股页",
    url: "https://xueqiu.com/S/SZ300308",
    domain: "xueqiu.com",
    kind: "community",
    publishedAt: null,
    note: "查看个股讨论与资讯聚合"
  },
  {
    id: "300308.SZ:cninfo_irm",
    label: "互动易入口",
    url: "https://irm.cninfo.com.cn/ircs/company/companyDetails?stockcode=300308",
    domain: "irm.cninfo.com.cn",
    kind: "forum",
    publishedAt: null,
    note: "查看投资者问答与关注问题"
  }
];

const fallbackReport: ResearchResponse = {
  symbol: "300308.SZ",
  companyName: "中际旭创",
  market: "创业板",
  sector: "光模块 / AI 算力",
  conceptTags: ["AI 算力", "CPO", "高速光模块"],
  sourceLinks: demoSources,
  sources: [
    {
      id: "300308.SZ:market_quote",
      label: "中际旭创 东方财富行情页",
      url: "https://quote.eastmoney.com/sz300308.html",
      domain: "quote.eastmoney.com",
      kind: "market",
      publishedAt: null,
      note: "行情、成交、盘口和板块入口。"
    },
    {
      id: "300308.SZ:cninfo_profile",
      label: "中际旭创 巨潮资讯公司页",
      url: "https://www.cninfo.com.cn/new/snapshot/companyDetailCn?code=300308",
      domain: "www.cninfo.com.cn",
      kind: "filing",
      publishedAt: null,
      note: "公告、财报和监管披露入口。"
    },
    {
      id: "300308.SZ:eastmoney_forum",
      label: "中际旭创 东方财富股吧",
      url: "https://guba.eastmoney.com/list,300308.html",
      domain: "guba.eastmoney.com",
      kind: "forum",
      publishedAt: null,
      note: "散户讨论、热帖与情绪入口。"
    },
    {
      id: "300308.SZ:ths_stock",
      label: "中际旭创 同花顺个股页",
      url: "https://stockpage.10jqka.com.cn/300308/",
      domain: "stockpage.10jqka.com.cn",
      kind: "community",
      publishedAt: null,
      note: "同花顺资讯、讨论和资金标签入口。"
    },
    {
      id: "300308.SZ:xueqiu_stock",
      label: "中际旭创 雪球个股页",
      url: "https://xueqiu.com/S/SZ300308",
      domain: "xueqiu.com",
      kind: "community",
      publishedAt: null,
      note: "观点、讨论和资讯聚合入口。"
    },
    {
      id: "300308.SZ:cninfo_irm",
      label: "中际旭创 互动易入口",
      url: "https://irm.cninfo.com.cn/ircs/company/companyDetails?stockcode=300308",
      domain: "irm.cninfo.com.cn",
      kind: "forum",
      publishedAt: null,
      note: "互动易问答与投资者关注问题入口。"
    },
    {
      id: "300308.SZ:theme_reference",
      label: "中际旭创 题材参考入口",
      url: "https://quote.eastmoney.com/sz300308.html",
      domain: "quote.eastmoney.com",
      kind: "theme",
      publishedAt: "2026-03-09",
      note: "当前版本用作题材脉络和板块映射的参考入口。"
    },
    {
      id: "300308.SZ:stage_build",
      label: "中际旭创 算力主线观察入口",
      url: "https://xueqiu.com/S/SZ300308",
      domain: "xueqiu.com",
      kind: "narrative",
      publishedAt: "2025-04-18",
      note: "用于观察算力主线、讨论热度和观点变化。"
    },
    {
      id: "300308.SZ:stage_diverge",
      label: "中际旭创 公告与验证入口",
      url: "https://www.cninfo.com.cn/new/snapshot/companyDetailCn?code=300308",
      domain: "www.cninfo.com.cn",
      kind: "filing",
      publishedAt: "2025-09-03",
      note: "用于核对公告、业绩与监管披露。"
    }
  ],
  dataReadiness: [
    {
      key: "market",
      label: "行情与板块",
      status: "mock",
      detail: "当前使用本地规则和静态样本，尚未接入实时行情与板块异动。"
    },
    {
      key: "filings",
      label: "公告与财报",
      status: "missing",
      detail: "链接已准备，但还没有自动抓取公告、问询函和财报原文。"
    },
    {
      key: "news",
      label: "新闻聚合",
      status: "mock",
      detail: "当前由 mock provider 生成主题摘要，尚未接入多源新闻召回。"
    },
    {
      key: "forum",
      label: "股吧与社区",
      status: "mock",
      detail: "当前情绪结果为规则模拟值，尚未抓取原帖。"
    },
    {
      key: "llm",
      label: "报告生成",
      status: "ready",
      detail: "当前结构化报告和 Markdown 导出链路已可用。"
    }
  ],
  narrativeStages: [
    {
      title: "预热建仓",
      dateRange: "2025-03-10 - 2025-05-20",
      status: "build",
      summary: "市场开始把它纳入 AI 算力主线观察名单，先走预期差和题材映射。",
      driver: "算力资本开支与景气验证预期抬升。",
      sourceIds: ["300308.SZ:stage_build", "300308.SZ:xueqiu_stock"],
      links: [demoSources[0], demoSources[4]]
    },
    {
      title: "主升扩散",
      dateRange: "2025-05-20 - 2025-07-25",
      status: "accelerate",
      summary: "板块高度打开后，资金从龙头向弹性标的扩散，个股进入主升段。",
      driver: "龙头打开高度，成交和社区热度同步放大。",
      sourceIds: ["300308.SZ:market_quote", "300308.SZ:eastmoney_forum"],
      links: [demoSources[0], demoSources[2]]
    },
    {
      title: "高位分歧",
      dateRange: "2025-07-25 - 2025-09-10",
      status: "diverge",
      summary: "高预期下市场开始重新审视兑现能力和估值承压点。",
      driver: "新增催化边际减弱，高位换手和分歧抬升。",
      sourceIds: ["300308.SZ:stage_diverge", "300308.SZ:eastmoney_forum"],
      links: [demoSources[1], demoSources[2]]
    },
    {
      title: "退潮或再定价",
      dateRange: "2025-09-10 - 2026-03-09",
      status: "cooldown",
      summary: "后续走二波还是退潮，取决于真实业绩验证和主线是否重回算力。",
      driver: "业绩、政策和市场风格决定最终再定价方向。",
      sourceIds: ["300308.SZ:cninfo_profile", "300308.SZ:xueqiu_stock"],
      links: [demoSources[1], demoSources[4]]
    }
  ],
  overview: {
    tradingStyle: "高弹性主线博弈",
    dominantNarrative: "当前更像 AI 算力方向的高景气弹性标的。",
    bullCase: "如果算力链景气延续且成交承接维持，个股仍可能保持主线关注。",
    bearCase: "若主线切换或业绩验证不及预期，高预期会快速回摆。",
    keyQuestion: "它还能否继续留在当前主线梯队里？"
  },
  marketPulse: {
    regime: "题材轮动加快，主线集中度中等",
    riskAppetite: "中性偏进攻",
    dominantThemes: ["AI 算力", "业绩验证", "资金切换"],
    commentary: "当前算力链仍有关注度，但交易已经进入比拼持续催化和业绩兑现的阶段。"
  },
  thesis:
    "这是一份演示级研究报告。正式版本会在同样的结构下替换为真实行情、公告、新闻和论坛证据。",
  riskLevel: "high",
  riskScore: 68,
  confidence: 0.72,
  provider: "mock",
  fromCache: false,
  usingLiveData: false,
  generatedAt: "2026-03-09T00:00:00Z",
  timeline: [
    {
      date: "2025-04-18",
      move: "up",
      changePct: 8.34,
      summary: "算力链热度提升，个股出现放量上攻。",
      catalyst: "板块龙头打开高度，带动资金向同题材扩散。",
      sector: "光模块 / AI 算力",
      ladderPosition: "跟风前排",
      interpretation: "这一段更偏主线强化下的扩散性行情。",
      confidence: 0.76,
      evidence: [
        {
          source: "market",
          signal: "放量上涨",
          summary: "板块与个股同步转强。",
          role: "main",
          score: 0.82,
          sourceIds: ["300308.SZ:market_quote"],
          links: [demoSources[0]]
        },
        {
          source: "news",
          signal: "催化映射",
          summary: "市场重新聚焦算力资本开支与景气验证。",
          role: "support",
          score: 0.69,
          sourceIds: ["300308.SZ:cninfo_profile", "300308.SZ:theme_reference"],
          links: [demoSources[1], demoSources[4]]
        },
        {
          source: "forum",
          signal: "讨论热度抬升",
          summary: "散户讨论集中在龙头扩散和景气验证。",
          role: "support",
          score: 0.63,
          sourceIds: ["300308.SZ:eastmoney_forum", "300308.SZ:xueqiu_stock"],
          links: [demoSources[2], demoSources[4]]
        }
      ]
    },
    {
      date: "2025-09-03",
      move: "down",
      changePct: -5.27,
      summary: "主线退潮后资金兑现，个股快速回撤。",
      catalyst: "高位分歧放大，前期获利盘集中兑现。",
      sector: "光模块 / AI 算力",
      ladderPosition: "跟风后排",
      interpretation: "这更像高位一致性被打破后的退潮波段。",
      confidence: 0.7,
      evidence: [
        {
          source: "market",
          signal: "放量回撤",
          summary: "高弹性方向整体承压。",
          role: "main",
          score: 0.8,
          sourceIds: ["300308.SZ:market_quote"],
          links: [demoSources[0]]
        },
        {
          source: "news",
          signal: "催化降温",
          summary: "边际新增利好不足，交易开始回归兑现。",
          role: "main",
          score: 0.74,
          sourceIds: ["300308.SZ:cninfo_profile", "300308.SZ:theme_reference"],
          links: [demoSources[1], demoSources[4]]
        },
        {
          source: "forum",
          signal: "分歧显著增大",
          summary: "讨论区从趋势延续转向高位风险。",
          role: "counter",
          score: 0.71,
          sourceIds: ["300308.SZ:eastmoney_forum", "300308.SZ:xueqiu_stock"],
          links: [demoSources[2], demoSources[4]]
        }
      ]
    }
  ],
  risks: [
    {
      title: "高波动题材回撤风险",
      level: "high",
      score: 82,
      detail: "主线切换和高位分歧会放大回撤速度。",
      watch: true
    },
    {
      title: "高预期透支风险",
      level: "medium",
      score: 59,
      detail: "若景气验证不及预期，估值回摆会比较明显。",
      watch: false
    }
  ],
  comparables: [
    {
      symbol: "000977.SZ",
      name: "浪潮信息",
      reason: "同属 AI 算力主线，受服务器与国产算力叙事带动。",
      edge: "波动更低，更适合稳健替代",
      qualityScore: 76,
      volatilityScore: 74
    }
  ],
  filingsDigest: [
    {
      title: "年报与业绩说明入口",
      category: "定期报告",
      publishedAt: "2026-03-09",
      signal: "跟踪业绩兑现与利润率变化",
      summary: "正式版本会把年报、季报、问询函和风险提示公告细化成逐条摘要，并保留可点击原文链接。",
      sourceIds: ["300308.SZ:cninfo_profile"],
      links: [demoSources[1]]
    },
    {
      title: "股东和交易结构观察",
      category: "股权变动",
      publishedAt: "2026-03-09",
      signal: "跟踪减持、质押和重要股东动作",
      summary: "暴雷与交易风险评估会吸收股东减持、质押、回购与异常波动公告信号。",
      sourceIds: ["300308.SZ:cninfo_profile", "300308.SZ:market_quote"],
      links: [demoSources[1], demoSources[0]]
    }
  ],
  eventClusters: [
    {
      id: "event:0:订单与产能",
      topic: "订单与产能",
      publishedAt: "2026-03-09 08:06:33",
      direction: "positive",
      summary: "订单与产能事件簇汇总了 3 条跨源线索，核心包括中际旭创：公司订单饱满 产能利用率充足；中际旭创：公司订单饱满，产能利用率充足。",
      sourceKinds: ["forum", "news"],
      sourceIds: ["300308.SZ:news:1", "300308.SZ:eastmoney_forum", "300308.SZ:ths_stock"],
      links: [demoSources[2], demoSources[3]]
    },
    {
      id: "event:1:业绩预期",
      topic: "业绩预期",
      publishedAt: "2026-02-28",
      direction: "negative",
      summary: "业绩预期事件簇汇总了公告与新闻线索，核心包括 2025年度业绩快报 与公司目前未发布任何业绩指引。",
      sourceKinds: ["filing", "news"],
      sourceIds: ["300308.SZ:cninfo_profile", "300308.SZ:news:4"],
      links: [demoSources[1], demoSources[0]]
    }
  ],
  forumDigest: [
    {
      title: "中际旭创股吧热议主线仍围绕 AI 算力",
      platform: "东方财富股吧",
      topic: "产品与题材",
      publishedAt: "2026-03-09 14:30",
      heat: "阅读 2410 / 评论 7",
      summary: "热帖标题能反映短线资金关注点和散户叙事焦点。",
      sourceIds: ["300308.SZ:eastmoney_forum"],
      links: [demoSources[2]]
    },
    {
      title: "中际旭创：公司订单饱满，产能利用率充足",
      platform: "同花顺",
      topic: "订单与产能",
      publishedAt: "2026-03-08 22:09",
      heat: "资讯热度",
      summary: "同花顺个股页会把资金、公告和公司问答聚合到高频资讯流里。",
      sourceIds: ["300308.SZ:ths_stock"],
      links: [demoSources[3]]
    }
  ],
  newsDigest: [
    {
      headline: "AI 算力讨论热度抬升",
      category: "热门话题",
      topic: "算力链产品",
      impact: "若热度延续，算力链标的容易获得增量关注。",
      sourceIds: ["300308.SZ:xueqiu_stock", "300308.SZ:eastmoney_forum"],
      links: [demoSources[4], demoSources[2]]
    },
    {
      headline: "产业链景气验证成为焦点",
      category: "产业链",
      topic: "订单与产能",
      impact: "后续订单、出货和利润率数据将决定估值能否站稳。",
      sourceIds: ["300308.SZ:cninfo_profile", "300308.SZ:market_quote"],
      links: [demoSources[1], demoSources[0]]
    }
  ],
  retailSentiment: {
    bullishRatio: 0.54,
    bearishRatio: 0.19,
    neutralityRatio: 0.27,
    summary: "讨论区偏多，但一致性已经不低，需要防止高位接力风险。",
    keywords: ["AI 算力", "CPO", "趋势", "龙头"],
    sourceIds: ["300308.SZ:cninfo_irm", "300308.SZ:eastmoney_forum", "300308.SZ:xueqiu_stock"],
    links: [demoSources[5], demoSources[2], demoSources[4]]
  },
  monitorPoints: ["是否连续放量滞涨", "板块龙头高度是否被压制", "是否有新的业绩低预期信号"],
  disclaimer:
    "当前结果由本地规则引擎和 mock provider 生成，不构成投资建议。现阶段链接指向证据入口页，接入真实数据后会细化到公告、新闻和帖子级链接。"
};

const fallbackComparison: CompareResponse = {
  primarySymbol: "300308.SZ",
  rows: [
    {
      symbol: "300308.SZ",
      companyName: "中际旭创",
      sector: "光模块 / AI 算力",
      riskLevel: "high",
      riskScore: 68,
      confidence: 0.72,
      tradingStyle: "高弹性主线博弈",
      thesis: "更偏主线强化下的高弹性交易。",
      relation: "primary"
    },
    {
      symbol: "000977.SZ",
      companyName: "浪潮信息",
      sector: "服务器 / AI 算力",
      riskLevel: "high",
      riskScore: 66,
      confidence: 0.68,
      tradingStyle: "高弹性主线博弈",
      thesis: "算力主线相关性强，但波动和分歧也偏高。",
      relation: "peer"
    }
  ]
};

const SOURCE_KIND_LABELS: Record<string, string> = {
  market: "行情",
  filing: "公告",
  news: "新闻",
  forum: "论坛",
  community: "社区",
  theme: "题材",
  narrative: "叙事"
};

const EVIDENCE_ROLE_LABELS = {
  main: "主因",
  support: "次因",
  counter: "反证"
} as const;

const EVENT_DIRECTION_LABELS = {
  positive: "偏利多",
  negative: "偏利空",
  mixed: "多空交织",
  neutral: "中性"
} as const;

function getSourceKindLabel(kind: string) {
  return SOURCE_KIND_LABELS[kind] ?? kind;
}

function groupSourcesByKind(sources: SourceLink[]) {
  const order = ["filing", "news", "market", "forum", "community", "theme", "narrative"];
  const groups = new Map<string, SourceLink[]>();

  for (const source of sources) {
    const bucket = groups.get(source.kind) ?? [];
    bucket.push(source);
    groups.set(source.kind, bucket);
  }

  return Array.from(groups.entries())
    .sort(([left], [right]) => {
      const leftIndex = order.indexOf(left);
      const rightIndex = order.indexOf(right);
      return (leftIndex === -1 ? order.length : leftIndex) - (rightIndex === -1 ? order.length : rightIndex);
    })
    .map(([kind, entries]) => ({ kind, label: getSourceKindLabel(kind), entries }));
}

function App() {
  const [symbol, setSymbol] = useState("300308.SZ");
  const [companyName, setCompanyName] = useState("");
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [copying, setCopying] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ResearchResponse>(fallbackReport);
  const [comparison, setComparison] = useState<CompareResponse>(fallbackComparison);
  const [quickPicks, setQuickPicks] = useState<StockLookupResult[]>(fallbackQuickPicks);
  const [suggestions, setSuggestions] = useState<StockLookupResult[]>([]);
  const [recentReports, setRecentReports] = useState<ReportSnapshotSummary[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const deferredSymbol = useDeferredValue(symbol);
  const groupedSources = groupSourcesByKind(report.sources);

  useEffect(() => {
    void fetchQuickPicks();
    void fetchSystemStatus();
    void fetchRecentReports();
  }, []);

  useEffect(() => {
    void fetchComparison(report);
  }, [report]);

  useEffect(() => {
    const query = deferredSymbol.trim();
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    const timer = window.setTimeout(() => {
      void fetchSuggestions(query);
    }, 180);

    return () => {
      window.clearTimeout(timer);
    };
  }, [deferredSymbol]);

  async function fetchQuickPicks() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/stocks/search?q=&limit=6`);
      if (!response.ok) {
        return;
      }
      const data = (await response.json()) as StockLookupResult[];
      if (data.length > 0) {
        setQuickPicks(data);
      }
    } catch {
      // Keep fallback quick picks when the API is unavailable.
    }
  }

  async function fetchSuggestions(query: string) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/stocks/search?q=${encodeURIComponent(query)}&limit=6`
      );
      if (!response.ok) {
        return;
      }
      const data = (await response.json()) as StockLookupResult[];
      setSuggestions(
        data.filter((item) => item.symbol !== report.symbol || item.name !== report.companyName)
      );
    } catch {
      setSuggestions([]);
    }
  }

  async function fetchSystemStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/system/status`);
      if (!response.ok) {
        return;
      }
      const status = (await response.json()) as SystemStatus;
      setSystemStatus(status);
    } catch {
      setSystemStatus(null);
    }
  }

  async function fetchRecentReports() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research/recent?limit=6`);
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as ReportSnapshotSummary[];
      setRecentReports(payload);
    } catch {
      setRecentReports([]);
    }
  }

  async function fetchComparison(currentReport: ResearchResponse) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research/compare`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          symbol: currentReport.symbol,
          peerSymbols: currentReport.comparables.map((item) => item.symbol),
          includeRetailSentiment: false
        })
      });
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as CompareResponse;
      setComparison(payload);
    } catch {
      setComparison(fallbackComparison);
    }
  }

  async function loadLatestReport(symbolToLoad: string) {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research/latest/${encodeURIComponent(symbolToLoad)}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      const nextReport = (await response.json()) as ResearchResponse;
      setReport(nextReport);
      setSymbol(nextReport.symbol);
      setCompanyName(nextReport.companyName);
    } catch (submissionError) {
      const message =
        submissionError instanceof Error ? submissionError.message : "Unknown error";
      setError(`读取历史失败: ${message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await fetchReport({
      symbol,
      companyName: companyName || undefined,
      analysisWindowDays: 365,
      includeRetailSentiment: true
    });
  }

  async function fetchReport(payload: ResearchRequest) {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research/report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const nextReport = (await response.json()) as ResearchResponse;
      setReport(nextReport);
      setSymbol(nextReport.symbol);
      setCompanyName(nextReport.companyName);
      setSuggestions([]);
      void fetchRecentReports();
    } catch (submissionError) {
      const message =
        submissionError instanceof Error ? submissionError.message : "Unknown error";
      setError(`研究请求失败: ${message}`);
    } finally {
      setLoading(false);
    }
  }

  async function refreshReport() {
    setRefreshing(true);
    await fetchReport({
      symbol: report.symbol,
      companyName: report.companyName,
      analysisWindowDays: 365,
      includeRetailSentiment: true,
      forceRefresh: true
    });
    setRefreshing(false);
  }

  async function exportMarkdown() {
    setExporting(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research/report/markdown`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          symbol: report.symbol,
          companyName: report.companyName,
          analysisWindowDays: 365,
          includeRetailSentiment: true
        } satisfies ResearchRequest)
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const markdown = await response.text();
      const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${report.symbol}-research.md`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (submissionError) {
      const message =
        submissionError instanceof Error ? submissionError.message : "Unknown error";
      setError(`导出失败: ${message}`);
    } finally {
      setExporting(false);
    }
  }

  async function copyMarkdown() {
    setCopying(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research/report/markdown`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          symbol: report.symbol,
          companyName: report.companyName,
          analysisWindowDays: 365,
          includeRetailSentiment: true
        } satisfies ResearchRequest)
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const markdown = await response.text();
      if (!navigator.clipboard) {
        throw new Error("Clipboard API is unavailable");
      }
      await navigator.clipboard.writeText(markdown);
    } catch (submissionError) {
      const message =
        submissionError instanceof Error ? submissionError.message : "Unknown error";
      setError(`复制失败: ${message}`);
    } finally {
      setCopying(false);
    }
  }

  return (
    <main className="workspace-shell">
      <section className="toolbar-card">
        <div className="toolbar-copy">
          <p className="eyebrow">Research Console</p>
          <h1>Stock Box</h1>
          <p>
            输入股票后，系统按市场脉搏、主线叙事、关键涨跌日、风险和情绪来组织调研结果，并附上可点击的证据入口。
          </p>
          {systemStatus ? (
            <div className="status-banner">
              <span>环境 {systemStatus.environment}</span>
              <span>请求 provider {systemStatus.requestedProvider}</span>
              <span>当前 provider {systemStatus.activeProvider}</span>
              {systemStatus.degraded ? <span>已降级: {systemStatus.reason}</span> : <span>未降级</span>}
            </div>
          ) : null}
        </div>

        <form className="query-form" onSubmit={handleSubmit}>
          <label>
            股票代码
            <input
              value={symbol}
              onChange={(event) => setSymbol(event.target.value.toUpperCase())}
              placeholder="如 300308.SZ"
            />
          </label>
          <label>
            公司名称
            <input
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
              placeholder="可选"
            />
          </label>
          <button disabled={loading} type="submit">
            {loading ? "分析中..." : "生成研究报告"}
          </button>
          {error ? <p className="error-text">{error}</p> : null}
          {suggestions.length > 0 ? (
            <div className="suggestion-list">
              {suggestions.map((item) => (
                <button
                  className="suggestion-item"
                  key={item.symbol}
                  onClick={() => {
                    setSymbol(item.symbol);
                    setCompanyName(item.name);
                    setSuggestions([]);
                    void fetchReport({
                      symbol: item.symbol,
                      companyName: item.name,
                      analysisWindowDays: 365,
                      includeRetailSentiment: true
                    });
                  }}
                  type="button"
                >
                  <strong>{item.name}</strong>
                  <span>{item.symbol}</span>
                  <small>{item.sector}</small>
                </button>
              ))}
            </div>
          ) : null}
        </form>

        <div className="quick-picks">
          {quickPicks.map((item) => (
            <button
              className="quick-pick"
              key={item.symbol}
              onClick={() =>
                void fetchReport({
                  symbol: item.symbol,
                  companyName: item.name,
                  analysisWindowDays: 365,
                  includeRetailSentiment: true
                })
              }
              type="button"
            >
              <strong>{item.name}</strong>
              <span>{item.symbol}</span>
              <small>{item.sector}</small>
            </button>
          ))}
        </div>
        {recentReports.length > 0 ? (
          <div className="recent-block">
            <p className="panel-label">最近研究</p>
            <div className="recent-list">
              {recentReports.map((item) => (
                <button
                  className="recent-item"
                  key={item.symbol}
                  onClick={() => void loadLatestReport(item.symbol)}
                  type="button"
                >
                  <strong>{item.companyName}</strong>
                  <span>{item.symbol}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      <section className="hero-card">
        <div className="hero-main">
          <p className="eyebrow">Target</p>
          <h2>
            {report.companyName} <span>{report.symbol}</span>
          </h2>
          <p className="muted">{report.market} · {report.sector}</p>
          <div className="chip-row">
            {report.conceptTags.map((tag) => (
              <span className="chip" key={tag}>
                {tag}
              </span>
            ))}
          </div>
        </div>
        <div className="hero-metrics">
          <Metric label="风险等级" value={report.riskLevel} tone={report.riskLevel} />
          <Metric label="风险分" value={String(report.riskScore)} />
          <Metric label="置信度" value={`${Math.round(report.confidence * 100)}%`} />
          <Metric label="数据状态" value={report.usingLiveData ? "实时数据" : "演示数据"} />
        </div>
      </section>

      <section className="status-strip">
        <span className="status-chip">provider {report.provider}</span>
        <span className="status-chip">{report.fromCache ? "来自缓存快照" : "实时生成"}</span>
      </section>

      <section className="action-row">
        <button className="secondary-button" disabled={exporting} onClick={() => void exportMarkdown()} type="button">
          {exporting ? "导出中..." : "导出 Markdown"}
        </button>
        <button className="secondary-button" disabled={copying} onClick={() => void copyMarkdown()} type="button">
          {copying ? "复制中..." : "复制 Markdown"}
        </button>
        <button className="secondary-button" disabled={refreshing || loading} onClick={() => void refreshReport()} type="button">
          {refreshing ? "刷新中..." : "强制刷新"}
        </button>
      </section>

      <section className="source-card">
        <div className="source-card-head">
          <div>
            <p className="panel-label">依据入口</p>
            <h3>报告中的判断需要能回到原始入口页核对</h3>
          </div>
          <p className="muted">
            优先展示行情、公告、股吧、同花顺、雪球和互动易入口，细项来源会在下方按类型归档。
          </p>
        </div>
        <div className="source-grid">
          {report.sourceLinks.map((link) => (
            <SourceAnchor key={`${link.label}-${link.url}`} link={link} />
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="panel-label">来源明细</p>
            <h3>本报告引用过的来源记录</h3>
          </div>
        </div>
        <div className="source-groups">
          {groupedSources.map((group) => (
            <div className="source-group" key={group.kind}>
              <div className="source-group-head">
                <strong>{group.label}</strong>
                <span>{group.entries.length} 条</span>
              </div>
              <div className="detail-source-grid">
                {group.entries.map((source) => (
                  <article className="source-detail-card" key={source.id}>
                    <div className="stack-title">
                      <strong>{source.label}</strong>
                      <span>{getSourceKindLabel(source.kind)}</span>
                    </div>
                    <p>{source.note}</p>
                    <small>
                      {source.domain}
                      {source.publishedAt ? ` · ${source.publishedAt}` : ""}
                    </small>
                    <a className="inline-link" href={source.url} rel="noreferrer" target="_blank">
                      打开来源
                    </a>
                  </article>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="panel-label">数据就绪状态</p>
            <h3>当前报告哪些模块是真数据，哪些还是占位</h3>
          </div>
        </div>
        <div className="readiness-grid">
          {report.dataReadiness.map((item) => (
            <div className={`readiness-card readiness-${item.status}`} key={item.key}>
              <div className="stack-title">
                <strong>{item.label}</strong>
                <span className={`status-pill status-${item.status}`}>{item.status}</span>
              </div>
              <p>{item.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="summary-grid">
        <article className="panel panel-span-3">
          <div className="section-head">
            <div>
              <p className="panel-label">阶段化脉络</p>
              <h3>过去一年的炒作路径</h3>
            </div>
          </div>
          <div className="stage-grid">
            {report.narrativeStages.map((stage) => (
              <div className={`stage-card stage-${stage.status}`} key={`${stage.title}-${stage.dateRange}`}>
                <span className="stage-range">{stage.dateRange}</span>
                <strong>{stage.title}</strong>
                <p>{stage.summary}</p>
                <small>{stage.driver}</small>
                <LinkRow links={stage.links} />
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <p className="panel-label">市场脉搏</p>
          <h3>{report.marketPulse.regime}</h3>
          <p className="muted">{report.marketPulse.commentary}</p>
          <div className="stat-line">
            <span>风险偏好</span>
            <strong>{report.marketPulse.riskAppetite}</strong>
          </div>
          <div className="stat-line">
            <span>主导主题</span>
            <strong>{report.marketPulse.dominantThemes.join(" / ")}</strong>
          </div>
        </article>

        <article className="panel">
          <p className="panel-label">核心判断</p>
          <p className="thesis-text">{report.thesis}</p>
          <div className="stack-list compact">
            <div className="stack-item">
              <strong>交易风格</strong>
              <p>{report.overview.tradingStyle}</p>
            </div>
            <div className="stack-item">
              <strong>当前叙事</strong>
              <p>{report.overview.dominantNarrative}</p>
            </div>
          </div>
        </article>

        <article className="panel">
          <p className="panel-label">多空场景</p>
          <div className="stack-list compact">
            <div className="stack-item">
              <strong>多头场景</strong>
              <p>{report.overview.bullCase}</p>
            </div>
            <div className="stack-item">
              <strong>空头场景</strong>
              <p>{report.overview.bearCase}</p>
            </div>
          </div>
          <div className="key-question">{report.overview.keyQuestion}</div>
        </article>
      </section>

      <section className="panel timeline-panel">
        <div className="section-head">
          <div>
            <p className="panel-label">一年内炒作脉络</p>
            <h3>关键涨跌日与证据栈</h3>
          </div>
        </div>
        <div className="timeline-list">
          {report.timeline.map((item) => (
            <div className="timeline-item" key={`${item.date}-${item.summary}`}>
              <div className="timeline-header">
                <div>
                  <strong>{item.date}</strong>
                  <span className={`move move-${item.move}`}>
                    {item.move === "up" ? "+" : item.move === "down" ? "-" : ""}
                    {Math.abs(item.changePct).toFixed(2)}%
                  </span>
                </div>
                <span className="chip subtle">{item.ladderPosition}</span>
              </div>
              <p>{item.summary}</p>
              <p className="muted">{item.interpretation}</p>
              <small>催化: {item.catalyst}</small>
              <div className="evidence-list">
                {item.evidence.map((evidence, index) => (
                  <div className="evidence-item" key={`${item.date}-${evidence.source}-${index}`}>
                    <div className="evidence-head">
                      <span>{evidence.source}</span>
                      <div className="evidence-meta">
                        <span className={`evidence-role role-${evidence.role}`}>
                          {EVIDENCE_ROLE_LABELS[evidence.role]}
                        </span>
                        <strong>{evidence.signal}</strong>
                        <small>{Math.round(evidence.score * 100)}分</small>
                      </div>
                    </div>
                    <p>{evidence.summary}</p>
                    <LinkRow links={evidence.links} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="detail-grid">
        <article className="panel panel-span-2">
          <p className="panel-label">同类对比</p>
          <div className="comparison-table">
            <div className="comparison-row comparison-head">
              <span>标的</span>
              <span>关系</span>
              <span>赛道</span>
              <span>风险</span>
              <span>置信度</span>
              <span>交易风格</span>
            </div>
            {comparison.rows.map((row) => (
              <div className="comparison-row" key={`${row.symbol}-${row.relation}`}>
                <strong>{row.companyName} {row.symbol}</strong>
                <span>{row.relation === "primary" ? "当前标的" : "可比标的"}</span>
                <span>{row.sector}</span>
                <span className={`risk risk-${row.riskLevel}`}>{row.riskLevel} / {row.riskScore}</span>
                <span>{Math.round(row.confidence * 100)}%</span>
                <span>{row.tradingStyle}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <p className="panel-label">暴雷与交易风险</p>
          <div className="stack-list">
            {report.risks.map((item) => (
              <div className="stack-item" key={item.title}>
                <div className="stack-title">
                  <strong>{item.title}</strong>
                  <span className={`risk risk-${item.level}`}>{item.level}</span>
                </div>
                <p>{item.detail}</p>
                <small>风险分 {item.score} {item.watch ? "· 重点跟踪" : ""}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-span-2">
          <p className="panel-label">公告与披露</p>
          <div className="filing-grid">
            {report.filingsDigest.map((item) => (
              <div className="filing-card" key={`${item.publishedAt}-${item.title}`}>
                <div className="stack-title">
                  <strong>{item.title}</strong>
                  <span>{item.publishedAt}</span>
                </div>
                <div className="tag-row">
                  <span className="chip subtle">{item.category}</span>
                  <span className="signal-pill">{item.signal}</span>
                </div>
                <p>{item.summary}</p>
                <LinkRow links={item.links} />
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-span-2">
          <p className="panel-label">事件簇</p>
          <div className="filing-grid">
            {report.eventClusters.map((item) => (
              <div className="filing-card" key={item.id}>
                <div className="stack-title">
                  <strong>{item.topic}</strong>
                  <span>{item.publishedAt}</span>
                </div>
                <div className="tag-row">
                  <span className="chip subtle">{EVENT_DIRECTION_LABELS[item.direction]}</span>
                  <span className="signal-pill">{item.sourceKinds.join(" / ")}</span>
                </div>
                <p>{item.summary}</p>
                <LinkRow links={item.links} />
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <p className="panel-label">可比标的</p>
          <div className="stack-list">
            {report.comparables.map((item) => (
              <div className="stack-item" key={item.symbol}>
                <div className="stack-title">
                  <strong>{item.name}</strong>
                  <span>{item.symbol}</span>
                </div>
                <p>{item.reason}</p>
                <small>{item.edge}</small>
                <div className="mini-stats">
                  <span>质量 {item.qualityScore}</span>
                  <span>波动 {item.volatilityScore}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <p className="panel-label">新闻影响</p>
          <div className="stack-list">
            {report.newsDigest.map((item) => (
              <div className="stack-item" key={item.headline}>
                <div className="stack-title">
                  <strong>{item.headline}</strong>
                  <span>{item.category}</span>
                </div>
                <div className="tag-row">
                  <span className="chip subtle">{item.topic}</span>
                </div>
                <p>{item.impact}</p>
                <LinkRow links={item.links} />
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <p className="panel-label">社区热议</p>
          <div className="stack-list">
            {report.forumDigest.map((item) => (
              <div className="stack-item" key={`${item.platform}-${item.title}`}>
                <div className="stack-title">
                  <strong>{item.title}</strong>
                  <span>{item.platform}</span>
                </div>
                <div className="tag-row">
                  <span className="chip subtle">{item.topic}</span>
                </div>
                <p>{item.summary}</p>
                <small>{item.publishedAt} · {item.heat}</small>
                <LinkRow links={item.links} />
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <p className="panel-label">散户情绪</p>
          {report.retailSentiment ? (
            <>
              <div className="sentiment-bars">
                <div>
                  <span>看多</span>
                  <strong>{Math.round(report.retailSentiment.bullishRatio * 100)}%</strong>
                </div>
                <div>
                  <span>看空</span>
                  <strong>{Math.round(report.retailSentiment.bearishRatio * 100)}%</strong>
                </div>
                <div>
                  <span>中性</span>
                  <strong>{Math.round(report.retailSentiment.neutralityRatio * 100)}%</strong>
                </div>
              </div>
              <p>{report.retailSentiment.summary}</p>
              <small>{report.retailSentiment.keywords.join(" / ")}</small>
              {report.retailSentiment.links.length > 0 ? <LinkRow links={report.retailSentiment.links} /> : null}
            </>
          ) : (
            <p>当前请求未开启散户情绪分析。</p>
          )}
        </article>
      </section>

      <section className="panel">
        <p className="panel-label">后续监控点</p>
        <div className="monitor-list">
          {report.monitorPoints.map((item) => (
            <div className="monitor-item" key={item}>
              {item}
            </div>
          ))}
        </div>
        <p className="footnote">
          生成时间 {new Date(report.generatedAt).toLocaleString("zh-CN")} ·
          {report.usingLiveData ? " 实时数据" : " 演示数据"}
        </p>
      </section>

      <footer className="footer-note">{report.disclaimer}</footer>
    </main>
  );
}

function Metric(props: { label: string; value: string; tone?: string }) {
  return (
    <div className="metric-card">
      <span>{props.label}</span>
      <strong className={props.tone ? `risk risk-${props.tone}` : undefined}>{props.value}</strong>
    </div>
  );
}

function SourceAnchor(props: { link: SourceLink }) {
  const { link } = props;

  return (
    <a className="source-link-card" href={link.url} rel="noreferrer" target="_blank">
      <strong>{link.label}</strong>
      <span>{link.domain}</span>
      <small>{link.note}</small>
    </a>
  );
}

function LinkRow(props: { links: SourceLink[] }) {
  return (
    <div className="link-row">
      {props.links.map((link) => (
        <a className="inline-link" href={link.url} key={`${link.label}-${link.url}`} rel="noreferrer" target="_blank">
          {link.label}
        </a>
      ))}
    </div>
  );
}

export default App;
