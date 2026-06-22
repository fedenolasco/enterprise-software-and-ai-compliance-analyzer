"use client";

import { useState } from "react";
import { Loader2, Workflow, Play, Check, X } from "lucide-react";
import { apiPost, type WorkflowState } from "@/lib/api";
import { PageIntro } from "@/components/common/PageIntro";
import { Callout } from "@/components/common/Callout";
import { CliEquivalent } from "@/components/common/CliEquivalent";

export default function WorkflowPage() {
  const [userQuery, setUserQuery] = useState("");
  const [softwareCode, setSoftwareCode] = useState("");
  const [requestedSeats, setRequestedSeats] = useState<number | "">("");
  const [workflowResult, setWorkflowResult] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // HITL form
  const [reviewer, setReviewer] = useState("");
  const [rationale, setRationale] = useState("");
  const [hitlLoading, setHitlLoading] = useState(false);

  const handleRun = async () => {
    if (!userQuery.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiPost<WorkflowState>("/workflow/run", {
        user_query: userQuery,
        pricing_software_code: softwareCode || null,
        pricing_requested_seats: requestedSeats || null,
      });
      setWorkflowResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow failed");
    } finally {
      setLoading(false);
    }
  };

  const handleHitl = async (outcome: string) => {
    if (!workflowResult?.thread_id) return;
    if (!reviewer.trim() || !rationale.trim()) {
      setError("Reviewer name and rationale are required for HITL decisions.");
      return;
    }
    setHitlLoading(true);
    setError(null);
    try {
      const data = await apiPost<WorkflowState>(
        `/workflow/hitl/${workflowResult.thread_id}`,
        { outcome, reviewer, rationale }
      );
      setWorkflowResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "HITL submission failed");
    } finally {
      setHitlLoading(false);
    }
  };

  const hitlPause = workflowResult?.hitl_pause as Record<string, unknown> | null;
  const isHitlRequired = hitlPause?.required === true;

  return (
    <div className="space-y-6">
      <PageIntro page="workflow" />

      <div className="flex items-center gap-2">
        <Workflow className="h-5 w-5" />
        <h2 className="text-2xl font-bold">Workflow & HITL</h2>
      </div>

      {/* Workflow input form */}
      <div className="rounded-md border p-4">
        <h3 className="mb-3 text-sm font-medium">Start Workflow</h3>
        <label className="mb-1 block text-xs font-medium">User Query</label>
        <textarea
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          placeholder="Enter the compliance question for the workflow..."
          className="mb-3 w-full rounded-md border p-3 text-sm"
          rows={2}
        />

        <div className="mb-3 flex gap-4">
          <div className="flex-1">
            <label className="mb-1 block text-xs font-medium">Pricing Software Code (optional)</label>
            <input
              value={softwareCode}
              onChange={(e) => setSoftwareCode(e.target.value)}
              placeholder="SW-OPENAI-CHATGPT-ENT"
              className="w-full rounded-md border p-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium">Requested Seats</label>
            <input
              type="number"
              value={requestedSeats}
              onChange={(e) => setRequestedSeats(e.target.value ? Number(e.target.value) : "")}
              placeholder="50"
              className="w-24 rounded-md border p-2 text-sm"
            />
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading || !userQuery.trim()}
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          Run Workflow
        </button>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          {error}
        </div>
      )}

      {/* Workflow result */}
      {workflowResult && (
        <div className="space-y-4">
          <div className="rounded-md border p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Workflow Status</h3>
              <span className="rounded bg-muted px-2 py-0.5 text-xs font-medium">
                {workflowResult.workflow_status}
              </span>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Thread ID: {workflowResult.thread_id}
            </p>
          </div>

          {/* HITL pause panel */}
          {isHitlRequired && (
            <div className="rounded-md border border-yellow-300 bg-yellow-50 p-4">
              <Callout calloutId="hitl_pause" />
              <div className="mt-4 space-y-3">
                <div>
                  <label className="mb-1 block text-xs font-medium">Reviewer Name</label>
                  <input
                    value={reviewer}
                    onChange={(e) => setReviewer(e.target.value)}
                    placeholder="Your name"
                    className="w-full rounded-md border p-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium">Rationale</label>
                  <textarea
                    value={rationale}
                    onChange={(e) => setRationale(e.target.value)}
                    placeholder="Why are you approving or rejecting this recommendation?"
                    className="w-full rounded-md border p-2 text-sm"
                    rows={2}
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleHitl("APPROVED")}
                    disabled={hitlLoading}
                    className="flex items-center gap-1.5 rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                  >
                    {hitlLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                    Approve
                  </button>
                  <button
                    onClick={() => handleHitl("REJECTED")}
                    disabled={hitlLoading}
                    className="flex items-center gap-1.5 rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                  >
                    <X className="h-4 w-4" />
                    Reject
                  </button>
                  <button
                    onClick={() => handleHitl("REVISION_REQUESTED")}
                    disabled={hitlLoading}
                    className="flex items-center gap-1.5 rounded-md border px-3 py-2 text-sm font-medium hover:bg-accent disabled:opacity-50"
                  >
                    Request Revision
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Final output */}
          {workflowResult.final_output && (
            <div className="rounded-md border border-green-300 bg-green-50 p-4">
              <h3 className="mb-2 text-sm font-medium text-green-900">Final Output</h3>
              <p className="text-sm text-green-800">{workflowResult.final_output}</p>
            </div>
          )}

          {/* State inspector */}
          <div className="rounded-md border p-4">
            <h3 className="mb-2 text-sm font-medium">State Inspector</h3>
            <pre className="overflow-x-auto rounded-md bg-muted/50 p-3 text-xs">
              {JSON.stringify(workflowResult.state, null, 2)}
            </pre>
          </div>

          {workflowResult.cli_equivalent && (
            <CliEquivalent command={workflowResult.cli_equivalent} />
          )}
        </div>
      )}
    </div>
  );
}
