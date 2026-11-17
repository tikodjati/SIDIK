"use client";

import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { Button, Card, ErrorNote, Field, Row, inputClass } from "@/components/ui";
import { changePassword } from "@/lib/api";

const PASSWORD_MIN = 10;

export default function AkunPage() {
  const { user, clear } = useAuth();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [repeat, setRepeat] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (next !== repeat) {
      setError("Kata sandi baru tidak sama.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await changePassword(current, next);
      clear(); // semua sesi dicabut server: masuk lagi dengan sandi baru
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mengganti kata sandi.");
      setBusy(false);
    }
  }

  if (!user) return null;
  return (
    <div className="mx-auto max-w-xl space-y-4">
      <h1 className="font-mono text-2xl font-bold text-accent">Akun Saya</h1>
      <Card>
        <dl>
          <Row label="Nama pengguna">
            <span className="font-mono">{user.username}</span>
          </Row>
          <Row label="Nama">{user.full_name}</Row>
          <Row label="Peran">{user.role}</Row>
        </dl>
      </Card>
      <Card title="Ganti kata sandi">
        <form onSubmit={submit} className="space-y-3">
          <Field label="Kata sandi saat ini">
            <input
              required
              type="password"
              autoComplete="current-password"
              className={inputClass}
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
            />
          </Field>
          <Field label={`Kata sandi baru (minimal ${PASSWORD_MIN} karakter)`}>
            <input
              required
              type="password"
              minLength={PASSWORD_MIN}
              autoComplete="new-password"
              className={inputClass}
              value={next}
              onChange={(e) => setNext(e.target.value)}
            />
          </Field>
          <Field label="Ulangi kata sandi baru">
            <input
              required
              type="password"
              autoComplete="new-password"
              className={inputClass}
              value={repeat}
              onChange={(e) => setRepeat(e.target.value)}
            />
          </Field>
          <ErrorNote message={error} />
          <Button disabled={busy}>Ganti kata sandi</Button>
          <p className="text-xs text-foreground/60">
            Semua sesi akan berakhir; Anda perlu masuk lagi. Ganti sandi awal dari admin supaya hanya
            Anda yang tahu, karena nama akun inilah yang tercatat di buku besar audit.
          </p>
        </form>
      </Card>
    </div>
  );
}
