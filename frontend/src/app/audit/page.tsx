"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, ErrorNote } from "@/components/ui";
import { type LedgerEntry, type VerifyResult, listLedger, verifyLedger } from "@/lib/api";
import { formatTime, parseBody, shortHash, summarize } from "@/lib/format";

const loadLedger = () => Promise.all([listLedger(100), verifyLedger()]);

export default function AuditPage() {
  const [entries, setEntries] = useState<LedgerEntry[] | null>(null);
  const [verify, setVerify] = useState<VerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<Set<number>>(new Set());
  const [checking, setChecking] = useState(false);

  const apply = useCallback(([list, result]: [LedgerEntry[], VerifyResult]) => {
    setEntries(list);
    setVerify(result);
    setError(null);
  }, []);

  useEffect(() => {
    loadLedger()
      .then(apply)
      .catch((e) => setError(e instanceof Error ? e.message : "Gagal memuat buku besar."));
  }, [apply]);

  async function check() {
    setChecking(true);
    try {
      apply(await loadLedger());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal memuat buku besar.");
    } finally {
      setChecking(false);
    }
  }

  const toggle = (seq: number) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (!next.delete(seq)) next.add(seq);
      return next;
    });

  const copyAnchor = () => {
    if (verify?.head_hash) {
      void navigator.clipboard?.writeText(`#${verify.head_seq} ${verify.head_hash}`).catch(() => undefined);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <h1 className="font-mono text-2xl font-bold text-accent">Audit Trail</h1>
      <ErrorNote message={error} />

      <Card title="Integritas rantai">
        <div className="flex flex-wrap items-center gap-4">
          {verify ? (
            <Badge tone={verify.ok ? "ok" : "danger"}>
              {verify.ok ? "RANTAI VALID" : "RANTAI RUSAK"}
            </Badge>
          ) : (
            <Badge>memeriksa…</Badge>
          )}
          {verify && (
            <span className="text-sm text-foreground/70">{verify.entries} entri diperiksa</span>
          )}
          <Button tone="muted" onClick={check} disabled={checking}>
            {checking ? "Memeriksa…" : "Verifikasi ulang"}
          </Button>
        </div>

        {verify && !verify.ok && (
          <p role="alert" className="mt-3 rounded border border-danger/60 bg-danger/10 px-3 py-2 text-sm text-danger">
            Entri #{verify.bad_seq}: {verify.reason}
          </p>
        )}

        {verify?.head_hash && (
          <div className="mt-4 border-t border-border pt-3 text-xs text-foreground/70">
            <p>
              Ujung rantai (jangkar) #{verify.head_seq}:{" "}
              <span className="break-all font-mono text-foreground">{verify.head_hash}</span>
            </p>
            <p className="mt-1">
              Catat nilai ini di luar sistem (mis. berita acara). Pemotongan entri terakhir hanya
              terdeteksi bila ujung rantai dibandingkan dengan catatan eksternal.
            </p>
            <Button tone="muted" className="mt-2" onClick={copyAnchor}>
              Salin jangkar
            </Button>
          </div>
        )}
      </Card>

      <Card title="Riwayat (terbaru di atas)">
        {entries === null ? (
          <p className="text-sm text-foreground/60">Memuat…</p>
        ) : entries.length === 0 ? (
          <p className="text-sm text-foreground/60">Belum ada entri.</p>
        ) : (
          <ul className="divide-y divide-border/60">
            {entries.map((entry) => {
              const body = parseBody(entry);
              const expanded = open.has(entry.seq);
              return (
                <li key={entry.seq} className="py-2">
                  <button
                    type="button"
                    onClick={() => toggle(entry.seq)}
                    aria-expanded={expanded}
                    className="flex w-full flex-wrap items-center gap-x-4 gap-y-1 text-left text-sm"
                  >
                    <span className="w-10 font-mono text-accent">#{entry.seq}</span>
                    <Badge tone={body?.event === "LEAK_INTAKE_TEXT" ? "warn" : "ok"}>
                      {body?.event ?? "?"}
                    </Badge>
                    <span className="flex-1 text-foreground/80">{summarize(body)}</span>
                    <span className="text-xs text-foreground/60">
                      {body ? `${body.actor} · ${formatTime(body.at)}` : ""}
                    </span>
                  </button>
                  {expanded && (
                    <dl className="mt-2 grid gap-1 rounded border border-border bg-background p-3 font-mono text-xs">
                      <div>
                        <dt className="inline text-foreground/60">prev_hash </dt>
                        <dd className="inline break-all">{entry.prev_hash}</dd>
                      </div>
                      <div>
                        <dt className="inline text-foreground/60">entry_hash </dt>
                        <dd className="inline break-all">{entry.entry_hash}</dd>
                      </div>
                      <div>
                        <dt className="inline text-foreground/60">tanda tangan </dt>
                        <dd className="inline">
                          {shortHash(entry.signature, 24)} (Ed25519, kunci {entry.key_id})
                        </dd>
                      </div>
                      <pre className="mt-2 whitespace-pre-wrap break-all">
                        {body ? JSON.stringify(body, null, 2) : entry.body}
                      </pre>
                    </dl>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
