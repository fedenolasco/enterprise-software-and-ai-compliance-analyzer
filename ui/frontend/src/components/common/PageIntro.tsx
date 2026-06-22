"use client";

import { useState, useEffect } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import {
  getGuidancePreferences,
  shouldShowPageIntro,
  type GuidancePreferences,
} from "@/lib/guidance-preferences";
import { pageIntros } from "@/lib/guidance";

interface PageIntroProps {
  page: keyof typeof pageIntros;
}

export function PageIntro({ page }: PageIntroProps) {
  const [prefs, setPrefs] = useState<GuidancePreferences | null>(null);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    const p = getGuidancePreferences();
    setPrefs(p);
    // Check if this page's intro was previously collapsed
    const collapsed = localStorage.getItem(`page-intro-${page}-collapsed`);
    if (collapsed === "true") setExpanded(false);
  }, [page]);

  if (!prefs || !shouldShowPageIntro(prefs)) return null;

  const text = pageIntros[page];
  if (!text) return null;

  const toggle = () => {
    const next = !expanded;
    setExpanded(next);
    localStorage.setItem(`page-intro-${page}-collapsed`, String(!next));
  };

  return (
    <div className="mb-4 rounded-md border border-blue-200 bg-blue-50 p-4">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm text-blue-900">
          {expanded ? text : `${text.substring(0, 80)}...`}
        </p>
        <button
          onClick={toggle}
          className="flex-shrink-0 rounded-sm p-1 hover:bg-blue-100"
          aria-label={expanded ? "Collapse intro" : "Expand intro"}
        >
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-blue-700" />
          ) : (
            <ChevronDown className="h-4 w-4 text-blue-700" />
          )}
        </button>
      </div>
    </div>
  );
}
