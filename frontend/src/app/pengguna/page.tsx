"use client";

import { useEffect, useState } from "react";
import { RequireRole, useAuth } from "@/components/AuthProvider";
import { Badge, Button, Card, ErrorNote, Field, inputClass } from "@/components/ui";
import { type Role, type User, createUser, listUsers, setUserActive } from "@/lib/api";

const ROLES: { value: Role; hint: string }[] = [
  { value: "distributor", hint: "kelola penerima dan naskah, terbitkan salinan" },
  { value: "investigator", hint: "analisis bukti dan baca audit trail" },
  { value: "admin", hint: "semua akses, termasuk mengelola pengguna" },
];
const emptyForm = { username: "", full_name: "", role: "distributor" as Role, password: "" };

function UsersPanel() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listUsers()
      .then(setUsers)
      .catch((e) => setError(e instanceof Error ? e.message : "Gagal memuat pengguna."));
  }, []);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      setUsers(await listUsers());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Terjadi kesalahan.");
    } finally {
      setBusy(false);
    }
  }

  const add = (e: React.FormEvent) => {
    e.preventDefault();
    void run(async () => {
      await createUser(form);
      setForm(emptyForm);
    });
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="font-mono text-2xl font-bold text-accent">Pengguna</h1>
      <ErrorNote message={error} />

      <Card title="Tambah pengguna">
        <form onSubmit={add} className="grid gap-3 sm:grid-cols-2">
          <Field label="Nama pengguna (huruf kecil, angka, . _ -)">
            <input
              required
              pattern="[a-z0-9._\-]{3,32}"
              autoComplete="off"
              className={inputClass}
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          </Field>
          <Field label="Nama lengkap">
            <input
              required
              className={inputClass}
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </Field>
          <Field label="Peran">
            <select
              className={inputClass}
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
            >
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.value}: {r.hint}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Kata sandi awal (minimal 10 karakter)">
            <input
              required
              type="password"
              minLength={10}
              autoComplete="new-password"
              className={inputClass}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </Field>
          <div className="sm:col-span-2">
            <Button disabled={busy}>Tambah pengguna</Button>
          </div>
        </form>
      </Card>

      <Card title="Daftar pengguna">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-foreground/60">
              <tr>
                <th className="py-2">Nama pengguna</th>
                <th>Nama</th>
                <th>Peran</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-border/60">
                  <td className="py-2 font-mono">{u.username}</td>
                  <td>{u.full_name}</td>
                  <td>{u.role}</td>
                  <td>
                    <Badge tone={u.is_active ? "ok" : "danger"}>
                      {u.is_active ? "AKTIF" : "NONAKTIF"}
                    </Badge>
                  </td>
                  <td className="text-right">
                    {u.id !== me?.id && (
                      <Button
                        tone="muted"
                        disabled={busy}
                        onClick={() => void run(async () => void (await setUserActive(u.id, !u.is_active)))}
                      >
                        {u.is_active ? "Nonaktifkan" : "Aktifkan"}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

export default function PenggunaPage() {
  return (
    <RequireRole roles={["admin"]}>
      <UsersPanel />
    </RequireRole>
  );
}
