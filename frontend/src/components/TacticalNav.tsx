"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Role } from "@/lib/api";
import { useAuth } from "./AuthProvider";
import { Button } from "./ui";

const links: { href: string; label: string; roles: Role[] }[] = [
  { href: "/", label: "Dashboard", roles: ["admin", "distributor", "investigator"] },
  { href: "/distribusi", label: "Distribusi", roles: ["admin", "distributor"] },
  { href: "/personel", label: "Data Personel", roles: ["admin", "distributor"] },
  { href: "/investigasi", label: "Investigasi", roles: ["admin", "investigator"] },
  { href: "/audit", label: "Audit Trail", roles: ["admin", "investigator"] },
  { href: "/pengguna", label: "Pengguna", roles: ["admin"] },
];

export default function TacticalNav() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  if (!user) return null;

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-panel px-6 py-3">
      <Link href="/" className="font-mono text-lg font-bold tracking-widest text-accent">
        SIDIK
      </Link>
      <nav className="flex flex-wrap gap-5 text-sm">
        {links
          .filter((l) => l.roles.includes(user.role))
          .map((l) => {
            const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                aria-current={active ? "page" : undefined}
                className={active ? "font-bold text-accent" : "hover:text-accent"}
              >
                {l.label}
              </Link>
            );
          })}
      </nav>
      <div className="flex items-center gap-3 text-xs">
        <Link href="/akun" className="text-foreground/80 hover:text-accent">
          {user.full_name} <span className="font-mono text-foreground/60">({user.role})</span>
        </Link>
        <Button tone="muted" onClick={() => void signOut()}>
          Keluar
        </Button>
      </div>
    </header>
  );
}
