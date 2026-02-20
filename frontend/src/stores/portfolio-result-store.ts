import { create } from "zustand";
import type { BacktestResponse, PortfolioResponse } from "@/types/portfolio";

interface PortfolioResultState {
  portfolio: PortfolioResponse | null;
  backtest: BacktestResponse | null;
  explanation: string | null;

  setPortfolio: (portfolio: PortfolioResponse) => void;
  setBacktest: (backtest: BacktestResponse) => void;
  setExplanation: (explanation: string) => void;
  clear: () => void;
}

export const usePortfolioResultStore = create<PortfolioResultState>((set) => ({
  portfolio: null,
  backtest: null,
  explanation: null,

  setPortfolio: (portfolio) => set({ portfolio }),
  setBacktest: (backtest) => set({ backtest }),
  setExplanation: (explanation) => set({ explanation }),
  clear: () => set({ portfolio: null, backtest: null, explanation: null }),
}));
