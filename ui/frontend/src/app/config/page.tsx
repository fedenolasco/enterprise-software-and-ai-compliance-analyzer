"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Loader2, Settings, Power, AlertTriangle, Key, Trash2 } from "lucide-react";
import { apiGet, apiPost, apiPut, apiDelete, type ConfigResponse, type ConfigParameter } from "@/lib/api";
import { PageIntro } from "@/components/common/PageIntro";
import { Tooltip } from "@/components/common/Tooltip";
import { Callout } from "@/components/common/Callout";

const DEFAULT_FOUNDRY_CACHE_DIR = "C:\\Users\\feden\\.foundry\\cache\\models";

interface ProviderInfo {
  current: {
    model_provider: string;
    embedding_provider: string;
    foundry_local_endpoint: string | null;
    local_model_name: string;
    openvino_endpoint: string;
    openvino_model: string;
    openvino_embedding_model: string;
    openvino_device: string;
    hf_configured: boolean;
    hf_token_masked: string | null;
    openai_configured: boolean;
    openai_key_masked: string | null;
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
  foundry_local_models: Array<{
    alias: string;
    label: string;
    description: string;
    device: string;
  }>;
  openvino_models: Array<{
    alias: string;
    label: string;
    description: string;
    device: string;
  }>;
  openvino_embedding_models: Array<{
    alias: string;
    label: string;
    description: string;
    device: string;
    dimension: string;
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
  // OpenAI settings management
  const [openaiSettingsKey, setOpenaiSettingsKey] = useState("");
  const [openaiSettingsModel, setOpenaiSettingsModel] = useState("");
  const [savingOpenAI, setSavingOpenAI] = useState(false);
  const [openAIMessage, setOpenAIMessage] = useState<string | null>(null);
  const [openAIError, setOpenAIError] = useState<string | null>(null);
  // Foundry Local model management
  const [foundryModel, setFoundryModel] = useState("");
  const [savingFoundryModel, setSavingFoundryModel] = useState(false);
  const [foundryModelMessage, setFoundryModelMessage] = useState<string | null>(null);
  const [foundryModelError, setFoundryModelError] = useState<string | null>(null);
  const [foundrySteps, setFoundrySteps] = useState<Array<{ step: string; status: string; message: string }>>([]);
  const [downloadingModel, setDownloadingModel] = useState(false);
  const [downloadJobId, setDownloadJobId] = useState<string | null>(null);
  const [downloadStatus, setDownloadStatus] = useState<string | null>(null);
  const [downloadMessage, setDownloadMessage] = useState<string | null>(null);
  const [downloadPercent, setDownloadPercent] = useState(0);
  const [downloadOutput, setDownloadOutput] = useState<string[]>([]);
  const [foundryInstalled, setFoundryInstalled] = useState<boolean | null>(null);
  const [foundryServiceRunning, setFoundryServiceRunning] = useState<boolean>(false);
  const [installingFoundry, setInstallingFoundry] = useState(false);
  const [installMessage, setInstallMessage] = useState<string | null>(null);
  const [installError, setInstallError] = useState<string | null>(null);
  const [installInstructions, setInstallInstructions] = useState<string | null>(null);
  const [installCommand, setInstallCommand] = useState<string | null>(null);
  const [foundryCacheDir, setFoundryCacheDir] = useState<string>("");
  const [newCacheDir, setNewCacheDir] = useState("");
  const [savingCacheDir, setSavingCacheDir] = useState(false);
  const [cacheDirMessage, setCacheDirMessage] = useState<string | null>(null);
  const [cacheDirError, setCacheDirError] = useState<string | null>(null);
  const _cacheDirInputRef = useRef<HTMLInputElement | null>(null);
  // OpenVINO Model Server management
  const [openvinoEndpoint, setOpenvinoEndpoint] = useState("");
  const [openvinoModel, setOpenvinoModel] = useState("");
  const [openvinoEmbeddingModel, setOpenvinoEmbeddingModel] = useState("");
  const [openvinoDevice, setOpenvinoDevice] = useState("NPU");
  const [hfToken, setHfToken] = useState("");
  const [savingOpenVINO, setSavingOpenVINO] = useState(false);
  const [openvinoMessage, setOpenvinoMessage] = useState<string | null>(null);
  const [openvinoError, setOpenvinoError] = useState<string | null>(null);
  const [openvinoRunning, setOpenvinoRunning] = useState<boolean | null>(null);
  const [downloadingOpenVINO, setDownloadingOpenVINO] = useState(false);
  const [openvinoDownloadJobId, setOpenvinoDownloadJobId] = useState<string | null>(null);
  const [openvinoDownloadMessage, setOpenvinoDownloadMessage] = useState<string | null>(null);

  const fetchAll = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
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
      if (!silent) setLoading(false);
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

    // Show a specific message when switching to Foundry Local (may take a few seconds to auto-start)
    if (provider === "microsoft-foundry-local") {
      setSwitchMessage("Switching to Foundry Local — starting service if needed, this may take a few seconds...");
    }
    if (provider === "openvino") {
      setSwitchMessage("Switching to OpenVINO Model Server. Start OVMS locally before running text generation or embeddings.");
    }

    try {
      const body: Record<string, unknown> = {};
      if (type === "model") body.model_provider = provider;
      if (type === "embedding") body.embedding_provider = provider;
      if (openaiKey.trim()) body.openai_api_key = openaiKey.trim();

      const result = await apiPost<{
        success: boolean;
        message: string;
        warnings: string[];
        foundry_auto_started: boolean;
      }>("/provider/switch", body);

      // Build a message that includes Foundry Local auto-start info
      let msg = result.message;
      if (result.foundry_auto_started) {
        msg += " Foundry Local service was auto-started.";
      }
      setSwitchMessage(msg);
      setSwitchWarnings(result.warnings || []);
      setOpenaiKey("");
      setShowKeyInput(false);
      await fetchAll(true);
      // Re-check Foundry status after switching to update the install/service indicators.
      // The service may take a few seconds to become responsive after auto-start,
      // so we retry the status check after a short delay.
      if (provider === "microsoft-foundry-local") {
        handleCheckFoundryStatus();
        // Retry after 5 seconds in case the service was still initializing
        setTimeout(() => handleCheckFoundryStatus(), 5000);
      }
      if (provider === "openvino") {
        handleCheckOpenVINOStatus();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to switch provider");
    } finally {
      setSwitching(false);
    }
  };

  const handleSaveOpenAISettings = async () => {
    setSavingOpenAI(true);
    setOpenAIMessage(null);
    setOpenAIError(null);
    try {
      const body: Record<string, string> = {};
      if (openaiSettingsKey.trim()) body.openai_api_key = openaiSettingsKey.trim();
      if (openaiSettingsModel.trim()) body.openai_model = openaiSettingsModel.trim();

      if (Object.keys(body).length === 0) {
        setOpenAIError("Enter a new API key and/or model name to update.");
        return;
      }

      const result = await apiPut<{
        success: boolean;
        message: string;
        openai_configured: boolean;
        openai_key_masked: string | null;
        openai_model: string;
      }>("/provider/openai-settings", body);

      setOpenAIMessage(result.message);
      setOpenaiSettingsKey("");
      setOpenaiSettingsModel("");
      await fetchAll(true);
    } catch (err) {
      setOpenAIError(err instanceof Error ? err.message : "Failed to update OpenAI settings");
    } finally {
      setSavingOpenAI(false);
    }
  };

  const handleRemoveOpenAIKey = async () => {
    setSavingOpenAI(true);
    setOpenAIMessage(null);
    setOpenAIError(null);
    try {
      const result = await apiDelete<{
        success: boolean;
        message: string;
        openai_configured: boolean;
        openai_model: string;
      }>("/provider/openai-key");

      setOpenAIMessage(result.message);
      await fetchAll(true);
    } catch (err) {
      setOpenAIError(err instanceof Error ? err.message : "Failed to remove OpenAI API key");
    } finally {
      setSavingOpenAI(false);
    }
  };

  const handleSaveFoundryModel = async () => {
    setSavingFoundryModel(true);
    setFoundryModelMessage(null);
    setFoundryModelError(null);
    setFoundrySteps([]);
    try {
      const result = await apiPut<{
        success: boolean;
        message: string;
        local_model_name: string;
        warning: string | null;
        warnings: string[];
        steps: Array<{ step: string; status: string; message: string }>;
        service_running: boolean;
        model_downloaded: boolean;
      }>("/provider/foundry-model", { local_model_name: foundryModel.trim() });

      setFoundryModelMessage(result.message);
      setFoundrySteps(result.steps || []);
      if (result.warnings && result.warnings.length > 0) {
        setFoundryModelError(result.warnings.join(" "));
      } else if (result.warning) {
        setFoundryModelError(result.warning);
      }
      setFoundryModel("");
      await fetchAll(true);
    } catch (err) {
      setFoundryModelError(err instanceof Error ? err.message : "Failed to update Foundry Local model");
    } finally {
      setSavingFoundryModel(false);
    }
  };

  const handleDownloadFoundryModel = async () => {
    const model = foundryModel.trim();
    if (!model) {
      setFoundryModelError("Select a verified Foundry Local model alias to download.");
      return;
    }

    setDownloadingModel(true);
    setDownloadJobId(null);
    setDownloadStatus("queued");
    setDownloadMessage(`Starting download for ${model}...`);
    setDownloadPercent(0);
    setDownloadOutput([]);
    setFoundryModelError(null);
    setFoundryModelMessage(null);

    try {
      const result = await apiPost<{
        job_id: string;
        status: string;
        message: string;
        percent: number;
        model: string;
        output: string[];
      }>("/provider/foundry-model/download", { local_model_name: model });

      setDownloadJobId(result.job_id || null);
      setDownloadStatus(result.status);
      setDownloadMessage(result.message);
      setDownloadPercent(result.percent || 0);
      setDownloadOutput(result.output || []);
      if (result.status === "complete") {
        setDownloadingModel(false);
        setFoundryModelMessage(result.message);
      }
    } catch (err) {
      setDownloadingModel(false);
      setDownloadStatus("error");
      setFoundryModelError(err instanceof Error ? err.message : "Failed to start model download");
    }
  };

  useEffect(() => {
    if (!downloadJobId || !downloadingModel) return;

    const interval = window.setInterval(async () => {
      try {
        const result = await apiGet<{
          job_id: string;
          status: string;
          message: string;
          percent: number;
          model: string;
          output: string[];
        }>(`/provider/foundry-model/download/${downloadJobId}`);

        setDownloadStatus(result.status);
        setDownloadMessage(result.message);
        setDownloadPercent(result.percent || 0);
        setDownloadOutput(result.output || []);

        if (result.status === "complete") {
          setDownloadingModel(false);
          setFoundryModelMessage(result.message);
          await fetchAll(true);
          window.clearInterval(interval);
        }
        if (result.status === "error") {
          setDownloadingModel(false);
          setFoundryModelError(result.message);
          window.clearInterval(interval);
        }
      } catch (err) {
        setDownloadingModel(false);
        setDownloadStatus("error");
        setFoundryModelError(err instanceof Error ? err.message : "Failed to fetch model download status");
        window.clearInterval(interval);
      }
    }, 1000);

    return () => window.clearInterval(interval);
  }, [downloadJobId, downloadingModel, fetchAll]);

  const handleCheckFoundryStatus = useCallback(async () => {
    try {
      const result = await apiGet<{
        installed: boolean;
        service_running: boolean;
        endpoint: string | null;
        platform: string;
        install_command: string;
        install_instructions: string;
        cache_dir: string;
      }>("/provider/foundry-status");
      setFoundryInstalled(result.installed);
      setFoundryServiceRunning(result.service_running);
      setInstallCommand(result.install_command);
      setInstallInstructions(result.install_instructions);
      setFoundryCacheDir(result.cache_dir || "");
    } catch {
      setFoundryInstalled(false);
    }
  }, []);

  const handleSaveCacheDir = async () => {
    setSavingCacheDir(true);
    setCacheDirMessage(null);
    setCacheDirError(null);
    try {
      const result = await apiPut<{
        success: boolean;
        message: string;
        cache_dir: string;
      }>("/provider/foundry-cache", { cache_dir: newCacheDir.trim() });
      setCacheDirMessage(result.message);
      setFoundryCacheDir(result.cache_dir);
      setNewCacheDir("");
    } catch (err) {
      setCacheDirError(err instanceof Error ? err.message : "Failed to update cache directory");
    } finally {
      setSavingCacheDir(false);
    }
  };

  const handleInstallFoundry = async () => {
    setInstallingFoundry(true);
    setInstallMessage(null);
    setInstallError(null);
    try {
      const result = await apiPost<{
        success: boolean;
        message: string;
        output: string;
        installed: boolean;
      }>("/provider/foundry-install", {});
      if (result.success) {
        setInstallMessage(result.message);
        setFoundryInstalled(true);
      } else {
        setInstallError(result.message);
      }
    } catch (err) {
      setInstallError(err instanceof Error ? err.message : "Failed to install Foundry Local");
    } finally {
      setInstallingFoundry(false);
    }
  };

  const handleResetCacheDir = async () => {
    setSavingCacheDir(true);
    setCacheDirMessage(null);
    setCacheDirError(null);
    try {
      const result = await apiPut<{
        success: boolean;
        message: string;
        cache_dir: string;
      }>("/provider/foundry-cache", { cache_dir: DEFAULT_FOUNDRY_CACHE_DIR });
      setCacheDirMessage(`Model cache directory reset to default: ${result.cache_dir}`);
      setFoundryCacheDir(result.cache_dir);
      setNewCacheDir("");
    } catch (err) {
      setCacheDirError(err instanceof Error ? err.message : "Failed to reset cache directory");
    } finally {
      setSavingCacheDir(false);
    }
  };

  const [startingService, setStartingService] = useState(false);
  const [startServiceMessage, setStartServiceMessage] = useState<string | null>(null);
  const [startServiceError, setStartServiceError] = useState<string | null>(null);

  const handleStartFoundryService = async () => {
    setStartingService(true);
    setStartServiceMessage(null);
    setStartServiceError(null);
    try {
      // Use the foundry-model endpoint with the current model name to trigger service start
      const currentModel = providerInfo?.current.local_model_name || "qwen2.5-0.5b";
      const result = await apiPut<{
        success: boolean;
        message: string;
        warnings: string[];
        steps: Array<{ step: string; status: string; message: string }>;
        service_running: boolean;
      }>("/provider/foundry-model", { local_model_name: currentModel });
      if (result.service_running) {
        setStartServiceMessage("Foundry Local service started successfully.");
        setFoundryServiceRunning(true);
      } else if (result.warnings && result.warnings.length > 0) {
        setStartServiceError(result.warnings.join(" "));
      } else {
        setStartServiceError("Service start may still be initializing. Please wait a moment and refresh.");
      }
      await fetchAll(true);
    } catch (err) {
      setStartServiceError(err instanceof Error ? err.message : "Failed to start Foundry Local service");
    } finally {
      setStartingService(false);
    }
  };

  const handleCheckOpenVINOStatus = useCallback(async () => {
    try {
      const result = await apiGet<{
        service_running: boolean;
        endpoint: string;
        model: string;
        embedding_model: string;
        device: string;
        hf_configured: boolean;
      }>("/provider/openvino-status");
      setOpenvinoRunning(result.service_running);
      setOpenvinoEndpoint(result.endpoint || "http://localhost:8100");
      setOpenvinoModel(result.model || "OpenVINO/Qwen3-8B-int4-cw-ov");
      setOpenvinoEmbeddingModel(result.embedding_model || "OpenVINO/Qwen3-Embedding-0.6B");
      setOpenvinoDevice(result.device || "NPU");
    } catch (err) {
      setOpenvinoRunning(false);
      setOpenvinoError(err instanceof Error ? err.message : "Failed to check OpenVINO status");
    }
  }, []);

  const handleSaveOpenVINOSettings = async () => {
    setSavingOpenVINO(true);
    setOpenvinoMessage(null);
    setOpenvinoError(null);
    try {
      const body: Record<string, string> = {
        endpoint: openvinoEndpoint.trim() || providerInfo?.current.openvino_endpoint || "http://localhost:8100",
        model: openvinoModel.trim() || providerInfo?.current.openvino_model || "OpenVINO/Qwen3-8B-int4-cw-ov",
        embedding_model: openvinoEmbeddingModel.trim() || providerInfo?.current.openvino_embedding_model || "OpenVINO/Qwen3-Embedding-0.6B",
        device: openvinoDevice,
      };
      if (hfToken.trim()) body.hf_token = hfToken.trim();
      const result = await apiPut<{ success: boolean; message: string }>("/provider/openvino-settings", body);
      setOpenvinoMessage(result.message);
      setHfToken("");
      await fetchAll(true);
      await handleCheckOpenVINOStatus();
    } catch (err) {
      setOpenvinoError(err instanceof Error ? err.message : "Failed to update OpenVINO settings");
    } finally {
      setSavingOpenVINO(false);
    }
  };

  const handleDownloadOpenVINOModel = async (modelId: string) => {
    setDownloadingOpenVINO(true);
    setOpenvinoDownloadMessage(`Starting Hugging Face download for ${modelId}...`);
    setOpenvinoError(null);
    try {
      const result = await apiPost<{ job_id: string; message: string; status: string }>("/provider/openvino-model/download", { model_id: modelId });
      setOpenvinoDownloadJobId(result.job_id);
      setOpenvinoDownloadMessage(result.message);
    } catch (err) {
      setOpenvinoError(err instanceof Error ? err.message : "Failed to start OpenVINO model download");
      setDownloadingOpenVINO(false);
    }
  };

  useEffect(() => {
    if (!openvinoDownloadJobId || !downloadingOpenVINO) return;
    const interval = window.setInterval(async () => {
      try {
        const result = await apiGet<{ status: string; message: string; path: string | null }>(`/provider/openvino-model/download/${openvinoDownloadJobId}`);
        setOpenvinoDownloadMessage(result.message);
        if (result.status === "complete") {
          setOpenvinoMessage(`${result.message} Cache path: ${result.path}`);
          setDownloadingOpenVINO(false);
          window.clearInterval(interval);
        }
        if (result.status === "error") {
          setOpenvinoError(result.message);
          setDownloadingOpenVINO(false);
          window.clearInterval(interval);
        }
      } catch (err) {
        setOpenvinoError(err instanceof Error ? err.message : "Failed to fetch OpenVINO download status");
        setDownloadingOpenVINO(false);
        window.clearInterval(interval);
      }
    }, 1500);
    return () => window.clearInterval(interval);
  }, [openvinoDownloadJobId, downloadingOpenVINO]);

  // Check Foundry Local installation status when microsoft-foundry-local is active
  useEffect(() => {
    if (config?.model_provider === "microsoft-foundry-local") {
      handleCheckFoundryStatus();
    }
  }, [config?.model_provider, handleCheckFoundryStatus]);

  useEffect(() => {
    if (config?.model_provider === "openvino" || config?.embedding_provider === "openvino") {
      handleCheckOpenVINOStatus();
    }
  }, [config?.model_provider, config?.embedding_provider, handleCheckOpenVINOStatus]);

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

        {/* OpenAI Settings Management — only shown when openai is the active model provider */}
        {config.model_provider === "openai" && (
          <div className="mt-4 rounded-md border p-4">
            <div className="mb-3 flex items-center gap-2">
              <Key className="h-4 w-4" />
              <h3 className="text-sm font-medium">OpenAI API Key & Model</h3>
            </div>
            <p className="mb-3 text-xs text-muted-foreground">
              Manage your OpenAI API key and model name here. The key is stored in the local{" "}
              <code className="rounded bg-muted px-1">.env</code> file (gitignored) and takes effect
              immediately for new workflow runs. You do not need to switch providers to update the key.
            </p>

            {/* Current status */}
            <div className="mb-3 grid grid-cols-2 gap-3">
              <div className="rounded-md border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">API Key Status</p>
                <p className="font-medium break-all">
                  {providerInfo.current.openai_configured ? (
                    <span className="text-green-700">
                      ✓ Configured ({providerInfo.current.openai_key_masked})
                    </span>
                  ) : (
                    <span className="text-muted-foreground">Not set</span>
                  )}
                </p>
              </div>
              <div className="rounded-md border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">OpenAI Model</p>
                <p className="font-medium font-mono text-sm break-all">{providerInfo.current.openai_model}</p>
              </div>
            </div>

            {/* Update form */}
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-medium">
                  New API Key{" "}
                  <span className="text-muted-foreground">(leave blank to keep current key)</span>
                </label>
                <input
                  type="password"
                  value={openaiSettingsKey}
                  onChange={(e) => setOpenaiSettingsKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full rounded-md border p-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">
                  OpenAI Model{" "}
                  <span className="text-muted-foreground">(e.g. gpt-4o-mini, gpt-4o, gpt-4-turbo)</span>
                </label>
                <input
                  type="text"
                  value={openaiSettingsModel}
                  onChange={(e) => setOpenaiSettingsModel(e.target.value)}
                  placeholder={providerInfo.current.openai_model || "gpt-4o-mini"}
                  className="w-full rounded-md border p-2 text-sm font-mono"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleSaveOpenAISettings}
                  disabled={savingOpenAI || (!openaiSettingsKey.trim() && !openaiSettingsModel.trim())}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {savingOpenAI ? "Saving..." : "Save Settings"}
                </button>
                {providerInfo.current.openai_configured && (
                  <button
                    onClick={handleRemoveOpenAIKey}
                    disabled={savingOpenAI}
                    className="flex items-center gap-1.5 rounded-md border border-red-200 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Remove Key
                  </button>
                )}
              </div>
            </div>

            {/* Messages */}
            {openAIMessage && (
              <div className="mt-3 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-900">
                {openAIMessage}
              </div>
            )}
            {openAIError && (
              <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900">
                {openAIError}
              </div>
            )}

            {/* OpenAI config table — all openai_* params grouped here */}
            {config.categories["Model"] && (
              <div className="mt-4">
                <h4 className="mb-2 text-sm font-semibold">OpenAI Parameters</h4>
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
                      {config.categories["Model"]
                        .filter((param: ConfigParameter) => param.name.startsWith("openai_") && param.name !== "openai_api_key" && param.name !== "openai_model")
                        .map((param: ConfigParameter) => (
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
            )}

          </div>
        )}

        {/* OpenVINO Model Server settings — shown when model or embedding provider uses openvino */}
        {(config.model_provider === "openvino" || config.embedding_provider === "openvino") && (
          <div className="mt-4 space-y-3 rounded-md border p-4">
            <h4 className="text-sm font-semibold">OpenVINO Model Server</h4>
            <p className="text-xs text-muted-foreground">
              OpenVINO Model Server can provide both local text inference and local embeddings via an
              OpenAI-compatible API. Start OVMS separately, then point this app at its endpoint.
              Hugging Face tokens are optional for public OpenVINO models and only needed for gated,
              private, or rate-limit-free downloads.
            </p>

            <div className={`rounded-md border p-3 text-xs ${openvinoRunning ? "border-green-200 bg-green-50 text-green-900" : "border-yellow-200 bg-yellow-50 text-yellow-900"}`}>
              {openvinoRunning === true
                ? `✓ OVMS is responding at ${providerInfo.current.openvino_endpoint}`
                : `⚠ OVMS is not responding at ${providerInfo.current.openvino_endpoint || "http://localhost:8100"}. Start OpenVINO Model Server before using OpenVINO providers.`}
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium">OVMS Endpoint</label>
                <input
                  type="text"
                  value={openvinoEndpoint || providerInfo.current.openvino_endpoint || "http://localhost:8100"}
                  onChange={(e) => setOpenvinoEndpoint(e.target.value)}
                  className="w-full rounded-md border p-2 text-sm font-mono"
                />
                <p className="mt-1 text-xs text-muted-foreground">Default uses port 8100 to avoid the mock Pricing API on port 8000.</p>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">Target Device</label>
                <select
                  value={openvinoDevice || providerInfo.current.openvino_device || "NPU"}
                  onChange={(e) => setOpenvinoDevice(e.target.value)}
                  className="w-full rounded-md border p-2 text-sm"
                >
                  <option value="NPU">NPU (Intel AI Boost)</option>
                  <option value="GPU">GPU</option>
                  <option value="CPU">CPU</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">Text Generation Model</label>
                <select
                  value={openvinoModel || providerInfo.current.openvino_model || "OpenVINO/Qwen3-8B-int4-cw-ov"}
                  onChange={(e) => setOpenvinoModel(e.target.value)}
                  className="w-full rounded-md border p-2 text-sm"
                >
                  {providerInfo.openvino_models.map((m) => (
                    <option key={m.alias} value={m.alias}>{m.label} ({m.alias})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">Embedding Model</label>
                <select
                  value={openvinoEmbeddingModel || providerInfo.current.openvino_embedding_model || "OpenVINO/Qwen3-Embedding-0.6B"}
                  onChange={(e) => setOpenvinoEmbeddingModel(e.target.value)}
                  className="w-full rounded-md border p-2 text-sm"
                >
                  {providerInfo.openvino_embedding_models.map((m) => (
                    <option key={m.alias} value={m.alias}>{m.label} ({m.dimension}-dim)</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium">
                Hugging Face Token <span className="text-muted-foreground">(optional)</span>
              </label>
              <input
                type="password"
                value={hfToken}
                onChange={(e) => setHfToken(e.target.value)}
                placeholder={providerInfo.current.hf_configured ? `Configured (${providerInfo.current.hf_token_masked})` : "hf_... only needed for gated/private models"}
                className="w-full rounded-md border p-2 text-sm"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Public OpenVINO models do not require a token. Use one only after accepting gated model terms on Hugging Face or for private models.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                onClick={handleSaveOpenVINOSettings}
                disabled={savingOpenVINO}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {savingOpenVINO ? "Saving..." : "Save OpenVINO Settings"}
              </button>
              <button
                onClick={() => handleDownloadOpenVINOModel(openvinoModel || providerInfo.current.openvino_model)}
                disabled={downloadingOpenVINO}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
              >
                Download Text Model
              </button>
              <button
                onClick={() => handleDownloadOpenVINOModel(openvinoEmbeddingModel || providerInfo.current.openvino_embedding_model)}
                disabled={downloadingOpenVINO}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
              >
                Download Embedding Model
              </button>
              <button
                onClick={handleCheckOpenVINOStatus}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
              >
                Check OVMS Status
              </button>
            </div>

            {openvinoDownloadMessage && (
              <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
                {openvinoDownloadMessage}
              </div>
            )}
            {openvinoMessage && (
              <div className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-900">
                {openvinoMessage}
              </div>
            )}
            {openvinoError && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900">
                {openvinoError}
              </div>
            )}
          </div>
        )}

        {/* Foundry Local model selector + params — only relevant when microsoft-foundry-local is active */}
        {config.categories["Model"] && config.model_provider === "microsoft-foundry-local" && (
          <div className="mt-4 space-y-3">
            <h4 className="text-sm font-semibold">Foundry Local Model</h4>
            <p className="text-xs text-muted-foreground">
              Select a model from the Foundry Local catalog. Use{" "}
              <code className="rounded bg-muted px-1">{"foundry model download <alias>"}</code> to download
              a model before selecting it here.
            </p>

            {/* Foundry Local installation status */}
            {foundryInstalled === false && (
              <div className="rounded-md border border-yellow-200 bg-yellow-50 p-3">
                <p className="text-sm font-medium text-yellow-900">⚠️ Foundry Local SDK is not available</p>
                <p className="mt-1 text-xs text-yellow-800">
                  The UI backend cannot import the Foundry Local Python SDK in its current Python environment. Install it automatically or copy the command below, then restart the backend.
                </p>
                {installInstructions && (
                  <pre className="mt-2 overflow-x-auto rounded bg-yellow-100 p-2 text-xs text-yellow-900 whitespace-pre-wrap">
                    {installInstructions}
                  </pre>
                )}
                <div className="mt-2 flex gap-2">
                  <button
                    onClick={handleInstallFoundry}
                    disabled={installingFoundry}
                    className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {installingFoundry ? "Installing... (this may take a few minutes)" : "Install Foundry Local SDK"}
                  </button>
                  {installCommand && (
                    <button
                      onClick={() => navigator.clipboard?.writeText(installCommand)}
                      className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
                    >
                      Copy install command
                    </button>
                  )}
                </div>
                {installMessage && (
                  <div className="mt-2 rounded-md border border-green-200 bg-green-50 p-2 text-xs text-green-900">
                    {installMessage}
                  </div>
                )}
                {installError && (
                  <div className="mt-2 rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-900">
                    {installError}
                  </div>
                )}
              </div>
            )}
            {foundryInstalled === true && !foundryServiceRunning && (
              <div className="rounded-md border border-yellow-200 bg-yellow-50 p-3 text-xs text-yellow-900">
                <p>
                  ⚠️ Foundry Local is installed but the service is not running.
                </p>
                <div className="mt-2 flex gap-2">
                  <button
                    onClick={handleStartFoundryService}
                    disabled={startingService}
                    className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {startingService ? "Starting service..." : "Start Service Now"}
                  </button>
                </div>
                {startServiceMessage && (
                  <div className="mt-2 rounded-md border border-green-200 bg-green-50 p-2 text-xs text-green-900">
                    {startServiceMessage}
                  </div>
                )}
                {startServiceError && (
                  <div className="mt-2 rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-900">
                    {startServiceError}
                  </div>
                )}
              </div>
            )}
            {foundryInstalled === true && foundryServiceRunning && (
              <div className="rounded-md border border-green-200 bg-green-50 p-3 text-xs text-green-900">
                ✓ Foundry Local is installed and running.
              </div>
            )}

            {/* Model cache directory configuration — only when installed */}
            {foundryInstalled === true && (
              <div className="rounded-md border bg-muted/30 p-3">
                <p className="text-xs font-medium text-muted-foreground">Model Cache Directory</p>
                <p className="mt-1 font-mono text-xs break-all">
                  {foundryCacheDir || "(default — not yet configured)"}
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Downloaded models (2-10 GB each) are stored here. Change this if your default drive has limited space.
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    onClick={async () => {
                      // Use the File System Access API if available (Chromium-based browsers)
                      const w = window as unknown as { showDirectoryPicker?: () => Promise<{ name: string }> };
                      if (w.showDirectoryPicker) {
                        try {
                          const dirHandle = await w.showDirectoryPicker();
                          // Note: showDirectoryPicker only returns the folder name, not the full path.
                          // We set it in the text input so the user can verify/edit the full path.
                          setNewCacheDir(dirHandle.name);
                          setCacheDirError("Folder selected. Please verify the full path is correct (e.g. C:\\foundry_models) and click 'Set Cache Dir'.");
                        } catch {
                          // User cancelled — no action needed
                        }
                      } else {
                        // Fallback: focus the text input so the user can type a path
                        _cacheDirInputRef.current?.focus();
                      }
                    }}
                    className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
                  >
                    Browse...
                  </button>
                  <input
                    type="text"
                    value={newCacheDir}
                    onChange={(e) => setNewCacheDir(e.target.value)}
                    placeholder={foundryCacheDir || "D:\\foundry-models"}
                    className="flex-1 rounded-md border p-1.5 text-xs font-mono"
                    ref={_cacheDirInputRef}
                  />
                  <button
                    onClick={handleSaveCacheDir}
                    disabled={savingCacheDir || !newCacheDir.trim()}
                    className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {savingCacheDir ? "Saving..." : "Set Cache Dir"}
                  </button>
                  <button
                    onClick={handleResetCacheDir}
                    disabled={savingCacheDir}
                    className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
                    title={`Reset to the default cache directory (${DEFAULT_FOUNDRY_CACHE_DIR})`}
                  >
                    Reset to Default
                  </button>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Click "Browse..." to select a folder, or type a path manually. Then click "Set Cache Dir" to apply.
                  Click "Reset to Default" to revert to <code className="rounded bg-muted px-1">{DEFAULT_FOUNDRY_CACHE_DIR}</code>.
                </p>
                {cacheDirMessage && (
                  <div className="mt-2 rounded-md border border-green-200 bg-green-50 p-2 text-xs text-green-900">
                    {cacheDirMessage}
                  </div>
                )}
                {cacheDirError && (
                  <div className="mt-2 rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-900">
                    {cacheDirError}
                  </div>
                )}
              </div>
            )}

            {/* Current model */}
            <div className="rounded-md border bg-muted/30 p-3">
              <p className="text-xs text-muted-foreground">Current Model</p>
              <p className="font-medium font-mono text-sm break-all">
                {providerInfo.current.local_model_name || "Not set"}
              </p>
            </div>

            {/* Model selector */}
            <div>
              <label className="mb-1 block text-xs font-medium">
                Select Model{" "}
                <span className="text-muted-foreground">(from Foundry Local catalog)</span>
              </label>
              <select
                value={foundryModel}
                onChange={(e) => setFoundryModel(e.target.value)}
                className="w-full rounded-md border p-2 text-sm"
              >
                <option value="">— Select a model —</option>
                {providerInfo.foundry_local_models?.map((m) => (
                  <option key={m.alias} value={m.alias}>
                    {m.label} ({m.alias})
                  </option>
                ))}
              </select>
            </div>

            {/* Custom model name input */}
            <div>
              <label className="mb-1 block text-xs font-medium">
                Or enter a custom model name{" "}
                <span className="text-muted-foreground">(if not in the list above)</span>
              </label>
              <input
                type="text"
                value={foundryModel}
                onChange={(e) => setFoundryModel(e.target.value)}
                    placeholder={providerInfo.current.local_model_name || "qwen2.5-0.5b"}
                className="w-full rounded-md border p-2 text-sm font-mono"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleDownloadFoundryModel}
                disabled={downloadingModel || savingFoundryModel || !foundryModel.trim()}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
              >
                {downloadingModel ? "Downloading..." : "Download Model"}
              </button>
              <button
                onClick={handleSaveFoundryModel}
                disabled={savingFoundryModel || downloadingModel || !foundryModel.trim()}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {savingFoundryModel ? "Saving..." : "Save Model"}
              </button>
            </div>

            {(downloadingModel || downloadStatus) && (
              <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="font-medium">
                    {downloadMessage || "Preparing model download..."}
                  </span>
                  <span className="font-mono text-xs">{downloadPercent}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-blue-100">
                  <div
                    className="h-full rounded-full bg-blue-600 transition-all"
                    style={{ width: `${Math.max(0, Math.min(100, downloadPercent))}%` }}
                  />
                </div>
                <p className="mt-2 text-xs text-blue-800">
                  Status: <span className="font-mono">{downloadStatus}</span>. Large models can take several minutes.
                </p>
                {downloadOutput.length > 0 && (
                  <pre className="mt-2 max-h-32 overflow-y-auto rounded bg-blue-100 p-2 text-xs text-blue-950 whitespace-pre-wrap">
                    {downloadOutput.slice(-8).join("\n")}
                  </pre>
                )}
              </div>
            )}

            {/* Model descriptions */}
            {providerInfo.foundry_local_models && providerInfo.foundry_local_models.length > 0 && (
              <div className="overflow-hidden rounded-md border">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium">Alias</th>
                      <th className="px-4 py-2 text-left font-medium">Device</th>
                      <th className="px-4 py-2 text-left font-medium">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {providerInfo.foundry_local_models.map((m) => (
                      <tr key={m.alias} className="border-t">
                        <td className="px-4 py-2 font-mono text-xs">{m.alias}</td>
                        <td className="px-4 py-2 text-xs">
                          <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{m.device}</span>
                        </td>
                        <td className="px-4 py-2 text-xs text-muted-foreground">{m.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Foundry Local config params */}
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
                  {config.categories["Model"]
                    .filter((param: ConfigParameter) => !param.name.startsWith("openai_") && param.name !== "model_provider")
                    .map((param: ConfigParameter) => (
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

            {/* Messages */}
            {foundryModelMessage && (
              <div className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-900">
                {foundryModelMessage}
              </div>
            )}
            {foundryModelError && (
              <div className="rounded-md border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-900">
                {foundryModelError}
              </div>
            )}

            {/* Step-by-step progress */}
            {foundrySteps.length > 0 && (
              <div className="mt-3 space-y-1">
                <p className="text-xs font-medium text-muted-foreground">Setup Progress:</p>
                {foundrySteps.map((s, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-2 rounded-md border p-2 text-xs ${
                      s.status === "ok"
                        ? "border-green-200 bg-green-50 text-green-900"
                        : s.status === "error"
                        ? "border-red-200 bg-red-50 text-red-900"
                        : s.status === "warning"
                        ? "border-yellow-200 bg-yellow-50 text-yellow-900"
                        : "border-blue-200 bg-blue-50 text-blue-900"
                    }`}
                  >
                    <span className="font-mono">
                      {s.status === "ok" ? "✓" : s.status === "error" ? "✗" : s.status === "warning" ? "⚠" : "ℹ"}
                    </span>
                    <span>{s.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Embedding Provider Switcher */}
      <div className="rounded-md border p-4">
        <h3 className="mb-3 text-sm font-medium">
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

        {/* Embeddings config table — rendered here for proximity to the switcher */}
        {config.categories["Embeddings"] && (
          <div className="mt-4">
            <h4 className="mb-2 text-sm font-semibold">Embeddings</h4>
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
                  {config.categories["Embeddings"]
                    .filter((param: ConfigParameter) => param.name !== "embedding_provider")
                    .map((param: ConfigParameter) => (
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
        )}

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
      </div>

      {/* Config parameters by category (excluding Embeddings and Model, shown above) */}
      {categories.filter(([category]) => category !== "Embeddings" && category !== "Model").map(([category, params]) => (
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
                {params
                  .filter((param: ConfigParameter) => param.name !== "phoenix_enabled" && param.name !== "langfuse_enabled")
                  .map((param: ConfigParameter) => (
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
