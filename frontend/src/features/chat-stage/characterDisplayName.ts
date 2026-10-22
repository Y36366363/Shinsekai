/** Presentation only: never change the name used for sprites, memory, or TTS. */
export function characterDisplayName(
  name: string | undefined,
  speech: string,
  voiceLanguage?: string,
): string | undefined {
  const englishMode = voiceLanguage?.toLowerCase().split(/[-_]/)[0] === "en";
  if (name?.trim() === "四宫辉夜" && englishMode) {
    return "Kaguya Shinomiya";
  }
  if (name === "四宫辉夜" && /[a-zA-Z]/.test(speech) && !/[\u3040-\u30ff\u3400-\u9fff]/.test(speech)) {
    return "Kaguya Shinomiya";
  }
  return name;
}
