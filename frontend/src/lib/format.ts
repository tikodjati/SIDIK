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

/** Peristiwa analisis bukti (teks, foto, dan dump data) di buku besar. */
export const isIntake = (event?: string) =>
  event === "LEAK_INTAKE_TEXT" || event === "LEAK_INTAKE_PHOTO" || event === "LEAK_INTAKE_DUMP";

export function summarize(body: LedgerBody | null): string {
  if (!body) return "(isi tidak terbaca)";
  const d = body.data;
  if (body.event === "COPY_ISSUED") {
    return `salinan ${hexId(Number(d.copy_id))} untuk NRP ${String(d.recipient_nrp)} (${String(d.document_nomor)})`;
  }
  if (body.event === "COPY_EXPORTED") {
    return `PDF salinan ${hexId(Number(d.copy_id))} diunduh (${String(d.document_nomor)})`;
  }
  if (body.event === "COPY_REQUESTED") {
    return `pengajuan salinan ${hexId(Number(d.copy_id))} untuk NRP ${String(d.recipient_nrp)} (${String(d.document_nomor)}, ${String(d.klasifikasi)}) menunggu persetujuan`;
  }
  if (body.event === "COPY_APPROVED") {
    return `salinan ${hexId(Number(d.copy_id))} disetujui (diajukan oleh ${String(d.requested_by)})`;
  }
  if (body.event === "COPY_REJECTED") {
    return `pengajuan salinan ${hexId(Number(d.copy_id))} ditolak: ${String(d.reason)}`;
  }
  if (body.event === "DATA_EXPORTED") {
    return `ekspor data personel #${String(d.export_id)} · ${d.satuan ? String(d.satuan) : "semua satuan"} · ${String(d.rows)} baris · ${String(d.purpose)}`;
  }
  if (body.event === "PERSONNEL_SEEDED") return `data personel demo diisi (${String(d.rows)} baris)`;
  if (body.event === "CORPUS_REGISTERED") {
    return `korpus data publik "${String(d.label)}" (${String(d.entries)} identitas)`;
  }
  if (body.event === "LEAK_INTAKE_DUMP") {
    const ids = Array.isArray(d.export_ids) && d.export_ids.length ? ` · ekspor #${d.export_ids.join(", #")}` : "";
    const db = d.db_direct ? " · DB langsung" : "";
    const ref = d.case_ref ? ` · perkara ${String(d.case_ref)}` : "";
    return `dump: ${String(d.status)}${ids}${db} · ${String(d.identifiers)} identitas${ref}`;
  }
  if (isIntake(body.event)) {
    const channel = body.event === "LEAK_INTAKE_PHOTO" ? "foto" : "teks";
    const ids = Array.isArray(d.copy_ids) ? d.copy_ids.map((c) => hexId(Number(c))).join(" + ") : null;
    const id = ids ?? (d.copy_id == null ? "tanpa ID" : hexId(Number(d.copy_id)));
    const ref = d.case_ref ? ` · perkara ${String(d.case_ref)}` : "";
    return `${channel}: ${String(d.status)} · ${id} · ${String(d.observed_bits)}/${String(d.total_bits)}${ref}`;
  }
  if (body.event === "LOGIN_FAILED") {
    return `login gagal: ${String(d.username)}${d.locked ? " (akun dikunci)" : ""}`;
  }
  if (typeof d.username === "string") {
    return d.role ? `${d.username} (${String(d.role)})` : d.username;
  }
  return JSON.stringify(d); // peristiwa baru yang belum punya ringkasan; detail lengkap saat dibuka
}
