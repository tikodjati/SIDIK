import BackendStatus from "@/components/BackendStatus";

export default function Home() {
  return (
    <section className="mx-auto max-w-4xl">
      <h1 className="font-mono text-2xl font-bold text-accent">Dashboard Taktis</h1>
      <p className="mt-2 text-sm opacity-70">Platform forensik atribusi dokumen dan deteksi kebocoran.</p>
      <BackendStatus />
    </section>
  );
}
