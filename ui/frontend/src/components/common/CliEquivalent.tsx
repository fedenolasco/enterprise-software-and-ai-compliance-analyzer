"use client";

import { useState, useEffect } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getGuidancePreferences,
  shouldShowCliEquivalent,
  type GuidancePreferences,
} from "@/lib/guidance-preferences";

interface CliEquivalentProps {
  command: string;
  className?: string;
}

export function CliEquivalent({ command, className }: CliEquivalentProps) {
  const [prefs, setPrefs] = useState<GuidancePreferences | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setPrefs(getGuidancePreferences());
  }, []);

  if (!prefs || !shouldShowCliEquivalent(prefs)) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-2 rounded-md border bg-muted/50 px-3 py-2",
        className
      )}
    >
      <div className="flex items-center gap-2 overflow-hidden">
        <span className="flex-shrink-0 text-xs font-medium text-muted-foreground">
          CLI equivalent:
        </span>
        <code className="font-mono text-xs text-muted-foreground">{command}</code>
      </div>
      <button
        onClick={handleCopy}
        className="flex-shrink-0 rounded-sm p-1 hover:bg-accent"
        aria-label="Copy command"
      >
        {copied ? (
          <Check className="h-3.5 w-3.5 text-green-600" />
        ) : (
          <Copy className="h-3.5 w-3.5 text-muted-foreground" />
        )}
      </button>
    </div>
  );
}
