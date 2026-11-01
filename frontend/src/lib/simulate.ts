export type LeakOptions = {
  /** bagian teks dari atas yang "dicuri" (0-1) */
  fraction: number;
  upper: boolean;
  /** peluang tiap huruf terhapus/salah ketik, mensimulasikan pengetikan ulang */
  typoRate: number;
};

/** Teks bocor simulasi dari naskah bertanda: potongan dari atas, huruf kapital, typo ringan. */
export function simulateLeak(text: string, { fraction, upper, typoRate }: LeakOptions): string {
  const lines = text.split("\n");
  let out = lines.slice(0, Math.max(1, Math.round(lines.length * fraction))).join("\n");
  if (upper) out = out.toUpperCase();
  if (typoRate > 0) {
    out = [...out].filter((ch) => !(/\p{L}/u.test(ch) && Math.random() < typoRate)).join("");
  }
  return out;
}
