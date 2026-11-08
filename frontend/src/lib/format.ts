import type { LedgerEntry } from "./api";

export const shortHash = (hash: string, n = 12) => `${hash.slice(0, n)}…`;

export const hexId = (id: number) => `0x${id.toString(16).toUpperCase().padStart(8, "0")}`;

export function formatTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("id-ID", { timeZone: "Asia/Jakarta", hour12: false }) + " WIB";
}

export type LedgerBody = {
  event: string;
  actor: string;
  at: string;
  data: Record<string, unknown>;
};

/** Isi entri ledger (JSON kanonik); null bila tidak terbaca. */
export function parseBody(entry: LedgerEntry): LedgerBody | null {
  try {
    return JSON.parse(entry.body) as LedgerBody;
  } catch {
    return null;
  }
}

export function summarize(body: LedgerBody | null): string {
  if (!body) return "(isi tidak terbaca)";
  const d = body.data;
  if (body.event === "COPY_ISSUED") {
    return `salinan ${hexId(Number(d.copy_id))} untuk NRP ${String(d.recipient_nrp)} (${String(d.document_nomor)})`;
  }
  if (body.event === "LEAK_INTAKE_TEXT") {
    const id = d.copy_id == null ? "tanpa ID" : hexId(Number(d.copy_id));
    return `${String(d.status)} · ${id} · bit ${String(d.observed_bits)}/${String(d.total_bits)}`;
  }
  if (body.event === "LOGIN_FAILED") {
    return `login gagal: ${String(d.username)}${d.locked ? " (akun dikunci)" : ""}`;
  }
  if (typeof d.username === "string") {
    return d.role ? `${d.username} (${String(d.role)})` : d.username;
  }
  return JSON.stringify(d);
}
