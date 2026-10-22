import { describe, expect, it } from "vitest";
import { characterDisplayName } from "../../../features/chat-stage/characterDisplayName";

describe("characterDisplayName", () => {
  it("uses the English name for English lines only", () => {
    expect(characterDisplayName("四宫辉夜", "Welcome back!")).toBe("Kaguya Shinomiya");
    expect(characterDisplayName("四宫辉夜", "欢迎回来！")).toBe("四宫辉夜");
    expect(characterDisplayName("四宫辉夜", "Hello，你好")).toBe("四宫辉夜");
    expect(characterDisplayName("四宫辉夜", "")).toBe("四宫辉夜");
    expect(characterDisplayName("Other", "Hello")).toBe("Other");
    expect(characterDisplayName(undefined, "Hello")).toBeUndefined();
  });
});
