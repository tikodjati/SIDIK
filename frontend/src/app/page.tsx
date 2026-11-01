"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge, Card, type Tone } from "@/components/ui";
import {
  type LedgerEntry,
  type VerifyResult,
  getHealth,
  listCopies,
  listDocuments,
  listLedger,
  listRecipients,
  verifyLedger,
} from "@/lib/api";
import { formatTime, parseBody, summarize } from "@/lib/format";

type Overview = {
  recipients: number;
  documents: number;
  copies: number;
  ledger: LedgerEntry[];
  verify: VerifyResult;
};

function Stat({ label, value, tone }: { label: string; value: string | number; tone?: Tone }) {
  return (
    <Card>
      <p className="text-xs uppercase tracking-wide text-foreground/60">{label}</p>
      <p className={`mt-1 font-mono text-2xl font-bold ${tone === "danger" ? "text-danger" : "text-accent"}`}>
        {value}
      </p>
    </Card>
  );
}

export default function Home() {
  const [online, setOnline] = useState<boolean | null>(null);
  const [data, setData] = useState<Overview | null>(null);

  useEffect(() => {
    getHealth()
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
    Promise.all([listRecipients(), listDocuments(), listCopies(), listLedger(200), verifyLedger()])
      .then(([r, d, c, ledger, verify]) =>
        setData({ recipients: r.length, documents: d.length, copies: c.length, ledger, verify }),
      )
      .catch(() => setData(null));
  }, []);

  const investigations =
    data?.ledger.filter((e) => parseBody(e)?.event === "LEAK_INTAKE_TEXT").length ?? 0;

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div>
        <h1 className="font-mono text-2xl font-bold text-accent">Dashboard Taktis</h1>
        <p className="mt-1 text-sm text-foreground/70">
          Sistem Identifikasi Dokumen dan Investigasi Kebocoran.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-xs uppercase tracking-wide text-foreground/60">Server API</p>
          <div className="mt-2">
            <Badge tone={online === null ? "muted" : online ? "ok" : "danger"}>
              {online === null ? "MEMERIKSA" : online ? "ONLINE" : "OFFLINE"}
            </Badge>
          </div>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-foreground/60">Integritas ledger</p>
          <div className="mt-2">
            <Badge tone={!data ? "muted" : data.verify.ok ? "ok" : "danger"}>
              {!data ? "—" : data.verify.ok ? `VALID · ${data.verify.entries} ENTRI` : "RUSAK"}
            </Badge>
          </div>
        </Card>
        <Stat label="Salinan diterbitkan" value={data?.copies ?? "—"} />
        <Stat label="Investigasi tercatat" value={data ? investigations : "—"} />
        <Stat label="Penerima" value={data?.recipients ?? "—"} />
        <Stat label="Naskah" value={data?.documents ?? "—"} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <Card title="Aktivitas terakhir">
          {!data || data.ledger.length === 0 ? (
            <p className="text-sm text-foreground/60">
              {online === false ? "Server API tidak dapat dihubungi." : "Belum ada aktivitas."}
            </p>
          ) : (
            <ul className="divide-y divide-border/60 text-sm">
              {data.ledger.slice(0, 6).map((entry) => {
                const body = parseBody(entry);
                return (
                  <li key={entry.seq} className="py-2">
                    <span className="font-mono text-accent">#{entry.seq}</span>{" "}
                    <span className="font-bold">{body?.event}</span>
                    <p className="text-foreground/80">{summarize(body)}</p>
                    <p className="text-xs text-foreground/60">
                      {body ? `${body.actor} · ${formatTime(body.at)}` : ""}
                    </p>
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        <Card title="Alur demo">
          <ol className="list-inside list-decimal space-y-2 text-sm">
            <li>
              <Link className="text-accent hover:underline" href="/distribusi">
                Distribusi
              </Link>
              : daftarkan penerima dan naskah, terbitkan salinan.
            </li>
            <li>
              <Link className="text-accent hover:underline" href="/investigasi">
                Investigasi
              </Link>
              : simulasikan kebocoran, lihat siapa pembocornya.
            </li>
            <li>
              <Link className="text-accent hover:underline" href="/audit">
                Audit Trail
              </Link>
              : buktikan rantai catatan tak berubah.
            </li>
          </ol>
        </Card>
      </div>
    </div>
  );
}
