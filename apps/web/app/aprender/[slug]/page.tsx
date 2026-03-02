/**
 * /aprender/[slug] — Individual learning module page
 */

import type { Metadata } from "next";
import ModuleContent from "./module-content";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  return {
    title: `Aprender — Mentor Digital`,
    description: `Módulo de aprendizagem: ${slug.replace(/-/g, " ")}`,
  };
}

export default async function ModulePage({ params }: Props) {
  const { slug } = await params;
  return <ModuleContent slug={slug} />;
}
