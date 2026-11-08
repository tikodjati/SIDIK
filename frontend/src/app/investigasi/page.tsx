"use client";

import { useEffect, useMemo, useState } from "react";
import { RequireRole, useAuth } from "@/components/AuthProvider";
import { Badge, Button, Card, ErrorNote, Field, Row, inputClass, type Tone } from "@/components/ui";
import {
  type CopyRow,
  type IntakeResult,
  type LayerReading,
  getCopyText,
  intakePhoto,
  intakeText,
  listCopies,
} from "@/lib/api";
import { formatTime, hexId, shortHash } from "@/lib/format";
import { simulateLeak } from "@/lib/simulate";

const LAYER_LABEL: Record<LayerReading["layer"], string> = {
  L1_SPASI: "Lapis 1 · spasi antar-kata",
  L2_KATA: "Lapis 2 · pilihan kata",
};

const STATUS: Record<IntakeResult["status"], { label: string; tone: Tone; headline: string }> = {
  IDENTIFIED: { label: "TARGET TERIDENTIFIKASI", tone: "ok", headline: "Salinan teridentifikasi" },
  UNREGISTERED: {
    label: "TIDAK TERDAFTAR",
    tone: "warn",
    headline: "Payload terbaca tetapi tidak terdaftar",
  },
  CONFLICTING_EVIDENCE: {
    label: "BUKTI BERTENTANGAN",
    tone: "danger",
    headline: "Kedua lapis menunjuk salinan berbeda",
  },
  INSUFFICIENT_FORENSIC_ARTIFACTS: {
    label: "BUKTI TIDAK CUKUP",
    tone: "danger",
    headline: "Sistem menolak menebak",
  },
};

type Mode = "foto" | "teks";

function InvestigasiPanel() {
  const { user } = useAuth();
  const canSimulate = user?.role === "admin"; // teks salinan hanya boleh dibaca admin
  const [mode, setMode] = useState<Mode>("foto");
  const [text, setText] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [caseRef, setCaseRef] = useState("");
  const [result, setResult] = useState<IntakeResult | null>(null);
  const [resultMode, setResultMode] = useState<Mode>("foto");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  const [copies, setCopies] = useState<CopyRow[]>([]);
  const [simCopy, setSimCopy] = useState("");
  const [fraction, setFraction] = useState(80);
  const [upper, setUpper] = useState(true);
  const [typos, setTypos] = useState(true);

  const photoUrl = useMemo(() => (photo ? URL.createObjectURL(photo) : null), [photo]);
  useEffect(() => () => void (photoUrl && URL.revokeObjectURL(photoUrl)), [photoUrl]);

  useEffect(() => {
    if (!busy) return;
    const started = Date.now();
    const timer = window.setInterval(() => setElapsed((Date.now() - started) / 1000), 200);
    return () => window.clearInterval(timer);
  }, [busy]);

  useEffect(() => {
    if (!canSimulate) return;
    listCopies()
      .then(setCopies)
      .catch(() => setCopies([]));
  }, [canSimulate]);

  async function analyse() {
    setBusy(true);
    setElapsed(0);
    setError(null);
    setResult(null);
    setResultMode(mode);
    try {
      const ref = caseRef.trim();
      setResult(mode === "foto" && photo ? await intakePhoto(photo, ref) : await intakeText(text, ref));
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

  const ready = mode === "foto" ? photo !== null : text.trim() !== "";
  const status = result ? STATUS[result.status] : null;
  const meter = result ? Math.round((result.observed_bits / result.total_bits) * 100) : 0;
  const tabClass = (m: Mode) =>
    `rounded border px-3 py-1.5 font-mono text-xs font-bold uppercase ${
      mode === m ? "border-accent bg-accent/15 text-accent" : "border-border text-foreground/70 hover:border-accent"
    }`;

  return (
    <div className="mx-auto grid max-w-6xl gap-4 lg:grid-cols-2">
      <div className="space-y-4">
        <h1 className="font-mono text-2xl font-bold text-accent">Investigasi Kebocoran</h1>

        <div className="flex gap-2" role="tablist" aria-label="Jenis bukti">
          <button type="button" role="tab" aria-selected={mode === "foto"} className={tabClass("foto")} onClick={() => setMode("foto")}>
            Foto / scan (Lapis 1 + 2)
          </button>
          <button type="button" role="tab" aria-selected={mode === "teks"} className={tabClass("teks")} onClick={() => setMode("teks")}>
            Teks / salin / ketik ulang (Lapis 2)
          </button>
        </div>

        <Card title={mode === "foto" ? "Foto halaman yang bocor" : "Teks yang bocor"}>
          <div className="space-y-3">
            {mode === "foto" ? (
              <>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  capture="environment"
                  aria-label="Foto bukti kebocoran"
                  onChange={(e) => {
                    setPhoto(e.target.files?.[0] ?? null);
                    setResult(null);
                  }}
                  className="block w-full text-sm file:mr-3 file:rounded file:border file:border-accent file:bg-accent/15 file:px-3 file:py-1.5 file:font-mono file:text-xs file:font-bold file:uppercase file:text-accent"
                />
                {photoUrl && (
                  // eslint-disable-next-line @next/next/no-img-element -- pratinjau berkas lokal (blob:)
                  <img src={photoUrl} alt="Pratinjau foto bukti" className="max-h-72 rounded border border-border" />
                )}
                <p className="text-xs text-foreground/60">
                  Foto kertas cetak PDF salinan dari halaman Distribusi. Usahakan seluruh halaman
                  terlihat dan tajam; miring atau terputar tidak masalah.
                </p>
              </>
            ) : (
              <textarea
                aria-label="Teks bukti kebocoran"
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={12}
                placeholder="Tempel teks yang beredar: disalin dari PDF, diketik ulang, potongan, atau berubah huruf…"
                className="w-full rounded border border-border bg-background p-3 font-mono text-xs outline-none focus:border-accent"
              />
            )}
            <Field label="Nomor perkara (opsional)">
              <input className={inputClass} value={caseRef} onChange={(e) => setCaseRef(e.target.value)} />
            </Field>
            <ErrorNote message={error} />
            <Button onClick={analyse} disabled={busy || !ready}>
              {busy ? "Menganalisis…" : "Analisis bukti"}
            </Button>
          </div>
        </Card>

        {canSimulate && mode === "teks" && (
          <Card title="Simulasi kebocoran teks (untuk demo)">
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
          </Card>
        )}
      </div>

      <div className="lg:pt-12">
        <Card title="Hasil forensik" className="min-h-64">
          {busy && (
            <p className="animate-pulse font-mono text-sm text-accent">
              {resultMode === "foto"
                ? "Meluruskan halaman, membaca pilihan kata, lalu mengukur spasi antar-kata…"
                : "Membaca penanda semantik…"}{" "}
              {elapsed.toFixed(0)} dtk
            </p>
          )}
          {!busy && !result && (
            <p className="text-sm text-foreground/60">
              Unggah foto atau tempel teks, lalu jalankan analisis. Sistem hanya memberi atribusi
              bila bukti cukup dan salinan terdaftar; selain itu ia menolak.
            </p>
          )}
          {result && status && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <Badge tone={status.tone}>{status.label}</Badge>
                <span className="text-sm text-foreground/70">{status.headline}</span>
                <span className="text-xs text-foreground/50">({elapsed.toFixed(1)} dtk)</span>
              </div>

              <div>
                <div className="mb-1 flex justify-between text-xs text-foreground/60">
                  <span>{resultMode === "foto" ? "Penanda terbaca (gabungan)" : "Bit penanda terbaca"}</span>
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

              {result.layers && result.layers.length > 0 && (
                <ul className="space-y-1 text-xs">
                  {result.layers.map((r) => (
                    <li key={r.layer} className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-foreground/70">{LAYER_LABEL[r.layer]}</span>
                      <span className="flex items-center gap-2">
                        <span className="font-mono text-foreground/60">
                          {r.observed_bits} / {r.total_bits}
                        </span>
                        <Badge tone={r.decoded_alone ? "ok" : "muted"}>
                          {r.decoded_alone ? "TERBACA" : "KURANG"}
                        </Badge>
                      </span>
                    </li>
                  ))}
                </ul>
              )}

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

              {result.aligned_preview && (
                <figure>
                  {/* eslint-disable-next-line @next/next/no-img-element -- gambar data: dari API */}
                  <img
                    src={`data:image/jpeg;base64,${result.aligned_preview}`}
                    alt="Foto setelah diluruskan ke template"
                    className="max-h-80 rounded border border-border"
                  />
                  <figcaption className="mt-1 text-xs text-foreground/60">
                    Foto setelah diluruskan (perspektif, rotasi, skala cetak dikoreksi).
                  </figcaption>
                </figure>
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
