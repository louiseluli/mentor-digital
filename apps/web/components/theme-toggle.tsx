"use client";

import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState<boolean | null>(null);

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains("dark"));
  }, []);

  function toggle() {
    const next = !isDark;
    setIsDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("mentor-theme", next ? "dark" : "light");
    } catch (_) {}
  }

  // Invisible placeholder while mounting — avoids hydration mismatch
  if (isDark === null) {
    return <span className="block w-8 h-8" aria-hidden="true" />;
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Mudar para tema claro" : "Mudar para tema escuro"}
      title={isDark ? "Tema claro" : "Tema escuro"}
      className="rounded-md p-1.5 text-lg leading-none text-muted-foreground
                 hover:text-foreground hover:bg-secondary transition-colors
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {isDark ? "☀️" : "🌙"}
    </button>
  );
}
