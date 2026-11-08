"use client";

import { useEffect, useState } from "react";
import { RequireRole, useAuth } from "@/components/AuthProvider";
import { Badge, Button, Card, ErrorNote, Field, Row, inputClass, type Tone } from "@/components/ui";
import { type CopyRow, type IntakeResult, getCopyText, intakeText, listCopies } from "@/lib/api";
import { formatTime, hexId, shortHash } from "@/lib/format";
import { simulateLeak } from "@/lib/simulate";

const STATUS: Record<IntakeResult["status"], { label: string; tone: Tone; headline: string }> = {
  IDENTIFIED: { label: "TARGET TERIDENTIFIKASI", tone: "ok", headline: "Salinan teridentifikasi" },
  UNREGISTERED: {
    label: "TIDAK TERDAFTAR",
    tone: "warn",
    headline: "Payload terbaca tetapi tidak terdaftar",
  },
  INSUFFICIENT_FORENSIC_ARTIFACTS: {
    label: "BUKTI TIDAK CUKUP",
    tone: "danger",
    headline: "Sistem menolak menebak",
  },
};

function InvestigasiPanel() {
  const { user } = useAuth();
  const canSimulate = user?.role === "admin"; // teks salinan hanya boleh dibaca admin
  const [text, setText] = useState("");
  const [caseRef, setCaseRef] = useState("");
  const [result, setResult] = useState<IntakeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [copies, setCopies] = useState<CopyRow[]>([]);
  const [simCopy, setSimCopy] = useState("");
  const [fraction, setFraction] = useState(80);
  const [upper, setUpper] = useState(true);
  const [typos, setTypos] = useState(true);

  useEffect(() => {
    if (!canSimulate) return;
    listCopies()
      .then(setCopies)
      .catch(() => setCopies([]));
  }, [canSimulate]);

  async function analyse() {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await intakeText(text, caseRef.trim()));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analisis gagal.");
    } finally {
      setBusy(false);
    }
  }

  async function simulate() {
    setError(null);
    try {
      const { text: full } = await getCopyText(Number(simCopy));
      setText(simulateLeak(full, { fraction: fraction / 100, upper, typoRate: typos ? 0.01 : 0 }));
      setResult(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal membuat teks simulasi.");
    }
  }

  const status = result ? STATUS[result.status] : null;
  const meter = result ? Math.round((result.observed_bits / result.total_bits) * 100) : 0;

  return (
    <div className="mx-auto grid max-w-6xl gap-4 lg:grid-cols-2">
      <div className="space-y-4">
        <h1 className="font-mono text-2xl font-bold text-accent lg:col-span-2">Investigasi Kebocoran</h1>

        <Card title="Bukti kebocoran (teks)">
          <div className="space-y-3">
            <textarea
              aria-label="Teks bukti kebocoran"
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={12}
              placeholder="Tempel teks yang beredar (boleh potongan, diketik ulang, atau berubah huruf)…"
              className="w-full rounded border border-border bg-background p-3 font-mono text-xs outline-none focus:border-accent"
            />
            <Field label="Nomor perkara (opsional)">
              <input className={inputClass} value={caseRef} onChange={(e) => setCaseRef(e.target.value)} />
            </Field>
            <ErrorNote message={error} />
            <Button onClick={analyse} disabled={busy || !text.trim()}>
              {busy ? "Menganalisis…" : "Analisis bukti"}
            </Button>
          </div>
        </Card>

        {canSimulate && <Card title="Simulasi kebocoran (untuk demo)">
          <div className="space-y-3">
            <Field label="Salinan yang bocor">
              <select className={inputClass} value={simCopy} onChange={(e) => setSimCopy(e.target.value)}>
                <option value="">pilih salinan…</option>
                {copies.map((c) => (
                  <option key={c.copy_id} value={c.copy_id}>
                    {hexId(c.copy_id)} · {c.recipient_nama}
                  </option>
                ))}
              </select>
            </Field>
            <Field label={`Bagian teks yang disalin: ${fraction}%`}>
              <input
                type="range"
                min={20}
                max={100}
                value={fraction}
                onChange={(e) => setFraction(Number(e.target.value))}
                className="w-full accent-accent"
              />
            </Field>
            <div className="flex gap-5 text-sm">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={upper} onChange={(e) => setUpper(e.target.checked)} />
                huruf kapital
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={typos} onChange={(e) => setTypos(e.target.checked)} />
                salah ketik (1%)
              </label>
            </div>
            <Button tone="muted" onClick={simulate} disabled={!simCopy}>
              Buat teks bocor simulasi
            </Button>
          </div>
        </Card>}
      </div>

      <div className="lg:pt-12">
        <Card title="Hasil forensik" className="min-h-64">
          {busy && <p className="animate-pulse font-mono text-sm text-accent">Menganalisis penanda semantik…</p>}
          {!busy && !result && (
            <p className="text-sm text-foreground/60">
              Tempel bukti lalu jalankan analisis. Sistem hanya memberi atribusi bila bukti cukup dan
              salinan terdaftar; selain itu ia menolak.
            </p>
          )}
          {result && status && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <Badge tone={status.tone}>{status.label}</Badge>
                <span className="text-sm text-foreground/70">{status.headline}</span>
              </div>

              <div>
                <div className="mb-1 flex justify-between text-xs text-foreground/60">
                  <span>Bit penanda terbaca</span>
                  <span className="font-mono">
                    {result.observed_bits} / {result.total_bits}
                  </span>
                </div>
                <div className="h-2 rounded bg-background" role="progressbar" aria-valuenow={meter} aria-valuemin={0} aria-valuemax={100}>
                  <div
                    className={`h-2 rounded ${result.status === "IDENTIFIED" ? "bg-accent" : "bg-danger"}`}
                    style={{ width: `${meter}%` }}
                  />
                </div>
              </div>

              {result.attribution && (
                <dl>
                  <Row label="Nama">{result.attribution.recipient.nama}</Row>
                  <Row label="Pangkat">{result.attribution.recipient.pangkat}</Row>
                  <Row label="NRP">
                    <span className="font-mono">{result.attribution.recipient.nrp}</span>
                  </Row>
                  <Row label="Jabatan">{result.attribution.recipient.jabatan}</Row>
                  <Row label="Satuan">{result.attribution.recipient.satuan}</Row>
                  <Row label="Naskah">
                    {result.attribution.document_nomor} · {result.attribution.klasifikasi}
                  </Row>
                  <Row label="Salinan diterbitkan">{formatTime(result.attribution.issued_at)}</Row>
                  <Row label="ID salinan">
                    <span className="font-mono">{hexId(result.attribution.copy_id)}</span>
                  </Row>
                </dl>
              )}

              <p className="text-xs text-foreground/70">{result.note}</p>
              <p className="border-t border-border pt-3 font-mono text-xs text-foreground/60">
                Tercatat di ledger #{result.ledger.seq} · {shortHash(result.ledger.entry_hash, 16)}
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

export default function InvestigasiPage() {
  return (
    <RequireRole roles={["admin", "investigator"]}>
      <InvestigasiPanel />
    </RequireRole>
  );
}
