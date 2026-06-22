/**
 * API client for the Compliance Analyzer UI backend.
 */

const API_BASE = "/api";

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail?.error || error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail?.error || error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { method: "DELETE" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail?.error || error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

// Type definitions for API responses

export interface ServiceHealth {
  name: string;
  status: "healthy" | "unhealthy" | "disabled" | "unknown";
  required: boolean;
  host: string;
  port: number | null;
  detail: string;
  remediation: string;
  checked_at: string;
}

export interface HealthSummary {
  services: ServiceHealth[];
  summary: {
    total: number;
    healthy: number;
    unhealthy: number;
    disabled: number;
  };
}

export interface ConfigParameter {
  name: string;
  value: string;
  category: string;
  description: string;
  editable: boolean;
  sensitive: boolean;
  is_none: boolean;
}

export interface ConfigResponse {
  parameters: ConfigParameter[];
  categories: Record<string, ConfigParameter[]>;
  model_provider: string;
  embedding_provider: string;
  phoenix_enabled: boolean;
  langfuse_enabled: boolean;
  foundry_local_configured: boolean;
  openai_configured: boolean;
}

export interface Vendor {
  vendorCode: string;
  name: string;
  country: string;
  aiRiskTier: string;
  aiProcessingPosture: string;
}

export interface Subscription {
  subscriptionCode: string;
  vendorCode: string;
  softwareCode: string;
  contractType: string;
  seats: number;
  annualCostUsd: number;
  renewalDate: string;
  status: string;
  owner: string;
}

export interface PricingRecord {
  vendor_code: string;
  vendor_name: string;
  software_code: string;
  software_name: string;
  currency: string;
  billing_cycle: string;
  list_unit_price_usd: number;
  annual_unit_price_usd: number;
  minimum_seats: number;
  included_support_tier: string;
  data_residency_available: boolean;
  enterprise_controls_available: boolean;
  notes: string;
}

export interface HybridRetrievalResult {
  vendor_name: string;
  software_name: string;
  subscription_code: string | null;
  annual_cost_usd: number | null;
  renewal_date: string | null;
  subscription_status: string | null;
  risk_tier: string | null;
  risk_category: string | null;
  risk_severity: string | null;
  evidence_excerpt: string | null;
  source_document: string | null;
  recommended_review_action: string;
  priority_score: number;
  vector_distance: number | null;
  matched_sources: string[];
}

export interface AuditEvent {
  eventType: string;
  status: string;
  actor: string;
  traceId: string;
  message: string;
  detail: Record<string, unknown>;
  createdAt: string;
}

export interface CliCommand {
  name: string;
  cli_name: string;
  description: string;
  args: Array<{
    name: string;
    required: boolean;
    description: string;
  }>;
}

export interface CliRunResult {
  command: string;
  cli_equivalent: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  success: boolean;
}

export interface WorkflowState {
  thread_id: string;
  state: Record<string, unknown>;
  workflow_status: string;
  hitl_pause: Record<string, unknown> | null;
  final_output: string | null;
  cli_equivalent?: string;
}
