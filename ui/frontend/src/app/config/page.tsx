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
    openvino_ovms_path: string | null;
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
    npu_recommended?: string;
    serving_note?: string;
  }>;
  openvino_embedding_models: Array<{
    alias: string;
    label: string;
    description: string;
    device: string;
    dimension: string;
    npu_recommended?: string;
    serving_note?: string;
  }>;
}

interface HardwareStatus {
  platform: string;
  cpu: { logical_cores: number; usage_percent: number | null };
  memory: { total_gb: number | null; available_gb: number | null; used_percent: number | null };
  gpu: { controllers: Array<{ Name?: string; AdapterRAM?: number; DriverVersion?: string }>; usage_percent: number | null };
  npu: { controllers: Array<{ FriendlyName?: string; Status?: string; Class?: string }> };
  local_ai_processes: Array<{ ProcessName: string; Id: number; WorkingSetMB: number }>;
  notes: string[];
}

interface HardwareEnvelope {
  status: "cached" | "stale";
  message?: string;
  result: HardwareStatus | null;
}

export default function ConfigPage() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
  const [providerLoading, setProviderLoading] = useState(true);
  const [hardwareStatus, setHardwareStatus] = useState<HardwareStatus | null>(null);
  const [hardwareError, setHardwareError] = useState<string | null>(null);
  const [hardwareJobId, setHardwareJobId] = useState<string | null>(null);
  const [hardwareJobStatus, setHardwareJobStatus] = useState<string | null>(null);
  const [hardwareJobMessage, setHardwareJobMessage] = useState<string | null>(null);
  const [hardwareJobPercent, setHardwareJobPercent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [switching, setSwitching] = useState(false);
  const [switchMessage, setSwitchMessage] = useState<string | null>(null);
  const [switchWarnings, setSwitchWarnings] = useState<string[]>([]);
  const [switchJobId, setSwitchJobId] = useState<string | null>(null);
  const [switchJobStatus, setSwitchJobStatus] = useState<string | null>(null);
  const [switchJobMessage, setSwitchJobMessage] = useState<string | null>(null);
  const [switchJobPercent, setSwitchJobPercent] = useState(0);
  const [pendingModelProvider, setPendingModelProvider] = useState<string | null>(null);
  const [pendingEmbeddingProvider, setPendingEmbeddingProvider] = useState<string | null>(null);
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
  const [foundryModelJobId, setFoundryModelJobId] = useState<string | null>(null);
  const [foundryModelJobStatus, setFoundryModelJobStatus] = useState<string | null>(null);
  const [foundryModelJobMessage, setFoundryModelJobMessage] = useState<string | null>(null);
  const [foundryModelJobPercent, setFoundryModelJobPercent] = useState(0);
  const [downloadingModel, setDownloadingModel] = useState(false);
  const [downloadJobId, setDownloadJobId] = useState<string | null>(null);
  const [downloadStatus, setDownloadStatus] = useState<string | null>(null);
  const [downloadMessage, setDownloadMessage] = useState<string | null>(null);
  const [downloadPercent, setDownloadPercent] = useState(0);
  const [downloadOutput, setDownloadOutput] = useState<string[]>([]);
  const [foundryInstalled, setFoundryInstalled] = useState<boolean | null>(null);
  const [foundryServiceRunning, setFoundryServiceRunning] = useState<boolean>(false);
  const [installingFoundry, setInstallingFoundry] = useState(false);
  const [installJobId, setInstallJobId] = useState<string | null>(null);
  const [installJobStatus, setInstallJobStatus] = useState<string | null>(null);
  const [installJobPercent, setInstallJobPercent] = useState(0);
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
  const [openvinoOvmsPath, setOpenvinoOvmsPath] = useState("");
  const [hfToken, setHfToken] = useState("");
  const [savingOpenVINO, setSavingOpenVINO] = useState(false);
  const [openvinoMessage, setOpenvinoMessage] = useState<string | null>(null);
  const [openvinoError, setOpenvinoError] = useState<string | null>(null);
  const [openvinoRunning, setOpenvinoRunning] = useState<boolean | null>(null);
  const [openvinoModelCacheDir, setOpenvinoModelCacheDir] = useState<string>("");
  const [openvinoModelCached, setOpenvinoModelCached] = useState(false);
  const [openvinoEmbeddingModelCached, setOpenvinoEmbeddingModelCached] = useState(false);
  const [openvinoModelRepositoryPath, setOpenvinoModelRepositoryPath] = useState<string>("");
  const [openvinoEmbeddingModelRepositoryPath, setOpenvinoEmbeddingModelRepositoryPath] = useState<string>("");
  const [openvinoServedModel, setOpenvinoServedModel] = useState<string | null>(null);
  const [openvinoServedModelMatchesSelection, setOpenvinoServedModelMatchesSelection] = useState(false);
  const [openvinoRuntimeMode, setOpenvinoRuntimeMode] = useState<string>("native-windows");
  const [openvinoSetupScript, setOpenvinoSetupScript] = useState<string>("scripts/setup-ovms.ps1");
  const [openvinoLatestRelease, setOpenvinoLatestRelease] = useState<string>("2026.2.1");
  const [openvinoWindowsDownloadUrl, setOpenvinoWindowsDownloadUrl] = useState<string>("");
  const [openvinoWindowsChecksumUrl, setOpenvinoWindowsChecksumUrl] = useState<string>("");
  const [openvinoBaremetalDocsUrl, setOpenvinoBaremetalDocsUrl] = useState<string>("");
  const [startingOpenVINO, setStartingOpenVINO] = useState(false);
  const [openvinoStartJobId, setOpenvinoStartJobId] = useState<string | null>(null);
  const [openvinoStartStatus, setOpenvinoStartStatus] = useState<string | null>(null);
  const [openvinoStartMessage, setOpenvinoStartMessage] = useState<string | null>(null);
  const [openvinoStartPercent, setOpenvinoStartPercent] = useState(0);
  const [openvinoStartOutput, setOpenvinoStartOutput] = useState<string[]>([]);
  const [stoppingOpenVINO, setStoppingOpenVINO] = useState(false);
  const [openvinoStopJobId, setOpenvinoStopJobId] = useState<string | null>(null);
  const [openvinoStopStatus, setOpenvinoStopStatus] = useState<string | null>(null);
  const [openvinoStopMessage, setOpenvinoStopMessage] = useState<string | null>(null);
  const [openvinoStopPercent, setOpenvinoStopPercent] = useState(0);
  const [downloadingOpenVINO, setDownloadingOpenVINO] = useState(false);
  const [openvinoDownloadJobId, setOpenvinoDownloadJobId] = useState<string | null>(null);
  const [openvinoDownloadMessage, setOpenvinoDownloadMessage] = useState<string | null>(null);
  const readinessStartedRef = useRef<Record<string, boolean>>({});

  const fetchAll = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    setProviderLoading(true);
    try {
      const configRes = await apiGet<ConfigResponse>("/config");
      setConfig(configRes);
      if (!silent) setLoading(false);
      const providerRes = await apiGet<ProviderInfo>("/provider");
      setProviderInfo(providerRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load config");
    } finally {
      setProviderLoading(false);
      if (!silent) setLoading(false);
    }
  }, []);

  const handleCheckHardwareStatus = useCallback(async () => {
    try {
      const cached = await apiGet<HardwareEnvelope>("/health/hardware");
      if (cached.result) setHardwareStatus(cached.result);
      const job = await apiPost<{ job_id: string; status: string; message: string; percent: number }>("/health/hardware/refresh", {});
      setHardwareJobId(job.job_id);
      setHardwareJobStatus(job.status);
      setHardwareJobMessage(job.message);
      setHardwareJobPercent(job.percent || 0);
      setHardwareError(null);
    } catch (err) {
      setHardwareError(err instanceof Error ? err.message : "Failed to load hardware telemetry");
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    if (config) handleCheckHardwareStatus();
  }, [config, handleCheckHardwareStatus]);

  useEffect(() => {
    if (!hardwareJobId) return;
    const interval = window.setInterval(async () => {
      try {
        const job = await apiGet<{ status: string; message: string; percent: number; result?: HardwareStatus }>(`/health/hardware/job/${hardwareJobId}`);
        setHardwareJobStatus(job.status);
        setHardwareJobMessage(job.message);
        setHardwareJobPercent(job.percent || 0);
        if (job.status === "complete") {
          if (job.result) setHardwareStatus(job.result);
          window.clearInterval(interval);
        }
        if (job.status === "error") {
          setHardwareError(job.message || "Hardware telemetry failed");
          window.clearInterval(interval);
        }
      } catch (err) {
        setHardwareError(err instanceof Error ? err.message : "Failed to poll hardware telemetry");
        window.clearInterval(interval);
      }
    }, 1000);
    return () => window.clearInterval(interval);
  }, [hardwareJobId]);

  useEffect(() => {
    if (!config) return;
    setPendingModelProvider(null);
    setPendingEmbeddingProvider(null);
  }, [config?.model_provider, config?.embedding_provider]);

  const effectiveModelProvider = pendingModelProvider ?? config?.model_provider;
  const effectiveEmbeddingProvider = pendingEmbeddingProvider ?? config?.embedding_provider;

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
    setSwitchJobId(null);
    setSwitchJobStatus(null);
    setSwitchJobMessage(null);
    setSwitchJobPercent(0);
    setError(null);
    if (type === "model") setPendingModelProvider(provider);
    if (type === "embedding") setPendingEmbeddingProvider(provider);

    // Show a specific message when switching to Microsoft Foundry Local (may take a few seconds to auto-start)
    if (provider === "microsoft-foundry-local") {
      setSwitchMessage("Switching to Microsoft Foundry Local — starting service if needed, this may take a few seconds...");
    }
    if (provider === "openvino") {
      setSwitchMessage("Switching to OpenVINO Model Server. Start OVMS locally before running text generation or embeddings.");
    }

    let keepSwitchingForJob = false;
    try {
      const body: Record<string, unknown> = {};
      if (type === "model") body.model_provider = provider;
      if (type === "embedding") body.embedding_provider = provider;
      if (openaiKey.trim()) body.openai_api_key = openaiKey.trim();

      const result = await apiPost<{
        job_id: string;
        status: string;
        success: boolean;
        message: string;
        percent?: number;
        warnings: string[];
        foundry_auto_started: boolean;
        result?: {
          success: boolean;
          message: string;
          warnings: string[];
          foundry_auto_started: boolean;
        };
      }>("/provider/switch-job", body);

      setSwitchJobId(result.job_id || null);
      setSwitchJobStatus(result.status || null);
      setSwitchJobMessage(result.message || null);
      setSwitchJobPercent(result.percent || 0);

      if (result.status !== "complete") {
        keepSwitchingForJob = true;
        return;
      }

      const switchResult = result.result || result;

      // Build a message that includes Microsoft Foundry Local auto-start info
      let msg = switchResult.message;
      if (switchResult.foundry_auto_started) {
        msg += " Microsoft Foundry Local service was auto-started.";
      }
      setSwitchMessage(msg);
      setSwitchWarnings(switchResult.warnings || []);
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
      if (type === "model") setPendingModelProvider(null);
      if (type === "embedding") setPendingEmbeddingProvider(null);
    } finally {
      if (!keepSwitchingForJob) setSwitching(false);
    }
  };

  useEffect(() => {
    if (!switchJobId || switchJobId === "synchronous" || !switching) return;
    const interval = window.setInterval(async () => {
      try {
        const job = await apiGet<{
          status: string;
          message: string;
          percent: number;
          warnings?: string[];
          foundry_auto_started?: boolean;
          result?: {
            message: string;
            warnings: string[];
            foundry_auto_started: boolean;
          };
        }>(`/provider/switch-job/${switchJobId}`);
        setSwitchJobStatus(job.status);
        setSwitchJobMessage(job.message);
        setSwitchJobPercent(job.percent || 0);
        if (job.status === "complete") {
          const switchResult = job.result || job;
          let msg = switchResult.message || job.message;
          if (switchResult.foundry_auto_started) msg += " Microsoft Foundry Local service was auto-started.";
          setSwitchMessage(msg);
          setSwitchWarnings(switchResult.warnings || []);
          setOpenaiKey("");
          setShowKeyInput(false);
          await fetchAll(true);
          handleCheckFoundryStatus();
          setTimeout(() => handleCheckFoundryStatus(), 5000);
          setSwitching(false);
          window.clearInterval(interval);
        }
        if (job.status === "error") {
          setError(job.message || "Provider switch failed");
          setPendingModelProvider(null);
          setPendingEmbeddingProvider(null);
          setSwitching(false);
          window.clearInterval(interval);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch provider switch status");
        setPendingModelProvider(null);
        setPendingEmbeddingProvider(null);
        setSwitching(false);
        window.clearInterval(interval);
      }
    }, 1000);
    return () => window.clearInterval(interval);
  }, [switchJobId, switching, fetchAll]);

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

      const result = await apiPost<{
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
    setFoundryModelJobId(null);
    setFoundryModelJobStatus("queued");
    setFoundryModelJobMessage("Queueing Microsoft Foundry Local model update...");
    setFoundryModelJobPercent(0);
    setFoundryModelMessage(null);
    setFoundryModelError(null);
    setFoundrySteps([]);
    try {
      const result = await apiPost<{
        job_id: string;
        status: string;
        percent: number;
        success: boolean;
        message: string;
        warnings: string[];
        steps: Array<{ step: string; status: string; message: string }>;
      }>("/provider/foundry-model/job", { local_model_name: foundryModel.trim() });
      setFoundryModelJobId(result.job_id || null);
      setFoundryModelJobStatus(result.status);
      setFoundryModelJobMessage(result.message);
      setFoundryModelJobPercent(result.percent || 0);
      setFoundrySteps(result.steps || []);
    } catch (err) {
      setFoundryModelError(err instanceof Error ? err.message : "Failed to update Microsoft Foundry Local model");
      setSavingFoundryModel(false);
    } finally {
      // Completion is handled by polling when a queued job is returned.
    }
  };

  const handleDownloadFoundryModel = async () => {
    const model = foundryModel.trim();
    if (!model) {
      setFoundryModelError("Select a verified Microsoft Foundry Local model alias to download.");
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
      const result = await apiPost<{
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
    setInstallJobId(null);
    setInstallJobStatus("queued");
    setInstallJobPercent(0);
    setInstallMessage(null);
    setInstallError(null);
    try {
      const result = await apiPost<{
        job_id: string;
        status: string;
        percent: number;
        success: boolean;
        message: string;
        output: string;
        installed: boolean;
      }>("/provider/foundry-install", {});
      setInstallJobId(result.job_id || null);
      setInstallJobStatus(result.status);
      setInstallJobPercent(result.percent || 0);
      setInstallMessage(result.message);
      if (result.status === "complete") setFoundryInstalled(Boolean(result.installed));
      if (result.status === "error") setInstallError(result.message);
    } catch (err) {
      setInstallError(err instanceof Error ? err.message : "Failed to install Microsoft Foundry Local");
      setInstallingFoundry(false);
    } finally {
      // Completion is handled by polling when a queued job is returned.
    }
  };

  useEffect(() => {
    if (!installJobId || !installingFoundry) return;
    const interval = window.setInterval(async () => {
      try {
        const result = await apiGet<{ status: string; percent: number; message: string; installed: boolean; output?: string }>(`/provider/foundry-install/${installJobId}`);
        setInstallJobStatus(result.status);
        setInstallJobPercent(result.percent || 0);
        setInstallMessage(result.message);
        if (result.status === "complete") {
          setFoundryInstalled(Boolean(result.installed));
          setInstallingFoundry(false);
          await handleCheckFoundryStatus();
          window.clearInterval(interval);
        }
        if (result.status === "error") {
          setInstallError(`${result.message}${result.output ? ` Details: ${result.output}` : ""}`);
          setInstallingFoundry(false);
          window.clearInterval(interval);
        }
      } catch (err) {
        setInstallError(err instanceof Error ? err.message : "Failed to poll Microsoft Foundry Local install status");
        setInstallingFoundry(false);
        window.clearInterval(interval);
      }
    }, 1500);
    return () => window.clearInterval(interval);
  }, [installJobId, installingFoundry, handleCheckFoundryStatus]);

  const handleResetCacheDir = async () => {
    setSavingCacheDir(true);
    setCacheDirMessage(null);
    setCacheDirError(null);
    try {
      const result = await apiPost<{
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
  const [stoppingFoundryService, setStoppingFoundryService] = useState(false);
  const [foundryStopJobId, setFoundryStopJobId] = useState<string | null>(null);
  const [foundryStopStatus, setFoundryStopStatus] = useState<string | null>(null);
  const [foundryStopPercent, setFoundryStopPercent] = useState(0);
  const [startServiceMessage, setStartServiceMessage] = useState<string | null>(null);
  const [startServiceError, setStartServiceError] = useState<string | null>(null);

  const handleStartFoundryService = async () => {
    setStartingService(true);
    setFoundryModelJobId(null);
    setFoundryModelJobStatus("queued");
    setFoundryModelJobMessage("Queueing Microsoft Foundry Local readiness...");
    setFoundryModelJobPercent(0);
    setFoundrySteps([]);
    setStartServiceMessage(null);
    setStartServiceError(null);
    try {
      // Use the foundry-model endpoint with the current model name to trigger service start
      const configuredModel = providerInfo?.current.local_model_name || "phi-4-mini";
      const currentModel = configuredModel.startsWith("OpenVINO/") ? "phi-4-mini" : configuredModel;
      const result = await apiPost<{
        job_id: string;
        status: string;
        percent: number;
        success: boolean;
        message: string;
        warnings: string[];
        steps: Array<{ step: string; status: string; message: string }>;
        service_running: boolean;
      }>("/provider/foundry-model/job", { local_model_name: currentModel });
      setFoundryModelJobId(result.job_id || null);
      setFoundryModelJobStatus(result.status);
      setFoundryModelJobMessage(result.message);
      setFoundryModelJobPercent(result.percent || 0);
      setFoundrySteps(result.steps || []);
    } catch (err) {
      setStartServiceError(err instanceof Error ? err.message : "Failed to start Microsoft Foundry Local service");
      setStartingService(false);
    }
  };

  useEffect(() => {
    if (!foundryModelJobId || (!startingService && !savingFoundryModel)) return;
    const interval = window.setInterval(async () => {
      try {
        const result = await apiGet<{
          status: string;
          message: string;
          percent: number;
          steps?: Array<{ step: string; status: string; message: string }>;
          warnings?: string[];
          service_running?: boolean;
          result?: {
            message: string;
            warnings: string[];
            steps: Array<{ step: string; status: string; message: string }>;
            service_running: boolean;
          };
        }>(`/provider/foundry-model/job/${foundryModelJobId}`);
        const payload = result.result || result;
        setFoundryModelJobStatus(result.status);
        setFoundryModelJobMessage(result.message);
        setFoundryModelJobPercent(result.percent || 0);
        setFoundrySteps(payload.steps || []);
        if (result.status === "complete") {
          setStartServiceMessage(payload.message || result.message);
          setFoundryModelMessage(payload.message || result.message);
          setFoundryServiceRunning(Boolean(payload.service_running));
          if (payload.warnings?.length) setStartServiceError(payload.warnings.join(" "));
          setStartingService(false);
          setSavingFoundryModel(false);
          await fetchAll(true);
          window.clearInterval(interval);
        }
        if (result.status === "error") {
          setStartServiceError(result.message || "Microsoft Foundry Local readiness failed");
          setFoundryModelError(result.message || "Microsoft Foundry Local readiness failed");
          setStartingService(false);
          setSavingFoundryModel(false);
          window.clearInterval(interval);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to poll Microsoft Foundry Local readiness";
        setStartServiceError(message);
        setFoundryModelError(message);
        setStartingService(false);
        setSavingFoundryModel(false);
        window.clearInterval(interval);
      }
    }, 1500);
    return () => window.clearInterval(interval);
  }, [foundryModelJobId, startingService, savingFoundryModel, fetchAll]);

  const handleStopFoundryService = async () => {
    setStoppingFoundryService(true);
    setFoundryStopJobId(null);
    setFoundryStopStatus("queued");
    setFoundryStopPercent(0);
    setStartServiceMessage(null);
    setStartServiceError(null);
    try {
      const result = await apiPost<{ job_id: string; status: string; stopped: boolean; message: string; percent: number }>('/provider/foundry-stop', {});
      setFoundryStopJobId(result.job_id || null);
      setFoundryStopStatus(result.status);
      setFoundryStopPercent(result.percent || 0);
      setStartServiceMessage(result.message);
      if (result.status === "complete" && result.stopped) {
        setFoundryServiceRunning(false);
        setStoppingFoundryService(false);
      }
    } finally {
      // Completion is handled by polling when a queued job is returned.
    }
  };

  useEffect(() => {
    if (!foundryStopJobId || !stoppingFoundryService) return;
    const interval = window.setInterval(async () => {
      try {
        const result = await apiGet<{ status: string; stopped: boolean; message: string; percent: number; output?: string }>(`/provider/foundry-stop/${foundryStopJobId}`);
        setFoundryStopStatus(result.status);
        setFoundryStopPercent(result.percent || 0);
        setStartServiceMessage(result.message);
        if (result.status === "complete") {
          setFoundryServiceRunning(!result.stopped);
          setStoppingFoundryService(false);
          await handleCheckFoundryStatus();
          window.clearInterval(interval);
        }
        if (result.status === "error") {
          setStartServiceError(`${result.message}${result.output ? ` Details: ${result.output}` : ""}`);
          setStoppingFoundryService(false);
          await handleCheckFoundryStatus();
          window.clearInterval(interval);
        }
      } catch (err) {
        setStartServiceError(err instanceof Error ? err.message : 'Failed to poll Microsoft Foundry Local stop status');
        setStoppingFoundryService(false);
        window.clearInterval(interval);
      }
    }, 1500);
    return () => window.clearInterval(interval);
  }, [foundryStopJobId, stoppingFoundryService, handleCheckFoundryStatus]);

  const handleCheckOpenVINOStatus = useCallback(async () => {
    try {
      const result = await apiGet<{
        service_running: boolean;
        endpoint: string;
        model: string;
        embedding_model: string;
        device: string;
        hf_configured: boolean;
        model_cache_dir: string;
        model_repository_path: string;
        embedding_model_repository_path: string;
        model_cached: boolean;
        embedding_model_cached: boolean;
        served_model: string | null;
        served_model_matches_selection: boolean;
        runtime_mode: string;
        setup_script: string;
        ovms_path: string | null;
        latest_release: string;
        windows_download_url: string;
        windows_checksum_url: string;
        baremetal_docs_url: string;
      }>("/provider/openvino-status");
      setOpenvinoRunning(result.service_running);
      setOpenvinoEndpoint(result.endpoint || "http://localhost:8100");
      setOpenvinoModel(result.model || "OpenVINO/Qwen3-8B-int4-cw-ov");
      setOpenvinoEmbeddingModel(result.embedding_model || "OpenVINO/Qwen3-Embedding-0.6B");
      setOpenvinoDevice(result.device || "NPU");
      setOpenvinoModelCacheDir(result.model_cache_dir || "");
      setOpenvinoModelRepositoryPath(result.model_repository_path || "");
      setOpenvinoEmbeddingModelRepositoryPath(result.embedding_model_repository_path || "");
      setOpenvinoModelCached(Boolean(result.model_cached));
      setOpenvinoEmbeddingModelCached(Boolean(result.embedding_model_cached));
      setOpenvinoServedModel(result.served_model || null);
      setOpenvinoServedModelMatchesSelection(Boolean(result.served_model_matches_selection));
      setOpenvinoRuntimeMode(result.runtime_mode || "native-windows");
      setOpenvinoSetupScript(result.setup_script || "scripts/setup-ovms.ps1");
      setOpenvinoOvmsPath(result.ovms_path || "");
      setOpenvinoLatestRelease(result.latest_release || "2026.2.1");
      setOpenvinoWindowsDownloadUrl(result.windows_download_url || "");
      setOpenvinoWindowsChecksumUrl(result.windows_checksum_url || "");
      setOpenvinoBaremetalDocsUrl(result.baremetal_docs_url || "");
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
        ovms_path: openvinoOvmsPath.trim(),
      };
      if (hfToken.trim()) body.hf_token = hfToken.trim();
      const result = await apiPut<{ success: boolean; message: string; ovms_path?: string | null }>("/provider/openvino-settings", body);
      setOpenvinoMessage(result.message);
      setOpenvinoOvmsPath(result.ovms_path || "");
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

  const handleStartOpenVINOService = async () => {
    setStartingOpenVINO(true);
    setOpenvinoStartJobId(null);
    setOpenvinoStartStatus("queued");
    setOpenvinoStartMessage("Queueing native OVMS start...");
    setOpenvinoStartPercent(0);
    setOpenvinoStartOutput([]);
    setOpenvinoMessage(null);
    setOpenvinoError(null);
    try {
      const result = await apiPost<{
        job_id: string;
        status: string;
        message: string;
        percent: number;
        output: string[];
        started?: boolean;
      }>("/provider/openvino-start", {});
      setOpenvinoStartJobId(result.job_id);
      setOpenvinoStartStatus(result.status);
      setOpenvinoStartMessage(result.message);
      setOpenvinoStartPercent(result.percent || 0);
      setOpenvinoStartOutput(result.output || []);
      if (result.status === "complete" || result.started) {
        setOpenvinoMessage(result.message);
        setOpenvinoRunning(true);
        setStartingOpenVINO(false);
      }
    } catch (err) {
      setOpenvinoError(err instanceof Error ? err.message : "Failed to start OpenVINO Model Server");
      setStartingOpenVINO(false);
    }
  };

  useEffect(() => {
    if (!openvinoStartJobId || !startingOpenVINO) return;
    const interval = window.setInterval(async () => {
      try {
        const result = await apiGet<{
          status: string;
          message: string;
          percent: number;
          output: string[];
          error_tail?: string;
          started?: boolean;
        }>(`/provider/openvino-start/${openvinoStartJobId}`);
        setOpenvinoStartStatus(result.status);
        setOpenvinoStartMessage(result.message);
        setOpenvinoStartPercent(result.percent || 0);
        setOpenvinoStartOutput(result.output || []);
        if (result.status === "complete") {
          setOpenvinoMessage(result.message);
          setOpenvinoRunning(Boolean(result.started));
          setStartingOpenVINO(false);
          await handleCheckOpenVINOStatus();
          window.clearInterval(interval);
        }
        if (result.status === "error") {
          setOpenvinoError(`${result.message}${result.error_tail ? `\n\n${result.error_tail}` : ""}`);
          setStartingOpenVINO(false);
          await handleCheckOpenVINOStatus();
          window.clearInterval(interval);
        }
      } catch (err) {
        setOpenvinoError(err instanceof Error ? err.message : "Failed to fetch OVMS start status");
        setStartingOpenVINO(false);
        window.clearInterval(interval);
      }
    }, 1500);
    return () => window.clearInterval(interval);
  }, [openvinoStartJobId, startingOpenVINO, handleCheckOpenVINOStatus]);

  const handleStopOpenVINOService = async () => {
    setStoppingOpenVINO(true);
    setOpenvinoStopJobId(null);
    setOpenvinoStopStatus("queued");
    setOpenvinoStopMessage("Queueing native OVMS stop...");
    setOpenvinoStopPercent(0);
    setOpenvinoMessage(null);
    setOpenvinoError(null);
    try {
      const result = await apiPost<{ job_id: string; status: string; stopped: boolean; message: string; percent: number; output?: string }>("/provider/openvino-stop", {});
      setOpenvinoStopJobId(result.job_id || null);
      setOpenvinoStopStatus(result.status);
      setOpenvinoStopMessage(result.message);
      setOpenvinoStopPercent(result.percent || 0);
      if (result.status === "complete" && result.stopped) {
        setOpenvinoMessage(result.message);
        setOpenvinoRunning(false);
        setStoppingOpenVINO(false);
      }
    } catch (err) {
      setOpenvinoError(err instanceof Error ? err.message : "Failed to stop OpenVINO Model Server");
      setStoppingOpenVINO(false);
    }
  };

  useEffect(() => {
    if (!openvinoStopJobId || !stoppingOpenVINO) return;
    const interval = window.setInterval(async () => {
      try {
        const result = await apiGet<{ status: string; stopped: boolean; message: string; percent: number; output?: string }>(`/provider/openvino-stop/${openvinoStopJobId}`);
        setOpenvinoStopStatus(result.status);
        setOpenvinoStopMessage(result.message);
        setOpenvinoStopPercent(result.percent || 0);
        if (result.status === "complete") {
          setOpenvinoMessage(result.message);
          setOpenvinoRunning(!result.stopped);
          setStoppingOpenVINO(false);
          await handleCheckOpenVINOStatus();
          window.clearInterval(interval);
        }
        if (result.status === "error") {
          setOpenvinoError(`${result.message}${result.output ? ` Details: ${result.output}` : ""}`);
          setStoppingOpenVINO(false);
          await handleCheckOpenVINOStatus();
          window.clearInterval(interval);
        }
      } catch (err) {
        setOpenvinoError(err instanceof Error ? err.message : "Failed to poll OVMS stop status");
        setStoppingOpenVINO(false);
        window.clearInterval(interval);
      }
    }, 1500);
    return () => window.clearInterval(interval);
  }, [openvinoStopJobId, stoppingOpenVINO, handleCheckOpenVINOStatus]);

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

  // Check local runtime status. These are lightweight health checks and support
  // local-runtime contention warnings even when a runtime is not the active provider.
  useEffect(() => {
    handleCheckFoundryStatus();
  }, [handleCheckFoundryStatus]);

  useEffect(() => {
    handleCheckOpenVINOStatus();
  }, [handleCheckOpenVINOStatus]);

  useEffect(() => {
    if (!providerInfo) return;

    const modelProvider = providerInfo.current.model_provider;
    const embeddingProvider = providerInfo.current.embedding_provider;
    const needsFoundry =
      modelProvider === "microsoft-foundry-local" ||
      embeddingProvider === "microsoft-foundry-local";
    const needsOpenVINO = modelProvider === "openvino" || embeddingProvider === "openvino";

    if (
      needsFoundry &&
      foundryInstalled === true &&
      !foundryServiceRunning &&
      !startingService &&
      !readinessStartedRef.current.foundry
    ) {
      readinessStartedRef.current.foundry = true;
      void handleStartFoundryService();
      setStartServiceMessage(
        "Active provider settings require Microsoft Foundry Local. Starting service and loading configured model(s)..."
      );
    }

    if (
      needsOpenVINO &&
      openvinoRunning === false &&
      !startingOpenVINO &&
      !readinessStartedRef.current.openvino
    ) {
      readinessStartedRef.current.openvino = true;
      void handleStartOpenVINOService();
      setOpenvinoStartMessage(
        "Active provider settings require OpenVINO. Starting OVMS and loading the configured model..."
      );
    }
  }, [
    providerInfo,
    foundryInstalled,
    foundryServiceRunning,
    startingService,
    openvinoRunning,
    startingOpenVINO,
  ]);

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

  if (!config) return null;

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

      {(hardwareStatus || hardwareJobStatus) && (
        <div className="rounded-md border p-4 text-sm">
          <div className="mb-2 flex items-center justify-between gap-3">
            <div className="font-semibold">Local hardware telemetry</div>
            <button
              onClick={handleCheckHardwareStatus}
              className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
              title="Refresh CPU/RAM/GPU/NPU and local AI process telemetry."
            >
              Refresh telemetry
            </button>
          </div>
          {hardwareJobStatus && hardwareJobStatus !== "complete" && (
            <div className="mb-3 rounded border border-blue-200 bg-blue-50 p-3 text-xs text-blue-900">
              <div className="mb-2 flex items-center justify-between gap-3">
                <span>{hardwareJobMessage || "Refreshing hardware telemetry..."}</span>
                <span className="font-mono">{hardwareJobPercent}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded bg-blue-100">
                <div className="h-full rounded bg-blue-600 transition-all" style={{ width: `${Math.min(100, Math.max(0, hardwareJobPercent))}%` }} />
              </div>
            </div>
          )}
          {hardwareStatus && (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
              <div className="rounded border bg-muted/20 p-3">
                <p className="text-xs text-muted-foreground">CPU</p>
                <p className="font-medium">{hardwareStatus.cpu.usage_percent ?? "?"}%</p>
                <p className="text-xs text-muted-foreground">{hardwareStatus.cpu.logical_cores} logical cores</p>
              </div>
              <div className="rounded border bg-muted/20 p-3">
                <p className="text-xs text-muted-foreground">Memory</p>
                <p className="font-medium">{hardwareStatus.memory.used_percent ?? "?"}% used</p>
                <p className="text-xs text-muted-foreground">{hardwareStatus.memory.available_gb ?? "?"} GB free / {hardwareStatus.memory.total_gb ?? "?"} GB total</p>
              </div>
              <div className="rounded border bg-muted/20 p-3">
                <p className="text-xs text-muted-foreground">GPU</p>
                <p className="font-medium">{hardwareStatus.gpu.usage_percent ?? "?"}%</p>
                <p className="text-xs text-muted-foreground break-all">{hardwareStatus.gpu.controllers?.[0]?.Name || "No GPU controller detected"}</p>
              </div>
              <div className="rounded border bg-muted/20 p-3">
                <p className="text-xs text-muted-foreground">NPU</p>
                <p className="font-medium">{hardwareStatus.npu.controllers.length > 0 ? "Detected" : "Not detected"}</p>
                <p className="text-xs text-muted-foreground break-all">{hardwareStatus.npu.controllers?.[0]?.FriendlyName || "No NPU device found"}</p>
                {hardwareStatus.npu.controllers.length > 0 && (
                  <p className="mt-1 text-xs text-muted-foreground">Memory telemetry unavailable via standard Windows counters</p>
                )}
              </div>
            </div>
          )}
          {hardwareStatus && hardwareStatus.local_ai_processes.length > 0 && (
            <div className="mt-3 rounded border bg-muted/20 p-3 text-xs">
              <p className="mb-1 font-medium">Local AI processes</p>
              <div className="flex flex-wrap gap-2">
                {hardwareStatus.local_ai_processes.map((p) => (
                  <span key={`${p.ProcessName}-${p.Id}`} className="rounded bg-background px-2 py-1 font-mono">
                    {p.ProcessName}#{p.Id}: {p.WorkingSetMB} MB
                  </span>
                ))}
              </div>
            </div>
          )}
          {hardwareStatus && (hardwareStatus.notes.length > 0 || (foundryServiceRunning && openvinoRunning)) && (
            <div className="mt-3 rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-950">
              {foundryServiceRunning && openvinoRunning && (
                <p className="mb-2">
                  Microsoft Foundry Local and OVMS are independent local runtimes. They can run at the same time, but they do not start or stop each other. If CPU/RAM/GPU/NPU usage is high, stop the unused runtime or switch to OpenAI/Placeholder.
                </p>
              )}
              {hardwareStatus.notes.map((note) => <p key={note}>{note}</p>)}
              <div className="mt-2 flex flex-wrap gap-2">
                {openvinoRunning && (
                  <button onClick={handleStopOpenVINOService} disabled={stoppingOpenVINO} className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-50">
                    {stoppingOpenVINO ? "Stopping OVMS..." : "Stop OVMS"}
                  </button>
                )}
                {foundryServiceRunning && (
                  <button onClick={handleStopFoundryService} disabled={stoppingFoundryService} className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-50">
                    {stoppingFoundryService ? "Stopping Microsoft Foundry..." : "Stop Microsoft Foundry Local"}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
      {hardwareError && (
        <div className="rounded-md border border-yellow-200 bg-yellow-50 p-3 text-xs text-yellow-900">
          Hardware telemetry unavailable: {hardwareError}
        </div>
      )}

      {effectiveModelProvider === "placeholder" && <Callout calloutId="placeholder_mode" />}

      {/* Provider Switcher */}
      {!providerInfo ? (
        <div className="rounded-md border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading provider details...
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Base configuration is available. Provider controls will appear as soon as the backend provider endpoint responds.
          </p>
        </div>
      ) : (
      <div className="rounded-md border p-4">
        <h3 className="mb-3 text-lg font-semibold">
          <Tooltip term="model_provider">Model Provider Switcher</Tooltip>
        </h3>
        <p className="mb-3 text-xs text-muted-foreground">
          Switch between providers to use different AI models for workflow execution.
          Previous observability data is preserved and tagged with the previous provider.
        </p>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
          {providerInfo.available_model_providers.map((p) => {
            const isActive = effectiveModelProvider === p.value;
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

        {switching && switchJobStatus && switchJobStatus !== "complete" && (
          <div className="mt-3 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
            <div className="mb-2 flex items-center justify-between gap-3">
              <span className="font-medium">{switchJobMessage || "Switching provider..."}</span>
              <span className="font-mono text-xs">{switchJobPercent}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded bg-blue-100">
              <div className="h-full rounded bg-blue-600 transition-all" style={{ width: `${Math.min(100, Math.max(0, switchJobPercent))}%` }} />
            </div>
            <p className="mt-2 text-xs">
              Status: <span className="font-mono">{switchJobStatus}</span>. Microsoft Foundry Local may need to start a local runtime process before the switch completes.
            </p>
          </div>
        )}

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
        {effectiveModelProvider === "openai" && (
          <div className="mt-4 rounded-md border p-4">
            <div className="mb-3 flex items-center gap-2">
              <Key className="h-4 w-4" />
              <h3 className="text-base font-semibold">OpenAI API Key & Model</h3>
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
                <h4 className="mb-2 text-base font-semibold">OpenAI Parameters</h4>
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

        {/* OpenVINO Model Server settings — shown only when the model provider uses openvino */}
        {effectiveModelProvider === "openvino" && (
          <div className="mt-4 space-y-3 rounded-md border p-4">
            <h4 className="text-base font-semibold">OpenVINO Model Server (shared local runtime)</h4>
            <p className="text-xs text-muted-foreground">
              You can mix and match providers. The text model below is used only when the Model Provider
              is OpenVINO; the embedding model below is used only when the Embedding Provider is OpenVINO.
              Both settings point at the same native Windows OVMS endpoint. Hugging Face tokens are optional for
              public OpenVINO models and only needed for gated, private, or rate-limit-free downloads.
            </p>

            <div className={`rounded-md border p-3 text-xs ${openvinoRunning ? "border-green-200 bg-green-50 text-green-900" : "border-yellow-200 bg-yellow-50 text-yellow-900"}`}>
              {openvinoRunning === true
                ? `✓ OVMS is responding at ${providerInfo.current.openvino_endpoint}`
                : `⚠ OVMS is not responding at ${providerInfo.current.openvino_endpoint || "http://localhost:8100"}. Start native OpenVINO Model Server before using OpenVINO providers.`}
            </div>

            <div className="rounded-md border bg-muted/30 p-3">
              <p className="text-xs font-medium text-muted-foreground">Native runtime and model/cache locations</p>
              <p className="mt-1 text-xs">
                Hugging Face downloads from the UI are cached under: <code className="rounded bg-muted px-1 font-mono break-all">{openvinoModelCacheDir || "(default Hugging Face cache)"}</code>
              </p>
              <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-3">
                <div className="rounded border bg-background p-2">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Selected text model</p>
                  <p className="break-all font-mono text-xs">{openvinoModel || providerInfo.current.openvino_model}</p>
                  <p className={openvinoModelCached ? "text-xs text-green-700" : "text-xs text-amber-700"}>
                    {openvinoModelCached ? "Cached in OVMS repository" : "Not detected in local OVMS repository"}
                  </p>
                </div>
                <div className="rounded border bg-background p-2">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Selected embedding model</p>
                  <p className="break-all font-mono text-xs">{openvinoEmbeddingModel || providerInfo.current.openvino_embedding_model}</p>
                  <p className={openvinoEmbeddingModelCached ? "text-xs text-green-700" : "text-xs text-amber-700"}>
                    {openvinoEmbeddingModelCached ? "Cached in OVMS repository" : "Not detected in local OVMS repository"}
                  </p>
                </div>
                <div className="rounded border bg-background p-2">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Currently served by OVMS</p>
                  <p className="break-all font-mono text-xs">{openvinoServedModel || "Unknown / not detected from logs"}</p>
                  <p className={openvinoServedModelMatchesSelection ? "text-xs text-green-700" : "text-xs text-amber-700"}>
                    {openvinoServedModelMatchesSelection ? "Matches selected text model" : "May not match the selected text model"}
                  </p>
                </div>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Runtime mode: <code className="rounded bg-muted px-1 font-mono">{openvinoRuntimeMode}</code>. Start/stop uses <code className="rounded bg-muted px-1 font-mono">{openvinoSetupScript}</code> so OVMS runs bare-metal on Windows with direct Intel NPU/GPU/CPU access.
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Latest package: OpenVINO Model Server {openvinoLatestRelease}.{" "}
                {openvinoWindowsDownloadUrl && <a className="text-primary underline" href={openvinoWindowsDownloadUrl} target="_blank" rel="noreferrer">Download Windows python_on zip</a>}
                {openvinoWindowsChecksumUrl && <> · <a className="text-primary underline" href={openvinoWindowsChecksumUrl} target="_blank" rel="noreferrer">SHA256</a></>}
                {openvinoBaremetalDocsUrl && <> · <a className="text-primary underline" href={openvinoBaremetalDocsUrl} target="_blank" rel="noreferrer">2026 bare-metal docs</a></>}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                If Start Native OVMS reports that <code className="rounded bg-muted px-1 font-mono">ovms.exe</code> is missing, either save the absolute path below or add its folder to <code className="rounded bg-muted px-1 font-mono">PATH</code> and restart the UI backend.
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Repository paths: text <code className="rounded bg-muted px-1 font-mono break-all">{openvinoModelRepositoryPath || "unknown"}</code>; embedding <code className="rounded bg-muted px-1 font-mono break-all">{openvinoEmbeddingModelRepositoryPath || "unknown"}</code>.
              </p>
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
                <p className="mt-1 text-xs text-muted-foreground">Default uses native Windows OVMS on port 8100 to avoid the mock Pricing API on port 8000.</p>
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
              <div className="md:col-span-2">
                <label className="mb-1 block text-xs font-medium">OVMS Executable Path</label>
                <input
                  type="text"
                  value={openvinoOvmsPath}
                  onChange={(e) => setOpenvinoOvmsPath(e.target.value)}
                  placeholder="Leave blank to use ovms.exe from PATH, or enter C:\\tools\\ovms\\2026.2.1\\ovms.exe"
                  className="w-full rounded-md border p-2 text-sm font-mono"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  Saved as <code className="rounded bg-muted px-1 font-mono">OPENVINO_OVMS_PATH</code>. Use this when the UI backend cannot find <code className="rounded bg-muted px-1 font-mono">ovms.exe</code> on PATH.
                </p>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">
                  Text Generation Model{" "}
                  <span className="text-muted-foreground">
                    {effectiveModelProvider === "openvino" ? "(active)" : "(saved for when Model Provider = OpenVINO)"}
                  </span>
                </label>
                <select
                  value={openvinoModel || providerInfo.current.openvino_model || "OpenVINO/Qwen3-8B-int4-cw-ov"}
                  onChange={(e) => setOpenvinoModel(e.target.value)}
                  className="w-full rounded-md border p-2 text-sm"
                >
                  {providerInfo.openvino_models.map((m) => (
                    <option key={m.alias} value={m.alias}>{m.npu_recommended === "true" ? "⚡ " : ""}{m.label} ({m.alias})</option>
                  ))}
                </select>
                {providerInfo.openvino_models.find((m) => m.alias === (openvinoModel || providerInfo.current.openvino_model)) && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    {providerInfo.openvino_models.find((m) => m.alias === (openvinoModel || providerInfo.current.openvino_model))?.serving_note}
                  </p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">
                  Embedding Model{" "}
                  <span className="text-muted-foreground">
                    {effectiveEmbeddingProvider === "openvino" ? "(active)" : "(saved for when Embedding Provider = OpenVINO)"}
                  </span>
                </label>
                <select
                  value={openvinoEmbeddingModel || providerInfo.current.openvino_embedding_model || "OpenVINO/Qwen3-Embedding-0.6B"}
                  onChange={(e) => setOpenvinoEmbeddingModel(e.target.value)}
                  className="w-full rounded-md border p-2 text-sm"
                >
                  {providerInfo.openvino_embedding_models.map((m) => (
                    <option key={m.alias} value={m.alias}>{m.npu_recommended === "true" ? "⚡ " : ""}{m.label} ({m.dimension}-dim)</option>
                  ))}
                </select>
                {providerInfo.openvino_embedding_models.find((m) => m.alias === (openvinoEmbeddingModel || providerInfo.current.openvino_embedding_model)) && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    {providerInfo.openvino_embedding_models.find((m) => m.alias === (openvinoEmbeddingModel || providerInfo.current.openvino_embedding_model))?.serving_note}
                  </p>
                )}
              </div>
            </div>

            <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-xs text-blue-900">
              <p className="font-medium">NPU-first serving behavior</p>
              <p className="mt-1">
                Models marked ⚡ are curated for NPU-first local inference. OVMS stores model files under the model repository/cache, then compiles and loads weights plus KV cache on the selected Target Device. Pre-cache is optional: it reduces first-start latency, but OVMS can also download/prepare the selected Hugging Face model during start.
              </p>
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
                title="Save endpoint, target device, selected models, optional ovms.exe path, and optional Hugging Face token to the local .env file. This does not start or stop OVMS."
              >
                {savingOpenVINO ? "Saving..." : "Save OpenVINO Settings"}
              </button>
              <button
                onClick={handleStartOpenVINOService}
                disabled={startingOpenVINO || stoppingOpenVINO}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                title="Start native OVMS if needed and load/serve the selected text model on the selected target device. If the model is not cached, OVMS may download and compile it during startup."
              >
                {startingOpenVINO ? "Starting / loading OVMS..." : "Start / Load OVMS"}
              </button>
              <button
                onClick={handleStopOpenVINOService}
                disabled={startingOpenVINO || stoppingOpenVINO}
                className="rounded-md border border-red-200 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                title="Stop the native OVMS process to free CPU/GPU/NPU memory, compiled model state, and LLM KV-cache resources."
              >
                {stoppingOpenVINO ? "Stopping native OVMS..." : "Stop Native OVMS"}
              </button>
              <button
                onClick={() => handleDownloadOpenVINOModel(openvinoModel || providerInfo.current.openvino_model)}
                disabled={downloadingOpenVINO}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
                title="Optional: downloads/caches the selected text model before starting OVMS. OVMS can also download it during start."
              >
                Pre-cache Text Model (optional)
              </button>
              <button
                onClick={() => handleDownloadOpenVINOModel(openvinoEmbeddingModel || providerInfo.current.openvino_embedding_model)}
                disabled={downloadingOpenVINO}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
                title="Optional: downloads/caches the selected embedding model before ingestion or embedding use."
              >
                Pre-cache Embedding Model (optional)
              </button>
              <button
                onClick={handleCheckOpenVINOStatus}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
                title="Refresh OVMS health, local cache detection, and served-model status. Useful after starting/stopping OVMS outside this page."
              >
                Refresh OVMS Status
              </button>
            </div>

            {startingOpenVINO && (
              <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="font-medium">{openvinoStartMessage || "Starting native OVMS..."}</span>
                  <span className="font-mono text-xs">{openvinoStartPercent}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded bg-blue-100">
                  <div className="h-full rounded bg-blue-600 transition-all" style={{ width: `${Math.min(100, Math.max(0, openvinoStartPercent))}%` }} />
                </div>
                <p className="mt-2 text-xs">
                  Status: <span className="font-mono">{openvinoStartStatus}</span>. Large NPU models may download, compile, and warm up for several minutes on first start.
                </p>
                {openvinoStartOutput.length > 0 && (
                  <pre className="mt-2 max-h-40 overflow-y-auto rounded bg-blue-100 p-2 text-xs text-blue-950 whitespace-pre-wrap">
                    {openvinoStartOutput.slice(-12).join("\n")}
                  </pre>
                )}
              </div>
            )}

            {stoppingOpenVINO && (
              <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="font-medium">{openvinoStopMessage || "Stopping native OVMS..."}</span>
                  <span className="font-mono text-xs">{openvinoStopPercent}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded bg-blue-100">
                  <div className="h-full rounded bg-blue-600 transition-all" style={{ width: `${Math.min(100, Math.max(0, openvinoStopPercent))}%` }} />
                </div>
                <p className="mt-2 text-xs">
                  Status: <span className="font-mono">{openvinoStopStatus}</span>. Stopping releases local runtime memory and device resources.
                </p>
              </div>
            )}

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

        {/* Microsoft Foundry Local model selector + params — only relevant when microsoft-foundry-local is active */}
        {config.categories["Model"] && effectiveModelProvider === "microsoft-foundry-local" && (
          <div className="mt-4 space-y-3">
            <h4 className="text-base font-semibold">Microsoft Foundry Local Model</h4>
            <p className="text-xs text-muted-foreground">
              Select a model from the Microsoft Foundry Local catalog. Use{" "}
              <code className="rounded bg-muted px-1">{"foundry model download <alias>"}</code> to download
              a model before selecting it here.
            </p>

            {/* Microsoft Foundry Local installation status */}
            {foundryInstalled === false && (
              <div className="rounded-md border border-yellow-200 bg-yellow-50 p-3">
                <p className="text-sm font-medium text-yellow-900">⚠️ Microsoft Foundry Local SDK is not available</p>
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
                    {installingFoundry ? "Installing... (this may take a few minutes)" : "Install Microsoft Foundry Local SDK"}
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
                {installingFoundry && (
                  <div className="mt-2 rounded-md border border-blue-200 bg-blue-50 p-2 text-xs text-blue-900">
                    <div className="mb-1 flex items-center justify-between gap-3">
                      <span>{installMessage || "Installing Microsoft Foundry Local SDK..."}</span>
                      <span className="font-mono">{installJobPercent}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded bg-blue-100">
                      <div className="h-full rounded bg-blue-600 transition-all" style={{ width: `${Math.min(100, Math.max(0, installJobPercent))}%` }} />
                    </div>
                    <p className="mt-1">Status: <span className="font-mono">{installJobStatus}</span></p>
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
                  ⚠️ Microsoft Foundry Local is installed but the service is not running.
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
                {(startingService || stoppingFoundryService) && (
                  <div className="mt-2 rounded-md border border-blue-200 bg-blue-50 p-2 text-xs text-blue-900">
                    <div className="mb-1 flex items-center justify-between gap-3">
                      <span>{startingService ? foundryModelJobMessage : startServiceMessage}</span>
                      <span className="font-mono">{startingService ? foundryModelJobPercent : foundryStopPercent}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded bg-blue-100">
                      <div className="h-full rounded bg-blue-600 transition-all" style={{ width: `${Math.min(100, Math.max(0, startingService ? foundryModelJobPercent : foundryStopPercent))}%` }} />
                    </div>
                    <p className="mt-1">Status: <span className="font-mono">{startingService ? foundryModelJobStatus : foundryStopStatus}</span></p>
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
                ✓ Microsoft Foundry Local is installed and running.
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
                <span className="text-muted-foreground">(from Microsoft Foundry Local catalog)</span>
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

            {savingFoundryModel && (
              <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="font-medium">{foundryModelJobMessage || "Loading Microsoft Foundry Local model..."}</span>
                  <span className="font-mono text-xs">{foundryModelJobPercent}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-blue-100">
                  <div className="h-full rounded-full bg-blue-600 transition-all" style={{ width: `${Math.max(0, Math.min(100, foundryModelJobPercent))}%` }} />
                </div>
                <p className="mt-2 text-xs text-blue-800">
                  Status: <span className="font-mono">{foundryModelJobStatus}</span>. The service and configured model(s) are prepared in a background job.
                </p>
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

            {/* Microsoft Foundry Local config params */}
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
      )}

      {/* Embedding Provider Switcher */}
      {!providerInfo ? (
        <div className="rounded-md border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading embedding provider details...
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Base embedding configuration is available. Provider controls will appear as soon as the backend provider endpoint responds.
          </p>
        </div>
      ) : (
      <div className="rounded-md border p-4">
        <h3 className="mb-3 text-lg font-semibold">
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
            <h4 className="mb-2 text-base font-semibold">Embeddings</h4>
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
      )}

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
