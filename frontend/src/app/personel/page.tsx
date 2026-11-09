"use client";

import { useCallback, useEffect, useState } from "react";
import { RequireRole, useAuth } from "@/components/AuthProvider";
import { Button, Card, ErrorNote, Field, inputClass } from "@/components/ui";
import {
  type Corpus,
  type DataExport,
  type PersonnelSummary,
  exportPersonnel,
  getPersonnelSummary,
  listCorpora,
  listExports,
  registerCorpus,
  saveBlob,
  seedPersonnel,
} from "@/lib/api";
import { formatTime } from "@/lib/format";

function PersonelPanel() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [summary, setSummary] = useState<PersonnelSummary | null>(null);
  const [exports, setExports] = useState<DataExport[]>([]);
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const [satuan, setSatuan] = useState("");
  const [purpose, setPurpose] = useState("");
  const [corpusFile, setCorpusFile] = useState<File | null>(null);
  const [corpusLabel, setCorpusLabel] = useState("");
  const [corpusNote, setCorpusNote] = useState("");

  const load = useCallback(
    () =>
      Promise.all([
        getPersonnelSummary(),
        listExports(),
        isAdmin ? listCorpora() : Promise.resolve([] as Corpus[]),
      ]),
    [isAdmin],
  );
  const apply = useCallback(([s, e, c]: [PersonnelSummary, DataExport[], Corpus[]]) => {
    setSummary(s);
    setExports(e);
    setCorpora(c);
  }, []);

  useEffect(() => {
    load()
      .then(apply)
      .catch((e) => setError(e instanceof Error ? e.message : "Gagal memuat data."));
  }, [load, apply]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await action();
      apply(await load());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Terjadi kesalahan.");
    } finally {
      setBusy(false);
    }
  }

  const seed = () =>
    void run(async () => {
      const r = await seedPersonnel();
      setNotice(`${r.rows} baris personel demo dibuat (${r.honey_records} di antaranya honey-record tertanam).`);
    });

  const doExport = (e: React.FormEvent) => {
    e.preventDefault();
    void run(async () => {
      const blob = await exportPersonnel(satuan || null, purpose.trim());
      const stamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, "");
      saveBlob(blob, `personel_${stamp}.csv`);
      setPurpose("");
      setNotice("Ekspor tercatat di ledger. Berkas memuat honey-record khusus ekspor ini.");
    });
  };

  const addCorpus = (e: React.FormEvent) => {
    e.preventDefault();
    if (!corpusFile) return;
    void run(async () => {
      const c = await registerCorpus(corpusFile, corpusLabel.trim(), corpusNote.trim());
      setNotice(`Korpus "${c.label}" terdaftar: ${c.entries} identitas (hanya hash yang disimpan).`);
      setCorpusFile(null);
      setCorpusLabel("");
      setCorpusNote("");
    });
  };

  const empty = summary !== null && summary.total === 0;

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div>
        <h1 className="font-mono text-2xl font-bold text-accent">Data Personel</h1>
        <p className="mt-1 text-sm text-foreground/70">
          Lapis 4 (honey-record): setiap ekspor diberi baris personel rekaan yang unik. Bila data
          ekspor bocor, baris itu menunjuk ekspor, akun, dan waktunya.
        </p>
      </div>
      <ErrorNote message={error} />
      {notice && <p className="rounded border border-accent/60 bg-accent/10 px-3 py-2 text-sm text-accent">{notice}</p>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Ringkasan (data demo pengganti SISFO)">
          {summary === null ? (
            <p className="text-sm text-foreground/60">Memuat…</p>
          ) : empty ? (
            <div className="space-y-3 text-sm">
              <p className="text-foreground/70">Belum ada data personel.</p>
              {isAdmin ? (
                <Button onClick={seed} disabled={busy}>
                  Isi data demo
                </Button>
              ) : (
                <p className="text-foreground/60">Minta admin mengisi data demo.</p>
              )}
            </div>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {summary.by_satuan.map((s) => (
                  <tr key={s.satuan} className="border-t border-border/60 first:border-0">
                    <td className="py-1.5">{s.satuan}</td>
                    <td className="py-1.5 text-right font-mono">{s.count}</td>
                  </tr>
                ))}
                <tr className="border-t border-border">
                  <td className="py-1.5 font-bold">Total</td>
                  <td className="py-1.5 text-right font-mono font-bold">{summary.total}</td>
                </tr>
              </tbody>
            </table>
          )}
        </Card>

        <Card title="Ekspor data personel">
          <form className="space-y-3" onSubmit={doExport}>
            <Field label="Satuan">
              <select className={inputClass} value={satuan} onChange={(e) => setSatuan(e.target.value)}>
                <option value="">Semua satuan</option>
                {summary?.by_satuan.map((s) => (
                  <option key={s.satuan} value={s.satuan}>
                    {s.satuan}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Keperluan (dicatat)">
              <input
                className={inputClass}
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="mis. rekap kesiapan bulan November"
                required
                minLength={3}
              />
            </Field>
            <Button type="submit" disabled={busy || empty || purpose.trim().length < 3}>
              Ekspor CSV
            </Button>
          </form>
        </Card>
      </div>

      <Card title="Riwayat ekspor">
        {exports.length === 0 ? (
          <p className="text-sm text-foreground/60">Belum ada ekspor.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-foreground/60">
                <tr>
                  <th className="py-1.5">#</th>
                  <th>Waktu</th>
                  <th>Akun</th>
                  <th>Satuan</th>
                  <th className="text-right">Baris</th>
                  <th className="pl-4">Keperluan</th>
                </tr>
              </thead>
              <tbody>
                {exports.map((x) => (
                  <tr key={x.id} className="border-t border-border/60">
                    <td className="py-1.5 font-mono">{x.id}</td>
                    <td>{formatTime(x.created_at)}</td>
                    <td className="font-mono">{x.username}</td>
                    <td>{x.satuan ?? "Semua"}</td>
                    <td className="text-right font-mono">{x.row_count}</td>
                    <td className="pl-4">{x.purpose}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {isAdmin && (
        <Card title="Korpus data publik lama (deteksi hoaks daur ulang)">
          <div className="grid gap-4 lg:grid-cols-2">
            <form className="space-y-3" onSubmit={addCorpus}>
              <input
                type="file"
                accept=".csv,.sql,.json,.txt,text/plain,text/csv,application/json"
                aria-label="Berkas korpus data publik"
                onChange={(e) => setCorpusFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm file:mr-3 file:rounded file:border file:border-accent file:bg-accent/15 file:px-3 file:py-1.5 file:font-mono file:text-xs file:font-bold file:uppercase file:text-accent"
              />
              <Field label="Nama korpus">
                <input className={inputClass} value={corpusLabel} onChange={(e) => setCorpusLabel(e.target.value)} placeholder="mis. Bocoran data publik 2021" />
              </Field>
              <Field label="Catatan (opsional)">
                <input className={inputClass} value={corpusNote} onChange={(e) => setCorpusNote(e.target.value)} />
              </Field>
              <Button type="submit" disabled={busy || !corpusFile || corpusLabel.trim().length < 3}>
                Daftarkan korpus
              </Button>
              <p className="text-xs text-foreground/60">
                Hanya hash NIK dan nomor HP yang disimpan; isi berkas tidak disimpan.
              </p>
            </form>
            <ul className="space-y-1 text-sm">
              {corpora.length === 0 && <li className="text-foreground/60">Belum ada korpus.</li>}
              {corpora.map((c) => (
                <li key={c.id} className="flex justify-between gap-3 border-b border-border/60 py-1.5">
                  <span>{c.label}</span>
                  <span className="font-mono text-foreground/60">{c.entries} identitas</span>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      )}
    </div>
  );
}

export default function PersonelPage() {
  return (
    <RequireRole roles={["admin", "distributor"]}>
      <PersonelPanel />
    </RequireRole>
  );
}
