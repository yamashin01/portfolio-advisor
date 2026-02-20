export interface LatestPrice {
  close: number;
  change_pct: number | null;
  date: string;
}

export interface AssetResponse {
  id: number;
  symbol: string;
  name_ja: string | null;
  asset_type: string;
  market: string;
  is_active: boolean;
  latest_price: LatestPrice | null;
}

export interface AssetPricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close: number | null;
  volume: number | null;
}

export interface AssetPricesResponse {
  symbol: string;
  prices: AssetPricePoint[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}
