"use client";

import { useState } from "react";

export default function CopyLinkButton() {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (_) {}
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label="Copiar link desta análise"
      className="inline-flex items-center gap-1.5 rounded-md border border-border
                 px-3 py-1.5 text-xs font-medium text-foreground
                 hover:bg-secondary transition-colors
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {copied ? (
        <>
          <span aria-hidden>✓</span> Copiado!
        </>
      ) : (
        <>
          <span aria-hidden>🔗</span> Copiar link
        </>
      )}
    </button>
  );
}
