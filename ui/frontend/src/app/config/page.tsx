"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, Settings, Power, AlertTriangle } from "lucide-react";
import { apiGet, apiPost, type ConfigResponse, type ConfigParameter } from "@/lib/api";
import { PageIntro } from "@/components/common/PageIntro";
import { Tooltip } from "@/components/common/Tooltip";
import { Callout } from "@/components/common/Callout";
import { CliEquivalent } from "@/components/common/CliEquivalent";

interface ProviderInfo {
  current: {
    model_provider: string;
    embedding_provider: string;
    foundry_local_endpoint: string | null;
    openai_configured: boolean;
    openai_model: string;
  };
  available_model_providers: Array<{
    value: string;
    label: string;
    description: string;
    requires_api_key: boolean;
    requires_local_runtime: boolean;
  }>;
  available_embedding_providers: Array<{
    value: string;
    label: string;
    description: string;
    requires_api_key: boolean;
  }>;
}

export default function ConfigPage() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [switching, setSwitching] = useState(false);
  const [switchMessage, setSwitchMessage] = useState<string | null>(null);
  const [switchWarnings, setSwitchWarnings] = useState<string[]>([]);
  const [openaiKey, setOpenaiKey] = useState("");
  const [showKeyInput, setShowKeyInput] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [configRes, providerRes] = await Promise.all([
        apiGet<ConfigResponse>("/config"),
        apiGet<ProviderInfo>("/provider"),
      ]);
      setConfig(configRes);
      setProviderInfo(providerRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load config");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleSwitchProvider = async (
    type: "model" | "embedding",
    provider: string
  ) => {
    // Check if OpenAI key is needed
    const needsKey =
      provider === "openai" && !providerInfo?.current.openai_configured;
    if (needsKey && !openaiKey.trim()) {
      setShowKeyInput(true);
      setSwitchMessage("OpenAI API key is required to switch to the OpenAI provider. Please enter your key below.");
      return;
    }

    setSwitching(true);
    setSwitchMessage(null);
    setSwitchWarnings([]);
    setError(null);

    try {
      const body: Record<string, unknown> = {};
      if (type === "model") body.model_provider = provider;
      if (type === "embedding") body.embedding_provider = provider;
      if (openaiKey.trim()) body.openai_api_key = openaiKey.trim();

      const result = await apiPost<{
        success: boolean;
        message: string;
        warnings: string[];
      }>("/provider/switch", body);

      setSwitchMessage(result.message);
      setSwitchWarnings(result.warnings || []);
      setOpenaiKey("");
      setShowKeyInput(false);
      await fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to switch provider");
    } finally {
      setSwitching(false);
    }
  };

  if (loading)
    return (
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading configuration...
      </div>
    );

  if (error && !config)
    return (
      <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
        Error: {error}
      </div>
    );

  if (!config || !providerInfo) return null;

  const categories = Object.entries(config.categories).sort(([a], [b]) =>
    a.localeCompare(b)
  );

  return (
    <div className="space-y-6">
      <PageIntro page="config" />

      <div className="flex items-center gap-2">
        <Settings className="h-5 w-5" />
        <h2 className="text-2xl font-bold">Configuration</h2>
      </div>

      {/* Provider status summary */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="rounded-md border p-3">
          <p className="text-xs text-muted-foreground">Model Provider</p>
          <p className="font-medium">{config.model_provider}</p>
        </div>
        <div className="rounded-md border p-3">
          <p className="text-xs text-muted-foreground">Embedding Provider</p>
          <p className="font-medium">{config.embedding_provider}</p>
        </div>
        <div className="rounded-md border p-3">
          <p className="text-xs text-muted-foreground">Phoenix</p>
          <p className="font-medium">{config.phoenix_enabled ? "Enabled" : "Disabled"}</p>
        </div>
        <div className="rounded-md border p-3">
          <p className="text-xs text-muted-foreground">Langfuse</p>
          <p className="font-medium">{config.langfuse_enabled ? "Enabled" : "Disabled"}</p>
        </div>
      </div>

      {config.model_provider === "placeholder" && <Callout calloutId="placeholder_mode" />}

      {/* Provider Switcher */}
      <div className="rounded-md border p-4">
        <h3 className="mb-3 text-sm font-medium">
          <Tooltip term="model_provider">Model Provider Switcher</Tooltip>
        </h3>
        <p className="mb-3 text-xs text-muted-foreground">
          Switch between providers to use different AI models for workflow execution.
          Previous observability data is preserved and tagged with the previous provider.
        </p>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
          {providerInfo.available_model_providers.map((p) => {
            const isActive = providerInfo.current.model_provider === p.value;
            const isDisabled = switching || (p.requires_api_key && !providerInfo.current.openai_configured && !openaiKey.trim() && p.value === "openai");
            return (
              <button
                key={p.value}
                onClick={() => !isActive && handleSwitchProvider("model", p.value)}
                disabled={isActive || isDisabled}
                className={`rounded-md border p-3 text-left transition-colors ${
                  isActive
                    ? "border-primary bg-primary/5"
                    : "hover:bg-accent"
                } ${isDisabled ? "cursor-not-allowed opacity-50" : ""}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{p.label}</span>
                  {isActive && (
                    <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-800">Active</span>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{p.description}</p>
                {p.requires_api_key && !providerInfo.current.openai_configured && (
                  <p className="mt-1 text-xs text-yellow-700">⚠️ Requires API key</p>
                )}
              </button>
            );
          })}
        </div>

        {/* OpenAI key input */}
        {showKeyInput && (
          <div className="mt-3 rounded-md border border-yellow-200 bg-yellow-50 p-3">
            <label className="mb-1 block text-xs font-medium text-yellow-900">
              OpenAI API Key
            </label>
            <input
              type="password"
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full rounded-md border p-2 text-sm"
            />
            <div className="mt-2 flex gap-2">
              <button
                onClick={() => handleSwitchProvider("model", "openai")}
                disabled={!openaiKey.trim() || switching}
                className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {switching ? "Switching..." : "Switch to OpenAI"}
              </button>
              <button
                onClick={() => { setShowKeyInput(false); setOpenaiKey(""); setSwitchMessage(null); }}
                className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Embedding Provider Switcher */}
        <h3 className="mb-3 mt-6 text-sm font-medium">
          <Tooltip term="embedding_provider">Embedding Provider Switcher</Tooltip>
        </h3>
        <p className="mb-3 text-xs text-muted-foreground">
          Switch between embedding providers for vector search. Note: changing embedding dimensions
          requires a schema migration and re-ingestion.
        </p>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
          {providerInfo.available_embedding_providers.map((p) => {
            const isActive = providerInfo.current.embedding_provider === p.value;
            return (
              <button
                key={p.value}
                onClick={() => !isActive && handleSwitchProvider("embedding", p.value)}
                disabled={isActive || switching}
                className={`rounded-md border p-3 text-left transition-colors ${
                  isActive
                    ? "border-primary bg-primary/5"
                    : "hover:bg-accent"
                } ${switching ? "cursor-not-allowed opacity-50" : ""}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{p.label}</span>
                  {isActive && (
                    <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-800">Active</span>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{p.description}</p>
              </button>
            );
          })}
        </div>

        {/* Switch messages */}
        {switchMessage && (
          <div className="mt-3 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
            {switchMessage}
          </div>
        )}
        {switchWarnings.map((w, i) => (
          <div key={i} className="mt-2 flex items-start gap-2 rounded-md border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-900">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <span>{w}</span>
          </div>
        ))}
        {error && (
          <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900">
            {error}
          </div>
        )}

        <CliEquivalent command="MODEL_PROVIDER=placeholder  # (or microsoft-foundry-local, openai) in .env" />
      </div>

      {/* Config parameters by category */}
      {categories.map(([category, params]) => (
        <div key={category}>
          <h3 className="mb-3 text-lg font-semibold">{category}</h3>
          <div className="overflow-hidden rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium">Parameter</th>
                  <th className="px-4 py-2 text-left font-medium">Value</th>
                  <th className="px-4 py-2 text-left font-medium">Description</th>
                </tr>
              </thead>
              <tbody>
                {params.map((param: ConfigParameter) => (
                  <tr key={param.name} className="border-t">
                    <td className="px-4 py-2 font-mono text-xs">
                      <Tooltip term={param.name}>{param.name}</Tooltip>
                    </td>
                    <td className="px-4 py-2 font-mono text-xs">
                      {param.is_none ? (
                        <span className="text-muted-foreground">None</span>
                      ) : param.sensitive ? (
                        <span className="text-yellow-700">{param.value}</span>
                      ) : (
                        param.value
                      )}
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground">
                      {param.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
