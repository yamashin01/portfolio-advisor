import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { MarketSummaryResponse } from "@/types/api";
import type { AssetResponse, PaginatedResponse } from "@/types/asset";

const STALE_TIME = 60 * 60 * 1000; // 1h

export function useMarketSummary() {
  return useQuery<MarketSummaryResponse>({
    queryKey: ["market", "summary"],
    queryFn: () => apiClient.getMarketSummary(),
    staleTime: STALE_TIME,
  });
}

export function useAssets(params?: {
  market?: string;
  asset_type?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery<PaginatedResponse<AssetResponse>>({
    queryKey: ["assets", params],
    queryFn: () => apiClient.getAssets(params),
    staleTime: STALE_TIME,
  });
}
