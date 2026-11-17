import type { ButtonHTMLAttributes, ReactNode } from "react";

export type Tone = "ok" | "warn" | "danger" | "muted";

const toneClass: Record<Tone, string> = {
  ok: "border-accent/60 bg-accent/10 text-accent",
  warn: "border-warn/60 bg-warn/10 text-warn",
  danger: "border-danger/60 bg-danger/10 text-danger",
  muted: "border-border bg-background text-foreground/70",
};

export function Card({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded border border-border bg-panel p-4 ${className}`}>
      {title && (
        <h2 className="mb-3 font-mono text-xs font-bold uppercase tracking-widest text-accent">
          {title}
        </h2>
      )}
      {children}
    </section>
  );
}

export function Badge({ tone = "muted", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-block rounded border px-2 py-0.5 font-mono text-xs font-bold ${toneClass[tone]}`}
    >
      {children}
    </span>
  );
}

export const inputClass =
  "w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-accent";

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-xs">
      <span className="mb-1 block uppercase tracking-wide text-foreground/60">{label}</span>
      {children}
    </label>
  );
}

export function Button({
  tone = "ok",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { tone?: "ok" | "muted" }) {
  const look =
    tone === "ok"
      ? "border-accent bg-accent/15 text-accent hover:bg-accent/25"
      : "border-border text-foreground/80 hover:border-accent";
  return (
    <button
      {...props}
      className={`rounded border px-3 py-2 font-mono text-xs font-bold uppercase tracking-wide transition disabled:cursor-not-allowed disabled:opacity-40 ${look} ${className}`}
    />
  );
}

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p role="alert" className="rounded border border-danger/60 bg-danger/10 px-3 py-2 text-sm text-danger">
      {message}
    </p>
  );
}

export function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex justify-between gap-4 border-b border-border/60 py-1.5 text-sm last:border-0">
      <dt className="text-foreground/60">{label}</dt>
      <dd className="text-right font-medium">{children}</dd>
    </div>
  );
}
