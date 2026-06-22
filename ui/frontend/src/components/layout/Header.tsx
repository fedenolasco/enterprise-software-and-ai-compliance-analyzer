"use client";

import { BookOpen, RefreshCw } from "lucide-react";
import { useState, useEffect } from "react";
import {
  getGuidancePreferences,
  updateGuidancePreference,
  type GuidanceDetailLevel,
} from "@/lib/guidance-preferences";
import type { GuidancePreferences } from "@/lib/guidance-preferences";

export function Header() {
  const [prefs, setPrefs] = useState<GuidancePreferences | null>(null);

  useEffect(() => {
    setPrefs(getGuidancePreferences());
  }, []);

  const cycleDetailLevel = () => {
    if (!prefs) return;
    const levels: GuidanceDetailLevel[] = ["full", "essential", "minimal"];
    const currentIndex = levels.indexOf(prefs.guidanceDetailLevel);
    const nextLevel = levels[(currentIndex + 1) % levels.length];
    const updated = updateGuidancePreference("guidanceDetailLevel", nextLevel);
    setPrefs(updated);
  };

  const detailLevelLabel = prefs?.guidanceDetailLevel
    ? prefs.guidanceDetailLevel.charAt(0).toUpperCase() +
      prefs.guidanceDetailLevel.slice(1)
    : "Full";

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div className="flex items-center gap-2">
        <h1 className="text-sm font-medium text-muted-foreground">
          Enterprise Software & AI Compliance Analyzer
        </h1>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={cycleDetailLevel}
          className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
          title="Cycle guidance detail level: Full → Essential → Minimal"
        >
          <BookOpen className="h-3.5 w-3.5" />
          Guidance: {detailLevelLabel}
        </button>
        <button
          onClick={() => window.location.reload()}
          className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
          title="Refresh page"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>
    </header>
  );
}
