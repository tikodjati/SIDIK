"use client";

import { useEffect, useState } from "react";
import { RequireRole } from "@/components/AuthProvider";
import BeaconRadar from "@/components/BeaconRadar";
import { ErrorNote } from "@/components/ui";
import { type CopyRow, listCopies } from "@/lib/api";

function SuarPanel() {
  const [copies, setCopies] = useState<CopyRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCopies()
      .then(setCopies)
      .catch((e) => setError(e instanceof Error ? e.message : "Gagal memuat daftar salinan."));
  }, []);

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div>
        <h1 className="font-mono text-2xl font-bold text-accent">Suar Pelacak</h1>
        <p className="mt-1 text-sm text-foreground/60">
          Histori pemicuan Canary Beacon, terpisah dari Audit Trail. Mencatat kapan dan dari mana
          salinan dibuka beserta telemetri perangkat (IP, GPU, zona waktu). Event-nya tetap
          tertanda tangan di rantai audit, tetapi tidak lagi meramaikan halaman Audit Trail.
        </p>
      </div>
      <ErrorNote message={error} />
      <BeaconRadar copies={copies} />
    </div>
  );
}

export default function SuarPage() {
  return (
    <RequireRole roles={["admin", "investigator"]}>
      <SuarPanel />
    </RequireRole>
  );
}
