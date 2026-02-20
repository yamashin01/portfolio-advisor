import { ApiError, type ChatRequest, type MarketSummaryResponse, type UsageSummaryResponse } from "@/types/api";
import type { AssetPricesResponse, AssetResponse, PaginatedResponse } from "@/types/asset";
import type {
  BacktestRequest,
  BacktestResponse,
  ExplainRequest,
  ExplainResponse,
  PortfolioGenerateRequest,
  PortfolioResponse,
} from "@/types/portfolio";
import type {
  QuestionsResponse,
  RiskAssessmentCalculateRequest,
  RiskAssessmentResult,
} from "@/types/risk-assessment";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new ApiError(response.status, error.detail, error.errors);
    }

    return response.json();
  }

  // --- Risk Assessment ---

  getQuestions(): Promise<QuestionsResponse> {
    return this.request("/risk-assessment/questions");
  }

  calculateRisk(data: RiskAssessmentCalculateRequest): Promise<RiskAssessmentResult> {
    return this.request("/risk-assessment/calculate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // --- Portfolio ---

  generatePortfolio(data: PortfolioGenerateRequest): Promise<PortfolioResponse> {
    return this.request("/portfolios/generate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  runBacktest(data: BacktestRequest): Promise<BacktestResponse> {
    return this.request("/portfolios/backtest", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  explainPortfolio(data: ExplainRequest): Promise<ExplainResponse> {
    return this.request("/portfolios/explain", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // --- Chat (SSE) ---

  async streamChat(data: ChatRequest): Promise<Response> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new ApiError(response.status, error.detail);
    }

    return response;
  }

  // --- Assets ---

  getAssets(params?: {
    market?: string;
    asset_type?: string;
    page?: number;
    per_page?: number;
  }): Promise<PaginatedResponse<AssetResponse>> {
    const searchParams = new URLSearchParams();
    if (params?.market) searchParams.set("market", params.market);
    if (params?.asset_type) searchParams.set("asset_type", params.asset_type);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.per_page) searchParams.set("per_page", String(params.per_page));
    const qs = searchParams.toString();
    return this.request(`/assets/${qs ? `?${qs}` : ""}`);
  }

  getAssetPrices(
    symbol: string,
    params?: { period?: string }
  ): Promise<AssetPricesResponse> {
    const searchParams = new URLSearchParams();
    if (params?.period) searchParams.set("period", params.period);
    const qs = searchParams.toString();
    return this.request(`/assets/${encodeURIComponent(symbol)}/prices${qs ? `?${qs}` : ""}`);
  }

  // --- Market ---

  getMarketSummary(): Promise<MarketSummaryResponse> {
    return this.request("/market/summary");
  }

  // --- Usage ---

  getUsage(): Promise<UsageSummaryResponse> {
    return this.request("/usage");
  }
}

export const apiClient = new ApiClient(
  (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1"
);
