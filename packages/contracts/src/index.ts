export type PriceMove = "up" | "down" | "flat";
export type RiskLevel = "low" | "medium" | "high";
export type EvidenceRole = "main" | "support" | "counter";

export interface ResearchRequest {
  symbol: string;
  companyName?: string;
  analysisWindowDays?: number;
  includeRetailSentiment?: boolean;
  forceRefresh?: boolean;
  maxSnapshotAgeMinutes?: number;
}

export interface StockLookupResult {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  concepts: string[];
}

export interface SourceLink {
  id: string;
  label: string;
  url: string;
  domain: string;
  kind: string;
  publishedAt?: string | null;
  note: string;
}

export interface DataReadinessItem {
  key: string;
  label: string;
  status: "ready" | "mock" | "missing";
  detail: string;
}

export interface SystemStatus {
  environment: string;
  requestedProvider: string;
  activeProvider: string;
  degraded: boolean;
  reason?: string | null;
  capabilities: DataReadinessItem[];
}

export interface ReportSnapshotSummary {
  symbol: string;
  companyName: string;
  market: string;
  sector: string;
  riskLevel: RiskLevel;
  generatedAt: string;
  thesis: string;
}

export interface CompareRequest {
  symbol: string;
  peerSymbols?: string[];
  includeRetailSentiment?: boolean;
  forceRefresh?: boolean;
}

export interface ComparisonRow {
  symbol: string;
  companyName: string;
  sector: string;
  riskLevel: RiskLevel;
  riskScore: number;
  confidence: number;
  tradingStyle: string;
  thesis: string;
  relation: "primary" | "peer";
}

export interface CompareResponse {
  primarySymbol: string;
  rows: ComparisonRow[];
}

export interface EvidenceLine {
  source: string;
  signal: string;
  summary: string;
  role: EvidenceRole;
  score: number;
  sourceIds: string[];
  links: SourceLink[];
}

export interface NarrativeStage {
  title: string;
  dateRange: string;
  status: "build" | "accelerate" | "diverge" | "cooldown";
  summary: string;
  driver: string;
  sourceIds: string[];
  links: SourceLink[];
}

export interface TimelineEvent {
  date: string;
  move: PriceMove;
  changePct: number;
  summary: string;
  catalyst: string;
  sector: string;
  ladderPosition: string;
  interpretation: string;
  confidence: number;
  evidence: EvidenceLine[];
}

export interface RiskItem {
  title: string;
  level: RiskLevel;
  score: number;
  detail: string;
  watch: boolean;
}

export interface ComparableStock {
  symbol: string;
  name: string;
  reason: string;
  edge: string;
  qualityScore: number;
  volatilityScore: number;
}

export interface SentimentSnapshot {
  bullishRatio: number;
  bearishRatio: number;
  neutralityRatio: number;
  summary: string;
  keywords: string[];
  sourceIds: string[];
  links: SourceLink[];
}

export interface NewsDigestItem {
  headline: string;
  category: string;
  topic: string;
  impact: string;
  sourceIds: string[];
  links: SourceLink[];
}

export interface FilingDigestItem {
  title: string;
  category: string;
  publishedAt: string;
  signal: string;
  summary: string;
  sourceIds: string[];
  links: SourceLink[];
}

export interface ForumDigestItem {
  title: string;
  platform: string;
  topic: string;
  publishedAt: string;
  heat: string;
  summary: string;
  sourceIds: string[];
  links: SourceLink[];
}

export interface EventCluster {
  id: string;
  topic: string;
  publishedAt: string;
  direction: "positive" | "negative" | "mixed" | "neutral";
  summary: string;
  sourceKinds: string[];
  sourceIds: string[];
  links: SourceLink[];
}

export interface MarketPulse {
  regime: string;
  riskAppetite: string;
  dominantThemes: string[];
  commentary: string;
}

export interface ResearchOverview {
  tradingStyle: string;
  dominantNarrative: string;
  bullCase: string;
  bearCase: string;
  keyQuestion: string;
}

export interface ResearchResponse {
  symbol: string;
  companyName: string;
  market: string;
  sector: string;
  conceptTags: string[];
  sourceLinks: SourceLink[];
  sources: SourceLink[];
  dataReadiness: DataReadinessItem[];
  narrativeStages: NarrativeStage[];
  overview: ResearchOverview;
  marketPulse: MarketPulse;
  thesis: string;
  riskLevel: RiskLevel;
  riskScore: number;
  confidence: number;
  provider: string;
  fromCache: boolean;
  usingLiveData: boolean;
  generatedAt: string;
  timeline: TimelineEvent[];
  risks: RiskItem[];
  comparables: ComparableStock[];
  filingsDigest: FilingDigestItem[];
  forumDigest: ForumDigestItem[];
  eventClusters: EventCluster[];
  newsDigest: NewsDigestItem[];
  retailSentiment?: SentimentSnapshot | null;
  monitorPoints: string[];
  disclaimer: string;
}
