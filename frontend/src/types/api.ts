export interface IndexData {
  name: string;
  symbol: string;
  value: number | null;
  change_pct: number | null;
  as_of: string | null;
}

export interface BondData {
  name: string;
  indicator_type: string;
  value: number | null;
  as_of: string | null;
}

export interface ForexData {
  pair: string;
  rate: number | null;
  change_pct: number | null;
  as_of: string | null;
}

export interface MarketSummaryResponse {
  indices: IndexData[];
  bonds: BondData[];
  forex: ForexData[];
  updated_at: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface PortfolioContextAllocation {
  symbol: string;
  name_ja?: string;
  weight: number;
}

export interface PortfolioContext {
  strategy?: string;
  risk_tolerance?: string;
  allocations?: PortfolioContextAllocation[];
  metrics?: Record<string, number>;
}

export interface ChatRequest {
  messages: ChatMessage[];
  portfolio_context?: PortfolioContext;
}

export interface DailyUsage {
  date: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  budget_tokens: number;
  remaining_tokens: number;
}

export interface MonthlyUsage {
  month: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  budget_tokens: number;
  remaining_tokens: number;
}

export interface UsageSummaryResponse {
  daily: DailyUsage;
  monthly: MonthlyUsage;
}

export class ApiError extends Error {
  status: number;
  detail: string;
  errors?: { field: string; message: string }[];

  constructor(
    status: number,
    detail: string,
    errors?: { field: string; message: string }[]
  ) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.errors = errors;
  }
}
