"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

export default function BackendStatus() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    getHealth()
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
  }, []);

  const label = online === null ? "CHECKING" : online ? "ONLINE" : "OFFLINE";
  const color = online === null ? "opacity-60" : online ? "text-accent" : "text-danger";

  return (
    <div className="mt-6 rounded border border-border bg-panel p-4 font-mono text-sm">
      Backend API: <span className={color}>{label}</span>
    </div>
  );
}
