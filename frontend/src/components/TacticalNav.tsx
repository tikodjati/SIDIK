const links = [
  { href: "/", label: "Dashboard" },
  { href: "/distribusi", label: "Distribusi" },
  { href: "/investigasi", label: "Investigasi" },
  { href: "/verifikasi", label: "Verifikasi Klaim" },
  { href: "/audit", label: "Audit Trail" },
];

export default function TacticalNav() {
  return (
    <header className="flex items-center justify-between border-b border-border bg-panel px-6 py-3">
      <span className="font-mono text-lg font-bold tracking-widest text-accent">SIDIK</span>
      <nav className="flex gap-5 text-sm">
        {links.map((l) => (
          <a key={l.href} href={l.href} className="hover:text-accent">
            {l.label}
          </a>
        ))}
      </nav>
    </header>
  );
}
