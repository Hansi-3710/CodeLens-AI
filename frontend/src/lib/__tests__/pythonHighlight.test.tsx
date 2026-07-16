import { render } from "@testing-library/react";
import { highlightPython } from "../pythonHighlight";

describe("highlightPython", () => {
  it("preserves the full text content (no characters lost in tokenizing)", () => {
    const code = "def add(a, b):\n    return a + b  # sum\n";
    const { container } = render(<>{highlightPython(code)}</>);
    expect(container.textContent).toBe(code);
  });

  it("wraps keywords in a styled span", () => {
    const { container } = render(<>{highlightPython("def f(): return 1")}</>);
    const keywordSpans = Array.from(container.querySelectorAll("span")).filter(
      (el) => el.textContent === "def" || el.textContent === "return"
    );
    expect(keywordSpans.length).toBe(2);
  });

  it("handles code with no strings/comments without throwing", () => {
    expect(() => render(<>{highlightPython("x = 1 + 2")}</>)).not.toThrow();
  });
});
