import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScoreGauge } from "./score-gauge";

describe("ScoreGauge", () => {
  it("renders score value", () => {
    render(<ScoreGauge score={7} tolerance="moderate" />);
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("/ 10")).toBeInTheDocument();
  });

  it("renders conservative label", () => {
    render(<ScoreGauge score={2} tolerance="conservative" />);
    expect(screen.getByText("安定型")).toBeInTheDocument();
  });

  it("renders moderate label", () => {
    render(<ScoreGauge score={5} tolerance="moderate" />);
    expect(screen.getByText("中立型")).toBeInTheDocument();
  });

  it("renders aggressive label", () => {
    render(<ScoreGauge score={9} tolerance="aggressive" />);
    expect(screen.getByText("積極型")).toBeInTheDocument();
  });

  it("clamps score to 1-10 range", () => {
    render(<ScoreGauge score={15} tolerance="aggressive" />);
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("renders SVG with aria-label", () => {
    render(<ScoreGauge score={5} tolerance="moderate" />);
    const svg = screen.getByRole("img");
    expect(svg).toHaveAttribute("aria-label", "リスクスコア: 5 / 10");
  });
});
