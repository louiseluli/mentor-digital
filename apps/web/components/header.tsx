/**
 * Header — Mentor Digital
 * Sticky top bar com branding e link de retorno à landing.
 */

import Link from "next/link";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-2xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm font-semibold tracking-tight hover:opacity-80 transition-opacity"
        >
          <span
            aria-hidden="true"
            className="inline-flex h-6 w-6 items-center justify-center rounded bg-foreground text-background text-xs font-bold"
          >
            M
          </span>
          Mentor Digital
        </Link>

        <nav className="hidden sm:flex items-center gap-4">
          <Link
            href="/analytics"
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Impacto
          </Link>
          <span className="text-xs text-muted-foreground">
            Apoio ao pensamento crítico
          </span>
        </nav>
      </div>
    </header>
  );
}
