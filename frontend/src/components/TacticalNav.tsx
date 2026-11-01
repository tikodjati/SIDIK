"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { getActor, setActor } from "@/lib/api";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/distribusi", label: "Distribusi" },
  { href: "/investigasi", label: "Investigasi" },
  { href: "/audit", label: "Audit Trail" },
];

export default function TacticalNav() {
  const pathname = usePathname();
  const actorRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (actorRef.current) actorRef.current.value = getActor() === "anonim" ? "" : getActor();
  }, []);

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-panel px-6 py-3">
      <Link href="/" className="font-mono text-lg font-bold tracking-widest text-accent">
        SIDIK
      </Link>
      <nav className="flex gap-5 text-sm">
        {links.map((l) => {
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
      <label className="flex items-center gap-2 text-xs text-foreground/70">
        Petugas
        <input
          ref={actorRef}
          placeholder="nama / pangkat"
          onChange={(e) => setActor(e.target.value.trim())}
          className="w-40 rounded border border-border bg-background px-2 py-1 text-sm outline-none focus:border-accent"
        />
      </label>
    </header>
  );
}
