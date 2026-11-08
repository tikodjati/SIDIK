"use client";

import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { Button, Card, ErrorNote, Field, inputClass } from "@/components/ui";

export default function LoginPage() {
  const { signIn } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signIn(username.trim(), password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login gagal.");
      setPassword("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto mt-12 max-w-sm">
      <h1 className="mb-1 font-mono text-2xl font-bold tracking-widest text-accent">SIDIK</h1>
      <p className="mb-4 text-sm text-foreground/70">
        Sistem Identifikasi Dokumen dan Investigasi Kebocoran
      </p>
      <Card title="Masuk">
        <form onSubmit={submit} className="space-y-3">
          <Field label="Nama pengguna">
            <input
              required
              autoFocus
              autoComplete="username"
              className={inputClass}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </Field>
          <Field label="Kata sandi">
            <input
              required
              type="password"
              autoComplete="current-password"
              className={inputClass}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          <ErrorNote message={error} />
          <Button disabled={busy}>{busy ? "Memeriksa…" : "Masuk"}</Button>
        </form>
      </Card>
    </div>
  );
}
