import type { DumpResult } from "@/lib/api";
import { formatTime, shortHash } from "@/lib/format";
import { Badge, Row, type Tone } from "./ui";

const STATUS: Record<DumpResult["status"], { label: string; tone: Tone; headline: string }> = {
  AUTHENTIC_LEAK: {
    label: "KEBOCORAN ASLI",
    tone: "danger",
    headline: "Dump memuat honey-record: berasal dari basis data kita",
  },
  UNTRACED_MATCH: {
    label: "COCOK, SUMBER TAK TERLACAK",
    tone: "warn",
    headline: "Identitas cocok dengan data kita, honey-record tidak cukup",
  },
  RECYCLED_PUBLIC: { label: "HOAKS: DAUR ULANG", tone: "ok", headline: "Data publik lama yang dikemas ulang" },
  FABRICATED: { label: "HOAKS: DATA REKAAN", tone: "ok", headline: "Format NIK banyak yang tidak valid" },
  NOT_FROM_OUR_DB: { label: "BUKAN DATA KITA", tone: "ok", headline: "Identitas tidak cocok dengan data personel" },
  INSUFFICIENT_DATA: { label: "TIDAK ADA IDENTITAS", tone: "muted", headline: "Tak ada NIK, nomor HP, atau NRP" },
};

const pct = (x: number) => `${Math.round(x * 100)}%`;

export default function DumpReport({ result, elapsed }: { result: DumpResult; elapsed: number }) {
  const status = (result.status && STATUS[result.status]) ?? {
    label: result.status || "STATUS TIDAK DIKENAL",
    tone: "muted" as Tone,
    headline: "Status hasil tidak dikenali",
  };
  const ids = result.identifiers;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone={status.tone}>{status.label}</Badge>
        <span className="text-sm text-foreground/70">{status.headline}</span>
        <span className="text-xs text-foreground/50">({elapsed.toFixed(1)} dtk)</span>
      </div>

      <dl>
        <Row label="Identitas ditemukan">
          <span className="font-mono">
            {ids.nik} NIK · {ids.no_hp} HP · {ids.nrp} NRP
          </span>
        </Row>
        <Row label="Cocok dengan data personel kita">{pct(result.personnel_ratio)}</Row>
        <Row label="Cocok dengan korpus data publik">
          {pct(result.corpus_ratio)}
          {result.corpus_label ? ` · ${result.corpus_label}` : ""}
        </Row>
        <Row label="NIK berformat tidak valid">{pct(result.invalid_ratio)}</Row>
      </dl>

      {result.sources && result.sources.length > 0 && (
        <div>
          <p className="mb-1 text-xs text-foreground/60">Sumber honey-record di dalam dump</p>
          <ul className="space-y-2 text-sm">
            {result.sources.map((s) => (
              <li key={s.export?.id ?? "db"} className="rounded border border-border p-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-bold">
                    {s.export ? `Ekspor #${s.export.id}` : "Tertanam di basis data (akses langsung)"}
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="font-mono text-xs text-foreground/60">{s.matched_rows} baris</span>
                    <Badge tone={s.proven ? "danger" : "muted"}>{s.proven ? "TERBUKTI" : "INDIKASI"}</Badge>
                  </span>
                </div>
                {s.export ? (
                  <p className="mt-1 text-xs text-foreground/70">
                    oleh <span className="font-mono">{s.export.username}</span> · {formatTime(s.export.created_at)} ·{" "}
                    {s.export.satuan ?? "semua satuan"} · {s.export.purpose}
                  </p>
                ) : (
                  <p className="mt-1 text-xs text-foreground/70">
                    Tabel personel dicuri langsung (mis. SQL injection), bukan lewat ekspor tercatat.
                    Periksa log akses basis data.
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-foreground/70">{result.note}</p>
      <p className="border-t border-border pt-3 font-mono text-xs text-foreground/60">
        Tercatat di ledger #{result.ledger.seq} · {shortHash(result.ledger.entry_hash, 16)}
      </p>
    </div>
  );
}
