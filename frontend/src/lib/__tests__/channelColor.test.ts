import { channelColorFor } from "../channelColor";

describe("channelColorFor", () => {
  it("is deterministic for the same model name", () => {
    expect(channelColorFor("gpt-4")).toBe(channelColorFor("gpt-4"));
  });

  it("returns a valid hex color", () => {
    expect(channelColorFor("llama-3-70b")).toMatch(/^#[0-9A-Fa-f]{6}$/);
  });

  it("distributes different names across channels (not all identical)", () => {
    const names = ["gpt-4", "llama-3-70b", "gemma-7b", "gpt-4o-mini", "claude-3"];
    const colors = new Set(names.map(channelColorFor));
    expect(colors.size).toBeGreaterThan(1);
  });
});
