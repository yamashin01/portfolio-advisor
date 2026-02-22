import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QuestionStep } from "./question-step";
import type { Question } from "@/types/risk-assessment";

const mockQuestion: Question = {
  id: 1,
  question: "あなたの年齢を教えてください",
  type: "single_choice",
  options: [
    { value: "20s", label: "20代", score_weight: 3 },
    { value: "30s", label: "30代", score_weight: 3 },
    { value: "40s", label: "40代", score_weight: 2 },
  ],
};

describe("QuestionStep", () => {
  it("renders question text", () => {
    render(<QuestionStep question={mockQuestion} onAnswer={vi.fn()} />);
    expect(screen.getByText("あなたの年齢を教えてください")).toBeInTheDocument();
  });

  it("renders all options", () => {
    render(<QuestionStep question={mockQuestion} onAnswer={vi.fn()} />);
    expect(screen.getByText("20代")).toBeInTheDocument();
    expect(screen.getByText("30代")).toBeInTheDocument();
    expect(screen.getByText("40代")).toBeInTheDocument();
  });

  it("calls onAnswer when option is clicked", async () => {
    const user = userEvent.setup();
    const onAnswer = vi.fn();
    render(<QuestionStep question={mockQuestion} onAnswer={onAnswer} />);

    await user.click(screen.getByText("30代"));
    expect(onAnswer).toHaveBeenCalledWith("30s");
  });

  it("marks selected option with aria-checked", () => {
    render(
      <QuestionStep
        question={mockQuestion}
        onAnswer={vi.fn()}
        selectedValue="20s"
      />
    );
    const radios = screen.getAllByRole("radio");
    const selected = radios.find(
      (r) => r.getAttribute("aria-checked") === "true"
    );
    expect(selected).toBeTruthy();
  });

  it("renders radiogroup with aria-label", () => {
    render(<QuestionStep question={mockQuestion} onAnswer={vi.fn()} />);
    expect(screen.getByRole("radiogroup")).toHaveAttribute(
      "aria-label",
      "あなたの年齢を教えてください"
    );
  });
});
