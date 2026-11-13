"use client";

import { useEffect, useState } from "react";
import { Badge, Button, Card, ErrorNote, Field, Row, inputClass } from "./ui";
import { type BeaconHit, type CopyRow, listBeaconHits, simulateBeaconHit } from "@/lib/api";
import { formatTime, hexId } from "@/lib/format";

interface BeaconRadarProps {
  copies: CopyRow[];
}

export default function BeaconRadar({ copies }: BeaconRadarProps) {
  const [hits, setHits] = useState<BeaconHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form simulasi
  const [selectedCopyId, setSelectedCopyId] = useState<string>("");
  const [simIp, setSimIp] = useState("185.220.101.5");
  const [simUa, setSimUa] = useState(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Adobe Acrobat Reader/2026.001"
  );
  const [simBusy, setSimBusy] = useState(false);
  const [lastSimulated, setLastSimulated] = useState<BeaconHit | null>(null);

  async function refreshHits() {
    setLoading(true);
    setError(null);
    try {
      const data = await listBeaconHits();
      setHits(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat data radar suar.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshHits();
    // Auto-refresh radar setiap 10 detik
    const timer = setInterval(refreshHits, 10000);
    return () => clearInterval(timer);
  }, []);

  // Set default copy id jika ada salinan
  useEffect(() => {
    if (!selectedCopyId && copies.length > 0) {
      setSelectedCopyId(String(copies[0].copy_id));
    }
  }, [copies, selectedCopyId]);

  async function handleSimulate() {
    if (!selectedCopyId) return;
    setSimBusy(true);
    setError(null);
    try {
      const hit = await simulateBeaconHit(Number(selectedCopyId), simIp, simUa);
      setLastSimulated(hit);
      await refreshHits();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menjalankan simulasi suar.");
    } finally {
      setSimBusy(false);
    }
  }

  const selectedCopy = copies.find((c) => String(c.copy_id) === selectedCopyId);
  const beaconUrl = selectedCopyId
    ? `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/beacon/${selectedCopyId}`
    : "";

  return (
    <div className="space-y-6">
      {error && <ErrorNote message={error} />}

      {/* Panel Radar & Ringkasan */}
      <Card title="Radar Suar Siber Aktif (Canary Token Receiver)">
        <div className="mb-3 flex justify-end">
          <Button tone="muted" onClick={refreshHits} disabled={loading}>
            {loading ? "Memindai…" : "Pindai Ulang"}
          </Button>
        </div>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-4 rounded border border-border/70 bg-background/50 p-3">
          <div className="flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-accent" />
            </span>
            <div>
              <p className="text-xs font-bold text-foreground">SENSOR SUAR ISO 32000 AKTIF</p>
              <p className="text-xs text-foreground/60">
                Mendeteksi pemicuan otomatis OpenAction &amp; mikro-tautan saat PDF dibuka pihak luar
              </p>
            </div>
          </div>
          <div className="flex gap-4 text-xs font-mono">
            <div>
              <span className="text-foreground/50">Total Deteksi: </span>
              <span className="font-bold text-accent">{hits.length}</span>
            </div>
            <div>
              <span className="text-foreground/50">Status: </span>
              <Badge tone="ok">SIAGA 1</Badge>
            </div>
          </div>
        </div>

        {hits.length === 0 ? (
          <div className="rounded border border-dashed border-border p-6 text-center text-sm text-foreground/60">
            Belum ada suar pelacak yang terpicu. Dokumen yang beredar aman atau belum dibuka di jaringan luar.
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-foreground/60">
              Riwayat deteksi suar pelacak (diurutkan dari yang terbaru):
            </p>
            <div className="divide-y divide-border rounded border border-border bg-card">
              {hits.map((h) => (
                <div key={h.id} className="p-3 text-xs space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge tone="danger">SUAR TERDETEKSI</Badge>
                      <span className="font-mono font-bold text-accent text-sm">{h.ip_address}</span>
                      {h.klasifikasi && (
                        <span className="rounded bg-danger/10 px-1.5 py-0.5 text-[10px] font-bold text-danger">
                          {h.klasifikasi}
                        </span>
                      )}
                    </div>
                    <span className="font-mono text-foreground/50">{formatTime(h.detected_at)}</span>
                  </div>

                  <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1">
                    <Row label="Naskah">{h.document_nomor || "-"}</Row>
                    <Row label="Pemegang Asli">
                      {h.recipient_nama} {h.recipient_nrp ? `(${h.recipient_nrp})` : ""}
                    </Row>
                    <Row label="ID Salinan">
                      <span className="font-mono">{hexId(h.copy_id)}</span>
                    </Row>
                    <Row label="Software / OS">
                      <span className="truncate max-w-[280px] inline-block" title={h.user_agent || ""}>
                        {h.user_agent || "Tidak Diketahui"}
                      </span>
                    </Row>
                  </dl>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Panel Simulasi & Demonstrasi Langsung */}
      <Card title="Simulasi &amp; Pengujian Forensik Suar Siber">
        <p className="mb-4 text-xs text-foreground/70">
          Uji cara kerja pelacakan suar ISO 32000. Saat peretas mengunduh atau mengekstrak dokumen curian dan membukanya di komputernya, sinyal suar terkirim seketika membawa IP dan identitas perangkatnya ke Buku Besar SIDIK.
        </p>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Field label="Pilih Salinan Target yang Beredar">
            <select
              value={selectedCopyId}
              onChange={(e) => setSelectedCopyId(e.target.value)}
              className={inputClass}
            >
              {copies.length === 0 && <option value="">Tidak ada salinan beredar</option>}
              {copies.map((c) => (
                <option key={c.copy_id} value={c.copy_id}>
                  {c.document_nomor} · {c.recipient_nama} ({c.recipient_nrp}) [{hexId(c.copy_id)}]
                </option>
              ))}
            </select>
          </Field>

          <Field label="Alamat IP Pembaca Eksternal (Simulasi)">
            <input
              type="text"
              value={simIp}
              onChange={(e) => setSimIp(e.target.value)}
              placeholder="Contoh: 185.220.101.5 (Tor Exit)"
              className={inputClass}
            />
          </Field>

          <div className="md:col-span-2">
            <Field label="User-Agent / Perangkat Eksternal (Simulasi)">
              <input
                type="text"
                value={simUa}
                onChange={(e) => setSimUa(e.target.value)}
                className={inputClass}
              />
            </Field>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
          <div className="text-xs text-foreground/60">
            {beaconUrl && (
              <span>
                URL Suar Nyata:{" "}
                <code className="rounded bg-background px-1.5 py-0.5 text-accent">{beaconUrl}</code>
              </span>
            )}
          </div>
          <div className="flex gap-2">
            {beaconUrl && (
              <a
                href={beaconUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center rounded border border-border px-3 py-1.5 text-xs font-semibold hover:bg-background/80"
              >
                Uji Buka URL di Tab Baru
              </a>
            )}
            <Button tone="ok" onClick={handleSimulate} disabled={simBusy || !selectedCopyId}>
              {simBusy ? "Memproses…" : "Picukan Suar Simulasi"}
            </Button>
          </div>
        </div>

        {lastSimulated && (
          <div className="mt-4 rounded border border-ok/30 bg-ok/5 p-3 text-xs">
            <p className="font-bold text-ok">Suar Berhasil Dipicu &amp; Dikunci di Buku Besar Audit!</p>
            <p className="mt-1 text-foreground/70">
              IP <span className="font-mono font-bold text-accent">{lastSimulated.ip_address}</span> terdeteksi membuka naskah <span className="font-bold">{lastSimulated.document_nomor}</span> milik <span className="font-bold">{lastSimulated.recipient_nama}</span>.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
