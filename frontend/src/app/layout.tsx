import type { Metadata } from "next";
import "./globals.css";
import AuthProvider from "@/components/AuthProvider";
import TacticalNav from "@/components/TacticalNav";

export const metadata: Metadata = {
  title: "SIDIK - Pusat Operasi Forensik Dokumen",
  description: "Sistem Identifikasi Dokumen dan Investigasi Kebocoran",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="id" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          <TacticalNav />
          <main className="flex-1 p-6">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
