"use client";

import { useState, useEffect, useCallback } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Play,
  RotateCcw,
  Database,
  Terminal,
  Power,
} from "lucide-react";
import { apiGet, apiPost, type HealthSummary, type ServiceHealth } from "@/lib/api";
import { PageIntro } from "@/components/common/PageIntro";
import { Callout } from "@/components/common/Callout";
import { CliEquivalent } from "@/components/common/CliEquivalent";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  const [startingService, setStartingService] = useState<string | null>(null);
  const [serviceMessages, setServiceMessages] = useState<Record<string, string>>({});
  const [autoStarting, setAutoStarting] = useState(false);
  const [autoStartAttempted, setAutoStartAttempted] = useState(false);

  const fetchHealth = useCallback(async (clearMessages = false) => {
    setLoading(true);
    setError(null);
    if (clearMessages) {
      setServiceMessages({});
    }
    try {
      const data = await apiGet<HealthSummary>("/health");
      setHealth(data);
      // Clear service messages for services that are now healthy
      setServiceMessages((prev) => {
        const updated = { ...prev };
        for (const service of data.services) {
          if (service.status === "healthy" && updated[service.name]) {
            delete updated[service.name];
          }
        }
        return updated;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch health");
    } finally {
      setLoading(false);
    }
  }, []);

  const autoStartRequiredServices = useCallback(async () => {
    setAutoStarting(true);
    try {
      const result = await apiPost<{
        auto_started: string[];
        summary: { attempted_start: number; needs_start: string[] };
      }>("/services/auto-start-required");

      if (result.summary.attempted_start > 0) {
        const messages: Record<string, string> = {};
        for (const serviceName of result.auto_started) {
          messages[serviceName] = "Auto-started. Health will update shortly.";
        }
        setServiceMessages(messages);
      }
    } catch {
      // Auto-start failed silently — user can manually start via button
    } finally {
      setAutoStarting(false);
      setAutoStartAttempted(true);
      await fetchHealth();
    }
  }, [fetchHealth]);

  useEffect(() => {
    // On initial load, fetch health first
    fetchHealth().then(() => {
      // Then attempt auto-start of required services if needed (only once)
      if (!autoStartAttempted) {
        autoStartRequiredServices();
      }
    });
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFullReset = async () => {
    const confirmed = window.confirm(
      "Full environment reset. This will delete ALL data and rebuild from committed fixtures. Continue?"
    );
    if (!confirmed) return;
    const typed = window.prompt('Type "RESET" to confirm:');
    if (typed !== "RESET") return;

    setResetting(true);
    try {
      await apiPost("/reset/full");
      await fetchHealth();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setResetting(false);
    }
  };

  const handleStartService = async (serviceName: string) => {
    setStartingService(serviceName);
    setServiceMessages((prev) => ({ ...prev, [serviceName]: "Starting..." }));
    try {
      const result = await apiPost<{ success: boolean; message: string; started: boolean }>(
        `/services/${serviceName}/start`
      );
      setServiceMessages((prev) => ({ ...prev, [serviceName]: result.message }));
      if (result.started) {
        await fetchHealth();
      }
    } catch (err) {
      setServiceMessages((prev) => ({
        ...prev,
        [serviceName]: err instanceof Error ? err.message : "Failed to start service",
      }));
    } finally {
      setStartingService(null);
    }
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case "unhealthy":
        return <XCircle className="h-5 w-5 text-red-600" />;
      case "disabled":
        return <AlertCircle className="h-5 w-5 text-yellow-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-400" />;
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "border-green-200 bg-green-50";
      case "unhealthy":
        return "border-red-200 bg-red-50";
      case "disabled":
        return "border-yellow-200 bg-yellow-50";
      default:
        return "border-gray-200 bg-gray-50";
    }
  };

  return (
    <div className="space-y-6">
      <PageIntro page="dashboard" />

      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <div className="flex gap-2">
          <button
            onClick={() => fetchHealth(true)}
            className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium hover:bg-accent"
          >
            <RotateCcw className="h-4 w-4" />
            Refresh Health
          </button>
          <button
            onClick={handleFullReset}
            disabled={resetting}
            className="flex items-center gap-2 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
          >
            {resetting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RotateCcw className="h-4 w-4" />
            )}
            Reset Demo Environment
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          Error: {error}
        </div>
      )}

      {/* Service Health Cards */}
      <div>
        <h3 className="mb-3 text-lg font-semibold">Service Health</h3>
        {loading && !health ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Checking services...
          </div>
        ) : (
          <>
            {autoStarting && (
              <div className="mb-3 flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
                <Loader2 className="h-4 w-4 animate-spin" />
                Auto-starting required services (PostgreSQL, Neo4j, Pricing API)...
              </div>
            )}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
            {health?.services
              .filter((service: ServiceHealth) => service.name !== "foundry-local")
              .map((service: ServiceHealth) => (
              <div
                key={service.name}
                className={cn(
                  "rounded-md border p-4",
                  statusColor(service.status)
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {statusIcon(service.status)}
                    <span className="font-medium">{service.name}</span>
                    {service.required && (
                      <span className="rounded bg-gray-200 px-1.5 py-0.5 text-xs text-gray-700">
                        Required
                      </span>
                    )}
                  </div>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  {service.detail}
                </p>
                {service.remediation && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs font-medium text-blue-600">
                      How to fix
                    </summary>
                    <p className="mt-1 rounded bg-white/50 p-2 text-xs">
                      {service.remediation}
                    </p>
                  </details>
                )}
                {(service.status === "unhealthy" || service.status === "disabled") &&
                  service.name !== "foundry-local" && (
                    <button
                      onClick={() => handleStartService(service.name)}
                      disabled={startingService === service.name}
                      className="mt-2 flex items-center gap-1.5 rounded-md border border-blue-300 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50"
                    >
                      {startingService === service.name ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Power className="h-3.5 w-3.5" />
                      )}
                      {startingService === service.name ? "Starting..." : "Start Service"}
                    </button>
                  )}
                {serviceMessages[service.name] && (
                  <p className="mt-1 rounded bg-white/50 p-2 text-xs text-blue-700">
                    {serviceMessages[service.name]}
                  </p>
                )}
              </div>
            ))}
          </div>
          </>
        )}
      </div>

      {/* Quick Actions */}
      <div>
        <h3 className="mb-3 text-lg font-semibold">Quick Actions</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <a
            href="/retrieval"
            className="flex items-center gap-3 rounded-md border p-4 hover:bg-accent"
          >
            <Play className="h-5 w-5 text-blue-600" />
            <div>
              <p className="font-medium">Run Curated Demo</p>
              <p className="text-xs text-muted-foreground">
                Execute Phase 2 demo queries
              </p>
            </div>
          </a>
          <a
            href="/data"
            className="flex items-center gap-3 rounded-md border p-4 hover:bg-accent"
          >
            <Database className="h-5 w-5 text-green-600" />
            <div>
              <p className="font-medium">Browse Data</p>
              <p className="text-xs text-muted-foreground">
                Vendors, subscriptions, documents
              </p>
            </div>
          </a>
          <a
            href="/cli"
            className="flex items-center gap-3 rounded-md border p-4 hover:bg-accent"
          >
            <Terminal className="h-5 w-5 text-purple-600" />
            <div>
              <p className="font-medium">CLI Launcher</p>
              <p className="text-xs text-muted-foreground">
                Run CLI commands from UI
              </p>
            </div>
          </a>
        </div>
      </div>

      {/* Placeholder mode callout */}
      {health?.summary.disabled && health.summary.disabled > 0 && (
        <Callout calloutId="placeholder_mode" />
      )}

      {/* Reset CLI equivalent */}
      <CliEquivalent command="./scripts/reset-demo-environment.ps1" />
    </div>
  );
}
