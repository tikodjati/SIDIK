"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, ErrorNote, Field, inputClass } from "@/components/ui";
import {
  type CopyIssued,
  type CopyRow,
  type DocumentRow,
  type Recipient,
  createDocument,
  createRecipient,
  issueCopy,
  listCopies,
  listDocuments,
  listRecipients,
} from "@/lib/api";
import { formatTime, hexId } from "@/lib/format";

const fetchAll = () => Promise.all([listRecipients(), listDocuments(), listCopies()]);

const KLASIFIKASI = ["BIASA", "TERBATAS", "KONFIDENSIAL", "RAHASIA", "SANGAT RAHASIA"] as const;
const emptyRecipient = { nrp: "", nama: "", pangkat: "", jabatan: "", satuan: "" };
const emptyDocument = { nomor: "", judul: "", klasifikasi: "RAHASIA" as (typeof KLASIFIKASI)[number] };

export default function DistribusiPage() {
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [copies, setCopies] = useState<CopyRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [recipientForm, setRecipientForm] = useState(emptyRecipient);
  const [documentForm, setDocumentForm] = useState(emptyDocument);
  const [documentId, setDocumentId] = useState("");
  const [recipientId, setRecipientId] = useState("");
  const [issued, setIssued] = useState<CopyIssued | null>(null);
  const [busy, setBusy] = useState(false);

  const applyAll = useCallback(([r, d, c]: [Recipient[], DocumentRow[], CopyRow[]]) => {
    setRecipients(r);
    setDocuments(d);
    setCopies(c);
  }, []);

  useEffect(() => {
    fetchAll()
      .then(applyAll)
      .catch((e) => setError(e instanceof Error ? e.message : "Gagal memuat data."));
  }, [applyAll]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      applyAll(await fetchAll());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Terjadi kesalahan.");
    } finally {
      setBusy(false);
    }
  }

  const addRecipient = (e: React.FormEvent) => {
    e.preventDefault();
    void run(async () => {
      await createRecipient(recipientForm);
      setRecipientForm(emptyRecipient);
    });
  };

  const addDocument = (e: React.FormEvent) => {
    e.preventDefault();
    void run(async () => {
      await createDocument(documentForm);
      setDocumentForm(emptyDocument);
    });
  };

  const issue = (e: React.FormEvent) => {
    e.preventDefault();
    void run(async () => {
      setIssued(await issueCopy(Number(documentId), Number(recipientId)));
    });
  };

  const download = () => {
    if (!issued) return;
    const url = URL.createObjectURL(new Blob([issued.text], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `salinan_${hexId(issued.copy_id)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyText = () => {
    if (issued) void navigator.clipboard?.writeText(issued.text).catch(() => undefined);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <h1 className="font-mono text-2xl font-bold text-accent">Distribusi Naskah</h1>
      <ErrorNote message={error} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="1. Daftarkan penerima">
          <form onSubmit={addRecipient} className="grid grid-cols-2 gap-3">
            {(Object.keys(emptyRecipient) as (keyof typeof emptyRecipient)[]).map((key) => (
              <Field key={key} label={key === "nrp" ? "NRP" : key}>
                <input
                  required
                  className={inputClass}
                  value={recipientForm[key]}
                  onChange={(e) => setRecipientForm({ ...recipientForm, [key]: e.target.value })}
                />
              </Field>
            ))}
            <div className="col-span-2">
              <Button disabled={busy}>Tambah penerima</Button>
            </div>
          </form>
          <p className="mt-3 text-xs text-foreground/60">{recipients.length} penerima terdaftar.</p>
        </Card>

        <Card title="2. Daftarkan naskah">
          <form onSubmit={addDocument} className="grid grid-cols-2 gap-3">
            <Field label="Nomor naskah">
              <input
                required
                className={inputClass}
                value={documentForm.nomor}
                onChange={(e) => setDocumentForm({ ...documentForm, nomor: e.target.value })}
              />
            </Field>
            <Field label="Klasifikasi">
              <select
                className={inputClass}
                value={documentForm.klasifikasi}
                onChange={(e) =>
                  setDocumentForm({
                    ...documentForm,
                    klasifikasi: e.target.value as (typeof KLASIFIKASI)[number],
                  })
                }
              >
                {KLASIFIKASI.map((k) => (
                  <option key={k}>{k}</option>
                ))}
              </select>
            </Field>
            <div className="col-span-2">
              <Field label="Judul">
                <input
                  required
                  className={inputClass}
                  value={documentForm.judul}
                  onChange={(e) => setDocumentForm({ ...documentForm, judul: e.target.value })}
                />
              </Field>
            </div>
            <div className="col-span-2">
              <Button disabled={busy}>Tambah naskah</Button>
            </div>
          </form>
          <p className="mt-3 text-xs text-foreground/60">{documents.length} naskah terdaftar.</p>
        </Card>
      </div>

      <Card title="3. Terbitkan salinan bertanda">
        <form onSubmit={issue} className="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
          <Field label="Naskah">
            <select required className={inputClass} value={documentId} onChange={(e) => setDocumentId(e.target.value)}>
              <option value="">pilih naskah…</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nomor} · {d.judul}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Penerima">
            <select required className={inputClass} value={recipientId} onChange={(e) => setRecipientId(e.target.value)}>
              <option value="">pilih penerima…</option>
              {recipients.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.pangkat} {r.nama} · {r.nrp}
                </option>
              ))}
            </select>
          </Field>
          <Button disabled={busy}>Terbitkan</Button>
        </form>

        {issued && (
          <div className="mt-4 space-y-3 border-t border-border pt-4">
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <Badge tone="ok">SALINAN DITERBITKAN</Badge>
              <span className="font-mono">ID {hexId(issued.copy_id)}</span>
              <span className="text-foreground/60">tercatat di ledger #{issued.ledger_seq}</span>
            </div>
            <textarea
              readOnly
              aria-label="Teks naskah bertanda"
              value={issued.text}
              rows={12}
              className="w-full rounded border border-border bg-background p-3 font-mono text-xs"
            />
            <div className="flex gap-2">
              <Button tone="muted" type="button" onClick={copyText}>
                Salin teks
              </Button>
              <Button tone="muted" type="button" onClick={download}>
                Unduh .txt
              </Button>
            </div>
          </div>
        )}
      </Card>

      <Card title="Salinan yang sudah diterbitkan">
        {copies.length === 0 ? (
          <p className="text-sm text-foreground/60">Belum ada salinan.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-foreground/60">
                <tr>
                  <th className="py-2">ID salinan</th>
                  <th>Penerima</th>
                  <th>NRP</th>
                  <th>Naskah</th>
                  <th>Diterbitkan</th>
                </tr>
              </thead>
              <tbody>
                {copies.map((c) => (
                  <tr key={c.copy_id} className="border-t border-border/60">
                    <td className="py-2 font-mono">{hexId(c.copy_id)}</td>
                    <td>{c.recipient_nama}</td>
                    <td className="font-mono">{c.recipient_nrp}</td>
                    <td>{c.document_nomor}</td>
                    <td>{formatTime(c.issued_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
