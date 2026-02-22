import { describe, it, expect, beforeEach } from "vitest";
import { useRiskAssessmentStore } from "./risk-assessment-store";

describe("useRiskAssessmentStore", () => {
  beforeEach(() => {
    useRiskAssessmentStore.setState({
      currentStep: 0,
      answers: {},
      isSubmitting: false,
      result: null,
    });
  });

  it("has correct initial state", () => {
    const state = useRiskAssessmentStore.getState();
    expect(state.currentStep).toBe(0);
    expect(state.answers).toEqual({});
    expect(state.isSubmitting).toBe(false);
    expect(state.result).toBeNull();
  });

  it("sets an answer", () => {
    useRiskAssessmentStore.getState().setAnswer(1, "20s");
    expect(useRiskAssessmentStore.getState().answers[1]).toBe("20s");
  });

  it("overwrites an answer", () => {
    const { setAnswer } = useRiskAssessmentStore.getState();
    setAnswer(1, "20s");
    setAnswer(1, "30s");
    expect(useRiskAssessmentStore.getState().answers[1]).toBe("30s");
  });

  it("advances step with nextStep", () => {
    useRiskAssessmentStore.getState().nextStep();
    expect(useRiskAssessmentStore.getState().currentStep).toBe(1);
  });

  it("does not advance past last step", () => {
    for (let i = 0; i < 20; i++) {
      useRiskAssessmentStore.getState().nextStep();
    }
    expect(useRiskAssessmentStore.getState().currentStep).toBe(7); // 0-indexed, 8 questions
  });

  it("goes back with prevStep", () => {
    useRiskAssessmentStore.getState().nextStep();
    useRiskAssessmentStore.getState().nextStep();
    useRiskAssessmentStore.getState().prevStep();
    expect(useRiskAssessmentStore.getState().currentStep).toBe(1);
  });

  it("does not go below 0 with prevStep", () => {
    useRiskAssessmentStore.getState().prevStep();
    expect(useRiskAssessmentStore.getState().currentStep).toBe(0);
  });

  it("resets state", () => {
    const store = useRiskAssessmentStore.getState();
    store.setAnswer(1, "20s");
    store.nextStep();
    store.setIsSubmitting(true);
    store.reset();

    const state = useRiskAssessmentStore.getState();
    expect(state.currentStep).toBe(0);
    expect(state.answers).toEqual({});
    expect(state.isSubmitting).toBe(false);
    expect(state.result).toBeNull();
  });

  it("calculates progress", () => {
    const store = useRiskAssessmentStore.getState();
    expect(store.getProgress()).toBe(0);
    store.setAnswer(1, "20s");
    store.setAnswer(2, "retirement");
    expect(useRiskAssessmentStore.getState().getProgress()).toBe(2 / 8);
  });

  it("sets result", () => {
    const result = {
      risk_score: 7,
      risk_tolerance: "moderate",
      investment_horizon: "medium",
      investment_experience: "intermediate",
      recommended_strategy: "hrp",
      description: "test",
    };
    useRiskAssessmentStore.getState().setResult(result);
    expect(useRiskAssessmentStore.getState().result).toEqual(result);
  });
});
