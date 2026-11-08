"use client";

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, createContext, useContext, useEffect, useState } from "react";
import { type Role, type User, UNAUTHORIZED_EVENT, getMe, login, logout } from "@/lib/api";
import { Card } from "./ui";

type Auth = {
  user: User | null;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  /** Sesi sudah berakhir di server (mis. setelah ganti sandi). */
  clear: () => void;
};

const AuthContext = createContext<Auth | null>(null);
const LOGIN_PATH = "/login";

export function useAuth(): Auth {
  const auth = useContext(AuthContext);
  if (!auth) throw new Error("useAuth harus dipakai di dalam AuthProvider");
  return auth;
}

/** Menyediakan status login dan mengarahkan tamu ke /login.
 *  Ini hanya tampilan: penegakan akses sebenarnya ada di server. */
export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null));
    const onUnauthorized = () => setUser(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  useEffect(() => {
    if (user === null && pathname !== LOGIN_PATH) router.replace(LOGIN_PATH);
    if (user && pathname === LOGIN_PATH) router.replace("/");
  }, [user, pathname, router]);

  const value: Auth = {
    user: user ?? null,
    signIn: async (username, password) => setUser(await login(username, password)),
    signOut: async () => {
      await logout().catch(() => undefined);
      setUser(null);
    },
    clear: () => setUser(null),
  };

  // Halaman tetap dirender (Next.js memvalidasi segmennya); halaman terlindung kosong tanpa user.
  const waiting = !user && pathname !== LOGIN_PATH;
  return (
    <AuthContext.Provider value={value}>
      {waiting && <p className="p-6 font-mono text-sm text-foreground/60">Memuat…</p>}
      {children}
    </AuthContext.Provider>
  );
}

/** Tampilkan isi hanya untuk peran tertentu, supaya halaman tak memanggil API yang pasti ditolak. */
export function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return null;
  if (!roles.includes(user.role)) {
    return (
      <Card title="Akses ditolak" className="mx-auto max-w-xl">
        <p className="text-sm">
          Peran <span className="font-mono">{user.role}</span> tidak diizinkan membuka halaman ini.
        </p>
      </Card>
    );
  }
  return <>{children}</>;
}
