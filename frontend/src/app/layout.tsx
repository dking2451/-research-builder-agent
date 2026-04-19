import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Research Builder Agent",
  description: "Personal research, reasoning, and builder workbench",
};

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="rounded-md px-2 py-1 text-sm text-ink-800 hover:bg-paper-100 no-underline"
    >
      {children}
    </Link>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-full">
          <header className="border-b border-paper-100 bg-white">
            <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
              <div className="flex items-baseline gap-3">
                <Link href="/" className="text-sm font-semibold tracking-tight text-ink-950 no-underline">
                  Research Builder Agent
                </Link>
                <span className="hidden text-xs text-ink-700 sm:inline">Evidence-first personal workbench</span>
              </div>
              <nav className="flex flex-wrap items-center gap-1">
                <NavLink href="/">Dashboard</NavLink>
                <NavLink href="/projects">Projects</NavLink>
                <NavLink href="/knowledge">Knowledge</NavLink>
                <NavLink href="/artifacts">Artifacts</NavLink>
                <NavLink href="/search">Search</NavLink>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
