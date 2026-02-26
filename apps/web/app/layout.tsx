import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, VT323 } from "next/font/google";
import Header from "@/components/header";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

/** VT323 — retro pixel-display font. Used ONLY for HUD headings. */
const vt323 = VT323({
  variable: "--font-vt323",
  weight: "400",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Mentor Digital — Análise de Conteúdo",
  description:
    "Ferramenta de apoio ao pensamento crítico sobre conteúdo digital. " +
    "Resultados de análise gerados pelo Mentor Digital.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f8f5ef" },
    { media: "(prefers-color-scheme: dark)", color: "#080810" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        {/*
          Inline theme script — runs before React hydrates to prevent
          flash of wrong theme. Sets both .dark class (Tailwind) and
          data-theme attribute (retro CSS tokens).
        */}
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var t=localStorage.getItem('mentor-theme');var d=window.matchMedia('(prefers-color-scheme:dark)').matches;var dark=t==='dark'||(t===null&&d);document.documentElement.classList.toggle('dark',dark);document.documentElement.setAttribute('data-theme',dark?'dark':'light');}catch(_){}`,
          }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${vt323.variable} antialiased`}
      >
        <Header />
        {children}
      </body>
    </html>
  );
}
