import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Satu container / satu domain: isi BACKEND_URL dan NEXT_PUBLIC_API_URL=/ supaya browser hanya
  // bicara ke satu alamat dan cookie sesi (SameSite=Strict) tetap terkirim. Kosong = perilaku lokal.
  // /health dipakai badge "Server API" di dashboard; /docs dan /openapi.json adalah dokumentasi API.
  async rewrites() {
    const backend = process.env.BACKEND_URL?.replace(/\/$/, "");
    if (!backend) return [];
    return ["/api/:path*", "/health", "/docs", "/openapi.json"].map((source) => ({
      source,
      destination: `${backend}${source}`,
    }));
  },
  // Proxy rewrite Next memutus permintaan setelah ~30 dtk (analisis foto bisa selama itu atau lebih)
  // dan memotong body di atas 10 MB (foto HP, dump 20 MB). Batas ukuran sebenarnya ada di backend
  // (max_photo_mb, max_dump_mb), jadi proxy dilonggarkan di atasnya.
  experimental: { proxyTimeout: 180_000, proxyClientMaxBodySize: "25mb" },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
