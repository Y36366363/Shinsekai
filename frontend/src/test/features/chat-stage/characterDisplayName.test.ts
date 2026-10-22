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
    expect(characterDisplayName("四宫辉夜", "How was your day?")).toBe("Kaguya Shinomiya");
    expect(characterDisplayName("四宫辉夜", "You are welcome.")).toBe("Kaguya Shinomiya");
    expect(characterDisplayName("四宫辉夜", "", "en")).toBe("Kaguya Shinomiya");
    expect(characterDisplayName("四宫辉夜", "你好", "en-US")).toBe("Kaguya Shinomiya");
    expect(characterDisplayName("四宫辉夜", "你好", "ja")).toBe("四宫辉夜");
  });
});
