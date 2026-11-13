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

  // Form simulasi intelijen canggih
  const [selectedCopyId, setSelectedCopyId] = useState<string>("");
  const [simIp, setSimIp] = useState("185.220.101.5");
  const [simUa, setSimUa] = useState(
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
  );
  const [simWebRtcIp, setSimWebRtcIp] = useState("114.124.210.88");
  const [simLocalIp, setSimLocalIp] = useState("192.168.1.45");
  const [simGpu, setSimGpu] = useState("NVIDIA GeForce RTX 4070 Laptop GPU");
  const [simCores, setSimCores] = useState("16");
  const [simLang, setSimLang] = useState("id-ID");
  const [simTz, setSimTz] = useState("Asia/Jakarta");
  const [simRes, setSimRes] = useState("1920x1080");
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
    // Auto-refresh radar setiap 5 detik agar responsif saat suar dipicu
    const timer = setInterval(refreshHits, 5000);
    return () => clearInterval(timer);
  }, []);

  // Set default copy id jika ada salinan
  useEffect(() => {
    if (!selectedCopyId && copies.length > 0) {
      setSelectedCopyId(String(copies[0].copy_id));
    }
  }, [copies, selectedCopyId]);

  function applyPreset(type: "tor_bypass" | "foreign_apt") {
    if (type === "tor_bypass") {
      setSimIp("185.220.101.5"); // Tor Exit Node
      setSimWebRtcIp("114.124.210.88"); // IP Asli Telkomsel
      setSimLocalIp("192.168.1.45");
      setSimGpu("NVIDIA GeForce RTX 4070 Laptop GPU");
      setSimCores("16");
      setSimLang("id-ID");
      setSimTz("Asia/Jakarta");
      setSimRes("2560x1440");
    } else {
      setSimIp("45.154.255.2"); // VPN Belanda / Russia
      setSimWebRtcIp("95.173.136.20"); // IP Asli Moskow
      setSimLocalIp("10.8.0.2");
      setSimGpu("AMD Radeon RX 7900 XTX");
      setSimCores("24");
      setSimLang("ru-RU");
      setSimTz("Europe/Moscow");
      setSimRes("1920x1080");
    }
  }

  async function handleSimulate() {
    if (!selectedCopyId) return;
    setSimBusy(true);
    setError(null);
    try {
      const hit = await simulateBeaconHit(Number(selectedCopyId), {
        ipAddress: simIp,
        userAgent: simUa,
        webrtcIp: simWebRtcIp,
        localIp: simLocalIp,
        gpuInfo: simGpu,
        cpuCores: simCores ? Number(simCores) : undefined,
        systemLanguage: simLang,
        timezone: simTz,
        screenRes: simRes,
      });
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
    ? `http://127.0.0.1:8000/api/v1/beacon/${selectedCopyId}`
    : "";

  return (
    <div className="space-y-6">
      {error && <ErrorNote message={error} />}

      {/* Panel Radar & Ringkasan */}
      <Card title="Radar Suar Siber Aktif (Canary Token & Deception Enclave)">
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
              <p className="text-xs font-bold text-foreground">SENSOR SUAR ISO 32000 &amp; DECOY AKTIF</p>
              <p className="text-xs text-foreground/60">
                Mengekstrak IP publik, bypass VPN via WebRTC, sidik jari GPU WebGL, dan spesifikasi fisik perangkat peretas
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
              Riwayat deteksi suar &amp; telemetri intelijen perangkat peretas (diurutkan dari yang terbaru):
            </p>
            <div className="divide-y divide-border rounded border border-border bg-card">
              {hits.map((h) => {
                const hasVpnBypass = h.webrtc_ip && h.webrtc_ip !== h.ip_address;
                return (
                  <div key={h.id} className="p-3 text-xs space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone="danger">SUAR TERDETEKSI</Badge>
                        <span className="font-mono font-bold text-foreground/80">
                          IP HTTP: <span className="text-amber-400">{h.ip_address}</span>
                        </span>
                        {hasVpnBypass && (
                          <span className="rounded bg-ok/20 border border-ok/40 px-2 py-0.5 text-[11px] font-bold text-ok font-mono">
                            ⚡ BYPASS VPN (IP ASLI): {h.webrtc_ip}
                          </span>
                        )}
                        {h.local_ip && (
                          <span className="rounded bg-background px-1.5 py-0.5 text-[10px] text-foreground/60 font-mono">
                            LAN: {h.local_ip}
                          </span>
                        )}
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
                        <span className="truncate max-w-[280px] inline-block font-mono" title={h.user_agent || ""}>
                          {h.user_agent || "Tidak Diketahui"}
                        </span>
                      </Row>
                    </dl>

                    {/* Informasi Forensik Perangkat Keras / Telemetri Lanjutan */}
                    {(h.gpu_info || h.cpu_cores || h.timezone || h.system_language) && (
                      <div className="rounded border border-accent/20 bg-accent/5 p-2.5">
                        <p className="text-[11px] font-bold text-accent uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                          <span>🔍</span> Telemetri Intelijen Perangkat Peretas (Hardware Fingerprint)
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-[11px] font-mono">
                          {h.gpu_info && (
                            <div className="col-span-1 sm:col-span-2">
                              <span className="text-foreground/50">Model GPU: </span>
                              <span className="font-semibold text-foreground/90">{h.gpu_info}</span>
                            </div>
                          )}
                          {h.cpu_cores && (
                            <div>
                              <span className="text-foreground/50">CPU Cores: </span>
                              <span className="font-semibold text-foreground/90">{h.cpu_cores} Cores</span>
                            </div>
                          )}
                          {h.screen_res && (
                            <div>
                              <span className="text-foreground/50">Resolusi Layar: </span>
                              <span className="font-semibold text-foreground/90">{h.screen_res}</span>
                            </div>
                          )}
                          {h.timezone && (
                            <div>
                              <span className="text-foreground/50">Zona Waktu: </span>
                              <span className="font-semibold text-foreground/90">{h.timezone}</span>
                            </div>
                          )}
                          {h.system_language && (
                            <div>
                              <span className="text-foreground/50">Bahasa Sistem: </span>
                              <span className="font-semibold text-foreground/90">{h.system_language}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </Card>

      {/* Panel Simulasi & Demonstrasi Langsung */}
      <Card title="Simulasi &amp; Pengujian Forensik Siber Canggih">
        <p className="mb-3 text-xs text-foreground/70">
          Uji cara kerja ekstraksi intelijen ISO 32000 &amp; Decoy Gateway. Saat peretas membuka dokumen atau mengeklik portal verifikasi dengan VPN/Tor aktif, sistem secara aktif mengekstrak IP asli (WebRTC), kartu grafis fisik, dan spesifikasi komputernya ke Buku Besar SIDIK.
        </p>

        <div className="mb-4 flex flex-wrap gap-2">
          <span className="text-xs text-foreground/50 self-center mr-1">Preset Skenario:</span>
          <button
            type="button"
            onClick={() => applyPreset("tor_bypass")}
            className="rounded border border-accent/40 bg-accent/10 px-2.5 py-1 text-xs font-mono font-semibold text-accent hover:bg-accent/20"
          >
            Skenario 1: Peretas Indonesia Pakai Tor/VPN (Bypass WebRTC)
          </button>
          <button
            type="button"
            onClick={() => applyPreset("foreign_apt")}
            className="rounded border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 text-xs font-mono font-semibold text-amber-400 hover:bg-amber-500/20"
          >
            Skenario 2: Foreign APT Actor (Moscow / VPN Proxy)
          </button>
        </div>

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

          <Field label="Alamat IP Samaran (VPN / Tor Exit Node)">
            <input
              type="text"
              value={simIp}
              onChange={(e) => setSimIp(e.target.value)}
              placeholder="Contoh: 185.220.101.5 (Tor Exit)"
              className={inputClass}
            />
          </Field>

          <Field label="IP Publik Asli (Bypass VPN via WebRTC STUN)">
            <input
              type="text"
              value={simWebRtcIp}
              onChange={(e) => setSimWebRtcIp(e.target.value)}
              placeholder="Contoh: 114.124.210.88 (ISP Telkomsel)"
              className={inputClass}
            />
          </Field>

          <Field label="IP Jaringan Lokal (LAN)">
            <input
              type="text"
              value={simLocalIp}
              onChange={(e) => setSimLocalIp(e.target.value)}
              placeholder="Contoh: 192.168.1.45"
              className={inputClass}
            />
          </Field>

          <Field label="Model Kartu Grafis / GPU (WebGL)">
            <input
              type="text"
              value={simGpu}
              onChange={(e) => setSimGpu(e.target.value)}
              className={inputClass}
            />
          </Field>

          <div className="grid grid-cols-3 gap-2">
            <Field label="CPU Cores">
              <input
                type="number"
                value={simCores}
                onChange={(e) => setSimCores(e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Zona Waktu">
              <input
                type="text"
                value={simTz}
                onChange={(e) => setSimTz(e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Bahasa Sistem">
              <input
                type="text"
                value={simLang}
                onChange={(e) => setSimLang(e.target.value)}
                className={inputClass}
              />
            </Field>
          </div>

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
                URL Decoy Langsung:{" "}
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
                Uji Buka Laman Decoy di Tab Baru
              </a>
            )}
            <Button tone="ok" onClick={handleSimulate} disabled={simBusy || !selectedCopyId}>
              {simBusy ? "Memproses…" : "Picukan Telemetri Intelijen"}
            </Button>
          </div>
        </div>

        {lastSimulated && (
          <div className="mt-4 rounded border border-ok/30 bg-ok/5 p-3 text-xs">
            <p className="font-bold text-ok">Telemetri Berhasil Dipicu &amp; Dikunci di Buku Besar Audit!</p>
            <p className="mt-1 text-foreground/70">
              IP VPN <span className="font-mono font-bold text-amber-400">{lastSimulated.ip_address}</span> terdeteksi. Berhasil membongkar IP Asli <span className="font-mono font-bold text-ok">{lastSimulated.webrtc_ip || lastSimulated.ip_address}</span> ({lastSimulated.gpu_info || "GPU terdeteksi"}) pada naskah <span className="font-bold">{lastSimulated.document_nomor}</span>.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
