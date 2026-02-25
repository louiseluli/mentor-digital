import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Mentor Digital — Análise de Conteúdo",
    short_name: "Mentor Digital",
    description:
      "Ferramenta de apoio ao pensamento crítico sobre conteúdo digital.",
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#171717",
    icons: [
      {
        src: "/icon?size=192",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/icon?size=512",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
    ],
  };
}
