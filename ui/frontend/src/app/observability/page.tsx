"use client";

import { useState, useEffect } from "react";
import { Loader2, Activity, Trash2 } from "lucide-react";
import { apiGet, apiDelete, type AuditEvent } from "@/lib/api";
import { PageIntro } from "@/components/common/PageIntro";
import { Callout } from "@/components/common/Callout";

interface ComparisonRow {
  provider: string;
  workflow_runs: number;
  prompt_tokens: number;
  completion_tokens: number;
  simulated_cost: number;
  hitl_approvals: number;
  safety_flags_raised: number;
}

export default function ObservabilityPage() {
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [comparison, setComparison] = useState<ComparisonRow[]>([]);
  const [providers, setProviders] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"audit" | "comparison" | "traces" | "usage">("audit");

  const fetchData = async (provider?: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const [auditRes, compRes, provRes] = await Promise.all([
        apiGet<{ audit_events: AuditEvent[] }>(
          `/observability/audit${provider ? `?provider=${provider}` : ""}`
        ).catch(() => ({ audit_events: [] })),
        apiGet<{ comparison: ComparisonRow[] }>("/observability/comparison").catch(() => ({
          comparison: [],
        })),
        apiGet<{ providers: string[] }>("/observability/providers").catch(() => ({
          providers: [],
        })),
      ]);
      setAuditEvents(auditRes.audit_events);
      setComparison(compRes.comparison);
      setProviders(provRes.providers);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load observability data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleProviderFilter = (provider: string | null) => {
    setSelectedProvider(provider);
    fetchData(provider);
  };

  const handleClearAudit = async () => {
    if (!window.confirm("Clear all audit events? This cannot be undone.")) return;
    try {
      await apiDelete(`/observability/audit${selectedProvider ? `?provider=${selectedProvider}` : ""}`);
      fetchData(selectedProvider);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clear audit events");
    }
  };

  if (loading)
    return (
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading observability data...
      </div>
    );

  return (
    <div className="space-y-6">
      <PageIntro page="observability" />

      <div className="flex items-center gap-2">
        <Activity className="h-5 w-5" />
        <h2 className="text-2xl font-bold">Observability & Governance</h2>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          {error}
        </div>
      )}

      {/* Provider filter */}
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">Provider:</span>
        <button
          onClick={() => handleProviderFilter(null)}
          className={`rounded-md border px-3 py-1 text-xs ${
            !selectedProvider ? "bg-primary text-primary-foreground" : "hover:bg-accent"
          }`}
        >
          All
        </button>
        {providers.map((p) => (
          <button
            key={p}
            onClick={() => handleProviderFilter(p)}
            className={`rounded-md border px-3 py-1 text-xs ${
              selectedProvider === p ? "bg-primary text-primary-foreground" : "hover:bg-accent"
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {(["audit", "comparison", "traces", "usage"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`border-b-2 px-4 py-2 text-sm font-medium capitalize ${
              activeTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Audit events tab */}
      {activeTab === "audit" && (
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold">Audit Events ({auditEvents.length})</h3>
            <button
              onClick={handleClearAudit}
              className="flex items-center gap-1.5 rounded-md border border-red-300 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear Audit Events
            </button>
          </div>
          <div className="overflow-x-auto rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-3 py-2 text-left">Type</th>
                  <th className="px-3 py-2 text-left">Status</th>
                  <th className="px-3 py-2 text-left">Trace ID</th>
                  <th className="px-3 py-2 text-left">Message</th>
                  <th className="px-3 py-2 text-left">Created</th>
                </tr>
              </thead>
              <tbody>
                {auditEvents.map((e, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-3 py-2 text-xs font-mono">{e.eventType}</td>
                    <td className="px-3 py-2">
                      <span className={`rounded px-2 py-0.5 text-xs ${
                        e.status === "SUCCESS" ? "bg-green-100 text-green-800" :
                        e.status === "PENDING" ? "bg-yellow-100 text-yellow-800" :
                        "bg-red-100 text-red-800"
                      }`}>
                        {e.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{e.traceId}</td>
                    <td className="px-3 py-2 text-xs">{e.message}</td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">{e.createdAt}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Comparison tab */}
      {activeTab === "comparison" && (
        <div>
          {comparison.length > 0 && <Callout calloutId="provider_comparison" />}
          <h3 className="mb-3 text-lg font-semibold">Provider Comparison</h3>
          <div className="overflow-x-auto rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-3 py-2 text-left">Provider</th>
                  <th className="px-3 py-2 text-right">Workflow Runs</th>
                  <th className="px-3 py-2 text-right">Prompt Tokens</th>
                  <th className="px-3 py-2 text-right">Completion Tokens</th>
                  <th className="px-3 py-2 text-right">Simulated Cost</th>
                  <th className="px-3 py-2 text-right">HITL Approvals</th>
                  <th className="px-3 py-2 text-right">Safety Flags</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((row, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-3 py-2 font-medium">{row.provider}</td>
                    <td className="px-3 py-2 text-right font-mono">{row.workflow_runs}</td>
                    <td className="px-3 py-2 text-right font-mono">{row.prompt_tokens}</td>
                    <td className="px-3 py-2 text-right font-mono">{row.completion_tokens}</td>
                    <td className="px-3 py-2 text-right font-mono">${row.simulated_cost.toFixed(4)}</td>
                    <td className="px-3 py-2 text-right font-mono">{row.hitl_approvals}</td>
                    <td className="px-3 py-2 text-right font-mono">{row.safety_flags_raised}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Traces tab */}
      {activeTab === "traces" && (
        <div>
          <h3 className="mb-3 text-lg font-semibold">Phoenix Traces</h3>
          <p className="text-sm text-muted-foreground">
            Phoenix trace data is available when Phoenix is enabled. Visit the Phoenix UI at
            localhost:6006 for full trace visualization.
          </p>
        </div>
      )}

      {/* Usage tab */}
      {activeTab === "usage" && (
        <div>
          <h3 className="mb-3 text-lg font-semibold">Langfuse Usage Events</h3>
          <p className="text-sm text-muted-foreground">
            Langfuse usage data is available when Langfuse is enabled. Visit the Langfuse UI at
            localhost:3000 for full usage visualization.
          </p>
        </div>
      )}
    </div>
  );
}
