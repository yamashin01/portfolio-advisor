import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "./api-client";

const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

function mockJsonResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  } as Response);
}

describe("apiClient", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  describe("getQuestions", () => {
    it("calls GET /risk-assessment/questions", async () => {
      const questions = { questions: [] };
      mockFetch.mockReturnValue(mockJsonResponse(questions));

      const result = await apiClient.getQuestions();
      expect(result).toEqual(questions);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/risk-assessment/questions"),
        expect.objectContaining({ headers: expect.any(Object) })
      );
    });
  });

  describe("calculateRisk", () => {
    it("calls POST /risk-assessment/calculate", async () => {
      const responseData = { risk_score: 5, risk_tolerance: "moderate" };
      mockFetch.mockReturnValue(mockJsonResponse(responseData));

      const result = await apiClient.calculateRisk({ answers: [] });
      expect(result).toEqual(responseData);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toContain("/risk-assessment/calculate");
      expect(opts.method).toBe("POST");
    });
  });

  describe("generatePortfolio", () => {
    it("calls POST /portfolios/generate", async () => {
      const responseData = { name: "Test" };
      mockFetch.mockReturnValue(mockJsonResponse(responseData));

      const result = await apiClient.generatePortfolio({
        risk_score: 5,
        risk_tolerance: "moderate",
        investment_horizon: "medium",
      } as Parameters<typeof apiClient.generatePortfolio>[0]);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toContain("/portfolios/generate");
      expect(opts.method).toBe("POST");
    });
  });

  describe("getMarketSummary", () => {
    it("calls GET /market/summary", async () => {
      const data = { indices: [], bonds: [], forex: [] };
      mockFetch.mockReturnValue(mockJsonResponse(data));

      await apiClient.getMarketSummary();
      expect(mockFetch.mock.calls[0][0]).toContain("/market/summary");
    });
  });

  describe("getAssets", () => {
    it("calls GET /assets/ with query params", async () => {
      mockFetch.mockReturnValue(mockJsonResponse({ items: [], total: 0 }));

      await apiClient.getAssets({ market: "us", per_page: 10 });
      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/assets/");
      expect(url).toContain("market=us");
      expect(url).toContain("per_page=10");
    });
  });

  describe("getUsage", () => {
    it("calls GET /usage", async () => {
      const data = { daily: {}, monthly: {} };
      mockFetch.mockReturnValue(mockJsonResponse(data));

      await apiClient.getUsage();
      expect(mockFetch.mock.calls[0][0]).toContain("/usage");
    });
  });

  describe("error handling", () => {
    it("throws ApiError on non-ok response", async () => {
      mockFetch.mockReturnValue(
        mockJsonResponse({ detail: "Not found" }, 404)
      );

      await expect(apiClient.getQuestions()).rejects.toThrow();
    });
  });
});
