"use client";

import { useState, useEffect } from "react";
import { Info, X, AlertTriangle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getGuidancePreferences,
  shouldShowCallout,
  dismissCallout,
  type GuidancePreferences,
} from "@/lib/guidance-preferences";
import { callouts } from "@/lib/guidance";

interface CalloutProps {
  calloutId: string;
  className?: string;
}

export function Callout({ calloutId, className }: CalloutProps) {
  const [prefs, setPrefs] = useState<GuidancePreferences | null>(null);

  useEffect(() => {
    setPrefs(getGuidancePreferences());
  }, []);

  if (!prefs || !shouldShowCallout(calloutId, prefs)) return null;

  const callout = callouts[calloutId];
  if (!callout) return null;

  const handleDismiss = () => {
    const updated = dismissCallout(calloutId);
    setPrefs(updated);
  };

  const icons = {
    info: Info,
    warning: AlertTriangle,
    error: AlertCircle,
  };

  const Icon = icons[callout.type];

  const styles = {
    info: "border-blue-200 bg-blue-50 text-blue-900",
    warning: "border-yellow-200 bg-yellow-50 text-yellow-900",
    error: "border-red-200 bg-red-50 text-red-900",
  };

  return (
    <div
      className={cn(
        "relative flex items-start gap-3 rounded-md border p-4 text-sm",
        styles[callout.type],
        className
      )}
      role={callout.type === "error" ? "alert" : "status"}
    >
      <Icon className="mt-0.5 h-4 w-4 flex-shrink-0" />
      <div className="flex-1">{callout.text}</div>
      <button
        onClick={handleDismiss}
        className="flex-shrink-0 rounded-sm p-0.5 hover:bg-black/10"
        aria-label="Dismiss"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
