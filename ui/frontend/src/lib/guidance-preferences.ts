/**
 * Guidance preferences stored in localStorage.
 */

export type GuidanceDetailLevel = "full" | "essential" | "minimal";

export interface GuidancePreferences {
  showOnboardingTour: boolean;
  showPageIntros: boolean;
  showInlineTooltips: boolean;
  showWhyThisMattersCallouts: boolean;
  showWorkflowStepper: boolean;
  showCliEquivalentCommands: boolean;
  guidanceDetailLevel: GuidanceDetailLevel;
  dismissedCallouts: string[];
  tourCompleted: boolean;
}

const STORAGE_KEY = "ui-guidance-preferences";

const defaultPreferences: GuidancePreferences = {
  showOnboardingTour: true,
  showPageIntros: true,
  showInlineTooltips: true,
  showWhyThisMattersCallouts: true,
  showWorkflowStepper: true,
  showCliEquivalentCommands: true,
  guidanceDetailLevel: "full",
  dismissedCallouts: [],
  tourCompleted: false,
};

export function getGuidancePreferences(): GuidancePreferences {
  if (typeof window === "undefined") return defaultPreferences;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return defaultPreferences;
    return { ...defaultPreferences, ...JSON.parse(stored) };
  } catch {
    return defaultPreferences;
  }
}

export function saveGuidancePreferences(prefs: GuidancePreferences): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
}

export function updateGuidancePreference(
  key: keyof GuidancePreferences,
  value: unknown
): GuidancePreferences {
  const prefs = getGuidancePreferences();
  const updated = { ...prefs, [key]: value };
  saveGuidancePreferences(updated);
  return updated;
}

export function dismissCallout(calloutId: string): GuidancePreferences {
  const prefs = getGuidancePreferences();
  if (!prefs.dismissedCallouts.includes(calloutId)) {
    prefs.dismissedCallouts.push(calloutId);
    saveGuidancePreferences(prefs);
  }
  return prefs;
}

export function resetDismissedCallouts(): GuidancePreferences {
  const prefs = getGuidancePreferences();
  prefs.dismissedCallouts = [];
  saveGuidancePreferences(prefs);
  return prefs;
}

export function resetToDefaults(): GuidancePreferences {
  saveGuidancePreferences(defaultPreferences);
  return defaultPreferences;
}

// Critical callouts that cannot be dismissed
export const criticalCallouts = new Set([
  "finalization_blocked",
  "embedding_dimension_mismatch",
  "full_reset",
]);

export function shouldShowCallout(
  calloutId: string,
  prefs: GuidancePreferences
): boolean {
  if (criticalCallouts.has(calloutId)) return true;
  if (prefs.guidanceDetailLevel === "minimal") return false;
  if (prefs.dismissedCallouts.includes(calloutId)) return false;
  return prefs.showWhyThisMattersCallouts;
}

export function shouldShowTooltip(prefs: GuidancePreferences): boolean {
  if (prefs.guidanceDetailLevel === "minimal") return false;
  return prefs.showInlineTooltips;
}

export function shouldShowPageIntro(prefs: GuidancePreferences): boolean {
  if (prefs.guidanceDetailLevel !== "full") return false;
  return prefs.showPageIntros;
}

export function shouldShowCliEquivalent(prefs: GuidancePreferences): boolean {
  if (prefs.guidanceDetailLevel === "minimal") return false;
  return prefs.showCliEquivalentCommands;
}
