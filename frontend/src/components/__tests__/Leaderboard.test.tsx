import { render, screen } from "@testing-library/react";
import Leaderboard from "../Leaderboard";

describe("Leaderboard", () => {
  it("shows an empty state with no rows", () => {
    render(<Leaderboard rows={[]} />);
    expect(screen.getByText(/no solutions yet/i)).toBeInTheDocument();
  });

  it("renders one row per model, sorted by correctness", () => {
    render(
      <Leaderboard
        rows={[
          { model: "gpt-4", correctness: 0.96, correctness_ci_95: [0.9, 1.0], avg_runtime_s: 0.03, complexity: "O(V+E)", n_solutions: 3 },
          { model: "gemma-7b", correctness: 0.7, correctness_ci_95: [0.5, 0.9], avg_runtime_s: 0.04, complexity: "O(n^2)", n_solutions: 3 },
        ]}
      />
    );
    expect(screen.getByText("gpt-4")).toBeInTheDocument();
    expect(screen.getByText("gemma-7b")).toBeInTheDocument();
    expect(screen.getByText("96%")).toBeInTheDocument();
  });
});
