"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { Badge, Card } from "@/components/ui";
import {
  type LedgerEntry,
  type Role,
  type VerifyResult,
  getHealth,
  listCopies,
  listDocuments,
  listLedger,
  listRecipients,
  verifyLedger,
} from "@/lib/api";
import { formatTime, isIntake, parseBody, summarize } from "@/lib/format";

type Registry = { recipients: number; documents: number; copies: number };
type Audit = { ledger: LedgerEntry[]; verify: VerifyResult };

const seesRegistry = (role: Role) => role === "admin" || role === "distributor";
const seesAudit = (role: Role) => role === "admin" || role === "investigator";

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <p className="text-xs uppercase tracking-wide text-foreground/60">{label}</p>
      <p className="mt-1 font-mono text-2xl font-bold text-accent">{value}</p>
    </Card>
  );
}

export default function Home() {
  const { user } = useAuth();
  const role = user?.role;
  const [online, setOnline] = useState<boolean | null>(null);
  const [registry, setRegistry] = useState<Registry | null>(null);
  const [audit, setAudit] = useState<Audit | null>(null);

  useEffect(() => {
    getHealth()
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
    if (role && seesRegistry(role)) {
      Promise.all([listRecipients(), listDocuments(), listCopies()])
        .then(([r, d, c]) => setRegistry({ recipients: r.length, documents: d.length, copies: c.length }))
        .catch(() => setRegistry(null));
    }
    if (role && seesAudit(role)) {
      Promise.all([listLedger(200), verifyLedger()])
        .then(([ledger, verify]) => setAudit({ ledger, verify }))
        .catch(() => setAudit(null));
    }
  }, [role]);

  if (!role) return null;
  const investigations =
    audit?.ledger.filter((e) => isIntake(parseBody(e)?.event)).length ?? 0;

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
        {seesAudit(role) && (
          <>
            <Card>
              <p className="text-xs uppercase tracking-wide text-foreground/60">Integritas ledger</p>
              <div className="mt-2">
                <Badge tone={!audit ? "muted" : audit.verify.ok ? "ok" : "danger"}>
                  {!audit ? "—" : audit.verify.ok ? `VALID · ${audit.verify.entries} ENTRI` : "RUSAK"}
                </Badge>
              </div>
            </Card>
            <Stat label="Investigasi tercatat" value={audit ? investigations : "—"} />
          </>
        )}
        {seesRegistry(role) && (
          <>
            <Stat label="Salinan diterbitkan" value={registry?.copies ?? "—"} />
            <Stat label="Penerima" value={registry?.recipients ?? "—"} />
            <Stat label="Naskah" value={registry?.documents ?? "—"} />
          </>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(16rem,1fr)] lg:items-start">
        {seesAudit(role) && (
          <Card title="Aktivitas terakhir" className="min-w-0">
            {!audit || audit.ledger.length === 0 ? (
              <p className="text-sm text-foreground/60">Belum ada aktivitas.</p>
            ) : (
              <ul className="divide-y divide-border/60 text-sm">
                {audit.ledger.slice(0, 6).map((entry) => {
                  const body = parseBody(entry);
                  return (
                    <li key={entry.seq} className="py-2">
                      <span className="font-mono text-accent">#{entry.seq}</span>{" "}
                      <span className="font-bold">{body?.event}</span>
                      <p className="break-words text-foreground/80 [overflow-wrap:anywhere]">{summarize(body)}</p>
                      <p className="text-xs text-foreground/60">
                        {body ? `${body.actor} · ${formatTime(body.at)}` : ""}
                      </p>
                    </li>
                  );
                })}
              </ul>
            )}
          </Card>
        )}

        <Card title="Tugas Anda" className="min-w-0">
          <ul className="space-y-2 text-sm leading-relaxed">
            {seesRegistry(role) && (
              <li>
                <Link className="text-accent hover:underline" href="/distribusi">
                  Distribusi
                </Link>
                : daftarkan penerima dan naskah, terbitkan salinan.
              </li>
            )}
            {seesRegistry(role) && (
              <li>
                <Link className="text-accent hover:underline" href="/personel">
                  Data Personel
                </Link>
                : ekspor data personel (bersisip honey-record).
              </li>
            )}
            {seesAudit(role) && (
              <>
                <li>
                  <Link className="text-accent hover:underline" href="/investigasi">
                    Investigasi
                  </Link>
                  : analisis bukti kebocoran.
                </li>
                <li>
                  <Link className="text-accent hover:underline" href="/audit">
                    Audit Trail
                  </Link>
                  : buktikan rantai catatan tak berubah.
                </li>
              </>
            )}
            {role === "admin" && (
              <li>
                <Link className="text-accent hover:underline" href="/pengguna">
                  Pengguna
                </Link>
                : kelola akun petugas.
              </li>
            )}
            <li>
              <Link className="text-accent hover:underline" href="/akun">
                Akun
              </Link>
              : ganti kata sandi.
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
