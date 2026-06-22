"use client";

import { useState, useEffect } from "react";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getGuidancePreferences,
  shouldShowTooltip,
  type GuidancePreferences,
} from "@/lib/guidance-preferences";
import { tooltips } from "@/lib/guidance";

interface TooltipProps {
  term: string;
  children?: React.ReactNode;
  className?: string;
}

export function Tooltip({ term, children, className }: TooltipProps) {
  const [prefs, setPrefs] = useState<GuidancePreferences | null>(null);
  const [show, setShow] = useState(false);

  useEffect(() => {
    setPrefs(getGuidancePreferences());
  }, []);

  if (!prefs || !shouldShowTooltip(prefs)) {
    return <>{children}</>;
  }

  const text = tooltips[term];
  if (!text) return <>{children}</>;

  return (
    <span
      className="relative inline-flex items-center"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      onFocus={() => setShow(true)}
      onBlur={() => setShow(false)}
      tabIndex={0}
    >
      {children}
      <Info className="ml-1 h-3 w-3 text-muted-foreground" />
      {show && (
        <span
          className={cn(
            "absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2 rounded-md border bg-popover p-3 text-xs text-popover-foreground shadow-md",
            className
          )}
          role="tooltip"
        >
          {text}
        </span>
      )}
    </span>
  );
}
