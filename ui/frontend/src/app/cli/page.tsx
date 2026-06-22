"use client";

import { useState, useEffect } from "react";
import { Loader2, Terminal, Play } from "lucide-react";
import { apiGet, apiPost, type CliCommand, type CliRunResult } from "@/lib/api";
import { PageIntro } from "@/components/common/PageIntro";
import { Callout } from "@/components/common/Callout";
import { CliEquivalent } from "@/components/common/CliEquivalent";

export default function CliPage() {
  const [commands, setCommands] = useState<CliCommand[]>([]);
  const [selectedCommand, setSelectedCommand] = useState<string>("");
  const [args, setArgs] = useState<string>("");
  const [result, setResult] = useState<CliRunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<{ commands: CliCommand[] }>("/cli")
      .then((data) => {
        setCommands(data.commands);
        if (data.commands.length > 0) setSelectedCommand(data.commands[0].name);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load CLI commands"));
  }, []);

  const handleRun = async () => {
    if (!selectedCommand) return;
    setLoading(true);
    setError(null);
    try {
      const argList = args.trim() ? args.trim().split(/\s+/) : [];
      const data = await apiPost<CliRunResult>(`/cli/${selectedCommand}`, {
        command: selectedCommand,
        args: argList,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Command execution failed");
    } finally {
      setLoading(false);
    }
  };

  const selectedCmd = commands.find((c) => c.name === selectedCommand);

  return (
    <div className="space-y-6">
      <PageIntro page="cli" />

      <div className="flex items-center gap-2">
        <Terminal className="h-5 w-5" />
        <h2 className="text-2xl font-bold">CLI Command Launcher</h2>
      </div>

      {/* Command selection */}
      <div className="rounded-md border p-4">
        <h3 className="mb-3 text-sm font-medium">Select Command</h3>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          {commands.map((cmd) => (
            <button
              key={cmd.name}
              onClick={() => {
                setSelectedCommand(cmd.name);
                setArgs("");
              }}
              className={`rounded-md border p-3 text-left ${
                selectedCommand === cmd.name
                  ? "border-primary bg-primary/5"
                  : "hover:bg-accent"
              }`}
            >
              <p className="font-mono text-sm font-medium">{cmd.cli_name}</p>
              <p className="mt-1 text-xs text-muted-foreground">{cmd.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Arguments form */}
      {selectedCmd && (
        <div className="rounded-md border p-4">
          <h3 className="mb-3 text-sm font-medium">Arguments</h3>
          {selectedCmd.args && selectedCmd.args.length > 0 ? (
            <div className="space-y-2">
              {selectedCmd.args.map((arg) => (
                <div key={arg.name} className="text-xs">
                  <span className="font-mono font-medium">{arg.name}</span>
                  {arg.required && <span className="text-red-600"> *required</span>}
                  <span className="ml-2 text-muted-foreground">{arg.description}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">This command takes no arguments.</p>
          )}
          <div className="mt-3">
            <label className="mb-1 block text-xs font-medium">Arguments (space-separated)</label>
            <input
              value={args}
              onChange={(e) => setArgs(e.target.value)}
              placeholder={selectedCmd.args?.[0]?.name || "No arguments needed"}
              className="w-full rounded-md border p-2 font-mono text-sm"
            />
          </div>
          <button
            onClick={handleRun}
            disabled={loading}
            className="mt-3 flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            Run Command
          </button>
        </div>
      )}

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          {error}
        </div>
      )}

      {/* Output */}
      {result && (
        <div className="space-y-3">
          {<Callout calloutId="cli_executed" />}

          <div className="rounded-md border p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-medium">Output</h3>
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium ${
                  result.success
                    ? "bg-green-100 text-green-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                Exit Code: {result.exit_code}
              </span>
            </div>

            {result.cli_equivalent && <CliEquivalent command={result.cli_equivalent} />}

            {result.stdout && (
              <div className="mt-3">
                <p className="mb-1 text-xs font-medium text-muted-foreground">stdout:</p>
                <pre className="overflow-x-auto rounded-md bg-black p-3 text-xs text-green-400">
                  {result.stdout}
                </pre>
              </div>
            )}

            {result.stderr && (
              <div className="mt-3">
                <p className="mb-1 text-xs font-medium text-muted-foreground">stderr:</p>
                <pre className="overflow-x-auto rounded-md bg-black p-3 text-xs text-red-400">
                  {result.stderr}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
