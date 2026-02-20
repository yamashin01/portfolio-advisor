import { create } from "zustand";
import type { RiskAssessmentResult } from "@/types/risk-assessment";

interface RiskAssessmentState {
  currentStep: number;
  answers: Record<number, string>;
  isSubmitting: boolean;
  result: RiskAssessmentResult | null;

  setAnswer: (questionId: number, value: string) => void;
  nextStep: () => void;
  prevStep: () => void;
  setIsSubmitting: (v: boolean) => void;
  setResult: (result: RiskAssessmentResult) => void;
  reset: () => void;
  getProgress: () => number;
}

const TOTAL_QUESTIONS = 8;

export const useRiskAssessmentStore = create<RiskAssessmentState>((set, get) => ({
  currentStep: 0,
  answers: {},
  isSubmitting: false,
  result: null,

  setAnswer: (questionId, value) =>
    set((state) => ({
      answers: { ...state.answers, [questionId]: value },
    })),

  nextStep: () =>
    set((state) => ({
      currentStep: Math.min(state.currentStep + 1, TOTAL_QUESTIONS - 1),
    })),

  prevStep: () =>
    set((state) => ({
      currentStep: Math.max(state.currentStep - 1, 0),
    })),

  setIsSubmitting: (v) => set({ isSubmitting: v }),

  setResult: (result) => set({ result }),

  reset: () =>
    set({
      currentStep: 0,
      answers: {},
      isSubmitting: false,
      result: null,
    }),

  getProgress: () => {
    const { answers } = get();
    return Object.keys(answers).length / TOTAL_QUESTIONS;
  },
}));
