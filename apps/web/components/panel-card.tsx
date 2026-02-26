/**
 * PanelCard — retro HUD panel wrapper.
 * Applies the .hud-panel utility class (double-border + shadow from globals.css)
 * plus rounded corners and optional extra className.
 */

import type { ElementType, ReactNode } from "react";

interface Props {
  children: ReactNode;
  className?: string;
  /** HTML element to render. Defaults to "div". */
  as?: ElementType;
}

export default function PanelCard({
  children,
  className = "",
  as: Tag = "div",
}: Props) {
  return (
    <Tag className={`hud-panel rounded-xl p-5 ${className}`}>{children}</Tag>
  );
}
