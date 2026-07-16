import { render, screen } from "@testing-library/react";
import ModelChannelTag from "../ModelChannelTag";

describe("ModelChannelTag", () => {
  it("renders the model name", () => {
    render(<ModelChannelTag modelName="gpt-4" />);
    expect(screen.getByText("gpt-4")).toBeInTheDocument();
  });
});
