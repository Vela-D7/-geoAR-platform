import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "GeoAR Operator Console",
  description: "Upload → process → deploy → monitor for GeoAR sites",
};

const nav = [
  { href: "/upload", label: "Upload" },
  { href: "/processing", label: "Processing" },
  { href: "/sites", label: "Site registry" },
  { href: "/deploy", label: "Deploy" },
  { href: "/monitor", label: "Field-test monitor" },
  { href: "/learning", label: "Self-learning" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100">
        <header className="border-b border-slate-800 bg-slate-900">
          <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-3">
            <Link href="/" className="font-semibold tracking-tight text-emerald-400">
              GeoAR
            </Link>
            <nav className="flex gap-4 text-sm text-slate-300">
              {nav.map((n) => (
                <Link key={n.href} href={n.href} className="hover:text-white">
                  {n.label}
                </Link>
              ))}
            </nav>
            <span className="ml-auto rounded bg-amber-900/60 px-2 py-0.5 text-xs text-amber-300">
              internal MVP — single-operator
            </span>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
